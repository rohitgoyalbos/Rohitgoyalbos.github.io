"""
Models package for LLM Content Quality Evaluator.
"""

from models.database import (
    Base,
    Product,
    ContentVersion,
    Translation,
    Evaluation,
    HumanReview,
    PerformanceMetrics,
    BrandGuidelines,
    init_db,
    get_session
)

from models.schemas import (
    ProductSpecifications,
    ProductCreate,
    Product as ProductSchema,
    ContentPiece,
    ContentVersionCreate,
    ContentVersion as ContentVersionSchema,
    Claim,
    VerificationResult,
    Issue,
    AccuracyScore,
    CompletenessScore,
    BrandVoiceScore,
    SEOScore,
    ReadabilityScore,
    StyleComplianceScore,
    TranslationScore,
    CompositeScore,
    VersionComparison,
    Annotation,
    HumanReviewCreate,
    HumanReview as HumanReviewSchema,
    BrandGuidelinesCreate,
    BrandGuidelines as BrandGuidelinesSchema
)

__all__ = [
    # Database models
    'Base',
    'Product',
    'ContentVersion',
    'Translation',
    'Evaluation',
    'HumanReview',
    'PerformanceMetrics',
    'BrandGuidelines',
    'init_db',
    'get_session',
    # Schemas
    'ProductSpecifications',
    'ProductCreate',
    'ProductSchema',
    'ContentPiece',
    'ContentVersionCreate',
    'ContentVersionSchema',
    'Claim',
    'VerificationResult',
    'Issue',
    'AccuracyScore',
    'CompletenessScore',
    'BrandVoiceScore',
    'SEOScore',
    'ReadabilityScore',
    'StyleComplianceScore',
    'TranslationScore',
    'CompositeScore',
    'VersionComparison',
    'Annotation',
    'HumanReviewCreate',
    'HumanReviewSchema',
    'BrandGuidelinesCreate',
    'BrandGuidelinesSchema'
]
