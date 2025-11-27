"""
Configuration and constants for LLM Content Quality Evaluator.
"""

from typing import Dict, Any

# Database configuration
DATABASE_PATH = "data/evaluator.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Default evaluation weights
DEFAULT_WEIGHTS: Dict[str, float] = {
    "accuracy": 0.25,
    "completeness": 0.20,
    "brand_voice": 0.15,
    "seo": 0.15,
    "readability": 0.10,
    "style": 0.10,
    "translation": 0.05
}

# Quality tiers based on composite score
QUALITY_TIERS: Dict[str, Dict[str, Any]] = {
    "excellent": {"min": 90, "max": 100, "color": "#22c55e", "label": "Excellent"},
    "good": {"min": 75, "max": 89, "color": "#84cc16", "label": "Good"},
    "acceptable": {"min": 60, "max": 74, "color": "#eab308", "label": "Acceptable"},
    "needs_improvement": {"min": 40, "max": 59, "color": "#f97316", "label": "Needs Improvement"},
    "poor": {"min": 0, "max": 39, "color": "#ef4444", "label": "Poor"}
}

# Routing thresholds for human review
ROUTING_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "auto_publish": {"score": 90, "confidence": 0.85},
    "light_review": {"score": 75, "confidence": 0.70},
    "standard_review": {"score": 60, "confidence": 0.60},
    "priority_review": {"score": 40, "confidence": 0.50},
    "reject": {"score": 0, "confidence": 0}
}

# SEO configuration
SEO_CONFIG: Dict[str, Any] = {
    "title_max_length": 60,
    "meta_description_min": 120,
    "meta_description_max": 160,
    "content_min_words": 300,
    "keyword_density_min": 0.01,
    "keyword_density_max": 0.03,
    "optimal_h2_count": {"min": 2, "max": 6},
    "optimal_bullet_count": {"min": 3, "max": 7}
}

# Readability targets by audience type
READABILITY_TARGETS: Dict[str, Dict[str, float]] = {
    "consumer": {"flesch_min": 60, "flesch_max": 80, "grade_max": 9},
    "technical": {"flesch_min": 45, "flesch_max": 65, "grade_max": 12},
    "luxury": {"flesch_min": 50, "flesch_max": 70, "grade_max": 10},
    "general": {"flesch_min": 60, "flesch_max": 80, "grade_max": 9}
}

# Translation length ratios (expected expansion/contraction)
TRANSLATION_LENGTH_RATIOS: Dict[str, Dict[str, float]] = {
    "en-fr": {"min": 1.15, "max": 1.25},
    "en-fr-ca": {"min": 1.15, "max": 1.25},
    "en-es": {"min": 1.15, "max": 1.25},
    "en-de": {"min": 1.10, "max": 1.30},
    "en-nl": {"min": 1.00, "max": 1.15},
    "en-sv": {"min": 0.95, "max": 1.10},
    "en-it": {"min": 1.10, "max": 1.20},
    "en-pt": {"min": 1.10, "max": 1.25}
}

# Category templates for completeness evaluation
CATEGORY_TEMPLATES: Dict[str, Dict[str, list]] = {
    "Consumer Electronics": {
        "critical": ["product_name", "price", "brand"],
        "required": ["description", "specifications", "features", "warranty"],
        "recommended": ["dimensions", "weight", "compatibility", "whats_included"],
        "optional": ["videos", "360_view", "comparison_chart", "user_reviews"]
    },
    "Fashion/Apparel": {
        "critical": ["product_name", "price", "size_available", "color"],
        "required": ["description", "material", "care_instructions"],
        "recommended": ["fit_guide", "model_measurements", "sustainability_info"],
        "optional": ["styling_suggestions", "outfit_ideas", "customer_photos"]
    },
    "Home & Garden": {
        "critical": ["product_name", "price", "brand"],
        "required": ["description", "dimensions", "materials", "assembly_info"],
        "recommended": ["weight_capacity", "care_instructions", "warranty"],
        "optional": ["room_planner", "customer_photos", "related_products"]
    },
    "Beauty & Personal Care": {
        "critical": ["product_name", "price", "brand", "size"],
        "required": ["description", "ingredients", "usage_instructions"],
        "recommended": ["skin_type", "benefits", "warnings", "cruelty_free"],
        "optional": ["before_after", "video_tutorial", "reviews"]
    },
    "Sports & Outdoors": {
        "critical": ["product_name", "price", "brand"],
        "required": ["description", "specifications", "material"],
        "recommended": ["size_guide", "weight", "suitable_activities"],
        "optional": ["athlete_endorsements", "training_tips", "accessories"]
    }
}

# Attribute tier weights for completeness scoring
ATTRIBUTE_WEIGHTS: Dict[str, float] = {
    "critical": 3.0,
    "required": 2.0,
    "recommended": 1.5,
    "optional": 1.0
}

# Quality level distribution for synthetic data
QUALITY_DISTRIBUTION: Dict[str, Dict[str, Any]] = {
    "excellent": {
        "accuracy": {"min": 95, "max": 100},
        "completeness": {"min": 95, "max": 100},
        "seo": {"min": 85, "max": 100},
        "readability": {"min": 65, "max": 75},
        "percentage": 0.20
    },
    "good": {
        "accuracy": {"min": 85, "max": 94},
        "completeness": {"min": 80, "max": 95},
        "seo": {"min": 70, "max": 84},
        "readability": {"min": 60, "max": 80},
        "percentage": 0.35
    },
    "acceptable": {
        "accuracy": {"min": 70, "max": 84},
        "completeness": {"min": 60, "max": 79},
        "seo": {"min": 50, "max": 69},
        "readability": {"min": 50, "max": 85},
        "percentage": 0.25
    },
    "poor": {
        "accuracy": {"min": 40, "max": 69},
        "completeness": {"min": 30, "max": 59},
        "seo": {"min": 20, "max": 49},
        "readability": {"min": 30, "max": 50},
        "percentage": 0.20
    }
}

# Brand voice severity levels
SEVERITY_LEVELS: Dict[str, Dict[str, Any]] = {
    "critical": {"weight": 1.0, "label": "Critical"},
    "major": {"weight": 0.7, "label": "Major"},
    "minor": {"weight": 0.3, "label": "Minor"},
    "suggestion": {"weight": 0.1, "label": "Suggestion"}
}

# Supported product categories
PRODUCT_CATEGORIES: list = [
    "Consumer Electronics",
    "Fashion/Apparel",
    "Home & Garden",
    "Beauty & Personal Care",
    "Sports & Outdoors"
]

# Supported languages for translation
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "fr": "French",
    "fr-ca": "French (Canada)",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "sv": "Swedish"
}
