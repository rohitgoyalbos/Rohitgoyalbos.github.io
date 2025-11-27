"""
Completeness Evaluator for LLM Content Quality Evaluator.
Ensures all required product information is present based on category-specific templates.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from config import CATEGORY_TEMPLATES, ATTRIBUTE_WEIGHTS


@dataclass
class AttributeCheck:
    """Result of checking an attribute's presence."""
    attribute: str
    present: bool
    quality: str  # none, partial, complete
    extracted_value: Optional[str] = None
    confidence: float = 1.0


@dataclass
class CompletenessScore:
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
    missing_critical: List[str] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    missing_recommended: List[str] = field(default_factory=list)
    attribute_checks: List[AttributeCheck] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class CompletenessEvaluator:
    """
    Evaluates content completeness against category-specific requirements.

    Attribute tiers:
    - Critical (weight 3.0): Missing = publishing blocked
    - Required (weight 2.0): Missing = 15% penalty each
    - Recommended (weight 1.5): Missing = 5% penalty each
    - Optional (weight 1.0): Present = bonus points
    """

    # Patterns for detecting attribute presence
    ATTRIBUTE_PATTERNS = {
        "product_name": [
            r'^\s*([A-Z][^\n.]+)',  # Title at start
            r'(?:introducing|meet|discover)\s+(?:the\s+)?([A-Z][^\n,.]+)',
        ],
        "price": [
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            r'\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD)',
            r'(?:starting\s+at|from|only)\s+\$?\d+',
            r'(?:price|cost|priced\s+at)',
        ],
        "brand": [
            r'(?:by|from)\s+([A-Z][a-zA-Z]+)',
            r'([A-Z][a-zA-Z]+(?:Brand|Pro|Max|Tech|Style))',
        ],
        "description": [
            r'.{100,}',  # At least 100 characters
        ],
        "specifications": [
            r'(?:specifications?|specs|technical)',
            r'\d+\.?\d*\s*(?:inch|mm|cm|g|kg|mAh|GB|TB)',
        ],
        "features": [
            r'(?:features?|includes?|with)',
            r'(?:•|·|\*|-)\s+[A-Z]',  # Bullet points
        ],
        "warranty": [
            r'(?:warranty|guarantee)',
            r'\d+\s*(?:year|month|day)s?\s*(?:warranty|guarantee|coverage)',
        ],
        "dimensions": [
            r'(?:dimensions?|size|measures?)',
            r'\d+\.?\d*\s*(?:x|×)\s*\d+\.?\d*',
            r'(?:length|width|height|depth)',
        ],
        "weight": [
            r'(?:weight|weighs?)',
            r'\d+\.?\d*\s*(?:g|grams?|kg|kilograms?|oz|ounces?|lbs?|pounds?)',
        ],
        "compatibility": [
            r'(?:compatible|works\s+with|supports?)',
            r'(?:iOS|Android|Windows|Mac)',
        ],
        "whats_included": [
            r'(?:included|in\s+the\s+box|comes\s+with|package\s+contains)',
            r'(?:accessories|charger|cable|adapter)',
        ],
        "material": [
            r'(?:made\s+(?:of|from|with)|material|fabric|constructed)',
            r'(?:cotton|polyester|leather|aluminum|steel|plastic|wood|glass)',
        ],
        "care_instructions": [
            r'(?:care|wash|clean|maintain)',
            r'(?:machine\s+wash|hand\s+wash|dry\s+clean|wipe)',
        ],
        "size_available": [
            r'(?:sizes?|available\s+in)',
            r'(?:XS|S|M|L|XL|XXL|\d+\s*(?:cm|inch))',
        ],
        "color": [
            r'(?:colors?|available\s+in)',
            r'(?:black|white|blue|red|green|gray|grey|silver|gold)',
        ],
        "fit_guide": [
            r'(?:fit|sizing|size\s+guide)',
            r'(?:regular|slim|loose|tight)',
        ],
        "model_measurements": [
            r'(?:model\s+(?:is|wears|measures))',
            r'(?:height|bust|waist|hips)',
        ],
        "sustainability_info": [
            r'(?:sustainable|eco|recycled|organic|environmental)',
            r'(?:carbon|footprint|green|renewable)',
        ],
        "assembly_info": [
            r'(?:assembly|assemble|put\s+together)',
            r'(?:tools?\s+(?:required|needed|included))',
        ],
        "ingredients": [
            r'(?:ingredients?|contains|formula)',
            r'(?:vitamin|acid|extract|oil)',
        ],
        "usage_instructions": [
            r'(?:how\s+to\s+use|apply|usage|directions)',
            r'(?:daily|twice|once|morning|night)',
        ],
        "skin_type": [
            r'(?:skin\s+type|for\s+(?:all|dry|oily|sensitive|combination)\s+skin)',
        ],
        "benefits": [
            r'(?:benefits?|helps?|provides?|delivers?)',
            r'(?:hydrat|moistur|firm|bright|anti)',
        ],
        "warnings": [
            r'(?:warning|caution|avoid|do\s+not)',
            r'(?:allergic|sensitive|discontinue)',
        ],
        "cruelty_free": [
            r'(?:cruelty|animal|vegan|not\s+tested)',
        ],
        "size_guide": [
            r'(?:size\s+(?:guide|chart)|sizing)',
            r'(?:measure|fit)',
        ],
        "suitable_activities": [
            r'(?:suitable|ideal|perfect|great)\s+for',
            r'(?:running|yoga|gym|hiking|training)',
        ],
    }

    def __init__(self, category_templates: Optional[Dict] = None):
        """Initialize the completeness evaluator."""
        self.templates = category_templates or CATEGORY_TEMPLATES
        self.weights = ATTRIBUTE_WEIGHTS

    def get_requirements(
        self,
        category: str,
        subcategory: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Get attribute requirements for product category."""
        if category not in self.templates:
            # Return default requirements
            return {
                "critical": ["product_name", "price"],
                "required": ["description", "features"],
                "recommended": ["specifications", "warranty"],
                "optional": []
            }

        return self.templates[category]

    def check_attribute_presence(
        self,
        content: str,
        attribute: str,
        specifications: Optional[Dict] = None
    ) -> AttributeCheck:
        """
        Check if a required attribute is present in content.

        Returns:
        - present: bool
        - quality: none/partial/complete
        - extracted_value: the found value if present
        """
        patterns = self.ATTRIBUTE_PATTERNS.get(attribute, [])

        # Check if attribute might be in specifications
        spec_value = None
        if specifications:
            spec_value = self._get_spec_value(attribute, specifications)

        # Search in content
        found = False
        quality = "none"
        extracted_value = None
        confidence = 0.0

        for pattern in patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
            if matches:
                found = True
                # Get the best match
                best_match = max(matches, key=lambda m: len(m.group(0)))
                extracted_value = best_match.group(0)[:100]  # Limit length
                confidence = max(confidence, 0.8)

                # Determine quality
                if len(best_match.group(0)) > 50:
                    quality = "complete"
                else:
                    quality = "partial"

        # Cross-check with specifications if available
        if spec_value and not found:
            # Check if spec value appears in content
            if str(spec_value).lower() in content.lower():
                found = True
                quality = "partial"
                extracted_value = str(spec_value)
                confidence = 0.7

        # Special handling for certain attributes
        if attribute == "description":
            # Check content length
            if len(content) >= 300:
                found = True
                quality = "complete"
            elif len(content) >= 100:
                found = True
                quality = "partial"

        if attribute == "features":
            # Check for bullet points or feature list
            bullet_count = len(re.findall(r'(?:•|·|\*|-)\s+\S', content))
            if bullet_count >= 3:
                found = True
                quality = "complete"
            elif bullet_count >= 1:
                found = True
                quality = "partial"

        return AttributeCheck(
            attribute=attribute,
            present=found,
            quality=quality if found else "none",
            extracted_value=extracted_value,
            confidence=confidence if found else 0.0
        )

    def _get_spec_value(
        self,
        attribute: str,
        specifications: Dict[str, Any]
    ) -> Optional[Any]:
        """Extract attribute value from specifications."""
        # Direct mapping
        if attribute in specifications:
            return specifications[attribute]

        # Handle nested or alternate names
        mappings = {
            "product_name": ["name", "title", "product_name"],
            "price": ["price", "msrp", "retail_price"],
            "brand": ["brand", "manufacturer"],
            "dimensions": ["dimensions", "size"],
            "weight": ["weight"],
            "warranty": ["warranty", "guarantee"],
            "material": ["materials", "material", "fabric"],
            "color": ["colors", "color", "available_colors"],
        }

        for key in mappings.get(attribute, []):
            if key in specifications:
                return specifications[key]

        return None

    def evaluate(
        self,
        content: str,
        category: str,
        subcategory: Optional[str] = None,
        specifications: Optional[Dict] = None
    ) -> CompletenessScore:
        """
        Evaluate content completeness.

        Returns CompletenessScore with:
        - score: 0-100 (weighted)
        - critical_present: count/total
        - required_present: count/total
        - recommended_present: count/total
        - optional_present: count/total
        - missing_critical: list (blocks publishing)
        - missing_required: list
        - missing_recommended: list
        """
        # Combine content if it's a dict
        if isinstance(content, dict):
            text_parts = []
            for field in ['description', 'marketing_copy', 'meta_description']:
                if field in content and content[field]:
                    text_parts.append(str(content[field]))
            if 'feature_bullets' in content and content['feature_bullets']:
                if isinstance(content['feature_bullets'], list):
                    text_parts.extend(content['feature_bullets'])
                else:
                    text_parts.append(str(content['feature_bullets']))
            content = " ".join(text_parts)

        requirements = self.get_requirements(category, subcategory)

        # Check each tier
        attribute_checks = []
        tier_results = {
            "critical": {"present": 0, "total": 0, "missing": []},
            "required": {"present": 0, "total": 0, "missing": []},
            "recommended": {"present": 0, "total": 0, "missing": []},
            "optional": {"present": 0, "total": 0, "missing": []}
        }

        for tier in ["critical", "required", "recommended", "optional"]:
            attributes = requirements.get(tier, [])
            tier_results[tier]["total"] = len(attributes)

            for attr in attributes:
                check = self.check_attribute_presence(content, attr, specifications)
                attribute_checks.append(check)

                if check.present:
                    tier_results[tier]["present"] += 1
                else:
                    tier_results[tier]["missing"].append(attr)

        # Calculate weighted score
        score = self._calculate_score(tier_results)

        return CompletenessScore(
            score=round(score, 2),
            critical_present=tier_results["critical"]["present"],
            critical_total=tier_results["critical"]["total"],
            required_present=tier_results["required"]["present"],
            required_total=tier_results["required"]["total"],
            recommended_present=tier_results["recommended"]["present"],
            recommended_total=tier_results["recommended"]["total"],
            optional_present=tier_results["optional"]["present"],
            optional_total=tier_results["optional"]["total"],
            missing_critical=tier_results["critical"]["missing"],
            missing_required=tier_results["required"]["missing"],
            missing_recommended=tier_results["recommended"]["missing"],
            attribute_checks=attribute_checks,
            details={
                "tier_results": tier_results,
                "category": category,
                "subcategory": subcategory
            }
        )

    def _calculate_score(self, tier_results: Dict[str, Dict]) -> float:
        """Calculate weighted completeness score."""
        total_weight = 0
        earned_weight = 0

        for tier, results in tier_results.items():
            if results["total"] == 0:
                continue

            tier_weight = self.weights.get(tier, 1.0)
            total_attributes = results["total"]
            present_attributes = results["present"]

            # Calculate tier contribution
            tier_total_weight = tier_weight * total_attributes
            tier_earned_weight = tier_weight * present_attributes

            total_weight += tier_total_weight
            earned_weight += tier_earned_weight

        if total_weight == 0:
            return 100.0

        base_score = (earned_weight / total_weight) * 100

        # Apply penalties for missing critical attributes
        critical_missing = len(tier_results["critical"]["missing"])
        if critical_missing > 0:
            # Severe penalty for missing critical attributes
            penalty = min(50, critical_missing * 20)  # Up to 50% penalty
            base_score = max(0, base_score - penalty)

        return base_score

    def evaluate_content_dict(
        self,
        content: Dict[str, Any],
        category: str,
        specifications: Optional[Dict] = None
    ) -> CompletenessScore:
        """Evaluate a content dictionary."""
        return self.evaluate(content, category, specifications=specifications)

    def get_missing_attributes_summary(
        self,
        score: CompletenessScore
    ) -> Dict[str, Any]:
        """Get a summary of missing attributes with priorities."""
        summary = {
            "blocking_issues": [],
            "high_priority": [],
            "medium_priority": [],
            "low_priority": []
        }

        # Critical = blocking
        for attr in score.missing_critical:
            summary["blocking_issues"].append({
                "attribute": attr,
                "message": f"Missing critical attribute: {attr.replace('_', ' ').title()}",
                "action": "Must be added before publishing"
            })

        # Required = high priority
        for attr in score.missing_required:
            summary["high_priority"].append({
                "attribute": attr,
                "message": f"Missing required attribute: {attr.replace('_', ' ').title()}",
                "action": "Should be added for quality content"
            })

        # Recommended = medium priority
        for attr in score.missing_recommended:
            summary["medium_priority"].append({
                "attribute": attr,
                "message": f"Missing recommended attribute: {attr.replace('_', ' ').title()}",
                "action": "Recommended for enhanced content"
            })

        return summary
