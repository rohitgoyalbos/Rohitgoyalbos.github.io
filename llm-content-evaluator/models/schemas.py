"""
Pydantic schemas for data validation in LLM Content Quality Evaluator.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============== Product Schemas ==============

class ProductSpecifications(BaseModel):
    """Product specifications (ground truth)."""
    name: str
    dimensions: Optional[Dict[str, Any]] = None
    weight: Optional[Dict[str, Any]] = None
    materials: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    features: List[str] = Field(default_factory=list)
    price: Optional[float] = None
    warranty: Optional[str] = None
    additional: Optional[Dict[str, Any]] = None


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    id: str
    category: str
    subcategory: Optional[str] = None
    brand: str
    name: str
    specifications: ProductSpecifications


class Product(ProductCreate):
    """Full product schema with timestamps."""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Content Schemas ==============

class ContentPiece(BaseModel):
    """Content piece to be evaluated."""
    description: Optional[str] = None
    marketing_copy: Optional[str] = None
    feature_bullets: Optional[List[str]] = None
    meta_description: Optional[str] = None


class ContentVersionCreate(BaseModel):
    """Schema for creating a content version."""
    product_id: str
    version_number: int
    description: Optional[str] = None
    marketing_copy: Optional[str] = None
    feature_bullets: Optional[List[str]] = None
    meta_description: Optional[str] = None
    prompt_used: Optional[str] = None
    model_version: Optional[str] = None
    quality_level: Optional[str] = None


class ContentVersion(ContentVersionCreate):
    """Full content version schema."""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Evaluation Schemas ==============

class Claim(BaseModel):
    """A verifiable claim extracted from content."""
    claim_type: str  # numerical, feature, material, performance
    claim_text: str
    confidence: float
    span_start: int
    span_end: int


class VerificationResult(BaseModel):
    """Result of verifying a claim against specifications."""
    verified: bool
    match_type: str  # exact, approximate, unverifiable
    source_value: Optional[str] = None
    discrepancy: Optional[str] = None


class Issue(BaseModel):
    """An issue found during evaluation."""
    dimension: str
    severity: str  # critical, major, minor, suggestion
    message: str
    location: Optional[str] = None
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    suggestion: Optional[str] = None


class AccuracyScore(BaseModel):
    """Accuracy evaluation result."""
    score: float
    verified_claims: int
    failed_claims: int
    unverifiable_claims: int
    errors: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    details: Dict[str, Any] = Field(default_factory=dict)


class CompletenessScore(BaseModel):
    """Completeness evaluation result."""
    score: float
    critical_present: int
    critical_total: int
    required_present: int
    required_total: int
    recommended_present: int
    recommended_total: int
    optional_present: int
    optional_total: int
    missing_critical: List[str] = Field(default_factory=list)
    missing_required: List[str] = Field(default_factory=list)
    missing_recommended: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class BrandVoiceScore(BaseModel):
    """Brand voice evaluation result."""
    score: float
    terminology_score: float
    tone_score: float
    style_score: float
    voice_consistency_score: float
    preferred_used: List[str] = Field(default_factory=list)
    preferred_missed: List[str] = Field(default_factory=list)
    prohibited_found: List[Dict[str, Any]] = Field(default_factory=list)
    tone_issues: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class SEOScore(BaseModel):
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
    issues: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class ReadabilityScore(BaseModel):
    """Readability evaluation result."""
    score: float
    flesch_ease: float
    flesch_grade: float
    gunning_fog: float
    smog_index: float
    avg_sentence_length: float
    avg_word_length: float
    complex_word_count: int
    long_sentences: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class StyleComplianceScore(BaseModel):
    """Style compliance evaluation result."""
    score: float
    formatting_score: float
    structure_score: float
    content_rules_score: float
    formatting_issues: List[str] = Field(default_factory=list)
    structure_issues: List[str] = Field(default_factory=list)
    content_issues: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class TranslationScore(BaseModel):
    """Translation quality evaluation result."""
    score: float
    length_score: float
    terminology_score: float
    locale_score: float
    semantic_score: float
    errors: List[str] = Field(default_factory=list)
    terminology_issues: List[Dict[str, str]] = Field(default_factory=list)
    locale_issues: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class CompositeScore(BaseModel):
    """Composite evaluation result combining all dimensions."""
    composite_score: float
    quality_tier: str
    routing_decision: str
    confidence: float

    accuracy_score: float
    completeness_score: float
    brand_voice_score: float
    seo_score: float
    readability_score: float
    style_score: float
    translation_score: Optional[float] = None

    dimension_scores: Dict[str, float]
    top_issues: List[Issue] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)

    accuracy_details: Optional[AccuracyScore] = None
    completeness_details: Optional[CompletenessScore] = None
    brand_voice_details: Optional[BrandVoiceScore] = None
    seo_details: Optional[SEOScore] = None
    readability_details: Optional[ReadabilityScore] = None
    style_details: Optional[StyleComplianceScore] = None
    translation_details: Optional[TranslationScore] = None


class VersionComparison(BaseModel):
    """Comparison result between two content versions."""
    winner: str  # version_a, version_b, tie
    score_delta: float
    dimension_deltas: Dict[str, float]
    version_a_score: float
    version_b_score: float
    recommendation: str
    improvements: List[str] = Field(default_factory=list)
    regressions: List[str] = Field(default_factory=list)


# ============== Human Review Schemas ==============

class Annotation(BaseModel):
    """Text annotation from human reviewer."""
    type: str  # accuracy_error, brand_voice_issue, style_issue, etc.
    severity: str  # critical, major, minor
    span_start: int
    span_end: int
    original_text: str
    correction: Optional[str] = None
    comment: Optional[str] = None


class HumanReviewCreate(BaseModel):
    """Schema for creating a human review."""
    evaluation_id: str
    reviewer_id: str
    accuracy_score: int = Field(ge=1, le=5)
    completeness_score: int = Field(ge=1, le=5)
    brand_voice_score: int = Field(ge=1, le=5)
    readability_score: int = Field(ge=1, le=5)
    seo_score: int = Field(ge=1, le=5)
    overall_score: int = Field(ge=1, le=5)
    annotations: List[Annotation] = Field(default_factory=list)
    verdict: str  # approve, conditional_approve, reject
    notes: Optional[str] = None
    review_duration_seconds: Optional[int] = None


class HumanReview(HumanReviewCreate):
    """Full human review schema."""
    id: str
    reviewed_at: datetime

    class Config:
        from_attributes = True


# ============== Brand Guidelines Schemas ==============

class StyleRules(BaseModel):
    """Style rules for brand guidelines."""
    sentence_length_max: int = 25
    sentence_length_ideal: int = 15
    paragraph_length_max: int = 4
    paragraph_length_ideal: int = 2
    bullets_per_list_min: int = 3
    bullets_per_list_max: int = 7
    capitalization: str = "sentence case"
    number_rule: str = "spell out 1-9, digits for 10+"


class SEORequirements(BaseModel):
    """SEO requirements for brand guidelines."""
    title_max_length: int = 60
    meta_description_min: int = 120
    meta_description_max: int = 160
    primary_keywords: List[str] = Field(default_factory=list)
    keyword_density_min: float = 0.01
    keyword_density_max: float = 0.03


class BrandGuidelinesCreate(BaseModel):
    """Schema for creating brand guidelines."""
    brand_name: str
    tone: str = "professional yet approachable"
    personality: List[str] = Field(default_factory=list)
    perspective: str = "second person"
    preferred_terms: Dict[str, str] = Field(default_factory=dict)
    prohibited_terms: List[str] = Field(default_factory=list)
    style_rules: StyleRules = Field(default_factory=StyleRules)
    seo_requirements: SEORequirements = Field(default_factory=SEORequirements)
    is_default: bool = False


class BrandGuidelines(BrandGuidelinesCreate):
    """Full brand guidelines schema."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Performance Metrics Schemas ==============

class TrafficMetrics(BaseModel):
    """Traffic metrics."""
    impressions: int
    clicks: int
    ctr: float
    avg_position: float


class EngagementMetrics(BaseModel):
    """Engagement metrics."""
    page_views: int
    avg_time_on_page: int  # seconds
    bounce_rate: float
    scroll_depth: float  # percentage


class ConversionMetrics(BaseModel):
    """Conversion metrics."""
    add_to_cart: int
    add_to_cart_rate: float
    purchases: int
    conversion_rate: float
    revenue: float


class PerformanceMetricsCreate(BaseModel):
    """Schema for creating performance metrics."""
    content_version_id: str
    period_start: datetime
    period_end: datetime
    traffic: TrafficMetrics
    engagement: EngagementMetrics
    conversion: ConversionMetrics


class PerformanceMetrics(PerformanceMetricsCreate):
    """Full performance metrics schema."""
    id: str

    class Config:
        from_attributes = True
