"""
SEO Evaluator for LLM Content Quality Evaluator.
Scores content for search engine and answer engine optimization.
"""

import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from collections import Counter

from config import SEO_CONFIG


@dataclass
class KeywordScore:
    """Keyword optimization result."""
    score: float
    primary_in_title: bool
    primary_in_first_100: bool
    keyword_density: float
    keyword_placements: Dict[str, List[int]] = field(default_factory=dict)


@dataclass
class SemanticScore:
    """Semantic coverage result."""
    score: float
    related_terms_found: int
    total_semantic_terms: int
    terms_found: List[str] = field(default_factory=list)


@dataclass
class DepthScore:
    """Content depth result."""
    score: float
    word_count: int
    target_word_count: int
    paragraphs: int
    sections: int


@dataclass
class AEOScore:
    """Answer Engine Optimization result."""
    score: float
    has_direct_answer: bool
    first_paragraph_words: int
    has_extractable_facts: bool
    issues: List[str] = field(default_factory=list)


@dataclass
class SEOScore:
    """SEO evaluation result."""
    score: float
    keyword_score: float
    semantic_score: float
    content_depth_score: float
    structured_data_score: float
    readability_for_seo_score: float
    technical_score: float
    word_count: int
    keyword_density: float
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class SEOEvaluator:
    """
    Evaluates SEO and AEO readiness of product content.

    Components:
    1. Keyword optimization (25%): Primary keyword placement
    2. Semantic coverage (20%): Related term density
    3. Content depth (20%): Word count and detail level
    4. Structured data readiness (15%): Schema.org compatibility
    5. Readability for SEO (10%): Optimal reading level
    6. Technical elements (10%): Meta tags, headers
    """

    # Semantic term clusters by category
    SEMANTIC_CLUSTERS = {
        "Consumer Electronics": [
            "technology", "device", "smart", "wireless", "battery", "screen",
            "display", "performance", "processor", "memory", "storage", "camera",
            "connectivity", "bluetooth", "wifi", "5g", "portable", "charging"
        ],
        "Fashion/Apparel": [
            "style", "fashion", "wear", "comfortable", "fit", "fabric", "material",
            "design", "collection", "trend", "casual", "formal", "size", "color",
            "quality", "durable", "sustainable", "premium"
        ],
        "Home & Garden": [
            "home", "furniture", "decor", "space", "room", "design", "storage",
            "comfort", "quality", "durable", "assembly", "modern", "classic",
            "functional", "versatile", "organize"
        ],
        "Beauty & Personal Care": [
            "skin", "beauty", "care", "natural", "ingredients", "formula",
            "moisturize", "hydrate", "anti-aging", "gentle", "dermatologist",
            "fragrance", "clean", "organic", "routine"
        ],
        "Sports & Outdoors": [
            "fitness", "workout", "exercise", "training", "performance", "active",
            "sport", "outdoor", "gear", "equipment", "durable", "lightweight",
            "comfortable", "breathable", "athletic"
        ]
    }

    # Default semantic terms (category-agnostic)
    DEFAULT_SEMANTIC_TERMS = [
        "quality", "premium", "design", "features", "performance", "value",
        "durable", "reliable", "innovative", "professional", "comfortable"
    ]

    def __init__(self, seo_config: Optional[Dict] = None):
        """Initialize the SEO evaluator."""
        self.config = seo_config or SEO_CONFIG

    def analyze_keyword_optimization(
        self,
        content: str,
        primary_keywords: List[str],
        secondary_keywords: Optional[List[str]] = None,
        title: Optional[str] = None
    ) -> KeywordScore:
        """
        Check keyword placement and density.

        Optimal placements:
        - Title: primary keyword present
        - First 100 words: primary keyword present
        - Throughout: 1-3% density
        """
        content_lower = content.lower()
        words = content_lower.split()
        word_count = len(words)

        if word_count == 0:
            return KeywordScore(
                score=0,
                primary_in_title=False,
                primary_in_first_100=False,
                keyword_density=0
            )

        # Check title
        primary_in_title = False
        if title:
            for keyword in primary_keywords:
                if keyword.lower() in title.lower():
                    primary_in_title = True
                    break
        else:
            # Use first sentence as title
            first_sentence = content.split('.')[0] if content else ""
            for keyword in primary_keywords:
                if keyword.lower() in first_sentence.lower():
                    primary_in_title = True
                    break

        # Check first 100 words
        first_100 = ' '.join(words[:100])
        primary_in_first_100 = any(kw.lower() in first_100 for kw in primary_keywords)

        # Calculate keyword density
        keyword_occurrences = 0
        keyword_placements = {}
        for keyword in primary_keywords:
            kw_lower = keyword.lower()
            count = content_lower.count(kw_lower)
            keyword_occurrences += count
            if count > 0:
                positions = [m.start() for m in re.finditer(re.escape(kw_lower), content_lower)]
                keyword_placements[keyword] = positions

        keyword_density = (keyword_occurrences / word_count) * 100 if word_count > 0 else 0

        # Calculate score
        score = 0

        # Title presence (25 points)
        if primary_in_title:
            score += 25

        # First 100 words (25 points)
        if primary_in_first_100:
            score += 25

        # Keyword density (50 points)
        min_density = self.config.get("keyword_density_min", 0.01) * 100
        max_density = self.config.get("keyword_density_max", 0.03) * 100

        if min_density <= keyword_density <= max_density:
            score += 50
        elif keyword_density > 0:
            if keyword_density < min_density:
                score += 25  # Some keywords present
            elif keyword_density > max_density:
                score += 30  # Too many keywords, slight penalty

        return KeywordScore(
            score=score,
            primary_in_title=primary_in_title,
            primary_in_first_100=primary_in_first_100,
            keyword_density=round(keyword_density, 2),
            keyword_placements=keyword_placements
        )

    def analyze_semantic_coverage(
        self,
        content: str,
        category: str = "general"
    ) -> SemanticScore:
        """
        Check for semantically related terms.

        Target: 14-60 relevant semantic terms for comprehensive coverage.
        """
        content_lower = content.lower()

        # Get semantic terms for category
        semantic_terms = self.SEMANTIC_CLUSTERS.get(category, self.DEFAULT_SEMANTIC_TERMS)

        # Count found terms
        terms_found = []
        for term in semantic_terms:
            if term.lower() in content_lower:
                terms_found.append(term)

        found_count = len(terms_found)
        total_terms = len(semantic_terms)

        # Calculate score based on coverage
        coverage_ratio = found_count / total_terms if total_terms > 0 else 0

        if coverage_ratio >= 0.7:
            score = 100
        elif coverage_ratio >= 0.5:
            score = 85
        elif coverage_ratio >= 0.3:
            score = 70
        elif coverage_ratio >= 0.15:
            score = 50
        else:
            score = 30

        return SemanticScore(
            score=score,
            related_terms_found=found_count,
            total_semantic_terms=total_terms,
            terms_found=terms_found
        )

    def check_content_depth(
        self,
        content: str,
        content_type: str = "product_description"
    ) -> DepthScore:
        """
        Evaluate content length and detail.

        Targets by type:
        - Product description: 300-500 words
        - Marketing copy: 150-300 words
        - Feature bullets: 5-7 items, 10-25 words each
        """
        words = content.split()
        word_count = len(words)

        # Get target based on content type
        targets = {
            "product_description": (300, 500),
            "marketing_copy": (150, 300),
            "feature_bullets": (50, 175),  # 5-7 bullets * 10-25 words
            "meta_description": (20, 30)
        }

        min_words, max_words = targets.get(content_type, (200, 400))

        # Count structure elements
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        sections = len(re.findall(r'(?:^|\n)#+\s', content))

        # Calculate score
        if min_words <= word_count <= max_words:
            score = 100
        elif word_count < min_words:
            ratio = word_count / min_words
            score = max(30, ratio * 100)
        else:
            # Too long - slight penalty
            over_ratio = word_count / max_words
            if over_ratio > 2:
                score = 70
            else:
                score = 90

        return DepthScore(
            score=score,
            word_count=word_count,
            target_word_count=int((min_words + max_words) / 2),
            paragraphs=paragraphs,
            sections=sections
        )

    def check_aeo_readiness(self, content: str) -> AEOScore:
        """
        Check Answer Engine Optimization factors.

        Checks:
        - Direct answer in first paragraph (40-60 words)
        - Question-based structure potential
        - Extractable definitions
        - Concise factual statements
        """
        issues = []

        # Get first paragraph
        paragraphs = content.split('\n\n')
        first_para = paragraphs[0] if paragraphs else ""
        first_para_words = len(first_para.split())

        # Check for direct answer in first paragraph
        has_direct_answer = 40 <= first_para_words <= 80

        if first_para_words < 40:
            issues.append("First paragraph too short for answer extraction")
        elif first_para_words > 80:
            issues.append("First paragraph too long for concise answer extraction")

        # Check for extractable facts
        # Look for patterns like "X is Y", "X features Y", "X provides Y"
        fact_patterns = [
            r'\b\w+\s+(?:is|are|was|were)\s+(?:a|an|the)?\s*\w+',
            r'\b\w+\s+(?:features?|provides?|offers?|includes?)\s+\w+',
            r'\b\w+\s+(?:has|have|had)\s+\w+',
        ]

        fact_count = 0
        for pattern in fact_patterns:
            fact_count += len(re.findall(pattern, content, re.IGNORECASE))

        has_extractable_facts = fact_count >= 3

        if fact_count < 3:
            issues.append("Content lacks easily extractable factual statements")

        # Calculate score
        score = 0
        if has_direct_answer:
            score += 50
        elif first_para_words > 0:
            score += 25

        if has_extractable_facts:
            score += 50
        elif fact_count >= 1:
            score += 25

        return AEOScore(
            score=score,
            has_direct_answer=has_direct_answer,
            first_paragraph_words=first_para_words,
            has_extractable_facts=has_extractable_facts,
            issues=issues
        )

    def check_structured_data_readiness(self, content: str, specifications: Optional[Dict] = None) -> float:
        """Check if content is ready for Schema.org structured data."""
        score = 0
        checks_passed = 0
        total_checks = 5

        # Check for product name pattern
        if re.search(r'^[A-Z][^\n]+', content):
            checks_passed += 1

        # Check for price mention
        if re.search(r'\$\d+', content):
            checks_passed += 1

        # Check for description (100+ chars)
        if len(content) >= 100:
            checks_passed += 1

        # Check for features/bullets
        if re.search(r'(?:•|·|\*|-)\s+\w+', content) or re.search(r'(?:features?|includes?)', content, re.IGNORECASE):
            checks_passed += 1

        # Check for specifications
        if specifications or re.search(r'\d+\s*(?:inch|mm|cm|g|kg|GB|TB)', content):
            checks_passed += 1

        score = (checks_passed / total_checks) * 100
        return score

    def check_technical_elements(
        self,
        content: str,
        meta_description: Optional[str] = None,
        title: Optional[str] = None
    ) -> Tuple[float, List[str]]:
        """Check technical SEO elements."""
        issues = []
        score = 100

        # Check meta description
        if meta_description:
            meta_len = len(meta_description)
            min_len = self.config.get("meta_description_min", 120)
            max_len = self.config.get("meta_description_max", 160)

            if meta_len < min_len:
                issues.append(f"Meta description too short ({meta_len} chars, min {min_len})")
                score -= 15
            elif meta_len > max_len:
                issues.append(f"Meta description too long ({meta_len} chars, max {max_len})")
                score -= 10
        else:
            issues.append("Missing meta description")
            score -= 20

        # Check title
        if title:
            title_len = len(title)
            max_title = self.config.get("title_max_length", 60)
            if title_len > max_title:
                issues.append(f"Title too long ({title_len} chars, max {max_title})")
                score -= 10
        else:
            # Use first line as implicit title
            first_line = content.split('\n')[0] if content else ""
            if len(first_line) > 60:
                issues.append("First line (implicit title) too long")
                score -= 5

        # Check for headers/structure
        if not re.search(r'(?:^|\n)#+\s|(?:^|\n)(?:•|·|\*|-)\s', content):
            issues.append("Content lacks structural elements (headers, bullets)")
            score -= 10

        return max(0, score), issues

    def evaluate(
        self,
        content: Any,
        keywords: Optional[List[str]] = None,
        category: str = "general",
        specifications: Optional[Dict] = None
    ) -> SEOScore:
        """
        Main evaluation method.

        Returns composite SEO score.
        """
        issues = []

        # Handle content dict
        if isinstance(content, dict):
            description = content.get('description', '')
            marketing_copy = content.get('marketing_copy', '')
            meta_description = content.get('meta_description', '')
            feature_bullets = content.get('feature_bullets', [])

            # Combine for analysis
            full_content = description + " " + marketing_copy
            if feature_bullets:
                if isinstance(feature_bullets, list):
                    full_content += " " + " ".join(feature_bullets)
                else:
                    full_content += " " + str(feature_bullets)

            title = description.split('.')[0] if description else None
        else:
            full_content = content
            meta_description = None
            title = content.split('.')[0] if content else None

        # Default keywords if not provided
        if not keywords:
            keywords = self._extract_likely_keywords(full_content)

        # Run component evaluations
        keyword_result = self.analyze_keyword_optimization(
            full_content, keywords, title=title
        )

        semantic_result = self.analyze_semantic_coverage(full_content, category)

        depth_result = self.check_content_depth(full_content)

        aeo_result = self.check_aeo_readiness(full_content)

        structured_score = self.check_structured_data_readiness(full_content, specifications)

        technical_score, technical_issues = self.check_technical_elements(
            full_content, meta_description, title
        )

        issues.extend(technical_issues)
        issues.extend(aeo_result.issues)

        # Calculate readability for SEO (simplified check)
        words = full_content.split()
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        readability_score = 100 if avg_word_length < 7 else max(60, 100 - (avg_word_length - 7) * 10)

        # Calculate composite score
        composite = (
            keyword_result.score * 0.25 +
            semantic_result.score * 0.20 +
            depth_result.score * 0.20 +
            structured_score * 0.15 +
            readability_score * 0.10 +
            technical_score * 0.10
        )

        return SEOScore(
            score=round(composite, 2),
            keyword_score=round(keyword_result.score, 2),
            semantic_score=round(semantic_result.score, 2),
            content_depth_score=round(depth_result.score, 2),
            structured_data_score=round(structured_score, 2),
            readability_for_seo_score=round(readability_score, 2),
            technical_score=round(technical_score, 2),
            word_count=depth_result.word_count,
            keyword_density=keyword_result.keyword_density,
            issues=issues,
            details={
                "keyword_in_title": keyword_result.primary_in_title,
                "keyword_in_first_100": keyword_result.primary_in_first_100,
                "semantic_terms_found": semantic_result.terms_found,
                "aeo_has_direct_answer": aeo_result.has_direct_answer,
                "paragraphs": depth_result.paragraphs,
                "target_word_count": depth_result.target_word_count
            }
        )

    def _extract_likely_keywords(self, content: str) -> List[str]:
        """Extract likely keywords from content."""
        words = re.findall(r'\b[a-z]{4,}\b', content.lower())
        word_freq = Counter(words)

        # Filter out common stop words
        stop_words = {
            'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they',
            'their', 'which', 'would', 'could', 'should', 'there', 'where',
            'when', 'what', 'about', 'into', 'your', 'more', 'some', 'than',
            'also', 'just', 'only', 'very', 'most', 'such', 'each', 'both'
        }

        keywords = [
            word for word, count in word_freq.most_common(10)
            if word not in stop_words and count >= 2
        ]

        return keywords[:5] if keywords else ["product"]
