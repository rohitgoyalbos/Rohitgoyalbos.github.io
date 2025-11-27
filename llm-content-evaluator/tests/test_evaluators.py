"""
Unit tests for evaluators in LLM Content Quality Evaluator.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluators.accuracy_evaluator import AccuracyEvaluator
from evaluators.completeness_evaluator import CompletenessEvaluator
from evaluators.brand_voice_evaluator import BrandVoiceEvaluator
from evaluators.seo_evaluator import SEOEvaluator
from evaluators.readability_evaluator import ReadabilityEvaluator
from evaluators.style_compliance_evaluator import StyleComplianceEvaluator
from evaluators.translation_evaluator import TranslationEvaluator
from evaluators.composite_scorer import CompositeScorer


class TestAccuracyEvaluator:
    """Tests for the accuracy evaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = AccuracyEvaluator()
        self.sample_specs = {
            "name": "TechBrand Pro Max 15",
            "dimensions": {"length": 6.7, "width": 2.8, "unit": "inches"},
            "weight": {"value": 187, "unit": "grams"},
            "price": 1199.99,
            "features": [
                "Super Retina XDR display",
                "A17 Pro chip",
                "48MP main camera"
            ],
            "materials": ["Aluminum", "Ceramic Shield glass"],
            "colors": ["Space Black", "Silver", "Gold"]
        }

    def test_accuracy_with_correct_specs(self):
        """Test accuracy evaluation with correct specifications."""
        content = """
        The TechBrand Pro Max 15 features a stunning 6.7-inch display and weighs 187 grams.
        Crafted with premium Aluminum, it's available in Space Black and Silver.
        Priced at $1199.99, it includes the A17 Pro chip.
        """

        result = self.evaluator.evaluate(content, self.sample_specs)

        assert result.score >= 70, f"Expected score >= 70, got {result.score}"
        assert result.verified_claims > 0

    def test_accuracy_catches_wrong_specs(self):
        """Test that accuracy evaluator catches specification mismatches."""
        content = """
        This device features a stunning 6.5-inch display and weighs only 180 grams.
        """

        result = self.evaluator.evaluate(content, self.sample_specs)

        # Should detect mismatches
        assert result.failed_claims > 0 or result.score < 100

    def test_extract_claims(self):
        """Test claim extraction from content."""
        content = "The phone has a 6.7-inch display, weighs 187g, and costs $999."

        claims = self.evaluator.extract_claims(content)

        assert len(claims) > 0
        claim_types = [c.claim_type for c in claims]
        assert "dimension" in claim_types or "price" in claim_types

    def test_empty_content(self):
        """Test handling of empty content."""
        result = self.evaluator.evaluate("", self.sample_specs)

        assert result.score == 100  # No claims to verify
        assert result.confidence < 1.0  # Low confidence


class TestCompletenessEvaluator:
    """Tests for the completeness evaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = CompletenessEvaluator()

    def test_complete_content(self):
        """Test completeness with all required attributes."""
        content = """
        TechBrand Pro Max 15 - Premium Smartphone

        Description: This premium smartphone features cutting-edge technology
        with a stunning display and powerful processor.

        Features:
        - Super Retina XDR display
        - A17 Pro chip
        - 48MP camera system

        Price: $1199.99
        Warranty: 1 year limited warranty

        Specifications:
        - Dimensions: 6.7 x 2.8 x 0.31 inches
        - Weight: 187 grams
        """

        result = self.evaluator.evaluate(content, "Consumer Electronics")

        assert result.score >= 60
        assert result.critical_present >= result.critical_total * 0.5

    def test_missing_critical_attributes(self):
        """Test completeness with missing critical attributes."""
        content = "This is a great product. You should buy it."

        result = self.evaluator.evaluate(content, "Consumer Electronics")

        assert result.score < 100
        assert len(result.missing_critical) > 0 or len(result.missing_required) > 0

    def test_category_templates(self):
        """Test that different categories have different requirements."""
        content = "Product name and description here. Price: $99."

        result_electronics = self.evaluator.evaluate(content, "Consumer Electronics")
        result_fashion = self.evaluator.evaluate(content, "Fashion/Apparel")

        # Both should work without errors
        assert result_electronics.score >= 0
        assert result_fashion.score >= 0


class TestBrandVoiceEvaluator:
    """Tests for the brand voice evaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.guidelines = {
            "terminology": {
                "prohibited": ["best in class", "revolutionary", "game-changing"],
                "preferred": {"smartphone": "device", "buy": "get yours"}
            },
            "voice_attributes": {
                "tone": "professional yet approachable",
                "perspective": "second person"
            },
            "style_rules": {
                "sentence_length": {"max": 25}
            }
        }
        self.evaluator = BrandVoiceEvaluator(self.guidelines)

    def test_brand_voice_catches_prohibited_terms(self):
        """Test that brand voice evaluator catches prohibited phrases."""
        content = "This best in class device is truly revolutionary and game-changing."

        result = self.evaluator.evaluate(content)

        assert result.terminology_score < 100
        assert len(result.prohibited_found) >= 2

    def test_brand_voice_clean_content(self):
        """Test brand voice with compliant content."""
        content = """
        Discover your new favorite device. With innovative features
        designed for you, this product delivers exceptional value.
        """

        result = self.evaluator.evaluate(content)

        assert result.score >= 70
        assert len(result.prohibited_found) == 0

    def test_tone_analysis(self):
        """Test tone analysis functionality."""
        formal_content = "Therefore, we hereby present our innovative solution."
        casual_content = "Hey, this is totally awesome and super cool!"

        formal_tone = self.evaluator.analyze_tone(formal_content)
        casual_tone = self.evaluator.analyze_tone(casual_content)

        assert formal_tone.formality_level in ["formal", "neutral"]
        assert casual_tone.formality_level in ["casual", "neutral"]


class TestSEOEvaluator:
    """Tests for the SEO evaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = SEOEvaluator()

    def test_seo_with_keywords(self):
        """Test SEO evaluation with proper keyword usage."""
        content = """
        Premium Smartphone with Advanced Camera

        Discover the ultimate smartphone experience. This premium device
        features a professional-grade camera system, powerful processor,
        and all-day battery life. The smartphone combines cutting-edge
        technology with elegant design for the modern user.

        Features include:
        - 48MP camera system
        - Fast charging
        - 5G connectivity

        Get your smartphone today and experience the difference.
        """

        keywords = ["smartphone", "camera", "premium"]
        result = self.evaluator.evaluate(content, keywords, "Consumer Electronics")

        assert result.score > 50
        assert result.word_count > 50

    def test_seo_thin_content(self):
        """Test SEO evaluation with thin content."""
        content = "Buy this product. It's good."

        result = self.evaluator.evaluate(content, ["product"])

        assert result.content_depth_score < 80
        assert result.word_count < 50

    def test_keyword_density(self):
        """Test keyword density calculation."""
        content = "smartphone " * 50 + " other words " * 50

        keywords = ["smartphone"]
        result = self.evaluator.analyze_keyword_optimization(content, keywords)

        assert result.keyword_density > 0


class TestReadabilityEvaluator:
    """Tests for the readability evaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = ReadabilityEvaluator()

    def test_readability_simple_content(self):
        """Test readability with simple, clear content."""
        content = """
        This phone is great. It has a big screen. The camera takes nice photos.
        You will love using it every day. The battery lasts all day long.
        """

        result = self.evaluator.evaluate(content)

        assert result.flesch_ease > 60
        assert result.flesch_grade < 10

    def test_readability_complex_content(self):
        """Test readability with complex content."""
        content = """
        The implementation of revolutionary paradigm-shifting technological
        innovations necessitates comprehensive understanding of multifaceted
        synergistic methodologies that leverage unprecedented advancements
        in computational capabilities while simultaneously optimizing
        holistic user experience frameworks.
        """

        result = self.evaluator.evaluate(content)

        assert result.flesch_ease < 50
        assert len(result.issues) > 0

    def test_sentence_analysis(self):
        """Test sentence structure analysis."""
        content = """
        Short sentence. Another short one.
        This is a much longer sentence that goes on and on with many words
        and clauses and additional phrases that make it quite difficult to
        read and understand for most people who encounter it.
        """

        analysis = self.evaluator.analyze_sentence_structure(content)

        assert analysis.total_sentences >= 2
        assert len(analysis.long_sentences) > 0 or len(analysis.very_long_sentences) > 0


class TestStyleComplianceEvaluator:
    """Tests for the style compliance evaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = StyleComplianceEvaluator()

    def test_style_with_formatting_issues(self):
        """Test style compliance with formatting issues."""
        content = """
        this sentence starts lowercase. UNNECESSARY CAPS HERE!!
        Missing space.After punctuation  double spaces present.
        """

        result = self.evaluator.evaluate(content)

        assert result.formatting_score < 100
        assert len(result.formatting_issues) > 0

    def test_style_clean_content(self):
        """Test style compliance with clean content."""
        content = """
        This is a well-formatted sentence. It follows proper capitalization.

        The paragraphs are nicely separated. Each sentence is clear.

        Features include:
        - First feature
        - Second feature
        - Third feature
        """

        result = self.evaluator.evaluate(content)

        assert result.score >= 60


class TestTranslationEvaluator:
    """Tests for the translation evaluator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = TranslationEvaluator()

    def test_translation_length_ratio(self):
        """Test translation length ratio checking."""
        source = "This is a test sentence with several words."
        # French is typically 15-25% longer
        translation_good = "Ceci est une phrase de test avec plusieurs mots importants."
        translation_short = "Test phrase."

        result_good = self.evaluator.check_length_ratio(source, translation_good, "en-fr")
        result_short = self.evaluator.check_length_ratio(source, translation_short, "en-fr")

        assert result_good.score > result_short.score

    def test_translation_locale_rules(self):
        """Test locale-specific rule checking."""
        # Spanish content without inverted punctuation
        spanish_wrong = "Donde esta el producto?"
        spanish_correct = "Donde esta el producto?"

        result = self.evaluator.check_locale_rules(spanish_wrong, "es")

        # Should detect missing inverted question mark
        assert result.score < 100 or len(result.issues) > 0


class TestCompositeScorer:
    """Tests for the composite scorer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = CompositeScorer()
        self.sample_content = {
            "description": "Premium smartphone with advanced features and elegant design.",
            "marketing_copy": "Experience the future of mobile technology.",
            "feature_bullets": ["48MP camera", "All-day battery", "5G connectivity"],
            "meta_description": "Buy the latest premium smartphone with advanced camera."
        }
        self.sample_specs = {
            "name": "TechBrand Pro",
            "price": 999.99,
            "features": ["48MP camera", "5G connectivity"],
            "materials": ["Aluminum"],
            "colors": ["Black", "Silver"]
        }

    def test_composite_evaluation(self):
        """Test full composite evaluation."""
        result = self.scorer.evaluate_content(
            self.sample_content,
            self.sample_specs,
            "Consumer Electronics"
        )

        assert 0 <= result.composite_score <= 100
        assert result.quality_tier in ["Excellent", "Good", "Acceptable", "Needs Improvement", "Poor"]
        assert result.routing_decision in [
            "auto_publish", "light_review", "standard_review",
            "priority_review", "reject_regenerate"
        ]
        assert 0 <= result.confidence <= 1

    def test_dimension_scores_present(self):
        """Test that all dimension scores are present."""
        result = self.scorer.evaluate_content(
            self.sample_content,
            self.sample_specs,
            "Consumer Electronics"
        )

        assert "accuracy" in result.dimension_scores
        assert "completeness" in result.dimension_scores
        assert "brand_voice" in result.dimension_scores
        assert "seo" in result.dimension_scores
        assert "readability" in result.dimension_scores
        assert "style" in result.dimension_scores

    def test_version_comparison(self):
        """Test version comparison functionality."""
        content_a = {
            "description": "Basic product description.",
            "marketing_copy": "",
            "feature_bullets": [],
            "meta_description": ""
        }

        content_b = {
            "description": "Premium smartphone with advanced features and elegant design for professionals.",
            "marketing_copy": "Experience innovation with every interaction.",
            "feature_bullets": ["48MP camera", "All-day battery", "5G connectivity"],
            "meta_description": "Premium smartphone with advanced camera and 5G."
        }

        result_a = self.scorer.evaluate_content(content_a, self.sample_specs, "Consumer Electronics")
        result_b = self.scorer.evaluate_content(content_b, self.sample_specs, "Consumer Electronics")

        comparison = self.scorer.compare_versions(result_a, result_b)

        assert comparison.winner in ["version_a", "version_b", "tie"]
        assert comparison.score_delta == result_b.composite_score - result_a.composite_score

    def test_routing_decision(self):
        """Test routing decision logic."""
        # High score, high confidence should auto-publish
        assert self.scorer.determine_routing(95, 0.90) == "auto_publish"

        # Medium score should require review
        assert self.scorer.determine_routing(65, 0.70) == "standard_review"

        # Low score should be rejected
        assert self.scorer.determine_routing(30, 0.50) == "reject_regenerate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
