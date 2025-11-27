"""
Text processing utilities for LLM Content Quality Evaluator.
"""

import re
from typing import List, Dict, Any, Tuple


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Convert to lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text."""
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]


def extract_words(text: str) -> List[str]:
    """Extract words from text."""
    return re.findall(r'\b[a-zA-Z]+\b', text.lower())


def count_syllables(word: str) -> int:
    """Count syllables in a word."""
    word = word.lower().strip()
    if len(word) <= 3:
        return 1

    if word.endswith('e'):
        word = word[:-1]

    vowels = 'aeiouy'
    count = 0
    prev_is_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel

    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1

    return max(1, count)


def get_word_frequency(text: str) -> Dict[str, int]:
    """Get word frequency distribution."""
    words = extract_words(text)
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    return freq


def highlight_text(text: str, patterns: List[str], tag: str = "**") -> str:
    """Highlight patterns in text."""
    for pattern in patterns:
        text = re.sub(
            f'({re.escape(pattern)})',
            f'{tag}\\1{tag}',
            text,
            flags=re.IGNORECASE
        )
    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_numbers(text: str) -> List[Tuple[float, str]]:
    """Extract numbers with their units from text."""
    patterns = [
        (r'(\d+\.?\d*)\s*(inches?|in|")', 'inches'),
        (r'(\d+\.?\d*)\s*(mm|millimeters?)', 'mm'),
        (r'(\d+\.?\d*)\s*(cm|centimeters?)', 'cm'),
        (r'(\d+\.?\d*)\s*(g|grams?)', 'g'),
        (r'(\d+\.?\d*)\s*(kg|kilograms?)', 'kg'),
        (r'(\d+\.?\d*)\s*(oz|ounces?)', 'oz'),
        (r'(\d+\.?\d*)\s*(lbs?|pounds?)', 'lbs'),
        (r'(\d+\.?\d*)\s*(mAh)', 'mAh'),
        (r'(\d+\.?\d*)\s*(GB|TB|MB)', 'storage'),
        (r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
    ]

    results = []
    for pattern, unit in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = float(match.group(1).replace(',', ''))
            results.append((value, unit))

    return results


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a value as a percentage string."""
    return f"{value:.{decimals}f}%"


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple word-based similarity between two texts."""
    words1 = set(extract_words(text1))
    words2 = set(extract_words(text2))

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0
