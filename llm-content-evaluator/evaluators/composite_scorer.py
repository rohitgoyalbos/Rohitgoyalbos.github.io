"""
Composite Scorer for LLM Content Quality Evaluator.
Combines all dimension scores into a final quality score.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from config import DEFAULT_WEIGHTS, QUALITY_TIERS, ROUTING_THRESHOLDS
from evaluators.accuracy_evaluator import AccuracyEvaluator, AccuracyScore
from evaluators.completeness_evaluator import CompletenessEvaluator, CompletenessScore
from evaluators.brand_voice_evaluator import BrandVoiceEvaluator, BrandVoiceScore
from evaluators.seo_evaluator import SEOEvaluator, SEOScore
from evaluators.readability_evaluator import ReadabilityEvaluator, ReadabilityScore
from evaluators.style_compliance_evaluator import StyleComplianceEvaluator, StyleComplianceScore
from evaluators.translation_evaluator import TranslationEvaluator, TranslationScore


@dataclass
class Issue:
    """An issue found during evaluation."""
    dimension: str
    severity: str  # critical, major, minor, suggestion
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class CompositeScore:
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

    dimension_scores: Dict[str, float] = field(default_factory=dict)
    top_issues: List[Issue] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

    accuracy_details: Optional[AccuracyScore] = None
    completeness_details: Optional[CompletenessScore] = None
    brand_voice_details: Optional[BrandVoiceScore] = None
    seo_details: Optional[SEOScore] = None
    readability_details: Optional[ReadabilityScore] = None
    style_details: Optional[StyleComplianceScore] = None
    translation_details: Optional[TranslationScore] = None


@dataclass
class VersionComparison:
    """Comparison result between two content versions."""
    winner: str  # version_a, version_b, tie
    score_delta: float
    dimension_deltas: Dict[str, float] = field(default_factory=dict)
    version_a_score: float = 0
    version_b_score: float = 0
    recommendation: str = ""
    improvements: List[str] = field(default_factory=list)
    regressions: List[str] = field(default_factory=list)


class CompositeScorer:
    """
    Combines individual dimension scores into composite quality score.

    Default weights (customizable):
    - Factual Accuracy: 25%
    - Completeness: 20%
    - Brand Voice: 15%
    - SEO: 15%
    - Readability: 10%
    - Style Compliance: 10%
    - Translation Quality: 5% (when applicable)
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        brand_guidelines: Optional[Dict] = None
    ):
        """Initialize the composite scorer with optional custom weights."""
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.brand_guidelines = brand_guidelines or {}

        # Initialize evaluators
        self.accuracy_evaluator = AccuracyEvaluator()
        self.completeness_evaluator = CompletenessEvaluator()
        self.brand_voice_evaluator = BrandVoiceEvaluator(brand_guidelines)
        self.seo_evaluator = SEOEvaluator()
        self.readability_evaluator = ReadabilityEvaluator()
        self.style_evaluator = StyleComplianceEvaluator()
        self.translation_evaluator = TranslationEvaluator()

    def evaluate_content(
        self,
        content: Dict[str, Any],
        specifications: Dict[str, Any],
        category: str = "Consumer Electronics",
        keywords: Optional[List[str]] = None,
        include_translation: bool = False,
        source_content: Optional[Dict[str, Any]] = None,
        target_language: Optional[str] = None
    ) -> CompositeScore:
        """
        Run all evaluators and compute composite score.

        Returns CompositeScore with:
        - composite_score: 0-100
        - quality_tier: Excellent/Good/Acceptable/Needs Improvement/Poor
        - routing_decision: auto_publish/light_review/standard_review/priority_review/reject
        - confidence: confidence in composite score
        - top_issues: prioritized list of issues to fix
        - improvement_suggestions: actionable recommendations
        """
        # Run individual evaluators
        accuracy_result = self.accuracy_evaluator.evaluate(content, specifications)
        completeness_result = self.completeness_evaluator.evaluate(content, category, specifications=specifications)
        brand_voice_result = self.brand_voice_evaluator.evaluate(content)
        seo_result = self.seo_evaluator.evaluate(content, keywords, category, specifications)
        readability_result = self.readability_evaluator.evaluate(content)
        style_result = self.style_evaluator.evaluate(content)

        # Translation evaluation (if applicable)
        translation_result = None
        if include_translation and source_content and target_language:
            translation_result = self.translation_evaluator.evaluate(
                source_content, content, "en", target_language
            )

        # Calculate composite score
        weighted_score = (
            accuracy_result.score * self.weights.get("accuracy", 0.25) +
            completeness_result.score * self.weights.get("completeness", 0.20) +
            brand_voice_result.score * self.weights.get("brand_voice", 0.15) +
            seo_result.score * self.weights.get("seo", 0.15) +
            readability_result.score * self.weights.get("readability", 0.10) +
            style_result.score * self.weights.get("style", 0.10)
        )

        # Adjust weights if translation is included
        if translation_result:
            translation_weight = self.weights.get("translation", 0.05)
            # Normalize other weights
            other_weight = 1.0 - translation_weight
            weighted_score = weighted_score * other_weight + translation_result.score * translation_weight

        # Calculate confidence (based on claim verification and content quality)
        confidence = self._calculate_confidence(
            accuracy_result, completeness_result, readability_result
        )

        # Determine quality tier
        quality_tier = self._determine_quality_tier(weighted_score)

        # Determine routing decision
        routing_decision = self.determine_routing(weighted_score, confidence)

        # Collect and prioritize issues
        top_issues = self._collect_issues(
            accuracy_result, completeness_result, brand_voice_result,
            seo_result, readability_result, style_result, translation_result
        )

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            accuracy_result, completeness_result, brand_voice_result,
            seo_result, readability_result, style_result
        )

        # Build dimension scores dict
        dimension_scores = {
            "accuracy": accuracy_result.score,
            "completeness": completeness_result.score,
            "brand_voice": brand_voice_result.score,
            "seo": seo_result.score,
            "readability": readability_result.score,
            "style": style_result.score
        }
        if translation_result:
            dimension_scores["translation"] = translation_result.score

        return CompositeScore(
            composite_score=round(weighted_score, 2),
            quality_tier=quality_tier,
            routing_decision=routing_decision,
            confidence=round(confidence, 2),
            accuracy_score=round(accuracy_result.score, 2),
            completeness_score=round(completeness_result.score, 2),
            brand_voice_score=round(brand_voice_result.score, 2),
            seo_score=round(seo_result.score, 2),
            readability_score=round(readability_result.score, 2),
            style_score=round(style_result.score, 2),
            translation_score=round(translation_result.score, 2) if translation_result else None,
            dimension_scores=dimension_scores,
            top_issues=top_issues[:10],
            improvement_suggestions=suggestions[:5],
            accuracy_details=accuracy_result,
            completeness_details=completeness_result,
            brand_voice_details=brand_voice_result,
            seo_details=seo_result,
            readability_details=readability_result,
            style_details=style_result,
            translation_details=translation_result
        )

    def _calculate_confidence(
        self,
        accuracy: AccuracyScore,
        completeness: CompletenessScore,
        readability: ReadabilityScore
    ) -> float:
        """Calculate confidence in the composite score."""
        # Base confidence
        confidence = 0.7

        # Adjust based on accuracy evaluation confidence
        if hasattr(accuracy, 'confidence'):
            confidence = (confidence + accuracy.confidence) / 2

        # Adjust based on completeness
        if completeness.critical_total > 0:
            critical_ratio = completeness.critical_present / completeness.critical_total
            confidence *= (0.5 + 0.5 * critical_ratio)

        # Adjust based on content availability
        if hasattr(readability, 'details') and readability.details:
            sentence_count = readability.details.get('total_sentences', 0)
            if sentence_count >= 5:
                confidence = min(confidence + 0.1, 0.95)
            elif sentence_count < 2:
                confidence = max(confidence - 0.15, 0.3)

        return min(0.95, max(0.3, confidence))

    def _determine_quality_tier(self, score: float) -> str:
        """Determine quality tier based on score."""
        for tier, config in QUALITY_TIERS.items():
            if config["min"] <= score <= config["max"]:
                return config["label"]
        return "Poor"

    def determine_routing(self, score: float, confidence: float) -> str:
        """
        Determine human review routing based on score and confidence.

        Routing logic:
        - score >= 90 AND confidence >= 0.85: auto_publish
        - score >= 75 AND confidence >= 0.70: light_review (5% audit sample)
        - score >= 60: standard_review
        - score >= 40: priority_review
        - score < 40: reject_regenerate
        """
        thresholds = ROUTING_THRESHOLDS

        if score >= thresholds["auto_publish"]["score"] and confidence >= thresholds["auto_publish"]["confidence"]:
            return "auto_publish"
        elif score >= thresholds["light_review"]["score"] and confidence >= thresholds["light_review"]["confidence"]:
            return "light_review"
        elif score >= thresholds["standard_review"]["score"]:
            return "standard_review"
        elif score >= thresholds["priority_review"]["score"]:
            return "priority_review"
        else:
            return "reject_regenerate"

    def _collect_issues(
        self,
        accuracy: AccuracyScore,
        completeness: CompletenessScore,
        brand_voice: BrandVoiceScore,
        seo: SEOScore,
        readability: ReadabilityScore,
        style: StyleComplianceScore,
        translation: Optional[TranslationScore]
    ) -> List[Issue]:
        """Collect and prioritize issues from all evaluators."""
        issues = []

        # Accuracy issues (critical if score < 70)
        severity = "critical" if accuracy.score < 70 else "major"
        for error in accuracy.errors:
            issues.append(Issue(
                dimension="accuracy",
                severity=severity,
                message=error,
                suggestion="Verify against product specifications"
            ))

        # Completeness issues
        for attr in completeness.missing_critical:
            issues.append(Issue(
                dimension="completeness",
                severity="critical",
                message=f"Missing critical attribute: {attr}",
                suggestion=f"Add {attr} to content"
            ))

        for attr in completeness.missing_required:
            issues.append(Issue(
                dimension="completeness",
                severity="major",
                message=f"Missing required attribute: {attr}",
                suggestion=f"Include {attr} information"
            ))

        # Brand voice issues
        for prohibited in brand_voice.prohibited_found:
            issues.append(Issue(
                dimension="brand_voice",
                severity="major",
                message=f"Prohibited phrase: '{prohibited.get('term', '')}'",
                location=f"Position {prohibited.get('location', 'unknown')}",
                suggestion="Replace with brand-approved terminology"
            ))

        for issue in brand_voice.tone_issues:
            issues.append(Issue(
                dimension="brand_voice",
                severity="minor",
                message=issue,
                suggestion="Adjust tone to match brand guidelines"
            ))

        # SEO issues
        for issue in seo.issues:
            issues.append(Issue(
                dimension="seo",
                severity="minor",
                message=issue,
                suggestion="Optimize for search engines"
            ))

        # Readability issues
        for issue in readability.issues:
            issues.append(Issue(
                dimension="readability",
                severity="minor" if readability.score >= 60 else "major",
                message=issue
            ))

        # Style issues
        for issue in style.formatting_issues + style.structure_issues:
            issues.append(Issue(
                dimension="style",
                severity="minor",
                message=issue
            ))

        # Translation issues
        if translation:
            for error in translation.errors:
                issues.append(Issue(
                    dimension="translation",
                    severity="major" if translation.score < 70 else "minor",
                    message=error
                ))

        # Sort by severity
        severity_order = {"critical": 0, "major": 1, "minor": 2, "suggestion": 3}
        issues.sort(key=lambda x: severity_order.get(x.severity, 3))

        return issues

    def _generate_suggestions(
        self,
        accuracy: AccuracyScore,
        completeness: CompletenessScore,
        brand_voice: BrandVoiceScore,
        seo: SEOScore,
        readability: ReadabilityScore,
        style: StyleComplianceScore
    ) -> List[str]:
        """Generate improvement suggestions based on lowest scores."""
        suggestions = []

        # Find lowest scoring dimensions
        scores = [
            ("accuracy", accuracy.score),
            ("completeness", completeness.score),
            ("brand_voice", brand_voice.score),
            ("seo", seo.score),
            ("readability", readability.score),
            ("style", style.score)
        ]
        scores.sort(key=lambda x: x[1])

        # Generate suggestions for lowest 3 dimensions
        for dimension, score in scores[:3]:
            if score >= 90:
                continue

            if dimension == "accuracy":
                suggestions.append(
                    "Verify all facts and figures against source specifications"
                )
            elif dimension == "completeness":
                if completeness.missing_critical:
                    suggestions.append(
                        f"Add missing critical attributes: {', '.join(completeness.missing_critical[:3])}"
                    )
                elif completeness.missing_required:
                    suggestions.append(
                        f"Add missing required attributes: {', '.join(completeness.missing_required[:3])}"
                    )
            elif dimension == "brand_voice":
                if brand_voice.prohibited_found:
                    suggestions.append(
                        "Remove prohibited phrases and use brand-approved terminology"
                    )
                else:
                    suggestions.append(
                        "Adjust tone and voice to better match brand guidelines"
                    )
            elif dimension == "seo":
                if hasattr(seo, 'details'):
                    if not seo.details.get('keyword_in_title'):
                        suggestions.append("Add primary keywords to the title")
                    elif seo.word_count < 200:
                        suggestions.append("Expand content to at least 300 words for better SEO")
                else:
                    suggestions.append("Improve keyword optimization and content depth")
            elif dimension == "readability":
                suggestions.extend(readability.suggestions[:2])
            elif dimension == "style":
                if style.formatting_issues:
                    suggestions.append("Fix formatting issues: capitalization, punctuation, numbers")
                if style.structure_issues:
                    suggestions.append("Improve content structure: shorter paragraphs, better lists")

        return suggestions

    def compare_versions(
        self,
        version_a: CompositeScore,
        version_b: CompositeScore
    ) -> VersionComparison:
        """
        Compare two content versions.

        Returns:
        - winner: version_a/version_b/tie
        - score_delta: difference in composite scores
        - dimension_deltas: per-dimension improvements/regressions
        - recommendation: which version to use and why
        """
        score_delta = version_b.composite_score - version_a.composite_score
        dimension_deltas = {}
        improvements = []
        regressions = []

        # Compare each dimension
        dimensions = ["accuracy", "completeness", "brand_voice", "seo", "readability", "style"]
        for dim in dimensions:
            score_a = version_a.dimension_scores.get(dim, 0)
            score_b = version_b.dimension_scores.get(dim, 0)
            delta = score_b - score_a
            dimension_deltas[dim] = round(delta, 2)

            if delta > 5:
                improvements.append(f"{dim.replace('_', ' ').title()}: +{delta:.0f}%")
            elif delta < -5:
                regressions.append(f"{dim.replace('_', ' ').title()}: {delta:.0f}%")

        # Determine winner
        if abs(score_delta) < 3:
            winner = "tie"
        elif score_delta > 0:
            winner = "version_b"
        else:
            winner = "version_a"

        # Generate recommendation
        if winner == "tie":
            recommendation = "Both versions are comparable. Consider other factors like brand voice consistency."
        elif winner == "version_b":
            if improvements:
                recommendation = f"Version B is better. Key improvements: {', '.join(improvements[:3])}"
            else:
                recommendation = f"Version B scores {score_delta:.0f} points higher overall."
        else:
            if regressions:
                recommendation = f"Version A is better. Version B regressed in: {', '.join(regressions[:3])}"
            else:
                recommendation = f"Version A scores {abs(score_delta):.0f} points higher overall."

        return VersionComparison(
            winner=winner,
            score_delta=round(score_delta, 2),
            dimension_deltas=dimension_deltas,
            version_a_score=version_a.composite_score,
            version_b_score=version_b.composite_score,
            recommendation=recommendation,
            improvements=improvements,
            regressions=regressions
        )

    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """Update scoring weights."""
        self.weights.update(new_weights)

    def update_brand_guidelines(self, guidelines: Dict) -> None:
        """Update brand guidelines for evaluators."""
        self.brand_guidelines = guidelines
        self.brand_voice_evaluator.update_guidelines(guidelines)
