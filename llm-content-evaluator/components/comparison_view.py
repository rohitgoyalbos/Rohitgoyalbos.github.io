"""
Version comparison component for LLM Content Quality Evaluator.
"""

import streamlit as st
from typing import Dict, Any, Optional
import difflib

from utils.helpers import get_score_color


def render_comparison_view():
    """Render the version comparison page."""
    st.title("Compare Content Versions")

    products = st.session_state.get('products', [])

    if not products:
        st.warning("No products loaded. Generate sample data from the Dashboard first.")
        return

    # Product selector
    product_options = {
        f"{p.get('specifications', {}).get('name', 'Unknown')} ({p.get('product_id', 'N/A')})": p
        for p in products
    }

    selected_name = st.selectbox(
        "Select Product",
        list(product_options.keys())
    )

    selected_product = product_options.get(selected_name)

    if not selected_product:
        return

    content_versions = selected_product.get('generated_content', {})
    version_names = list(content_versions.keys())

    if len(version_names) < 2:
        st.warning("This product only has one content version. Select a product with multiple versions.")
        return

    # Version selectors
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Version A")
        version_a_name = st.selectbox(
            "Select Version A",
            version_names,
            key="version_a_select"
        )

    with col2:
        st.subheader("Version B")
        remaining_versions = [v for v in version_names if v != version_a_name]
        version_b_name = st.selectbox(
            "Select Version B",
            remaining_versions,
            key="version_b_select"
        )

    version_a = content_versions[version_a_name]
    version_b = content_versions[version_b_name]

    # Compare button
    if st.button("Compare Versions", type="primary"):
        compare_and_display(
            version_a, version_b,
            selected_product.get('specifications', {}),
            selected_product.get('category', 'Consumer Electronics'),
            version_a_name, version_b_name
        )


def compare_and_display(
    version_a: Dict,
    version_b: Dict,
    specifications: Dict,
    category: str,
    name_a: str,
    name_b: str
):
    """Compare two versions and display results."""
    from evaluators.composite_scorer import CompositeScorer

    scorer = CompositeScorer(
        weights=st.session_state.get('weights', {}),
        brand_guidelines=st.session_state.get('brand_guidelines', {})
    )

    # Evaluate both versions
    with st.spinner("Evaluating versions..."):
        content_a = {
            'description': version_a.get('description', ''),
            'marketing_copy': version_a.get('marketing_copy', ''),
            'feature_bullets': version_a.get('feature_bullets', []),
            'meta_description': version_a.get('meta_description', '')
        }

        content_b = {
            'description': version_b.get('description', ''),
            'marketing_copy': version_b.get('marketing_copy', ''),
            'feature_bullets': version_b.get('feature_bullets', []),
            'meta_description': version_b.get('meta_description', '')
        }

        result_a = scorer.evaluate_content(content_a, specifications, category)
        result_b = scorer.evaluate_content(content_b, specifications, category)

        comparison = scorer.compare_versions(result_a, result_b)

    st.divider()

    # Score comparison header
    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        st.markdown(f"### {name_a}")
        score_a = result_a.composite_score
        color_a = get_score_color(score_a)
        st.markdown(f"<h1 style='text-align: center; color: {color_a};'>{score_a:.0f}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>{result_a.quality_tier}</p>", unsafe_allow_html=True)

    with col2:
        delta = comparison.score_delta
        delta_color = "#22c55e" if delta > 0 else "#ef4444" if delta < 0 else "#6b7280"
        delta_symbol = "+" if delta > 0 else ""
        st.markdown(f"""
            <div style='text-align: center; padding: 40px 0;'>
                <span style='font-size: 24px; color: {delta_color};'>{delta_symbol}{delta:.1f}</span>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"### {name_b}")
        score_b = result_b.composite_score
        color_b = get_score_color(score_b)
        st.markdown(f"<h1 style='text-align: center; color: {color_b};'>{score_b:.0f}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>{result_b.quality_tier}</p>", unsafe_allow_html=True)

    st.divider()

    # Dimension comparison
    st.subheader("Dimension Comparison")

    dimensions = ["accuracy", "completeness", "brand_voice", "seo", "readability", "style"]

    for dim in dimensions:
        score_a_dim = result_a.dimension_scores.get(dim, 0)
        score_b_dim = result_b.dimension_scores.get(dim, 0)
        delta_dim = score_b_dim - score_a_dim

        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 2, 1])

        with col1:
            st.write(dim.replace('_', ' ').title())

        with col2:
            st.progress(score_a_dim / 100)
            st.caption(f"{score_a_dim:.0f}%")

        with col3:
            delta_icon = "↑" if delta_dim > 5 else "↓" if delta_dim < -5 else "→"
            delta_color = "#22c55e" if delta_dim > 5 else "#ef4444" if delta_dim < -5 else "#6b7280"
            st.markdown(f"<span style='color: {delta_color};'>{delta_icon}</span>", unsafe_allow_html=True)

        with col4:
            st.progress(score_b_dim / 100)
            st.caption(f"{score_b_dim:.0f}%")

        with col5:
            delta_text = f"+{delta_dim:.0f}" if delta_dim > 0 else f"{delta_dim:.0f}"
            st.write(delta_text)

    st.divider()

    # Content diff
    st.subheader("Content Differences")

    with st.expander("View Description Diff", expanded=True):
        render_text_diff(
            version_a.get('description', ''),
            version_b.get('description', '')
        )

    with st.expander("View Marketing Copy Diff"):
        render_text_diff(
            version_a.get('marketing_copy', ''),
            version_b.get('marketing_copy', '')
        )

    st.divider()

    # Recommendation
    st.subheader("Recommendation")

    winner = comparison.winner
    if winner == "version_b":
        st.success(f"**Use {name_b}** - {comparison.recommendation}")
    elif winner == "version_a":
        st.success(f"**Use {name_a}** - {comparison.recommendation}")
    else:
        st.info(f"**Tie** - {comparison.recommendation}")

    # Improvements and regressions
    col1, col2 = st.columns(2)

    with col1:
        if comparison.improvements:
            st.write("**Improvements:**")
            for imp in comparison.improvements:
                st.write(f"✅ {imp}")

    with col2:
        if comparison.regressions:
            st.write("**Regressions:**")
            for reg in comparison.regressions:
                st.write(f"⚠️ {reg}")


def render_text_diff(text_a: str, text_b: str):
    """Render a diff between two texts."""
    if not text_a and not text_b:
        st.info("Both versions are empty.")
        return

    if text_a == text_b:
        st.info("No differences found.")
        return

    # Generate diff
    diff = difflib.unified_diff(
        text_a.splitlines(keepends=True),
        text_b.splitlines(keepends=True),
        fromfile='Version A',
        tofile='Version B',
        lineterm=''
    )

    diff_text = list(diff)

    if not diff_text:
        st.info("No significant differences found.")
        return

    # Display diff with highlighting
    for line in diff_text:
        if line.startswith('+') and not line.startswith('+++'):
            st.markdown(f"<span style='background-color: #d4edda; color: #155724;'>{line}</span>", unsafe_allow_html=True)
        elif line.startswith('-') and not line.startswith('---'):
            st.markdown(f"<span style='background-color: #f8d7da; color: #721c24;'>{line}</span>", unsafe_allow_html=True)
        elif line.startswith('@@'):
            st.markdown(f"<span style='color: #6c757d;'>{line}</span>", unsafe_allow_html=True)
        else:
            st.text(line)
