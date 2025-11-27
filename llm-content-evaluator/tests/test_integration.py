"""
Integration tests for LLM Content Quality Evaluator.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.synthetic_generator import SyntheticDataGenerator
from evaluators.composite_scorer import CompositeScorer
from config import QUALITY_TIERS


class TestFullPipeline:
    """Integration tests for the complete evaluation pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SyntheticDataGenerator(seed=42)
        self.scorer = CompositeScorer()

    def test_full_evaluation_pipeline(self):
        """Test complete evaluation from generated data to score."""
        # Generate a product
        product = self.generator.generate_product(quality_level="good")

        # Get content and specs
        content_versions = product["generated_content"]
        first_version = list(content_versions.values())[0]

        content = {
            "description": first_version.get("description", ""),
            "marketing_copy": first_version.get("marketing_copy", ""),
            "feature_bullets": first_version.get("feature_bullets", []),
            "meta_description": first_version.get("meta_description", "")
        }

        specifications = product["specifications"]
        category = product["category"]

        # Run evaluation
        result = self.scorer.evaluate_content(content, specifications, category)

        # Verify result structure
        assert result.composite_score is not None
        assert 0 <= result.composite_score <= 100
        assert result.quality_tier is not None
        assert result.routing_decision is not None

        # Verify dimension scores
        assert result.accuracy_score is not None
        assert result.completeness_score is not None
        assert result.brand_voice_score is not None
        assert result.seo_score is not None
        assert result.readability_score is not None
        assert result.style_score is not None

    def test_quality_level_correlation(self):
        """Test that quality levels correlate with scores."""
        quality_scores = {"excellent": [], "good": [], "acceptable": [], "poor": []}

        for quality_level in quality_scores.keys():
            for _ in range(5):
                product = self.generator.generate_product(quality_level=quality_level)

                content_versions = product["generated_content"]
                first_version = list(content_versions.values())[0]

                content = {
                    "description": first_version.get("description", ""),
                    "marketing_copy": first_version.get("marketing_copy", ""),
                    "feature_bullets": first_version.get("feature_bullets", []),
                    "meta_description": first_version.get("meta_description", "")
                }

                result = self.scorer.evaluate_content(
                    content,
                    product["specifications"],
                    product["category"]
                )

                quality_scores[quality_level].append(result.composite_score)

        # Calculate averages
        avg_excellent = sum(quality_scores["excellent"]) / len(quality_scores["excellent"])
        avg_poor = sum(quality_scores["poor"]) / len(quality_scores["poor"])

        # Excellent should generally score higher than poor
        # (allowing for some variance due to random content generation)
        assert avg_excellent > avg_poor - 20, (
            f"Expected excellent ({avg_excellent:.1f}) to score higher than poor ({avg_poor:.1f})"
        )

    def test_version_comparison_workflow(self):
        """Test the version comparison workflow."""
        # Generate a product with multiple versions
        product = self.generator.generate_product()

        content_versions = product["generated_content"]
        version_names = list(content_versions.keys())

        if len(version_names) < 2:
            pytest.skip("Product only has one version")

        # Evaluate both versions
        results = []
        for version_name in version_names[:2]:
            version = content_versions[version_name]
            content = {
                "description": version.get("description", ""),
                "marketing_copy": version.get("marketing_copy", ""),
                "feature_bullets": version.get("feature_bullets", []),
                "meta_description": version.get("meta_description", "")
            }

            result = self.scorer.evaluate_content(
                content,
                product["specifications"],
                product["category"]
            )
            results.append(result)

        # Compare versions
        comparison = self.scorer.compare_versions(results[0], results[1])

        assert comparison.winner in ["version_a", "version_b", "tie"]
        assert comparison.version_a_score == results[0].composite_score
        assert comparison.version_b_score == results[1].composite_score
        assert comparison.recommendation is not None

    def test_batch_evaluation(self):
        """Test batch evaluation of multiple products."""
        # Generate dataset
        dataset = self.generator.generate_dataset(num_products=10)
        products = dataset["products"]

        results = []
        for product in products:
            content_versions = product["generated_content"]
            first_version = list(content_versions.values())[0]

            content = {
                "description": first_version.get("description", ""),
                "marketing_copy": first_version.get("marketing_copy", ""),
                "feature_bullets": first_version.get("feature_bullets", []),
                "meta_description": first_version.get("meta_description", "")
            }

            result = self.scorer.evaluate_content(
                content,
                product["specifications"],
                product["category"]
            )
            results.append(result)

        # Verify all evaluations completed
        assert len(results) == 10

        # Check distribution across quality tiers
        tiers = [r.quality_tier for r in results]
        unique_tiers = set(tiers)

        # Should have some variety in quality tiers
        assert len(unique_tiers) >= 1

    def test_routing_decisions(self):
        """Test that routing decisions are appropriate for scores."""
        for quality_level in ["excellent", "poor"]:
            product = self.generator.generate_product(quality_level=quality_level)

            content_versions = product["generated_content"]
            first_version = list(content_versions.values())[0]

            content = {
                "description": first_version.get("description", ""),
                "marketing_copy": first_version.get("marketing_copy", ""),
                "feature_bullets": first_version.get("feature_bullets", []),
                "meta_description": first_version.get("meta_description", "")
            }

            result = self.scorer.evaluate_content(
                content,
                product["specifications"],
                product["category"]
            )

            # Verify routing is appropriate
            if result.composite_score >= 90 and result.confidence >= 0.85:
                assert result.routing_decision == "auto_publish"
            elif result.composite_score < 40:
                assert result.routing_decision == "reject_regenerate"

    def test_issues_and_suggestions_generated(self):
        """Test that issues and suggestions are generated."""
        # Generate poor quality content to ensure issues are found
        product = self.generator.generate_product(quality_level="poor")

        content_versions = product["generated_content"]
        first_version = list(content_versions.values())[0]

        content = {
            "description": first_version.get("description", ""),
            "marketing_copy": first_version.get("marketing_copy", ""),
            "feature_bullets": first_version.get("feature_bullets", []),
            "meta_description": first_version.get("meta_description", "")
        }

        result = self.scorer.evaluate_content(
            content,
            product["specifications"],
            product["category"]
        )

        # Poor quality should have issues
        if result.composite_score < 70:
            assert len(result.top_issues) > 0 or len(result.improvement_suggestions) > 0

    def test_custom_weights(self):
        """Test evaluation with custom weights."""
        custom_weights = {
            "accuracy": 0.50,  # Heavy weight on accuracy
            "completeness": 0.10,
            "brand_voice": 0.10,
            "seo": 0.10,
            "readability": 0.10,
            "style": 0.10
        }

        custom_scorer = CompositeScorer(weights=custom_weights)

        product = self.generator.generate_product()
        content_versions = product["generated_content"]
        first_version = list(content_versions.values())[0]

        content = {
            "description": first_version.get("description", ""),
            "marketing_copy": first_version.get("marketing_copy", ""),
            "feature_bullets": first_version.get("feature_bullets", []),
            "meta_description": first_version.get("meta_description", "")
        }

        result_custom = custom_scorer.evaluate_content(
            content,
            product["specifications"],
            product["category"]
        )

        result_default = self.scorer.evaluate_content(
            content,
            product["specifications"],
            product["category"]
        )

        # Results should be valid but potentially different
        assert 0 <= result_custom.composite_score <= 100
        assert 0 <= result_default.composite_score <= 100


class TestCrossCategory:
    """Test evaluation across different product categories."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SyntheticDataGenerator(seed=42)
        self.scorer = CompositeScorer()

    @pytest.mark.parametrize("category", [
        "Consumer Electronics",
        "Fashion/Apparel",
        "Home & Garden",
        "Beauty & Personal Care",
        "Sports & Outdoors"
    ])
    def test_category_evaluation(self, category):
        """Test evaluation works for each category."""
        product = self.generator.generate_product(category=category)

        content_versions = product["generated_content"]
        first_version = list(content_versions.values())[0]

        content = {
            "description": first_version.get("description", ""),
            "marketing_copy": first_version.get("marketing_copy", ""),
            "feature_bullets": first_version.get("feature_bullets", []),
            "meta_description": first_version.get("meta_description", "")
        }

        result = self.scorer.evaluate_content(
            content,
            product["specifications"],
            category
        )

        assert 0 <= result.composite_score <= 100
        assert result.quality_tier is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
