"""
SQLAlchemy database models for LLM Content Quality Evaluator.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Product(Base):
    """Product entity with source specifications."""
    __tablename__ = 'products'

    id = Column(String(50), primary_key=True)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    brand = Column(String(100))
    name = Column(String(255), nullable=False)
    specifications = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content_versions = relationship("ContentVersion", back_populates="product", cascade="all, delete-orphan")


class ContentVersion(Base):
    """Generated content version for a product."""
    __tablename__ = 'content_versions'

    id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey('products.id'), nullable=False)
    version_number = Column(Integer, nullable=False)

    # Content fields
    description = Column(Text)
    marketing_copy = Column(Text)
    feature_bullets = Column(JSON)  # List of bullet points
    meta_description = Column(String(500))

    # Generation metadata
    prompt_used = Column(Text)
    model_version = Column(String(100))
    quality_level = Column(String(50))  # excellent, good, acceptable, poor

    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="content_versions")
    evaluations = relationship("Evaluation", back_populates="content_version", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="content_version", cascade="all, delete-orphan")


class Translation(Base):
    """Translated content for a content version."""
    __tablename__ = 'translations'

    id = Column(String(50), primary_key=True)
    content_version_id = Column(String(50), ForeignKey('content_versions.id'), nullable=False)

    source_language = Column(String(10), default="en")
    target_language = Column(String(10), nullable=False)

    description = Column(Text)
    marketing_copy = Column(Text)
    feature_bullets = Column(JSON)
    meta_description = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)

    content_version = relationship("ContentVersion", back_populates="translations")


class Evaluation(Base):
    """Evaluation results for a content version."""
    __tablename__ = 'evaluations'

    id = Column(String(50), primary_key=True)
    content_version_id = Column(String(50), ForeignKey('content_versions.id'), nullable=False)

    # Composite score
    composite_score = Column(Float)
    quality_tier = Column(String(50))
    routing_decision = Column(String(50))
    confidence = Column(Float)

    # Dimension scores
    accuracy_score = Column(Float)
    completeness_score = Column(Float)
    brand_voice_score = Column(Float)
    seo_score = Column(Float)
    readability_score = Column(Float)
    style_score = Column(Float)
    translation_score = Column(Float)

    # Detailed results
    accuracy_details = Column(JSON)
    completeness_details = Column(JSON)
    brand_voice_details = Column(JSON)
    seo_details = Column(JSON)
    readability_details = Column(JSON)
    style_details = Column(JSON)
    translation_details = Column(JSON)

    issues = Column(JSON)  # List of issues found
    suggestions = Column(JSON)  # List of improvement suggestions

    evaluated_at = Column(DateTime, default=datetime.utcnow)

    content_version = relationship("ContentVersion", back_populates="evaluations")
    human_reviews = relationship("HumanReview", back_populates="evaluation", cascade="all, delete-orphan")


class HumanReview(Base):
    """Human reviewer feedback on an evaluation."""
    __tablename__ = 'human_reviews'

    id = Column(String(50), primary_key=True)
    evaluation_id = Column(String(50), ForeignKey('evaluations.id'), nullable=False)
    reviewer_id = Column(String(50), nullable=False)

    # Human scores (1-5 scale)
    accuracy_score = Column(Integer)
    completeness_score = Column(Integer)
    brand_voice_score = Column(Integer)
    readability_score = Column(Integer)
    seo_score = Column(Integer)
    overall_score = Column(Integer)

    # Annotations and feedback
    annotations = Column(JSON)  # List of text annotations
    verdict = Column(String(50))  # approve, conditional_approve, reject
    notes = Column(Text)

    reviewed_at = Column(DateTime, default=datetime.utcnow)
    review_duration_seconds = Column(Integer)

    evaluation = relationship("Evaluation", back_populates="human_reviews")


class PerformanceMetrics(Base):
    """Simulated e-commerce performance metrics."""
    __tablename__ = 'performance_metrics'

    id = Column(String(50), primary_key=True)
    content_version_id = Column(String(50), ForeignKey('content_versions.id'), nullable=False)

    period_start = Column(DateTime)
    period_end = Column(DateTime)

    # Traffic metrics
    impressions = Column(Integer)
    clicks = Column(Integer)
    ctr = Column(Float)  # Click-through rate
    avg_position = Column(Float)

    # Engagement metrics
    page_views = Column(Integer)
    avg_time_on_page = Column(Integer)  # seconds
    bounce_rate = Column(Float)
    scroll_depth = Column(Float)  # percentage

    # Conversion metrics
    add_to_cart = Column(Integer)
    add_to_cart_rate = Column(Float)
    purchases = Column(Integer)
    conversion_rate = Column(Float)
    revenue = Column(Float)


class BrandGuidelines(Base):
    """Brand guidelines for voice and style evaluation."""
    __tablename__ = 'brand_guidelines'

    id = Column(String(50), primary_key=True)
    brand_name = Column(String(100), nullable=False)

    # Voice attributes
    tone = Column(String(255))
    personality = Column(JSON)  # List of personality traits
    perspective = Column(String(50))  # first, second, third person

    # Terminology
    preferred_terms = Column(JSON)  # Dict of preferred term mappings
    prohibited_terms = Column(JSON)  # List of prohibited terms

    # Style rules
    style_rules = Column(JSON)

    # SEO requirements
    seo_requirements = Column(JSON)

    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db(database_url: str = "sqlite:///data/evaluator.db"):
    """Initialize the database and create all tables."""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Create a database session."""
    Session = sessionmaker(bind=engine)
    return Session()
