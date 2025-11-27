"""
Tests for synthetic data generation in LLM Content Quality Evaluator.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.synthetic_generator import SyntheticDataGenerator


class TestSyntheticDataGenerator:
    """Tests for the synthetic data generator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SyntheticDataGenerator(seed=42)

    def test_generate_product(self):
        """Test single product generation."""
        product = self.generator.generate_product()

        assert "product_id" in product
        assert "category" in product
        assert "specifications" in product
        assert "generated_content" in product

        # Check specifications
        specs = product["specifications"]
        assert "name" in specs
        assert "brand" in specs

        # Check generated content
        content = product["generated_content"]
        assert len(content) > 0

    def test_generate_product_with_category(self):
        """Test product generation with specific category."""
        product = self.generator.generate_product(category="Fashion/Apparel")

        assert product["category"] == "Fashion/Apparel"
        assert "specifications" in product

    def test_generate_product_with_quality_level(self):
        """Test product generation with specific quality level."""
        product_excellent = self.generator.generate_product(quality_level="excellent")
        product_poor = self.generator.generate_product(quality_level="poor")

        # Both should be valid products
        assert "generated_content" in product_excellent
        assert "generated_content" in product_poor

        # Check quality levels are set
        first_version_excellent = list(product_excellent["generated_content"].values())[0]
        first_version_poor = list(product_poor["generated_content"].values())[0]

        assert first_version_excellent["quality_level"] == "excellent"
        assert first_version_poor["quality_level"] == "poor"

    def test_generate_content_variations(self):
        """Test that content varies by quality level."""
        specs = {
            "name": "Test Product",
            "brand": "TestBrand",
            "features": ["Feature 1", "Feature 2"],
            "materials": ["Material 1"],
            "colors": ["Black", "White"],
            "price": 99.99
        }

        content_excellent = self.generator.generate_content(
            specs, "excellent", "Consumer Electronics"
        )
        content_poor = self.generator.generate_content(
            specs, "poor", "Consumer Electronics"
        )

        # Both should have content
        assert "description" in content_excellent
        assert "description" in content_poor

        # Poor content often has prohibited phrases injected
        # (though not guaranteed due to probability)
        assert content_excellent["description"] != content_poor["description"]

    def test_generate_translations(self):
        """Test translation generation."""
        content = {
            "description": "This is a product description.",
            "marketing_copy": "Buy this amazing product!",
            "feature_bullets": ["Feature 1", "Feature 2"]
        }

        translations = self.generator.generate_translations(content)

        assert "fr-CA" in translations
        assert "es" in translations
        assert "de" in translations

        # Check translation structure
        for lang, trans in translations.items():
            assert "description" in trans
            assert lang.upper() in trans["description"]

    def test_generate_human_review(self):
        """Test human review generation."""
        review = self.generator.generate_human_review("content-123", 75.0)

        assert "review_id" in review
        assert "content_id" in review
        assert review["content_id"] == "content-123"
        assert "scores" in review
        assert "verdict" in review
        assert review["verdict"] in ["approve", "conditional_approve", "reject"]

    def test_generate_performance_metrics(self):
        """Test performance metrics generation."""
        metrics = self.generator.generate_performance_metrics("content-123", 85.0)

        assert "content_id" in metrics
        assert "traffic_metrics" in metrics
        assert "engagement_metrics" in metrics
        assert "conversion_metrics" in metrics

        # Check that metrics are positive
        assert metrics["traffic_metrics"]["impressions"] > 0
        assert metrics["conversion_metrics"]["conversion_rate"] > 0

    def test_generate_brand_guidelines(self):
        """Test brand guidelines generation."""
        guidelines = self.generator.generate_brand_guidelines("TestBrand")

        assert guidelines["brand_name"] == "TestBrand"
        assert "voice_attributes" in guidelines
        assert "terminology" in guidelines
        assert "style_rules" in guidelines
        assert "seo_requirements" in guidelines

        # Check terminology structure
        assert "preferred" in guidelines["terminology"]
        assert "prohibited" in guidelines["terminology"]
        assert len(guidelines["terminology"]["prohibited"]) > 0

    def test_generate_dataset(self):
        """Test full dataset generation."""
        dataset = self.generator.generate_dataset(
            num_products=10,
            include_translations=True,
            include_reviews=True,
            include_metrics=True
        )

        assert "products" in dataset
        assert "human_reviews" in dataset
        assert "performance_metrics" in dataset
        assert "brand_guidelines" in dataset

        assert len(dataset["products"]) == 10
        assert dataset["total_products"] == 10
        assert dataset["total_content_versions"] >= 10

    def test_generate_dataset_without_optional_data(self):
        """Test dataset generation without optional data."""
        dataset = self.generator.generate_dataset(
            num_products=5,
            include_translations=False,
            include_reviews=False,
            include_metrics=False
        )

        assert len(dataset["products"]) == 5
        assert len(dataset["human_reviews"]) == 0
        assert len(dataset["performance_metrics"]) == 0

    def test_quality_distribution(self):
        """Test that quality levels follow expected distribution."""
        num_products = 100
        quality_counts = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0}

        for _ in range(num_products):
            product = self.generator.generate_product()
            first_version = list(product["generated_content"].values())[0]
            quality = first_version.get("quality_level", "unknown")
            if quality in quality_counts:
                quality_counts[quality] += 1

        # Check rough distribution (with some tolerance)
        total = sum(quality_counts.values())
        if total > 0:
            excellent_rate = quality_counts["excellent"] / total
            poor_rate = quality_counts["poor"] / total

            # Expected: excellent ~20%, poor ~20%
            # Allow significant tolerance due to randomness
            assert excellent_rate > 0.05, f"Too few excellent: {excellent_rate}"
            assert poor_rate > 0.05, f"Too few poor: {poor_rate}"

    def test_product_id_uniqueness(self):
        """Test that generated product IDs are unique."""
        products = [self.generator.generate_product() for _ in range(50)]
        product_ids = [p["product_id"] for p in products]

        assert len(product_ids) == len(set(product_ids))

    def test_all_categories_covered(self):
        """Test that all categories can be generated."""
        categories = [
            "Consumer Electronics",
            "Fashion/Apparel",
            "Home & Garden",
            "Beauty & Personal Care",
            "Sports & Outdoors"
        ]

        for category in categories:
            product = self.generator.generate_product(category=category)
            assert product["category"] == category


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
