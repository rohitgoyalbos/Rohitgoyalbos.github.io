"""
Accuracy Evaluator for LLM Content Quality Evaluator.
Verifies that generated content accurately reflects source product specifications.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class Claim:
    """A verifiable claim extracted from content."""
    claim_type: str  # numerical, feature, material, performance, color, price
    claim_text: str
    confidence: float
    span_start: int
    span_end: int
    extracted_value: Any = None
    unit: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of verifying a claim against specifications."""
    verified: bool
    match_type: str  # exact, approximate, unverifiable
    source_value: Optional[str] = None
    discrepancy: Optional[str] = None


@dataclass
class AccuracyScore:
    """Accuracy evaluation result."""
    score: float
    verified_claims: int
    failed_claims: int
    unverifiable_claims: int
    errors: List[str] = field(default_factory=list)
    confidence: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)


class AccuracyEvaluator:
    """
    Evaluates factual accuracy of generated content against source specifications.

    Scoring methodology:
    1. Extract all claims/facts from generated content using pattern matching
    2. Match each claim against source specifications
    3. Score = (verified_claims / total_claims) * 100

    Claim types to verify:
    - Numerical values (dimensions, weights, prices, percentages)
    - Feature assertions (capabilities, included items)
    - Material/composition statements
    - Color claims
    - Price claims
    """

    # Patterns for extracting numerical claims
    DIMENSION_PATTERNS = [
        r'(\d+\.?\d*)\s*(?:-\s*)?(?:inch|inches|in|")',
        r'(\d+\.?\d*)\s*(?:-\s*)?(?:mm|millimeter|millimeters)',
        r'(\d+\.?\d*)\s*(?:-\s*)?(?:cm|centimeter|centimeters)',
    ]

    WEIGHT_PATTERNS = [
        r'(\d+\.?\d*)\s*(?:g|grams?|gram)',
        r'(\d+\.?\d*)\s*(?:kg|kilograms?|kilogram)',
        r'(\d+\.?\d*)\s*(?:oz|ounces?|ounce)',
        r'(\d+\.?\d*)\s*(?:lbs?|pounds?|pound)',
    ]

    PRICE_PATTERNS = [
        r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)',
    ]

    BATTERY_PATTERNS = [
        r'(\d+\.?\d*)\s*(?:-\s*)?(?:hour|hours|hr|hrs)\s*(?:battery|life)?',
        r'(\d+\.?\d*)\s*mAh',
    ]

    PERCENTAGE_PATTERNS = [
        r'(\d+\.?\d*)\s*(?:%|percent)',
    ]

    # Common unit conversions
    UNIT_CONVERSIONS = {
        'inches_to_mm': 25.4,
        'mm_to_inches': 0.0393701,
        'kg_to_g': 1000,
        'g_to_kg': 0.001,
        'oz_to_g': 28.3495,
        'g_to_oz': 0.035274,
        'lbs_to_kg': 0.453592,
        'kg_to_lbs': 2.20462,
    }

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the accuracy evaluator."""
        self.config = config or {}
        self.tolerance = self.config.get('numerical_tolerance', 0.05)  # 5% tolerance

    def extract_claims(self, text: str) -> List[Claim]:
        """
        Extract verifiable claims from generated content.

        Returns list of Claim objects with:
        - claim_type: numerical, feature, material, performance
        - claim_text: the extracted claim
        - confidence: extraction confidence score
        - span: character positions in source text
        """
        claims = []

        # Extract dimension claims
        for pattern in self.DIMENSION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = float(match.group(1))
                unit = self._extract_unit(match.group(0))
                claims.append(Claim(
                    claim_type="dimension",
                    claim_text=match.group(0),
                    confidence=0.9,
                    span_start=match.start(),
                    span_end=match.end(),
                    extracted_value=value,
                    unit=unit
                ))

        # Extract weight claims
        for pattern in self.WEIGHT_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = float(match.group(1))
                unit = self._extract_unit(match.group(0))
                claims.append(Claim(
                    claim_type="weight",
                    claim_text=match.group(0),
                    confidence=0.9,
                    span_start=match.start(),
                    span_end=match.end(),
                    extracted_value=value,
                    unit=unit
                ))

        # Extract price claims
        for pattern in self.PRICE_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value_str = match.group(1).replace(',', '')
                value = float(value_str)
                claims.append(Claim(
                    claim_type="price",
                    claim_text=match.group(0),
                    confidence=0.95,
                    span_start=match.start(),
                    span_end=match.end(),
                    extracted_value=value,
                    unit="USD"
                ))

        # Extract battery/hours claims
        for pattern in self.BATTERY_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                value = float(match.group(1))
                claims.append(Claim(
                    claim_type="battery",
                    claim_text=match.group(0),
                    confidence=0.85,
                    span_start=match.start(),
                    span_end=match.end(),
                    extracted_value=value,
                    unit="hours" if "hour" in match.group(0).lower() else "mAh"
                ))

        # Extract feature claims (phrases that match known features)
        feature_patterns = [
            r'(?:features?|includes?|with|has)\s+([^,.]+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Title Case phrases
        ]
        for pattern in feature_patterns:
            for match in re.finditer(pattern, text):
                feature_text = match.group(1).strip()
                if len(feature_text) > 3 and len(feature_text) < 100:
                    claims.append(Claim(
                        claim_type="feature",
                        claim_text=feature_text,
                        confidence=0.7,
                        span_start=match.start(1),
                        span_end=match.end(1),
                        extracted_value=feature_text
                    ))

        # Extract material claims
        material_patterns = [
            r'(?:made\s+(?:of|from|with)|crafted\s+(?:from|with)|constructed\s+(?:of|from|with))\s+([^,.]+)',
            r'((?:aluminum|steel|leather|cotton|polyester|titanium|glass|ceramic|plastic|wood|metal|fabric|rubber|silicone)[^\s,.]*)',
        ]
        for pattern in material_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                material = match.group(1).strip()
                if len(material) > 2:
                    claims.append(Claim(
                        claim_type="material",
                        claim_text=material,
                        confidence=0.8,
                        span_start=match.start(1),
                        span_end=match.end(1),
                        extracted_value=material.lower()
                    ))

        # Extract color claims
        color_patterns = [
            r'(?:available\s+in|comes\s+in|in)\s+([^,.]+(?:black|white|silver|gold|blue|red|green|gray|grey|pink|purple|orange|brown|navy)[^,.]*)',
            r'((?:space\s+)?(?:black|white|silver|gold|blue|red|green|gray|grey|pink|purple|orange|brown|navy)(?:\s+\w+)?)',
        ]
        for pattern in color_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                color = match.group(1).strip()
                claims.append(Claim(
                    claim_type="color",
                    claim_text=color,
                    confidence=0.85,
                    span_start=match.start(1),
                    span_end=match.end(1),
                    extracted_value=color.lower()
                ))

        # Remove duplicate claims
        unique_claims = self._deduplicate_claims(claims)
        return unique_claims

    def _extract_unit(self, text: str) -> str:
        """Extract the unit from a measurement string."""
        text_lower = text.lower()
        if 'inch' in text_lower or '"' in text:
            return 'inches'
        elif 'mm' in text_lower or 'millimeter' in text_lower:
            return 'mm'
        elif 'cm' in text_lower or 'centimeter' in text_lower:
            return 'cm'
        elif 'kg' in text_lower or 'kilogram' in text_lower:
            return 'kg'
        elif 'gram' in text_lower or text_lower.endswith('g'):
            return 'g'
        elif 'oz' in text_lower or 'ounce' in text_lower:
            return 'oz'
        elif 'lb' in text_lower or 'pound' in text_lower:
            return 'lbs'
        return 'unknown'

    def _deduplicate_claims(self, claims: List[Claim]) -> List[Claim]:
        """Remove duplicate claims based on overlapping spans."""
        if not claims:
            return []

        # Sort by span start
        sorted_claims = sorted(claims, key=lambda c: (c.span_start, -c.confidence))
        unique = [sorted_claims[0]]

        for claim in sorted_claims[1:]:
            last = unique[-1]
            # Check for overlap
            if claim.span_start >= last.span_end:
                unique.append(claim)
            elif claim.confidence > last.confidence:
                unique[-1] = claim

        return unique

    def verify_claim(
        self,
        claim: Claim,
        specifications: Dict[str, Any]
    ) -> VerificationResult:
        """
        Verify a single claim against source specifications.

        Returns VerificationResult with:
        - verified: bool
        - match_type: exact, approximate, unverifiable
        - source_value: what spec says
        - discrepancy: description of mismatch if any
        """
        if claim.claim_type == "dimension":
            return self._verify_dimension(claim, specifications)
        elif claim.claim_type == "weight":
            return self._verify_weight(claim, specifications)
        elif claim.claim_type == "price":
            return self._verify_price(claim, specifications)
        elif claim.claim_type == "feature":
            return self._verify_feature(claim, specifications)
        elif claim.claim_type == "material":
            return self._verify_material(claim, specifications)
        elif claim.claim_type == "color":
            return self._verify_color(claim, specifications)
        elif claim.claim_type == "battery":
            return self._verify_battery(claim, specifications)
        else:
            return VerificationResult(
                verified=True,
                match_type="unverifiable"
            )

    def _verify_dimension(
        self,
        claim: Claim,
        specifications: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a dimension claim."""
        dims = specifications.get("dimensions", {})
        if not dims:
            return VerificationResult(verified=True, match_type="unverifiable")

        claim_value = claim.extracted_value
        claim_unit = claim.unit

        # Normalize to inches for comparison
        if claim_unit == "mm":
            claim_value = claim_value * self.UNIT_CONVERSIONS['mm_to_inches']
        elif claim_unit == "cm":
            claim_value = claim_value * 0.393701

        # Check against each dimension
        for dim_name in ['length', 'width', 'height', 'display_size']:
            spec_value = dims.get(dim_name)
            if spec_value is None:
                continue

            # Handle dict format
            if isinstance(spec_value, dict):
                spec_value = spec_value.get('value', spec_value.get('length', 0))

            if spec_value and abs(claim_value - spec_value) <= spec_value * self.tolerance:
                return VerificationResult(
                    verified=True,
                    match_type="exact" if abs(claim_value - spec_value) < 0.01 else "approximate",
                    source_value=str(spec_value)
                )

        # Check top-level dimension specs
        for key in ['display_size', 'screen_size']:
            spec_value = specifications.get(key)
            if spec_value and abs(claim_value - spec_value) <= spec_value * self.tolerance:
                return VerificationResult(
                    verified=True,
                    match_type="approximate",
                    source_value=str(spec_value)
                )

        # If we found dimension specs but didn't match
        if dims:
            return VerificationResult(
                verified=False,
                match_type="failed",
                source_value=str(dims),
                discrepancy=f"Claimed {claim_value:.1f} {claim_unit}, but specs show different dimensions"
            )

        return VerificationResult(verified=True, match_type="unverifiable")

    def _verify_weight(
        self,
        claim: Claim,
        specifications: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a weight claim."""
        weight_spec = specifications.get("weight", {})
        if not weight_spec:
            return VerificationResult(verified=True, match_type="unverifiable")

        claim_value = claim.extracted_value
        claim_unit = claim.unit

        # Get spec value
        if isinstance(weight_spec, dict):
            spec_value = weight_spec.get("value", 0)
            spec_unit = weight_spec.get("unit", "g")
        else:
            spec_value = weight_spec
            spec_unit = "g"

        # Normalize both to grams
        if claim_unit == "kg":
            claim_value *= 1000
        elif claim_unit == "oz":
            claim_value *= 28.3495
        elif claim_unit == "lbs":
            claim_value *= 453.592

        if spec_unit == "kg":
            spec_value *= 1000

        # Compare with tolerance
        if abs(claim_value - spec_value) <= spec_value * self.tolerance:
            return VerificationResult(
                verified=True,
                match_type="exact" if abs(claim_value - spec_value) < 1 else "approximate",
                source_value=f"{spec_value}g"
            )

        return VerificationResult(
            verified=False,
            match_type="failed",
            source_value=f"{spec_value}g",
            discrepancy=f"Claimed {claim.extracted_value}{claim.unit}, spec says {weight_spec}"
        )

    def _verify_price(
        self,
        claim: Claim,
        specifications: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a price claim."""
        spec_price = specifications.get("price")
        if spec_price is None:
            return VerificationResult(verified=True, match_type="unverifiable")

        claim_value = claim.extracted_value

        # Allow for small price variance (promotional pricing, etc.)
        if abs(claim_value - spec_price) <= spec_price * 0.10:  # 10% tolerance for prices
            return VerificationResult(
                verified=True,
                match_type="exact" if abs(claim_value - spec_price) < 0.01 else "approximate",
                source_value=f"${spec_price:.2f}"
            )

        return VerificationResult(
            verified=False,
            match_type="failed",
            source_value=f"${spec_price:.2f}",
            discrepancy=f"Claimed ${claim_value:.2f}, spec price is ${spec_price:.2f}"
        )

    def _verify_feature(
        self,
        claim: Claim,
        specifications: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a feature claim."""
        features = specifications.get("features", [])
        if not features:
            return VerificationResult(verified=True, match_type="unverifiable")

        claim_text = claim.extracted_value.lower() if claim.extracted_value else claim.claim_text.lower()

        # Check for exact or fuzzy match
        for feature in features:
            feature_lower = feature.lower()
            if claim_text in feature_lower or feature_lower in claim_text:
                return VerificationResult(
                    verified=True,
                    match_type="exact",
                    source_value=feature
                )

            # Check for word overlap
            claim_words = set(claim_text.split())
            feature_words = set(feature_lower.split())
            overlap = claim_words & feature_words
            if len(overlap) >= 2:  # At least 2 words match
                return VerificationResult(
                    verified=True,
                    match_type="approximate",
                    source_value=feature
                )

        # Feature not found - could be invented
        return VerificationResult(
            verified=True,  # Don't penalize for features we can't verify
            match_type="unverifiable"
        )

    def _verify_material(
        self,
        claim: Claim,
        specifications: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a material claim."""
        materials = specifications.get("materials", [])
        if not materials:
            return VerificationResult(verified=True, match_type="unverifiable")

        claim_material = claim.extracted_value.lower() if claim.extracted_value else ""

        for material in materials:
            material_lower = material.lower()
            if claim_material in material_lower or material_lower in claim_material:
                return VerificationResult(
                    verified=True,
                    match_type="exact",
                    source_value=material
                )

        return VerificationResult(
            verified=False,
            match_type="failed",
            source_value=", ".join(materials),
            discrepancy=f"Claimed material '{claim.claim_text}' not in specs: {materials}"
        )

    def _verify_color(
        self,
        claim: Claim,
        specifications: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a color claim."""
        colors = specifications.get("colors", [])
        if not colors:
            return VerificationResult(verified=True, match_type="unverifiable")

        claim_color = claim.extracted_value.lower() if claim.extracted_value else ""

        for color in colors:
            color_lower = color.lower()
            if claim_color in color_lower or color_lower in claim_color:
                return VerificationResult(
                    verified=True,
                    match_type="exact",
                    source_value=color
                )
            # Check for color word match
            for word in claim_color.split():
                if word in color_lower:
                    return VerificationResult(
                        verified=True,
                        match_type="approximate",
                        source_value=color
                    )

        return VerificationResult(
            verified=False,
            match_type="failed",
            source_value=", ".join(colors),
            discrepancy=f"Color '{claim.claim_text}' not in available colors"
        )

    def _verify_battery(
        self,
        claim: Claim,
        specifications: Dict[str, Any]
    ) -> VerificationResult:
        """Verify a battery/hours claim."""
        battery_spec = specifications.get("battery_hours") or specifications.get("battery")
        if battery_spec is None:
            return VerificationResult(verified=True, match_type="unverifiable")

        if isinstance(battery_spec, dict):
            battery_spec = battery_spec.get("value", 0)

        claim_value = claim.extracted_value

        if abs(claim_value - battery_spec) <= battery_spec * self.tolerance:
            return VerificationResult(
                verified=True,
                match_type="approximate",
                source_value=str(battery_spec)
            )

        return VerificationResult(
            verified=False,
            match_type="failed",
            source_value=str(battery_spec),
            discrepancy=f"Claimed {claim_value} hours, spec says {battery_spec}"
        )

    def evaluate(
        self,
        content: str,
        specifications: Dict[str, Any]
    ) -> AccuracyScore:
        """
        Main evaluation method.

        Returns AccuracyScore with:
        - score: 0-100
        - verified_claims: count
        - failed_claims: count
        - unverifiable_claims: count
        - errors: list of specific errors found
        - confidence: confidence in the score
        """
        # Combine all content fields if dict
        if isinstance(content, dict):
            text_parts = []
            for field in ['description', 'marketing_copy', 'meta_description']:
                if field in content and content[field]:
                    text_parts.append(content[field])
            if 'feature_bullets' in content and content['feature_bullets']:
                text_parts.extend(content['feature_bullets'])
            content = " ".join(text_parts)

        # Extract claims
        claims = self.extract_claims(content)

        if not claims:
            return AccuracyScore(
                score=100.0,
                verified_claims=0,
                failed_claims=0,
                unverifiable_claims=0,
                confidence=0.5,  # Low confidence when no claims found
                details={"message": "No verifiable claims found in content"}
            )

        # Verify each claim
        verified = 0
        failed = 0
        unverifiable = 0
        errors = []
        claim_results = []

        for claim in claims:
            result = self.verify_claim(claim, specifications)
            claim_results.append({
                "claim": claim.claim_text,
                "type": claim.claim_type,
                "result": result.match_type,
                "source_value": result.source_value,
                "discrepancy": result.discrepancy
            })

            if result.match_type == "unverifiable":
                unverifiable += 1
            elif result.verified:
                verified += 1
            else:
                failed += 1
                if result.discrepancy:
                    errors.append(result.discrepancy)

        # Calculate score
        verifiable_claims = verified + failed
        if verifiable_claims > 0:
            score = (verified / verifiable_claims) * 100
        else:
            score = 100.0

        # Calculate confidence based on number of claims
        confidence = min(0.95, 0.5 + (len(claims) * 0.05))

        return AccuracyScore(
            score=round(score, 2),
            verified_claims=verified,
            failed_claims=failed,
            unverifiable_claims=unverifiable,
            errors=errors,
            confidence=confidence,
            details={
                "total_claims": len(claims),
                "claim_results": claim_results
            }
        )

    def evaluate_content_dict(
        self,
        content: Dict[str, Any],
        specifications: Dict[str, Any]
    ) -> AccuracyScore:
        """Evaluate a content dictionary with multiple fields."""
        return self.evaluate(content, specifications)
