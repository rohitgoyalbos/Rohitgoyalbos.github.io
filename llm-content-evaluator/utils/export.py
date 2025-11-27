"""
Export utilities for LLM Content Quality Evaluator.
"""

import io
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

import pandas as pd


def export_to_excel(
    evaluation_data: Dict[str, Any],
    include_details: bool = True
) -> bytes:
    """
    Export evaluation results to Excel format.

    Returns bytes that can be downloaded.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = {
            'Metric': [
                'Composite Score',
                'Quality Tier',
                'Routing Decision',
                'Confidence',
                'Accuracy Score',
                'Completeness Score',
                'Brand Voice Score',
                'SEO Score',
                'Readability Score',
                'Style Score'
            ],
            'Value': [
                evaluation_data.get('composite_score', 0),
                evaluation_data.get('quality_tier', 'Unknown'),
                evaluation_data.get('routing_decision', 'Unknown'),
                evaluation_data.get('confidence', 0),
                evaluation_data.get('accuracy_score', 0),
                evaluation_data.get('completeness_score', 0),
                evaluation_data.get('brand_voice_score', 0),
                evaluation_data.get('seo_score', 0),
                evaluation_data.get('readability_score', 0),
                evaluation_data.get('style_score', 0)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Issues sheet
        issues = evaluation_data.get('top_issues', [])
        if issues:
            issues_data = []
            for issue in issues:
                if hasattr(issue, '__dict__'):
                    issues_data.append({
                        'Dimension': issue.dimension,
                        'Severity': issue.severity,
                        'Message': issue.message,
                        'Suggestion': issue.suggestion or ''
                    })
                elif isinstance(issue, dict):
                    issues_data.append({
                        'Dimension': issue.get('dimension', ''),
                        'Severity': issue.get('severity', ''),
                        'Message': issue.get('message', ''),
                        'Suggestion': issue.get('suggestion', '')
                    })

            if issues_data:
                issues_df = pd.DataFrame(issues_data)
                issues_df.to_excel(writer, sheet_name='Issues', index=False)

        # Suggestions sheet
        suggestions = evaluation_data.get('improvement_suggestions', [])
        if suggestions:
            suggestions_df = pd.DataFrame({
                'Priority': range(1, len(suggestions) + 1),
                'Suggestion': suggestions
            })
            suggestions_df.to_excel(writer, sheet_name='Suggestions', index=False)

        # Details sheets if requested
        if include_details:
            # Dimension scores over time (if available)
            dimension_scores = evaluation_data.get('dimension_scores', {})
            if dimension_scores:
                scores_df = pd.DataFrame([{
                    'Dimension': k.replace('_', ' ').title(),
                    'Score': v
                } for k, v in dimension_scores.items()])
                scores_df.to_excel(writer, sheet_name='Dimension Scores', index=False)

    output.seek(0)
    return output.getvalue()


def export_to_json(
    evaluation_data: Dict[str, Any],
    pretty: bool = True
) -> str:
    """Export evaluation results to JSON format."""
    # Convert dataclass objects to dicts if needed
    def convert_to_serializable(obj):
        if hasattr(obj, '__dict__'):
            return {k: convert_to_serializable(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        else:
            return obj

    serializable_data = convert_to_serializable(evaluation_data)
    serializable_data['exported_at'] = datetime.utcnow().isoformat() + 'Z'

    if pretty:
        return json.dumps(serializable_data, indent=2)
    return json.dumps(serializable_data)


def export_to_csv(
    evaluations: List[Dict[str, Any]],
    include_details: bool = False
) -> str:
    """Export multiple evaluations to CSV format."""
    rows = []

    for eval_data in evaluations:
        row = {
            'Product ID': eval_data.get('product_id', ''),
            'Content Version': eval_data.get('content_version', ''),
            'Composite Score': eval_data.get('composite_score', 0),
            'Quality Tier': eval_data.get('quality_tier', ''),
            'Routing': eval_data.get('routing_decision', ''),
            'Accuracy': eval_data.get('accuracy_score', 0),
            'Completeness': eval_data.get('completeness_score', 0),
            'Brand Voice': eval_data.get('brand_voice_score', 0),
            'SEO': eval_data.get('seo_score', 0),
            'Readability': eval_data.get('readability_score', 0),
            'Style': eval_data.get('style_score', 0),
            'Evaluated At': eval_data.get('evaluated_at', '')
        }

        if include_details:
            row['Issues Count'] = len(eval_data.get('top_issues', []))
            row['Confidence'] = eval_data.get('confidence', 0)

        rows.append(row)

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def generate_report_summary(evaluation_data: Dict[str, Any]) -> str:
    """Generate a text summary of evaluation results."""
    lines = [
        "=" * 60,
        "LLM CONTENT QUALITY EVALUATION REPORT",
        "=" * 60,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "SUMMARY",
        "-" * 40,
        f"Composite Score: {evaluation_data.get('composite_score', 0):.1f}/100",
        f"Quality Tier: {evaluation_data.get('quality_tier', 'Unknown')}",
        f"Routing Decision: {evaluation_data.get('routing_decision', 'Unknown')}",
        f"Confidence: {evaluation_data.get('confidence', 0):.0%}",
        "",
        "DIMENSION SCORES",
        "-" * 40,
    ]

    dimension_scores = evaluation_data.get('dimension_scores', {})
    for dimension, score in dimension_scores.items():
        status = "PASS" if score >= 70 else "REVIEW" if score >= 50 else "FAIL"
        lines.append(f"  {dimension.replace('_', ' ').title():20} {score:5.1f}  [{status}]")

    lines.extend([
        "",
        "TOP ISSUES",
        "-" * 40,
    ])

    issues = evaluation_data.get('top_issues', [])
    if issues:
        for i, issue in enumerate(issues[:5], 1):
            if hasattr(issue, 'message'):
                lines.append(f"  {i}. [{issue.severity.upper()}] {issue.message}")
            elif isinstance(issue, dict):
                lines.append(f"  {i}. [{issue.get('severity', 'UNKNOWN').upper()}] {issue.get('message', '')}")
    else:
        lines.append("  No critical issues found.")

    lines.extend([
        "",
        "RECOMMENDATIONS",
        "-" * 40,
    ])

    suggestions = evaluation_data.get('improvement_suggestions', [])
    if suggestions:
        for i, suggestion in enumerate(suggestions[:3], 1):
            lines.append(f"  {i}. {suggestion}")
    else:
        lines.append("  Content meets quality standards.")

    lines.extend([
        "",
        "=" * 60
    ])

    return "\n".join(lines)


def create_comparison_report(
    comparison: Dict[str, Any],
    version_a_name: str = "Version A",
    version_b_name: str = "Version B"
) -> str:
    """Generate a comparison report between two versions."""
    lines = [
        "=" * 60,
        "VERSION COMPARISON REPORT",
        "=" * 60,
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "OVERALL COMPARISON",
        "-" * 40,
        f"  {version_a_name}: {comparison.get('version_a_score', 0):.1f}/100",
        f"  {version_b_name}: {comparison.get('version_b_score', 0):.1f}/100",
        f"  Difference: {comparison.get('score_delta', 0):+.1f} points",
        f"  Winner: {comparison.get('winner', 'Unknown').replace('_', ' ').title()}",
        "",
        "DIMENSION CHANGES",
        "-" * 40,
    ]

    dimension_deltas = comparison.get('dimension_deltas', {})
    for dimension, delta in dimension_deltas.items():
        indicator = "+" if delta > 0 else "" if delta == 0 else ""
        status = "IMPROVED" if delta > 5 else "DECLINED" if delta < -5 else "STABLE"
        lines.append(f"  {dimension.replace('_', ' ').title():20} {indicator}{delta:+5.1f}  [{status}]")

    improvements = comparison.get('improvements', [])
    regressions = comparison.get('regressions', [])

    if improvements:
        lines.extend([
            "",
            "IMPROVEMENTS",
            "-" * 40,
        ])
        for imp in improvements:
            lines.append(f"  - {imp}")

    if regressions:
        lines.extend([
            "",
            "REGRESSIONS",
            "-" * 40,
        ])
        for reg in regressions:
            lines.append(f"  - {reg}")

    lines.extend([
        "",
        "RECOMMENDATION",
        "-" * 40,
        f"  {comparison.get('recommendation', 'No recommendation available.')}",
        "",
        "=" * 60
    ])

    return "\n".join(lines)
