"""
General utility helpers for LLM Content Quality Evaluator.
"""

import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID."""
    unique_id = uuid.uuid4().hex[:12]
    if prefix:
        return f"{prefix}-{unique_id}"
    return unique_id


def generate_product_id() -> str:
    """Generate a product ID."""
    return f"SKU-{uuid.uuid4().hex[:8].upper()}"


def generate_content_id(product_id: str, version: int) -> str:
    """Generate a content version ID."""
    return f"{product_id}-v{version}"


def generate_evaluation_id() -> str:
    """Generate an evaluation ID."""
    return f"EVAL-{uuid.uuid4().hex[:10]}"


def generate_review_id() -> str:
    """Generate a review ID."""
    return f"REV-{uuid.uuid4().hex[:8]}"


def hash_content(content: str) -> str:
    """Generate a hash of content for deduplication."""
    return hashlib.md5(content.encode()).hexdigest()


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format a datetime as ISO string."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat() + "Z"


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse an ISO timestamp string."""
    return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))


def get_quality_tier_color(tier: str) -> str:
    """Get the color associated with a quality tier."""
    colors = {
        "Excellent": "#22c55e",
        "Good": "#84cc16",
        "Acceptable": "#eab308",
        "Needs Improvement": "#f97316",
        "Poor": "#ef4444"
    }
    return colors.get(tier, "#6b7280")


def get_score_color(score: float) -> str:
    """Get color based on score value."""
    if score >= 90:
        return "#22c55e"  # Green
    elif score >= 75:
        return "#84cc16"  # Light green
    elif score >= 60:
        return "#eab308"  # Yellow
    elif score >= 40:
        return "#f97316"  # Orange
    else:
        return "#ef4444"  # Red


def format_score(score: float, include_status: bool = False) -> str:
    """Format a score for display."""
    formatted = f"{score:.1f}%"
    if include_status:
        if score >= 90:
            formatted += " (Excellent)"
        elif score >= 75:
            formatted += " (Good)"
        elif score >= 60:
            formatted += " (Acceptable)"
        elif score >= 40:
            formatted += " (Needs Improvement)"
        else:
            formatted += " (Poor)"
    return formatted


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 0 if new_value == 0 else 100
    return ((new_value - old_value) / old_value) * 100


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_get(d: Dict, *keys, default=None):
    """Safely get nested dictionary values."""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d


def merge_dicts(*dicts) -> Dict:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def sort_dict_by_value(d: Dict, reverse: bool = True) -> Dict:
    """Sort a dictionary by its values."""
    return dict(sorted(d.items(), key=lambda x: x[1], reverse=reverse))


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a value between min and max."""
    return max(min_value, min(max_value, value))


def normalize_score(score: float) -> float:
    """Normalize a score to 0-100 range."""
    return clamp(score, 0, 100)


def aggregate_scores(scores: List[float], weights: Optional[List[float]] = None) -> float:
    """Calculate weighted average of scores."""
    if not scores:
        return 0

    if weights is None:
        weights = [1.0] * len(scores)

    if len(weights) != len(scores):
        raise ValueError("Weights must have same length as scores")

    total_weight = sum(weights)
    if total_weight == 0:
        return 0

    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    return weighted_sum / total_weight


def format_list_for_display(items: List[str], max_items: int = 5) -> str:
    """Format a list for display, truncating if necessary."""
    if not items:
        return "None"

    if len(items) <= max_items:
        return ", ".join(items)

    displayed = items[:max_items]
    remaining = len(items) - max_items
    return f"{', '.join(displayed)}, and {remaining} more"


def get_severity_weight(severity: str) -> float:
    """Get numerical weight for severity level."""
    weights = {
        "critical": 1.0,
        "major": 0.7,
        "minor": 0.3,
        "suggestion": 0.1
    }
    return weights.get(severity.lower(), 0.5)


def prioritize_issues(issues: List[Dict]) -> List[Dict]:
    """Sort issues by severity and dimension importance."""
    severity_order = {"critical": 0, "major": 1, "minor": 2, "suggestion": 3}
    dimension_order = {
        "accuracy": 0, "completeness": 1, "brand_voice": 2,
        "seo": 3, "readability": 4, "style": 5, "translation": 6
    }

    def sort_key(issue):
        severity = severity_order.get(issue.get("severity", "minor"), 2)
        dimension = dimension_order.get(issue.get("dimension", ""), 5)
        return (severity, dimension)

    return sorted(issues, key=sort_key)
