"""
Brand Voice Evaluator for LLM Content Quality Evaluator.
Measures adherence to brand guidelines including tone, terminology, and style.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class TerminologyScore:
    """Terminology compliance result."""
    score: float
    preferred_used: List[str] = field(default_factory=list)
    preferred_missed: List[str] = field(default_factory=list)
    prohibited_found: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ToneScore:
    """Tone analysis result."""
    score: float
    formality_level: str  # formal, neutral, casual
    sentiment: str  # positive, neutral, negative
    energy_level: str  # enthusiastic, measured, reserved
    perspective: str  # first, second, third
    perspective_consistency: float
    issues: List[str] = field(default_factory=list)


@dataclass
class StyleScore:
    """Style compliance result."""
    score: float
    sentence_length_issues: List[str] = field(default_factory=list)
    capitalization_issues: List[str] = field(default_factory=list)
    number_format_issues: List[str] = field(default_factory=list)


@dataclass
class BrandVoiceScore:
    """Brand voice evaluation result."""
    score: float
    terminology_score: float
    tone_score: float
    style_score: float
    voice_consistency_score: float
    preferred_used: List[str] = field(default_factory=list)
    preferred_missed: List[str] = field(default_factory=list)
    prohibited_found: List[Dict[str, Any]] = field(default_factory=list)
    tone_issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class BrandVoiceEvaluator:
    """
    Evaluates brand voice consistency against provided guidelines.

    Components:
    1. Terminology compliance (30%): Required/prohibited terms
    2. Tone alignment (25%): Sentiment and formality matching
    3. Style guide adherence (25%): Structural rules
    4. Voice consistency (20%): Uniformity across content
    """

    # Default prohibited phrases (common marketing hyperbole)
    DEFAULT_PROHIBITED = [
        "best in class", "world's first", "revolutionary", "game-changing",
        "unbeatable", "unprecedented", "groundbreaking", "cutting-edge",
        "state-of-the-art", "industry-leading", "world-class", "one-of-a-kind",
        "second to none", "unparalleled", "unrivaled"
    ]

    # Formality indicators
    FORMAL_INDICATORS = [
        "therefore", "furthermore", "consequently", "subsequently",
        "nevertheless", "notwithstanding", "pursuant", "heretofore",
        "whereas", "hereby"
    ]

    CASUAL_INDICATORS = [
        "awesome", "cool", "amazing", "super", "totally", "gonna",
        "wanna", "gotta", "hey", "wow", "yay", "yeah", "nope"
    ]

    # Sentiment indicators
    POSITIVE_WORDS = [
        "excellent", "outstanding", "perfect", "wonderful", "great",
        "fantastic", "superb", "exceptional", "remarkable", "premium"
    ]

    NEGATIVE_WORDS = [
        "poor", "bad", "terrible", "awful", "disappointing", "mediocre",
        "inferior", "subpar", "weak", "lacking"
    ]

    def __init__(self, brand_guidelines: Optional[Dict] = None):
        """Initialize the brand voice evaluator."""
        self.guidelines = brand_guidelines or {}
        self._init_from_guidelines()

    def _init_from_guidelines(self):
        """Initialize settings from brand guidelines."""
        terminology = self.guidelines.get("terminology", {})
        self.preferred_terms = terminology.get("preferred", {})
        self.prohibited_terms = terminology.get("prohibited", self.DEFAULT_PROHIBITED)

        voice = self.guidelines.get("voice_attributes", {})
        self.target_tone = voice.get("tone", "professional yet approachable")
        self.target_perspective = voice.get("perspective", "second person")

        style = self.guidelines.get("style_rules", {})
        self.max_sentence_length = style.get("sentence_length", {}).get("max", 25)
        self.ideal_sentence_length = style.get("sentence_length", {}).get("ideal", 15)

    def check_terminology(self, content: str) -> TerminologyScore:
        """
        Check for required and prohibited terms.

        Returns:
        - score: 0-100
        - preferred_used: list of preferred terms found
        - preferred_missed: list of preferred terms that could have been used
        - prohibited_found: list of prohibited terms (with locations)
        """
        content_lower = content.lower()
        preferred_used = []
        preferred_missed = []
        prohibited_found = []

        # Check prohibited terms
        for term in self.prohibited_terms:
            pattern = re.compile(r'\b' + re.escape(term.lower()) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(content_lower))
            if matches:
                for match in matches:
                    prohibited_found.append({
                        "term": term,
                        "location": match.start(),
                        "context": content[max(0, match.start()-20):match.end()+20]
                    })

        # Check preferred term usage
        for original, preferred in self.preferred_terms.items():
            original_lower = original.lower()
            preferred_lower = preferred.lower()

            # Check if original term is used
            if original_lower in content_lower:
                # Check if preferred version is also used
                if preferred_lower not in content_lower:
                    preferred_missed.append({
                        "original": original,
                        "preferred": preferred
                    })
                else:
                    preferred_used.append(preferred)
            elif preferred_lower in content_lower:
                preferred_used.append(preferred)

        # Calculate score
        prohibited_penalty = min(50, len(prohibited_found) * 15)  # Up to 50% penalty
        preferred_penalty = min(20, len(preferred_missed) * 5)  # Up to 20% penalty
        score = max(0, 100 - prohibited_penalty - preferred_penalty)

        return TerminologyScore(
            score=score,
            preferred_used=preferred_used,
            preferred_missed=[p["original"] for p in preferred_missed],
            prohibited_found=prohibited_found
        )

    def analyze_tone(self, content: str) -> ToneScore:
        """
        Analyze content tone against brand specifications.

        Checks:
        - Formality level (formal/casual/neutral)
        - Sentiment (positive/neutral/negative)
        - Energy level (enthusiastic/measured/reserved)
        - Perspective consistency (first/second/third person)
        """
        content_lower = content.lower()
        words = content_lower.split()
        issues = []

        # Analyze formality
        formal_count = sum(1 for word in words if word in self.FORMAL_INDICATORS)
        casual_count = sum(1 for word in words if word in self.CASUAL_INDICATORS)

        if formal_count > casual_count * 2:
            formality = "formal"
        elif casual_count > formal_count * 2:
            formality = "casual"
        else:
            formality = "neutral"

        # Check formality against target
        target_formality = "neutral"
        if "professional" in self.target_tone.lower():
            target_formality = "formal"
        elif "casual" in self.target_tone.lower() or "friendly" in self.target_tone.lower():
            target_formality = "casual"

        if formality != target_formality and formality != "neutral":
            issues.append(f"Tone is too {formality}, expected {target_formality}")

        # Analyze sentiment
        positive_count = sum(1 for word in words if word in self.POSITIVE_WORDS)
        negative_count = sum(1 for word in words if word in self.NEGATIVE_WORDS)

        if positive_count > negative_count * 3:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Analyze energy level
        exclamation_count = content.count('!')
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)

        if exclamation_count > 3 or caps_ratio > 0.1:
            energy = "enthusiastic"
        elif exclamation_count == 0 and positive_count < 2:
            energy = "reserved"
        else:
            energy = "measured"

        # Analyze perspective
        first_person = len(re.findall(r'\b(I|we|our|us|my)\b', content, re.IGNORECASE))
        second_person = len(re.findall(r'\b(you|your|yours)\b', content, re.IGNORECASE))
        third_person = len(re.findall(r'\b(they|their|it|its|he|she|him|her)\b', content, re.IGNORECASE))

        total_perspective = first_person + second_person + third_person
        if total_perspective == 0:
            perspective = "neutral"
            consistency = 1.0
        else:
            if second_person > first_person and second_person > third_person:
                perspective = "second"
                consistency = second_person / total_perspective
            elif first_person > second_person and first_person > third_person:
                perspective = "first"
                consistency = first_person / total_perspective
            else:
                perspective = "third"
                consistency = third_person / total_perspective

        # Check perspective against target
        target_perspective = "second"
        if "first person" in self.target_perspective.lower():
            target_perspective = "first"
        elif "third person" in self.target_perspective.lower():
            target_perspective = "third"

        if perspective != target_perspective and perspective != "neutral":
            issues.append(f"Uses {perspective} person, expected {target_perspective} person")

        # Calculate score
        score = 100
        if formality != target_formality and formality != "neutral":
            score -= 15
        if sentiment == "negative":
            score -= 20
        if energy == "enthusiastic" and "professional" in self.target_tone.lower():
            score -= 10
        if perspective != target_perspective and perspective != "neutral":
            score -= 15
        score -= (1 - consistency) * 20  # Penalty for inconsistent perspective

        return ToneScore(
            score=max(0, score),
            formality_level=formality,
            sentiment=sentiment,
            energy_level=energy,
            perspective=perspective,
            perspective_consistency=round(consistency, 2),
            issues=issues
        )

    def check_style_rules(self, content: str) -> StyleScore:
        """
        Check adherence to style rules.

        Checks:
        - Sentence length limits
        - Capitalization rules
        - Number formatting
        """
        issues_sentence = []
        issues_capitalization = []
        issues_numbers = []

        # Analyze sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count > self.max_sentence_length:
                issues_sentence.append(
                    f"Sentence too long ({word_count} words): '{sentence[:50]}...'"
                )

        # Check capitalization
        # Look for ALL CAPS words (excluding common acronyms)
        caps_words = re.findall(r'\b[A-Z]{3,}\b', content)
        common_acronyms = {'USB', 'LED', 'LCD', 'HD', 'GPS', 'WIFI', 'OLED', 'RAM', 'SSD', 'GB', 'TB', 'MB', 'HZ'}
        for word in caps_words:
            if word not in common_acronyms:
                issues_capitalization.append(f"Unnecessary all-caps: '{word}'")

        # Check number formatting (spell out 1-9)
        small_digits = re.findall(r'\b[1-9]\b(?!\d)', content)
        for digit in small_digits:
            # Skip if part of a measurement or version
            context = content[max(0, content.find(digit)-5):content.find(digit)+10]
            if not re.search(r'(\d+\.|\.\d+|v\d|version)', context, re.IGNORECASE):
                issues_numbers.append(f"Number '{digit}' should be spelled out")

        # Calculate score
        sentence_penalty = min(30, len(issues_sentence) * 10)
        caps_penalty = min(15, len(issues_capitalization) * 5)
        number_penalty = min(10, len(issues_numbers) * 2)

        score = max(0, 100 - sentence_penalty - caps_penalty - number_penalty)

        return StyleScore(
            score=score,
            sentence_length_issues=issues_sentence[:5],  # Limit to 5
            capitalization_issues=issues_capitalization[:5],
            number_format_issues=issues_numbers[:5]
        )

    def evaluate(self, content: str) -> BrandVoiceScore:
        """
        Main evaluation method.

        Returns composite brand voice score with breakdown.
        """
        # Combine content if it's a dict
        if isinstance(content, dict):
            text_parts = []
            for field in ['description', 'marketing_copy', 'meta_description']:
                if field in content and content[field]:
                    text_parts.append(str(content[field]))
            if 'feature_bullets' in content and content['feature_bullets']:
                if isinstance(content['feature_bullets'], list):
                    text_parts.extend(content['feature_bullets'])
                else:
                    text_parts.append(str(content['feature_bullets']))
            content = " ".join(text_parts)

        # Run component evaluations
        term_score = self.check_terminology(content)
        tone_score = self.analyze_tone(content)
        style_score = self.check_style_rules(content)

        # Calculate voice consistency
        # (Check consistency across different parts of content)
        consistency_score = self._calculate_consistency(content)

        # Calculate weighted composite score
        composite = (
            term_score.score * 0.30 +
            tone_score.score * 0.25 +
            style_score.score * 0.25 +
            consistency_score * 0.20
        )

        # Collect all issues
        all_issues = []
        if term_score.prohibited_found:
            all_issues.extend([f"Prohibited phrase: '{p['term']}'" for p in term_score.prohibited_found])
        all_issues.extend(tone_score.issues)
        all_issues.extend(style_score.sentence_length_issues)
        all_issues.extend(style_score.capitalization_issues)

        return BrandVoiceScore(
            score=round(composite, 2),
            terminology_score=round(term_score.score, 2),
            tone_score=round(tone_score.score, 2),
            style_score=round(style_score.score, 2),
            voice_consistency_score=round(consistency_score, 2),
            preferred_used=term_score.preferred_used,
            preferred_missed=term_score.preferred_missed,
            prohibited_found=term_score.prohibited_found,
            tone_issues=all_issues,
            details={
                "formality": tone_score.formality_level,
                "sentiment": tone_score.sentiment,
                "energy": tone_score.energy_level,
                "perspective": tone_score.perspective,
                "perspective_consistency": tone_score.perspective_consistency,
                "style_issues": {
                    "sentence_length": style_score.sentence_length_issues,
                    "capitalization": style_score.capitalization_issues,
                    "numbers": style_score.number_format_issues
                }
            }
        )

    def _calculate_consistency(self, content: str) -> float:
        """Calculate voice consistency across content."""
        # Split content into paragraphs/sections
        sections = re.split(r'\n\n+', content)
        if len(sections) < 2:
            return 100.0

        # Analyze tone of each section
        tones = []
        for section in sections:
            if len(section) > 20:
                tone = self.analyze_tone(section)
                tones.append({
                    "formality": tone.formality_level,
                    "sentiment": tone.sentiment,
                    "perspective": tone.perspective
                })

        if len(tones) < 2:
            return 100.0

        # Check consistency
        consistency_score = 100

        # Formality consistency
        formalities = [t["formality"] for t in tones]
        if len(set(formalities)) > 1:
            consistency_score -= 15

        # Sentiment consistency
        sentiments = [t["sentiment"] for t in tones]
        if "negative" in sentiments and "positive" in sentiments:
            consistency_score -= 20

        # Perspective consistency
        perspectives = [t["perspective"] for t in tones]
        if len(set(perspectives) - {"neutral"}) > 1:
            consistency_score -= 15

        return max(0, consistency_score)

    def update_guidelines(self, guidelines: Dict) -> None:
        """Update brand guidelines."""
        self.guidelines = guidelines
        self._init_from_guidelines()
