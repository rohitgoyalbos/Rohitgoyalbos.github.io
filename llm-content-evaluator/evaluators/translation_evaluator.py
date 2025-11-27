"""
Translation Evaluator for LLM Content Quality Evaluator.
Evaluates translation quality across multiple dimensions.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from config import TRANSLATION_LENGTH_RATIOS


@dataclass
class LengthScore:
    """Length ratio analysis result."""
    score: float
    source_length: int
    target_length: int
    actual_ratio: float
    expected_min: float
    expected_max: float
    within_range: bool


@dataclass
class TerminologyScore:
    """Terminology consistency result."""
    score: float
    correct_terms: List[str] = field(default_factory=list)
    incorrect_terms: List[Dict[str, str]] = field(default_factory=list)
    missing_terms: List[str] = field(default_factory=list)


@dataclass
class LocaleScore:
    """Locale-specific rule compliance result."""
    score: float
    issues: List[str] = field(default_factory=list)
    locale: str = ""


@dataclass
class TranslationScore:
    """Translation quality evaluation result."""
    score: float
    length_score: float
    terminology_score: float
    locale_score: float
    semantic_score: float
    errors: List[str] = field(default_factory=list)
    terminology_issues: List[Dict[str, str]] = field(default_factory=list)
    locale_issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class TranslationEvaluator:
    """
    Evaluates translation quality using multiple approaches.

    Since we can't use COMET in the prototype (requires model download),
    we implement alternative metrics:

    1. Length ratio analysis (source vs target)
    2. Terminology consistency checking
    3. Locale-specific rule checking
    4. Basic semantic similarity estimation
    """

    # Common false friends / mistranslations to check
    FALSE_FRIENDS = {
        "es": {
            "embarrassed": "avergonzado",  # NOT embarazada (pregnant)
            "actually": "realmente",  # NOT actualmente (currently)
            "realize": "darse cuenta",  # NOT realizar (to carry out)
            "sensible": "sensato",  # NOT sensible (sensitive)
        },
        "fr": {
            "actually": "en fait",  # NOT actuellement (currently)
            "demand": "exiger",  # NOT demander (to ask)
            "library": "bibliothèque",  # NOT librairie (bookstore)
        },
        "de": {
            "become": "werden",  # NOT bekommen (to get)
            "gift": "Geschenk",  # NOT Gift (poison)
        }
    }

    # Locale-specific punctuation rules
    LOCALE_RULES = {
        "fr": {
            "space_before_punctuation": [";", ":", "!", "?"],
            "quote_style": ["«", "»"],
        },
        "fr-ca": {
            "no_space_before_punctuation": True,  # Quebec differs from France
            "terminology": {
                "email": "courriel",
                "computer": "ordinateur",
                "shopping": "magasinage",
            }
        },
        "de": {
            "noun_capitalization": True,
            "compound_words": True,
        },
        "es": {
            "inverted_punctuation": ["¿", "¡"],
            "accents_required": True,
        }
    }

    def __init__(self, terminology_glossary: Optional[Dict] = None):
        """Initialize the translation evaluator."""
        self.glossary = terminology_glossary or {}

    def check_length_ratio(
        self,
        source: str,
        translation: str,
        lang_pair: str
    ) -> LengthScore:
        """
        Check if translation length is within expected ratio.

        Expected ratios:
        - EN→FR: 1.15-1.25 (French typically 15-25% longer)
        - EN→ES: 1.15-1.25
        - EN→DE: 1.10-1.30 (German compounds can be longer)
        - EN→SV: 0.95-1.10
        """
        source_length = len(source.split())
        target_length = len(translation.split())

        if source_length == 0:
            return LengthScore(
                score=0,
                source_length=0,
                target_length=target_length,
                actual_ratio=0,
                expected_min=1.0,
                expected_max=1.0,
                within_range=False
            )

        actual_ratio = target_length / source_length

        # Get expected ratio
        ratios = TRANSLATION_LENGTH_RATIOS.get(lang_pair, {"min": 0.9, "max": 1.3})
        expected_min = ratios["min"]
        expected_max = ratios["max"]

        within_range = expected_min <= actual_ratio <= expected_max

        # Calculate score
        if within_range:
            score = 100
        else:
            # Calculate how far off we are
            if actual_ratio < expected_min:
                deviation = expected_min - actual_ratio
            else:
                deviation = actual_ratio - expected_max

            score = max(0, 100 - (deviation * 100))

        return LengthScore(
            score=score,
            source_length=source_length,
            target_length=target_length,
            actual_ratio=round(actual_ratio, 2),
            expected_min=expected_min,
            expected_max=expected_max,
            within_range=within_range
        )

    def check_terminology_consistency(
        self,
        source: str,
        translation: str,
        glossary: Optional[Dict] = None
    ) -> TerminologyScore:
        """
        Verify that glossary terms are translated correctly.

        Returns:
        - score: 0-100
        - correct_terms: list
        - incorrect_terms: list with expected vs actual
        - missing_terms: list
        """
        glossary = glossary or self.glossary

        if not glossary:
            return TerminologyScore(score=100)

        source_lower = source.lower()
        translation_lower = translation.lower()

        correct = []
        incorrect = []
        missing = []

        for source_term, expected_translation in glossary.items():
            source_term_lower = source_term.lower()
            expected_lower = expected_translation.lower()

            # Check if source term is in source text
            if source_term_lower in source_lower:
                # Check if expected translation is in translation
                if expected_lower in translation_lower:
                    correct.append(source_term)
                else:
                    # Term exists in source but translation might be wrong
                    missing.append(source_term)

        # Calculate score
        total_terms = len(correct) + len(incorrect) + len(missing)
        if total_terms == 0:
            score = 100
        else:
            score = (len(correct) / total_terms) * 100

        return TerminologyScore(
            score=score,
            correct_terms=correct,
            incorrect_terms=incorrect,
            missing_terms=missing
        )

    def check_locale_rules(
        self,
        translation: str,
        target_locale: str
    ) -> LocaleScore:
        """
        Check locale-specific formatting rules.

        FR-CA specific:
        - No spaces before punctuation (unlike FR-FR)
        - Quebec terminology (courriel, not email)

        ES specific:
        - Opening inverted punctuation (¿ ¡)
        - Proper accent usage

        DE specific:
        - Noun capitalization
        - Proper compound formation
        """
        issues = []
        score = 100

        rules = self.LOCALE_RULES.get(target_locale, {})

        # Check French rules
        if target_locale == "fr":
            # French (France) requires space before certain punctuation
            for punct in rules.get("space_before_punctuation", []):
                pattern = r'\w' + re.escape(punct)
                if re.search(pattern, translation):
                    issues.append(f"Missing space before '{punct}' (French rule)")
                    score -= 5

        # Check French Canadian rules
        elif target_locale == "fr-ca":
            # Quebec doesn't use space before punctuation
            if rules.get("no_space_before_punctuation"):
                for punct in [";", ":", "!", "?"]:
                    pattern = r'\s' + re.escape(punct)
                    if re.search(pattern, translation):
                        issues.append(f"Unexpected space before '{punct}' (Quebec French)")
                        score -= 3

            # Check terminology
            terminology = rules.get("terminology", {})
            for english, french_ca in terminology.items():
                if english.lower() in translation.lower():
                    if french_ca.lower() not in translation.lower():
                        issues.append(f"Use Quebec term '{french_ca}' instead of '{english}'")
                        score -= 5

        # Check Spanish rules
        elif target_locale == "es":
            # Check for inverted punctuation
            if "?" in translation and "¿" not in translation:
                issues.append("Missing inverted question mark (¿)")
                score -= 5
            if "!" in translation and "¡" not in translation:
                issues.append("Missing inverted exclamation mark (¡)")
                score -= 5

        # Check German rules
        elif target_locale == "de":
            # Check noun capitalization (simplified check)
            # German nouns should be capitalized
            words = translation.split()
            lowercase_nouns = []
            for word in words:
                # Skip first word and common words
                if word == words[0]:
                    continue
                # Check for potentially uncapitalized nouns (simplified)
                if word.lower() in ["produkt", "qualität", "gerät", "design"]:
                    if word[0].islower():
                        lowercase_nouns.append(word)

            if lowercase_nouns:
                issues.append(f"Nouns should be capitalized in German: {', '.join(lowercase_nouns[:3])}")
                score -= 10

        return LocaleScore(
            score=max(0, score),
            issues=issues,
            locale=target_locale
        )

    def estimate_semantic_similarity(
        self,
        source: str,
        translation: str
    ) -> float:
        """
        Estimate semantic similarity using simple heuristics.

        In production, this would use multilingual sentence embeddings.
        For the prototype, we use proxy metrics:
        - Number preservation
        - Named entity preservation
        - Structure similarity
        """
        score = 100

        # Check number preservation
        source_numbers = re.findall(r'\d+(?:\.\d+)?', source)
        translation_numbers = re.findall(r'\d+(?:\.\d+)?', translation)

        if source_numbers:
            preserved = sum(1 for n in source_numbers if n in translation_numbers)
            preservation_rate = preserved / len(source_numbers)
            if preservation_rate < 1:
                score -= (1 - preservation_rate) * 30

        # Check for untranslated English words (potential issues)
        common_english = ['the', 'and', 'or', 'is', 'are', 'this', 'that', 'with', 'for']
        translation_lower = translation.lower()

        # Only flag if these appear mid-sentence (not at boundaries)
        untranslated = []
        for word in common_english:
            if f" {word} " in translation_lower:
                untranslated.append(word)

        if len(untranslated) > 2:
            score -= min(20, len(untranslated) * 5)

        # Check structure similarity (bullet points, paragraphs)
        source_bullets = len(re.findall(r'(?:•|·|\*|-)\s', source))
        trans_bullets = len(re.findall(r'(?:•|·|\*|-)\s', translation))

        if source_bullets > 0 and trans_bullets == 0:
            score -= 10  # Lost structure

        return max(0, score)

    def evaluate(
        self,
        source: str,
        translation: str,
        source_lang: str = "en",
        target_lang: str = "fr"
    ) -> TranslationScore:
        """
        Main evaluation method.

        Returns TranslationScore with:
        - score: 0-100
        - length_score: length ratio assessment
        - terminology_score: glossary compliance
        - locale_score: locale rule compliance
        - semantic_score: meaning preservation estimate
        - errors: list of specific issues found
        """
        # Handle dict content
        if isinstance(source, dict):
            source_text = " ".join([
                str(source.get('description', '')),
                str(source.get('marketing_copy', '')),
                " ".join(source.get('feature_bullets', []) if isinstance(source.get('feature_bullets'), list) else [])
            ])
        else:
            source_text = source

        if isinstance(translation, dict):
            translation_text = " ".join([
                str(translation.get('description', '')),
                str(translation.get('marketing_copy', '')),
                " ".join(translation.get('feature_bullets', []) if isinstance(translation.get('feature_bullets'), list) else [])
            ])
        else:
            translation_text = translation

        # Build language pair key
        lang_pair = f"{source_lang}-{target_lang}"

        # Run component evaluations
        length_result = self.check_length_ratio(source_text, translation_text, lang_pair)
        terminology_result = self.check_terminology_consistency(source_text, translation_text)
        locale_result = self.check_locale_rules(translation_text, target_lang)
        semantic_score = self.estimate_semantic_similarity(source_text, translation_text)

        # Collect errors
        errors = []
        if not length_result.within_range:
            errors.append(
                f"Translation length ratio ({length_result.actual_ratio:.2f}) "
                f"outside expected range ({length_result.expected_min}-{length_result.expected_max})"
            )

        errors.extend([f"Terminology: {term}" for term in terminology_result.missing_terms])
        errors.extend(locale_result.issues)

        # Calculate composite score
        composite = (
            length_result.score * 0.25 +
            terminology_result.score * 0.25 +
            locale_result.score * 0.25 +
            semantic_score * 0.25
        )

        return TranslationScore(
            score=round(composite, 2),
            length_score=round(length_result.score, 2),
            terminology_score=round(terminology_result.score, 2),
            locale_score=round(locale_result.score, 2),
            semantic_score=round(semantic_score, 2),
            errors=errors,
            terminology_issues=[
                {"term": t, "status": "missing"}
                for t in terminology_result.missing_terms
            ],
            locale_issues=locale_result.issues,
            details={
                "source_word_count": length_result.source_length,
                "target_word_count": length_result.target_length,
                "length_ratio": length_result.actual_ratio,
                "lang_pair": lang_pair,
                "correct_terms": terminology_result.correct_terms,
                "locale": target_lang
            }
        )

    def evaluate_all_translations(
        self,
        source: str,
        translations: Dict[str, str],
        source_lang: str = "en"
    ) -> Dict[str, TranslationScore]:
        """Evaluate multiple translations at once."""
        results = {}
        for target_lang, translation in translations.items():
            results[target_lang] = self.evaluate(
                source, translation, source_lang, target_lang
            )
        return results
