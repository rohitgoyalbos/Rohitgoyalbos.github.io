"""
Main Streamlit application for LLM Content Quality Evaluator.

This is the entry point for the application. Run with:
    streamlit run app.py
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import QUALITY_TIERS, PRODUCT_CATEGORIES, DEFAULT_WEIGHTS
from utils.helpers import generate_id, get_score_color, get_quality_tier_color, format_score

# Import components
from components.content_input import render_content_input
from components.evaluation_display import render_evaluation_results
from components.comparison_view import render_comparison_view
from components.human_review import render_human_review
from components.analytics_dashboard import render_analytics_dashboard
from components.settings_panel import render_settings_panel


def init_session_state():
    """Initialize session state variables."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_evaluation = None
        st.session_state.evaluation_history = []
        st.session_state.review_queue = []
        st.session_state.brand_guidelines = None
        st.session_state.weights = DEFAULT_WEIGHTS.copy()
        st.session_state.sample_data_loaded = False
        st.session_state.products = []
        st.session_state.selected_product = None


def load_sample_data():
    """Load sample data if available."""
    sample_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_products.json')

    if os.path.exists(sample_path):
        try:
            with open(sample_path, 'r') as f:
                data = json.load(f)
                st.session_state.products = data.get('products', [])
                st.session_state.brand_guidelines = data.get('brand_guidelines', {})
                st.session_state.sample_data_loaded = True
                return True
        except Exception as e:
            st.error(f"Error loading sample data: {e}")
            return False
    return False


def render_dashboard():
    """Render the main dashboard page."""
    st.title("Content Quality Dashboard")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    # Calculate stats from evaluation history
    history = st.session_state.evaluation_history
    today = datetime.now().date()

    evaluations_today = sum(1 for e in history if e.get('timestamp', datetime.now()).date() == today)
    avg_score = sum(e.get('composite_score', 0) for e in history) / len(history) if history else 0
    pending_reviews = len(st.session_state.review_queue)
    excellent_count = sum(1 for e in history if e.get('quality_tier') == 'Excellent')
    excellent_rate = (excellent_count / len(history) * 100) if history else 0

    with col1:
        st.metric("Evaluated Today", evaluations_today, delta=None)

    with col2:
        st.metric("Average Score", f"{avg_score:.1f}", delta=None)

    with col3:
        st.metric("Pending Reviews", pending_reviews, delta=None)

    with col4:
        st.metric("Excellence Rate", f"{excellent_rate:.0f}%", delta=None)

    st.divider()

    # Two-column layout for charts and recent activity
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Quality Distribution")

        if history:
            # Create distribution data
            tier_counts = {}
            for tier in QUALITY_TIERS.keys():
                tier_label = QUALITY_TIERS[tier]['label']
                tier_counts[tier_label] = sum(1 for e in history if e.get('quality_tier') == tier_label)

            # Display as bar chart
            import pandas as pd
            df = pd.DataFrame({
                'Quality Tier': list(tier_counts.keys()),
                'Count': list(tier_counts.values())
            })
            st.bar_chart(df.set_index('Quality Tier'))
        else:
            st.info("No evaluations yet. Evaluate some content to see the distribution.")

    with col_right:
        st.subheader("Quick Actions")

        if st.button("Evaluate New Content", type="primary", use_container_width=True):
            st.session_state.nav_page = "Evaluate Content"
            st.rerun()

        if st.button("View Review Queue", use_container_width=True):
            st.session_state.nav_page = "Human Review"
            st.rerun()

        if st.button("Generate Sample Data", use_container_width=True):
            with st.spinner("Generating sample data..."):
                from data.synthetic_generator import generate_sample_data
                data_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_products.json')
                generate_sample_data(data_path, num_products=50)
                load_sample_data()
                st.success("Sample data generated!")
                st.rerun()

    st.divider()

    # Recent evaluations
    st.subheader("Recent Evaluations")

    if history:
        for eval_data in history[-5:][::-1]:
            with st.container():
                cols = st.columns([3, 1, 1, 1])
                with cols[0]:
                    st.write(f"**{eval_data.get('product_name', 'Unknown Product')}**")
                with cols[1]:
                    score = eval_data.get('composite_score', 0)
                    color = get_score_color(score)
                    st.markdown(f"<span style='color:{color};font-weight:bold;'>{score:.0f}</span>", unsafe_allow_html=True)
                with cols[2]:
                    st.write(eval_data.get('quality_tier', 'Unknown'))
                with cols[3]:
                    st.write(eval_data.get('routing_decision', 'Unknown'))
    else:
        st.info("No recent evaluations. Start by evaluating some content.")


def render_evaluation_page():
    """Render the content evaluation page."""
    st.title("Evaluate Content")

    # Content input section
    content_data, specifications, category = render_content_input()

    if st.button("Evaluate Content", type="primary", disabled=content_data is None):
        if content_data and specifications:
            with st.spinner("Evaluating content..."):
                # Import and run evaluation
                from evaluators.composite_scorer import CompositeScorer

                scorer = CompositeScorer(
                    weights=st.session_state.weights,
                    brand_guidelines=st.session_state.brand_guidelines
                )

                result = scorer.evaluate_content(
                    content=content_data,
                    specifications=specifications,
                    category=category
                )

                # Store result
                evaluation = {
                    'id': generate_id('EVAL'),
                    'product_name': specifications.get('name', 'Unknown'),
                    'composite_score': result.composite_score,
                    'quality_tier': result.quality_tier,
                    'routing_decision': result.routing_decision,
                    'confidence': result.confidence,
                    'dimension_scores': result.dimension_scores,
                    'top_issues': result.top_issues,
                    'improvement_suggestions': result.improvement_suggestions,
                    'timestamp': datetime.now(),
                    'accuracy_details': result.accuracy_details,
                    'completeness_details': result.completeness_details,
                    'brand_voice_details': result.brand_voice_details,
                    'seo_details': result.seo_details,
                    'readability_details': result.readability_details,
                    'style_details': result.style_details
                }

                st.session_state.current_evaluation = evaluation
                st.session_state.evaluation_history.append(evaluation)

                # Add to review queue if needed
                if result.routing_decision in ['standard_review', 'priority_review']:
                    st.session_state.review_queue.append(evaluation)

            st.success("Evaluation complete!")

    # Display results if available
    if st.session_state.current_evaluation:
        st.divider()
        render_evaluation_results(st.session_state.current_evaluation)


def render_batch_evaluation():
    """Render batch evaluation page."""
    st.title("Batch Evaluation")

    st.info("Batch evaluation allows you to evaluate multiple products at once.")

    # Check if sample data is loaded
    if not st.session_state.sample_data_loaded:
        st.warning("No sample data loaded. Generate sample data from the Dashboard first.")
        if st.button("Generate Sample Data"):
            with st.spinner("Generating..."):
                from data.synthetic_generator import generate_sample_data
                data_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_products.json')
                generate_sample_data(data_path, num_products=50)
                load_sample_data()
                st.success("Done!")
                st.rerun()
        return

    products = st.session_state.products

    st.write(f"**{len(products)} products available for evaluation**")

    # Category filter
    categories = list(set(p.get('category', 'Unknown') for p in products))
    selected_category = st.selectbox("Filter by category", ["All"] + categories)

    filtered_products = products
    if selected_category != "All":
        filtered_products = [p for p in products if p.get('category') == selected_category]

    # Number selector
    num_to_evaluate = st.slider("Number of products to evaluate", 1, min(len(filtered_products), 50), 10)

    if st.button("Run Batch Evaluation", type="primary"):
        from evaluators.composite_scorer import CompositeScorer

        scorer = CompositeScorer(
            weights=st.session_state.weights,
            brand_guidelines=st.session_state.brand_guidelines
        )

        progress = st.progress(0)
        results = []

        for i, product in enumerate(filtered_products[:num_to_evaluate]):
            # Get first content version
            content_versions = product.get('generated_content', {})
            if not content_versions:
                continue

            first_version = list(content_versions.values())[0]
            content = {
                'description': first_version.get('description', ''),
                'marketing_copy': first_version.get('marketing_copy', ''),
                'feature_bullets': first_version.get('feature_bullets', []),
                'meta_description': first_version.get('meta_description', '')
            }

            result = scorer.evaluate_content(
                content=content,
                specifications=product.get('specifications', {}),
                category=product.get('category', 'Consumer Electronics')
            )

            results.append({
                'product_id': product.get('product_id'),
                'product_name': product.get('specifications', {}).get('name', 'Unknown'),
                'composite_score': result.composite_score,
                'quality_tier': result.quality_tier,
                'routing_decision': result.routing_decision
            })

            progress.progress((i + 1) / num_to_evaluate)

        st.success(f"Evaluated {len(results)} products!")

        # Display results table
        import pandas as pd
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)

        # Summary stats
        avg_score = df['composite_score'].mean()
        tier_dist = df['quality_tier'].value_counts().to_dict()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Score", f"{avg_score:.1f}")
        with col2:
            st.write("**Distribution:**")
            for tier, count in tier_dist.items():
                st.write(f"- {tier}: {count}")


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="LLM Content Quality Evaluator",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply custom CSS
    st.markdown("""
        <style>
        .stMetric {
            background-color: #f0f2f6;
            padding: 10px;
            border-radius: 5px;
        }
        .score-excellent { color: #22c55e; }
        .score-good { color: #84cc16; }
        .score-acceptable { color: #eab308; }
        .score-needs-improvement { color: #f97316; }
        .score-poor { color: #ef4444; }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    init_session_state()

    # Try to load sample data
    if not st.session_state.sample_data_loaded:
        load_sample_data()

    # Sidebar navigation
    st.sidebar.title("📊 Content Evaluator")
    st.sidebar.divider()

    # Check for navigation override
    if 'nav_page' in st.session_state and st.session_state.nav_page:
        page = st.session_state.nav_page
        st.session_state.nav_page = None
    else:
        page = st.sidebar.radio(
            "Navigate",
            ["Dashboard", "Evaluate Content", "Batch Evaluation",
             "Compare Versions", "Human Review", "Analytics", "Settings"],
            label_visibility="collapsed"
        )

    st.sidebar.divider()

    # Sidebar info
    st.sidebar.info(
        "LLM Content Quality Evaluator helps you assess "
        "AI-generated product content across multiple quality dimensions."
    )

    # Sample data status
    if st.session_state.sample_data_loaded:
        st.sidebar.success(f"✓ {len(st.session_state.products)} products loaded")
    else:
        st.sidebar.warning("No sample data loaded")

    # Route to appropriate page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Evaluate Content":
        render_evaluation_page()
    elif page == "Batch Evaluation":
        render_batch_evaluation()
    elif page == "Compare Versions":
        render_comparison_view()
    elif page == "Human Review":
        render_human_review()
    elif page == "Analytics":
        render_analytics_dashboard()
    elif page == "Settings":
        render_settings_panel()


if __name__ == "__main__":
    main()
