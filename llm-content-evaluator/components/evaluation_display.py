"""
Evaluation display component for LLM Content Quality Evaluator.
"""

import streamlit as st
from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px

from utils.helpers import get_score_color, get_quality_tier_color
from utils.export import export_to_excel, export_to_json, generate_report_summary


def render_evaluation_results(evaluation: Dict[str, Any]):
    """Render evaluation results with visualizations."""
    st.subheader("Evaluation Results")

    # Main score display
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        score = evaluation.get('composite_score', 0)
        color = get_score_color(score)

        st.markdown(f"""
            <div style='text-align: center; padding: 20px;'>
                <div style='font-size: 48px; font-weight: bold; color: {color};'>
                    {score:.0f}
                </div>
                <div style='font-size: 16px; color: #666;'>
                    Composite Score
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        tier = evaluation.get('quality_tier', 'Unknown')
        routing = evaluation.get('routing_decision', 'Unknown')
        confidence = evaluation.get('confidence', 0)

        tier_color = get_quality_tier_color(tier)

        st.markdown(f"""
            <div style='padding: 20px;'>
                <p><strong>Quality Tier:</strong>
                    <span style='color: {tier_color}; font-weight: bold;'>{tier}</span>
                </p>
                <p><strong>Routing:</strong> {routing.replace('_', ' ').title()}</p>
                <p><strong>Confidence:</strong> {confidence:.0%}</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        # Export buttons
        st.write("**Export:**")
        if st.button("📥 Excel", key="export_excel"):
            excel_data = export_to_excel(evaluation)
            st.download_button(
                "Download Excel",
                data=excel_data,
                file_name="evaluation_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        if st.button("📄 JSON", key="export_json"):
            json_data = export_to_json(evaluation)
            st.download_button(
                "Download JSON",
                data=json_data,
                file_name="evaluation_report.json",
                mime="application/json"
            )

    st.divider()

    # Dimension scores breakdown
    st.subheader("Dimension Breakdown")

    render_dimension_chart(evaluation.get('dimension_scores', {}))

    # Detailed dimension scores
    render_dimension_details(evaluation)

    st.divider()

    # Issues and suggestions
    col_issues, col_suggestions = st.columns(2)

    with col_issues:
        st.subheader("Top Issues")
        render_issues_list(evaluation.get('top_issues', []))

    with col_suggestions:
        st.subheader("Improvement Suggestions")
        render_suggestions_list(evaluation.get('improvement_suggestions', []))


def render_dimension_chart(dimension_scores: Dict[str, float]):
    """Render dimension scores as a radar chart."""
    if not dimension_scores:
        st.info("No dimension scores available.")
        return

    # Prepare data for radar chart
    dimensions = list(dimension_scores.keys())
    scores = list(dimension_scores.values())

    # Create radar chart
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],  # Close the polygon
        theta=[d.replace('_', ' ').title() for d in dimensions] + [dimensions[0].replace('_', ' ').title()],
        fill='toself',
        name='Score',
        line_color='#3b82f6',
        fillcolor='rgba(59, 130, 246, 0.3)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

    # Also show as horizontal bars for clarity
    render_dimension_bars(dimension_scores)


def render_dimension_bars(dimension_scores: Dict[str, float]):
    """Render dimension scores as horizontal bars."""
    for dimension, score in sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True):
        color = get_score_color(score)
        status = "✓ Pass" if score >= 70 else "⚠ Review" if score >= 50 else "✗ Fail"

        col1, col2, col3 = st.columns([2, 6, 1])

        with col1:
            st.write(dimension.replace('_', ' ').title())

        with col2:
            st.progress(score / 100)

        with col3:
            st.markdown(f"<span style='color: {color};'>{score:.0f}%</span>", unsafe_allow_html=True)


def render_dimension_details(evaluation: Dict[str, Any]):
    """Render detailed information for each dimension."""
    with st.expander("View Detailed Scores", expanded=False):
        tabs = st.tabs(["Accuracy", "Completeness", "Brand Voice", "SEO", "Readability", "Style"])

        with tabs[0]:
            render_accuracy_details(evaluation.get('accuracy_details'))

        with tabs[1]:
            render_completeness_details(evaluation.get('completeness_details'))

        with tabs[2]:
            render_brand_voice_details(evaluation.get('brand_voice_details'))

        with tabs[3]:
            render_seo_details(evaluation.get('seo_details'))

        with tabs[4]:
            render_readability_details(evaluation.get('readability_details'))

        with tabs[5]:
            render_style_details(evaluation.get('style_details'))


def render_accuracy_details(details):
    """Render accuracy evaluation details."""
    if not details:
        st.info("No accuracy details available.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        verified = getattr(details, 'verified_claims', 0)
        st.metric("Verified Claims", verified)

    with col2:
        failed = getattr(details, 'failed_claims', 0)
        st.metric("Failed Claims", failed)

    with col3:
        unverifiable = getattr(details, 'unverifiable_claims', 0)
        st.metric("Unverifiable", unverifiable)

    errors = getattr(details, 'errors', [])
    if errors:
        st.write("**Errors Found:**")
        for error in errors:
            st.write(f"- {error}")


def render_completeness_details(details):
    """Render completeness evaluation details."""
    if not details:
        st.info("No completeness details available.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        critical = f"{getattr(details, 'critical_present', 0)}/{getattr(details, 'critical_total', 0)}"
        st.metric("Critical", critical)

    with col2:
        required = f"{getattr(details, 'required_present', 0)}/{getattr(details, 'required_total', 0)}"
        st.metric("Required", required)

    with col3:
        recommended = f"{getattr(details, 'recommended_present', 0)}/{getattr(details, 'recommended_total', 0)}"
        st.metric("Recommended", recommended)

    with col4:
        optional = f"{getattr(details, 'optional_present', 0)}/{getattr(details, 'optional_total', 0)}"
        st.metric("Optional", optional)

    missing = getattr(details, 'missing_critical', []) + getattr(details, 'missing_required', [])
    if missing:
        st.write("**Missing Attributes:**")
        for attr in missing:
            st.write(f"- {attr.replace('_', ' ').title()}")


def render_brand_voice_details(details):
    """Render brand voice evaluation details."""
    if not details:
        st.info("No brand voice details available.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Terminology", f"{getattr(details, 'terminology_score', 0):.0f}")

    with col2:
        st.metric("Tone", f"{getattr(details, 'tone_score', 0):.0f}")

    with col3:
        st.metric("Style", f"{getattr(details, 'style_score', 0):.0f}")

    with col4:
        st.metric("Consistency", f"{getattr(details, 'voice_consistency_score', 0):.0f}")

    prohibited = getattr(details, 'prohibited_found', [])
    if prohibited:
        st.write("**Prohibited Phrases Found:**")
        for item in prohibited:
            term = item.get('term', '') if isinstance(item, dict) else str(item)
            st.write(f"- '{term}'")


def render_seo_details(details):
    """Render SEO evaluation details."""
    if not details:
        st.info("No SEO details available.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Keyword Score", f"{getattr(details, 'keyword_score', 0):.0f}")
        st.metric("Content Depth", f"{getattr(details, 'content_depth_score', 0):.0f}")

    with col2:
        st.metric("Semantic Score", f"{getattr(details, 'semantic_score', 0):.0f}")
        st.metric("Technical", f"{getattr(details, 'technical_score', 0):.0f}")

    with col3:
        st.metric("Word Count", getattr(details, 'word_count', 0))
        st.metric("Keyword Density", f"{getattr(details, 'keyword_density', 0):.1f}%")


def render_readability_details(details):
    """Render readability evaluation details."""
    if not details:
        st.info("No readability details available.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Flesch Ease", f"{getattr(details, 'flesch_ease', 0):.0f}")
        st.metric("Flesch Grade", f"{getattr(details, 'flesch_grade', 0):.1f}")

    with col2:
        st.metric("Gunning Fog", f"{getattr(details, 'gunning_fog', 0):.1f}")
        st.metric("SMOG Index", f"{getattr(details, 'smog_index', 0):.1f}")

    with col3:
        st.metric("Avg Sentence Length", f"{getattr(details, 'avg_sentence_length', 0):.0f}")
        st.metric("Complex Words", getattr(details, 'complex_word_count', 0))

    long_sentences = getattr(details, 'long_sentences', [])
    if long_sentences:
        st.write("**Long Sentences:**")
        for sentence in long_sentences[:3]:
            st.write(f"- {sentence[:100]}...")


def render_style_details(details):
    """Render style compliance evaluation details."""
    if not details:
        st.info("No style details available.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Formatting", f"{getattr(details, 'formatting_score', 0):.0f}")

    with col2:
        st.metric("Structure", f"{getattr(details, 'structure_score', 0):.0f}")

    with col3:
        st.metric("Content Rules", f"{getattr(details, 'content_rules_score', 0):.0f}")

    issues = getattr(details, 'formatting_issues', []) + getattr(details, 'structure_issues', [])
    if issues:
        st.write("**Style Issues:**")
        for issue in issues[:5]:
            st.write(f"- {issue}")


def render_issues_list(issues: List):
    """Render list of issues."""
    if not issues:
        st.success("No significant issues found!")
        return

    for issue in issues[:10]:
        if hasattr(issue, 'severity'):
            severity = issue.severity
            message = issue.message
            dimension = issue.dimension
        elif isinstance(issue, dict):
            severity = issue.get('severity', 'minor')
            message = issue.get('message', '')
            dimension = issue.get('dimension', '')
        else:
            continue

        severity_icon = {
            'critical': '🔴',
            'major': '🟠',
            'minor': '🟡',
            'suggestion': '🔵'
        }.get(severity, '⚪')

        st.markdown(f"""
            {severity_icon} **{dimension.replace('_', ' ').title()}**: {message}
        """)


def render_suggestions_list(suggestions: List[str]):
    """Render list of improvement suggestions."""
    if not suggestions:
        st.info("No specific suggestions - content meets quality standards.")
        return

    for i, suggestion in enumerate(suggestions, 1):
        st.markdown(f"{i}. {suggestion}")
