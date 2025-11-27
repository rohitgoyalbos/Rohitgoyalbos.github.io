"""
Human review interface component for LLM Content Quality Evaluator.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.helpers import generate_id


def render_human_review():
    """Render the human review queue page."""
    st.title("Human Review Queue")

    review_queue = st.session_state.get('review_queue', [])

    # Queue stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pending", len(review_queue))

    with col2:
        reviews_today = len(st.session_state.get('completed_reviews', []))
        st.metric("Reviewed Today", reviews_today)

    with col3:
        avg_time = 3.2  # Placeholder
        st.metric("Avg Review Time", f"{avg_time:.1f}m")

    with col4:
        priority = sum(1 for r in review_queue if r.get('routing_decision') == 'priority_review')
        st.metric("Priority Items", priority)

    st.divider()

    if not review_queue:
        st.info("No items in the review queue. Evaluate some content to populate the queue.")
        return

    # Queue list
    st.subheader("Review Queue")

    # Sorting options
    sort_by = st.selectbox(
        "Sort by",
        ["Priority (High to Low)", "Score (Low to High)", "Most Recent"],
        key="review_sort"
    )

    # Sort the queue
    sorted_queue = list(review_queue)
    if sort_by == "Priority (High to Low)":
        priority_order = {'priority_review': 0, 'standard_review': 1, 'light_review': 2}
        sorted_queue.sort(key=lambda x: priority_order.get(x.get('routing_decision', 'standard_review'), 1))
    elif sort_by == "Score (Low to High)":
        sorted_queue.sort(key=lambda x: x.get('composite_score', 0))
    else:
        sorted_queue.sort(key=lambda x: x.get('timestamp', datetime.now()), reverse=True)

    # Display queue items
    for i, item in enumerate(sorted_queue):
        render_queue_item(item, i)


def render_queue_item(item: Dict[str, Any], index: int):
    """Render a single queue item."""
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])

        with col1:
            st.write(f"**{item.get('product_name', 'Unknown Product')}**")
            st.caption(f"ID: {item.get('id', 'N/A')}")

        with col2:
            score = item.get('composite_score', 0)
            st.metric("Score", f"{score:.0f}")

        with col3:
            routing = item.get('routing_decision', 'standard_review')
            if routing == 'priority_review':
                st.error("Priority")
            else:
                st.warning("Standard")

        with col4:
            confidence = item.get('confidence', 0)
            st.metric("Confidence", f"{confidence:.0%}")

        with col5:
            if st.button("Review", key=f"review_{index}"):
                st.session_state.current_review_item = item
                st.session_state.show_review_modal = True
                st.rerun()

        st.divider()

    # Review modal
    if st.session_state.get('show_review_modal') and st.session_state.get('current_review_item') == item:
        render_review_modal(item, index)


def render_review_modal(item: Dict[str, Any], index: int):
    """Render the review modal/expanded view."""
    st.markdown("---")
    st.subheader(f"Review: {item.get('product_name', 'Unknown')}")

    # Two-column layout
    col_content, col_specs = st.columns(2)

    with col_content:
        st.write("**Generated Content**")

        # Get content from the evaluation
        if 'content' in item:
            content = item['content']
        else:
            content = {
                'description': 'Content not available for preview',
                'marketing_copy': '',
                'feature_bullets': [],
                'meta_description': ''
            }

        # Display highlighted content with issues
        st.text_area(
            "Description",
            value=str(content.get('description', '')),
            height=150,
            disabled=True,
            key=f"review_content_{index}"
        )

        st.text_area(
            "Marketing Copy",
            value=str(content.get('marketing_copy', '')),
            height=100,
            disabled=True,
            key=f"review_marketing_{index}"
        )

    with col_specs:
        st.write("**Auto-Evaluation Results**")

        dimension_scores = item.get('dimension_scores', {})

        for dim, score in dimension_scores.items():
            col_dim, col_score = st.columns([3, 1])
            with col_dim:
                st.write(dim.replace('_', ' ').title())
            with col_score:
                if score >= 70:
                    st.success(f"{score:.0f}")
                elif score >= 50:
                    st.warning(f"{score:.0f}")
                else:
                    st.error(f"{score:.0f}")

        # Show issues
        issues = item.get('top_issues', [])
        if issues:
            st.write("**Flagged Issues:**")
            for issue in issues[:5]:
                if hasattr(issue, 'message'):
                    st.write(f"- {issue.message}")
                elif isinstance(issue, dict):
                    st.write(f"- {issue.get('message', '')}")

    st.divider()

    # Reviewer scoring
    st.subheader("Reviewer Scoring")

    reviewer_id = st.text_input("Reviewer ID", value="reviewer_01", key=f"reviewer_id_{index}")

    score_cols = st.columns(6)

    scores = {}
    dimensions = ['Accuracy', 'Completeness', 'Brand Voice', 'Readability', 'SEO', 'Overall']

    for i, dim in enumerate(dimensions):
        with score_cols[i]:
            scores[dim.lower().replace(' ', '_')] = st.select_slider(
                dim,
                options=[1, 2, 3, 4, 5],
                value=3,
                key=f"score_{dim}_{index}"
            )

    # Comments
    st.text_area(
        "Review Notes",
        placeholder="Add any notes or comments about this content...",
        key=f"review_notes_{index}"
    )

    # Verdict
    st.subheader("Verdict")

    verdict_col1, verdict_col2, verdict_col3 = st.columns(3)

    with verdict_col1:
        approve = st.button("✅ Approve", type="primary", key=f"approve_{index}")

    with verdict_col2:
        conditional = st.button("⚠️ Conditional Approve", key=f"conditional_{index}")

    with verdict_col3:
        reject = st.button("❌ Reject", key=f"reject_{index}")

    if approve or conditional or reject:
        # Create review record
        verdict = "approve" if approve else "conditional_approve" if conditional else "reject"

        review_record = {
            'id': generate_id('REV'),
            'evaluation_id': item.get('id'),
            'reviewer_id': reviewer_id,
            'scores': scores,
            'verdict': verdict,
            'notes': st.session_state.get(f'review_notes_{index}', ''),
            'reviewed_at': datetime.now()
        }

        # Update completed reviews
        if 'completed_reviews' not in st.session_state:
            st.session_state.completed_reviews = []
        st.session_state.completed_reviews.append(review_record)

        # Remove from queue
        st.session_state.review_queue = [
            r for r in st.session_state.review_queue
            if r.get('id') != item.get('id')
        ]

        # Reset modal state
        st.session_state.show_review_modal = False
        st.session_state.current_review_item = None

        st.success(f"Review submitted: {verdict.replace('_', ' ').title()}")
        st.rerun()

    # Cancel button
    if st.button("Cancel", key=f"cancel_{index}"):
        st.session_state.show_review_modal = False
        st.session_state.current_review_item = None
        st.rerun()


def render_review_history():
    """Render completed reviews history."""
    st.subheader("Review History")

    completed = st.session_state.get('completed_reviews', [])

    if not completed:
        st.info("No completed reviews yet.")
        return

    # Display as table
    import pandas as pd

    review_data = []
    for review in completed:
        review_data.append({
            'Review ID': review.get('id', ''),
            'Evaluation ID': review.get('evaluation_id', ''),
            'Reviewer': review.get('reviewer_id', ''),
            'Verdict': review.get('verdict', '').replace('_', ' ').title(),
            'Overall Score': review.get('scores', {}).get('overall', 0),
            'Reviewed At': review.get('reviewed_at', '').strftime('%Y-%m-%d %H:%M') if review.get('reviewed_at') else ''
        })

    df = pd.DataFrame(review_data)
    st.dataframe(df, use_container_width=True)
