"""
Readability Evaluator for LLM Content Quality Evaluator.
Assesses content readability and accessibility using established metrics.
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from config import READABILITY_TARGETS


@dataclass
class SentenceAnalysis:
    """Sentence-level analysis result."""
    avg_sentence_length: float
    sentence_length_variance: float
    total_sentences: int
    long_sentences: List[str] = field(default_factory=list)
    very_long_sentences: List[str] = field(default_factory=list)


@dataclass
class VocabularyAnalysis:
    """Vocabulary complexity analysis result."""
    avg_word_length: float
    avg_syllables_per_word: float
    complex_word_count: int
    complex_word_percentage: float
    jargon_detected: List[str] = field(default_factory=list)
    passive_voice_instances: List[str] = field(default_factory=list)


@dataclass
class ReadabilityScore:
    """Readability evaluation result."""
    score: float  # Normalized 0-100
    flesch_ease: float  # Raw Flesch Reading Ease score
    flesch_grade: float  # Flesch-Kincaid Grade Level
    gunning_fog: float  # Gunning Fog Index
    smog_index: float  # SMOG Index
    avg_sentence_length: float
    avg_word_length: float
    complex_word_count: int
    long_sentences: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class ReadabilityEvaluator:
    """
    Evaluates content readability using established metrics.

    Primary metric: Flesch Reading Ease
    Target range: 60-80 (8th-9th grade level)

    Secondary metrics:
    - Flesch-Kincaid Grade Level
    - Gunning Fog Index
    - SMOG Index
    - Average sentence length
    - Average syllables per word
    """

    # Common jargon/technical terms that may confuse general readers
    JARGON_TERMS = [
        "synergy", "leverage", "optimize", "paradigm", "holistic",
        "scalable", "bandwidth", "ecosystem", "disruptive", "pivot",
        "iterate", "granular", "deliverable", "actionable", "stakeholder",
        "value-add", "core competency", "best practice", "bleeding edge"
    ]

    # Passive voice indicators
    PASSIVE_PATTERNS = [
        r'\b(?:is|are|was|were|been|being)\s+\w+ed\b',
        r'\b(?:is|are|was|were)\s+\w+en\b',
        r'\b(?:has|have|had)\s+been\s+\w+ed\b'
    ]

    def __init__(self, target_audience: str = "general"):
        """Initialize the readability evaluator."""
        self.targets = READABILITY_TARGETS.get(target_audience, READABILITY_TARGETS["general"])

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word using a simple heuristic."""
        word = word.lower().strip()
        if len(word) <= 3:
            return 1

        # Remove trailing 'e' (usually silent)
        if word.endswith('e'):
            word = word[:-1]

        # Count vowel groups
        vowels = 'aeiouy'
        count = 0
        prev_is_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel

        # Handle special cases
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1

        return max(1, count)

    def _get_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]

    def _get_words(self, text: str) -> List[str]:
        """Extract words from text."""
        return re.findall(r'\b[a-zA-Z]+\b', text.lower())

    def calculate_flesch_reading_ease(self, text: str) -> float:
        """
        Calculate Flesch Reading Ease score.

        Formula: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)

        Interpretation:
        - 90-100: Very Easy (5th grade)
        - 80-89: Easy (6th grade)
        - 70-79: Fairly Easy (7th grade)
        - 60-69: Standard (8th-9th grade)
        - 50-59: Fairly Difficult (10th-12th grade)
        - 30-49: Difficult (College)
        - 0-29: Very Difficult (Professional)
        """
        sentences = self._get_sentences(text)
        words = self._get_words(text)

        if not sentences or not words:
            return 0

        total_syllables = sum(self._count_syllables(w) for w in words)

        asl = len(words) / len(sentences)  # Average Sentence Length
        asw = total_syllables / len(words)  # Average Syllables per Word

        flesch = 206.835 - (1.015 * asl) - (84.6 * asw)
        return max(0, min(100, flesch))

    def calculate_flesch_kincaid_grade(self, text: str) -> float:
        """
        Calculate Flesch-Kincaid Grade Level.

        Formula: 0.39*(words/sentences) + 11.8*(syllables/words) - 15.59
        """
        sentences = self._get_sentences(text)
        words = self._get_words(text)

        if not sentences or not words:
            return 0

        total_syllables = sum(self._count_syllables(w) for w in words)

        asl = len(words) / len(sentences)
        asw = total_syllables / len(words)

        grade = (0.39 * asl) + (11.8 * asw) - 15.59
        return max(0, grade)

    def calculate_gunning_fog(self, text: str) -> float:
        """
        Calculate Gunning Fog Index.

        Formula: 0.4 * (ASL + percentage of complex words)
        Complex words = words with 3+ syllables
        """
        sentences = self._get_sentences(text)
        words = self._get_words(text)

        if not sentences or not words:
            return 0

        asl = len(words) / len(sentences)
        complex_words = sum(1 for w in words if self._count_syllables(w) >= 3)
        complex_percentage = (complex_words / len(words)) * 100

        fog = 0.4 * (asl + complex_percentage)
        return fog

    def calculate_smog_index(self, text: str) -> float:
        """
        Calculate SMOG Index.

        Formula: 1.0430 * sqrt(polysyllables * (30/sentences)) + 3.1291
        Polysyllables = words with 3+ syllables
        """
        sentences = self._get_sentences(text)
        words = self._get_words(text)

        if len(sentences) < 3 or not words:
            # SMOG requires at least 30 sentences, but we'll approximate
            return self.calculate_flesch_kincaid_grade(text)

        polysyllables = sum(1 for w in words if self._count_syllables(w) >= 3)

        # Adjust for sample size
        adjustment = 30 / max(len(sentences), 1)
        smog = 1.0430 * math.sqrt(polysyllables * adjustment) + 3.1291

        return max(0, smog)

    def analyze_sentence_structure(self, text: str) -> SentenceAnalysis:
        """
        Analyze sentence-level characteristics.

        Returns:
        - avg_sentence_length
        - sentence_length_variance
        - long_sentences: list (>25 words)
        - very_long_sentences: list (>40 words)
        """
        sentences = self._get_sentences(text)

        if not sentences:
            return SentenceAnalysis(
                avg_sentence_length=0,
                sentence_length_variance=0,
                total_sentences=0
            )

        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)

        # Calculate variance
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)

        # Find long sentences
        long = []
        very_long = []
        for s, length in zip(sentences, lengths):
            if length > 40:
                very_long.append(f"({length} words) {s[:100]}...")
            elif length > 25:
                long.append(f"({length} words) {s[:100]}...")

        return SentenceAnalysis(
            avg_sentence_length=round(avg_length, 1),
            sentence_length_variance=round(variance, 2),
            total_sentences=len(sentences),
            long_sentences=long[:5],
            very_long_sentences=very_long[:5]
        )

    def analyze_vocabulary(self, text: str) -> VocabularyAnalysis:
        """
        Analyze vocabulary complexity.

        Returns:
        - avg_word_length
        - complex_words: list (3+ syllables)
        - jargon_detected: list
        - passive_voice_instances: list
        """
        words = self._get_words(text)

        if not words:
            return VocabularyAnalysis(
                avg_word_length=0,
                avg_syllables_per_word=0,
                complex_word_count=0,
                complex_word_percentage=0
            )

        # Word length analysis
        avg_word_length = sum(len(w) for w in words) / len(words)

        # Syllable analysis
        syllables = [self._count_syllables(w) for w in words]
        avg_syllables = sum(syllables) / len(syllables)

        # Complex words (3+ syllables)
        complex_words = [w for w, s in zip(words, syllables) if s >= 3]
        complex_count = len(complex_words)
        complex_percentage = (complex_count / len(words)) * 100

        # Jargon detection
        text_lower = text.lower()
        jargon_found = [term for term in self.JARGON_TERMS if term in text_lower]

        # Passive voice detection
        passive_instances = []
        for pattern in self.PASSIVE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            passive_instances.extend(matches[:5])

        return VocabularyAnalysis(
            avg_word_length=round(avg_word_length, 2),
            avg_syllables_per_word=round(avg_syllables, 2),
            complex_word_count=complex_count,
            complex_word_percentage=round(complex_percentage, 1),
            jargon_detected=jargon_found[:10],
            passive_voice_instances=passive_instances[:5]
        )

    def evaluate(
        self,
        content: str,
        target_audience: str = "general"
    ) -> ReadabilityScore:
        """
        Main evaluation method.

        Returns ReadabilityScore with:
        - score: 0-100 (normalized from Flesch)
        - grade_level: float
        - flesch_ease: raw score
        - issues: list of specific readability problems
        - suggestions: list of improvements
        """
        # Handle content dict
        if isinstance(content, dict):
            text_parts = []
            for field in ['description', 'marketing_copy', 'meta_description']:
                if field in content and content[field]:
                    text_parts.append(str(content[field]))
            if 'feature_bullets' in content and content['feature_bullets']:
                if isinstance(content['feature_bullets'], list):
                    text_parts.extend(content['feature_bullets'])
            content = " ".join(text_parts)

        # Update targets based on audience
        self.targets = READABILITY_TARGETS.get(target_audience, READABILITY_TARGETS["general"])

        # Calculate metrics
        flesch_ease = self.calculate_flesch_reading_ease(content)
        flesch_grade = self.calculate_flesch_kincaid_grade(content)
        gunning_fog = self.calculate_gunning_fog(content)
        smog = self.calculate_smog_index(content)

        # Analyze structure and vocabulary
        sentence_analysis = self.analyze_sentence_structure(content)
        vocab_analysis = self.analyze_vocabulary(content)

        # Determine issues and suggestions
        issues = []
        suggestions = []

        # Check Flesch score against targets
        flesch_min = self.targets.get("flesch_min", 60)
        flesch_max = self.targets.get("flesch_max", 80)
        grade_max = self.targets.get("grade_max", 9)

        if flesch_ease < flesch_min:
            issues.append(f"Content is too difficult to read (Flesch score: {flesch_ease:.0f}, target: {flesch_min}+)")
            suggestions.append("Simplify sentences and use shorter, more common words")
        elif flesch_ease > flesch_max:
            issues.append(f"Content may be overly simplified (Flesch score: {flesch_ease:.0f})")

        if flesch_grade > grade_max:
            issues.append(f"Reading level too high (Grade {flesch_grade:.1f}, target: Grade {grade_max} or below)")
            suggestions.append("Reduce sentence length and vocabulary complexity")

        # Check sentence length
        if sentence_analysis.very_long_sentences:
            issues.append(f"Found {len(sentence_analysis.very_long_sentences)} very long sentences (40+ words)")
            suggestions.append("Break very long sentences into shorter ones")

        if sentence_analysis.avg_sentence_length > 20:
            issues.append(f"Average sentence length is high ({sentence_analysis.avg_sentence_length:.0f} words)")
            suggestions.append("Aim for an average of 15-20 words per sentence")

        # Check vocabulary
        if vocab_analysis.complex_word_percentage > 20:
            issues.append(f"High percentage of complex words ({vocab_analysis.complex_word_percentage:.0f}%)")
            suggestions.append("Replace complex words with simpler alternatives")

        if vocab_analysis.jargon_detected:
            issues.append(f"Jargon detected: {', '.join(vocab_analysis.jargon_detected[:3])}")
            suggestions.append("Replace jargon with plain language")

        if len(vocab_analysis.passive_voice_instances) > 3:
            issues.append(f"Excessive passive voice usage ({len(vocab_analysis.passive_voice_instances)} instances)")
            suggestions.append("Convert passive voice to active voice where possible")

        # Calculate normalized score (0-100)
        # Target Flesch score is 60-80
        if flesch_ease >= flesch_min and flesch_ease <= flesch_max:
            score = 100
        elif flesch_ease > flesch_max:
            # Too easy - minor penalty
            over = flesch_ease - flesch_max
            score = max(70, 100 - (over * 0.5))
        else:
            # Too difficult - larger penalty
            under = flesch_min - flesch_ease
            score = max(30, 100 - (under * 1.5))

        # Apply additional penalties
        if sentence_analysis.very_long_sentences:
            score -= min(15, len(sentence_analysis.very_long_sentences) * 5)

        if vocab_analysis.complex_word_percentage > 25:
            score -= 10

        score = max(0, min(100, score))

        return ReadabilityScore(
            score=round(score, 2),
            flesch_ease=round(flesch_ease, 1),
            flesch_grade=round(flesch_grade, 1),
            gunning_fog=round(gunning_fog, 1),
            smog_index=round(smog, 1),
            avg_sentence_length=sentence_analysis.avg_sentence_length,
            avg_word_length=vocab_analysis.avg_word_length,
            complex_word_count=vocab_analysis.complex_word_count,
            long_sentences=sentence_analysis.long_sentences + sentence_analysis.very_long_sentences,
            issues=issues,
            suggestions=suggestions,
            details={
                "total_sentences": sentence_analysis.total_sentences,
                "sentence_variance": sentence_analysis.sentence_length_variance,
                "syllables_per_word": vocab_analysis.avg_syllables_per_word,
                "complex_word_percentage": vocab_analysis.complex_word_percentage,
                "jargon_found": vocab_analysis.jargon_detected,
                "passive_voice_count": len(vocab_analysis.passive_voice_instances),
                "target_flesch_min": flesch_min,
                "target_flesch_max": flesch_max,
                "target_grade_max": grade_max
            }
        )

    def get_grade_level_description(self, grade: float) -> str:
        """Get a human-readable description of the grade level."""
        if grade <= 5:
            return "Very Easy (5th grade and below)"
        elif grade <= 6:
            return "Easy (6th grade)"
        elif grade <= 8:
            return "Standard (7th-8th grade)"
        elif grade <= 10:
            return "Fairly Difficult (9th-10th grade)"
        elif grade <= 12:
            return "Difficult (11th-12th grade)"
        else:
            return "Very Difficult (College level)"
