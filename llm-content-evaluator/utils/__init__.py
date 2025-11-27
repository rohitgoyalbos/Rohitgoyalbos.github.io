"""
Utilities package for LLM Content Quality Evaluator.
"""

from utils.text_processing import (
    normalize_text,
    extract_sentences,
    extract_words,
    count_syllables,
    get_word_frequency,
    highlight_text,
    truncate_text,
    extract_numbers,
    format_percentage,
    calculate_similarity
)

from utils.helpers import (
    generate_id,
    generate_product_id,
    generate_content_id,
    generate_evaluation_id,
    generate_review_id,
    format_timestamp,
    get_score_color,
    get_quality_tier_color,
    format_score
)

from utils.export import (
    export_to_excel,
    export_to_json,
    export_to_csv,
    generate_report_summary,
    create_comparison_report
)

__all__ = [
    # Text processing
    'normalize_text',
    'extract_sentences',
    'extract_words',
    'count_syllables',
    'get_word_frequency',
    'highlight_text',
    'truncate_text',
    'extract_numbers',
    'format_percentage',
    'calculate_similarity',
    # Helpers
    'generate_id',
    'generate_product_id',
    'generate_content_id',
    'generate_evaluation_id',
    'generate_review_id',
    'format_timestamp',
    'get_score_color',
    'get_quality_tier_color',
    'format_score',
    # Export
    'export_to_excel',
    'export_to_json',
    'export_to_csv',
    'generate_report_summary',
    'create_comparison_report'
]
