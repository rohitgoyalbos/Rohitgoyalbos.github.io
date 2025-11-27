"""
Settings panel component for LLM Content Quality Evaluator.
"""

import streamlit as st
import json
from typing import Dict, Any

from config import DEFAULT_WEIGHTS, QUALITY_TIERS, ROUTING_THRESHOLDS


def render_settings_panel():
    """Render the settings configuration page."""
    st.title("Settings")

    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs([
        "Evaluation Weights",
        "Brand Guidelines",
        "Routing Thresholds",
        "Data Management"
    ])

    with tab1:
        render_weights_settings()

    with tab2:
        render_brand_guidelines_settings()

    with tab3:
        render_routing_settings()

    with tab4:
        render_data_management()


def render_weights_settings():
    """Render evaluation weights configuration."""
    st.subheader("Evaluation Dimension Weights")

    st.info(
        "Adjust the relative importance of each dimension in the composite score. "
        "Weights must sum to 1.0 (100%)."
    )

    current_weights = st.session_state.get('weights', DEFAULT_WEIGHTS.copy())

    col1, col2 = st.columns(2)

    with col1:
        accuracy = st.slider(
            "Accuracy",
            min_value=0.0,
            max_value=0.5,
            value=current_weights.get('accuracy', 0.25),
            step=0.05,
            format="%.2f",
            key="weight_accuracy"
        )

        completeness = st.slider(
            "Completeness",
            min_value=0.0,
            max_value=0.5,
            value=current_weights.get('completeness', 0.20),
            step=0.05,
            format="%.2f",
            key="weight_completeness"
        )

        brand_voice = st.slider(
            "Brand Voice",
            min_value=0.0,
            max_value=0.5,
            value=current_weights.get('brand_voice', 0.15),
            step=0.05,
            format="%.2f",
            key="weight_brand_voice"
        )

    with col2:
        seo = st.slider(
            "SEO",
            min_value=0.0,
            max_value=0.5,
            value=current_weights.get('seo', 0.15),
            step=0.05,
            format="%.2f",
            key="weight_seo"
        )

        readability = st.slider(
            "Readability",
            min_value=0.0,
            max_value=0.5,
            value=current_weights.get('readability', 0.10),
            step=0.05,
            format="%.2f",
            key="weight_readability"
        )

        style = st.slider(
            "Style Compliance",
            min_value=0.0,
            max_value=0.5,
            value=current_weights.get('style', 0.10),
            step=0.05,
            format="%.2f",
            key="weight_style"
        )

    # Calculate total
    total = accuracy + completeness + brand_voice + seo + readability + style

    if abs(total - 1.0) > 0.001:
        st.warning(f"Weights sum to {total:.2f}. They should sum to 1.0 for proper scoring.")
    else:
        st.success("Weights sum to 1.0 ")

    # Save button
    if st.button("Save Weights", type="primary"):
        new_weights = {
            'accuracy': accuracy,
            'completeness': completeness,
            'brand_voice': brand_voice,
            'seo': seo,
            'readability': readability,
            'style': style
        }
        st.session_state.weights = new_weights
        st.success("Weights saved successfully!")

    # Reset button
    if st.button("Reset to Defaults"):
        st.session_state.weights = DEFAULT_WEIGHTS.copy()
        st.success("Weights reset to defaults!")
        st.rerun()


def render_brand_guidelines_settings():
    """Render brand guidelines configuration."""
    st.subheader("Brand Guidelines Configuration")

    current_guidelines = st.session_state.get('brand_guidelines', {})

    # Brand name
    brand_name = st.text_input(
        "Brand Name",
        value=current_guidelines.get('brand_name', 'TechBrand'),
        key="brand_name"
    )

    st.divider()

    # Voice attributes
    st.write("**Voice Attributes**")

    col1, col2 = st.columns(2)

    with col1:
        tone = st.text_input(
            "Tone",
            value=current_guidelines.get('voice_attributes', {}).get('tone', 'professional yet approachable'),
            key="brand_tone"
        )

        perspective = st.selectbox(
            "Perspective",
            ["second person (you/your)", "first person (we/our)", "third person (they/their)"],
            index=0,
            key="brand_perspective"
        )

    with col2:
        personality = st.text_input(
            "Personality traits (comma-separated)",
            value=", ".join(current_guidelines.get('voice_attributes', {}).get('personality', ['innovative', 'reliable', 'premium'])),
            key="brand_personality"
        )

    st.divider()

    # Terminology
    st.write("**Terminology**")

    col1, col2 = st.columns(2)

    with col1:
        prohibited_text = st.text_area(
            "Prohibited Terms (one per line)",
            value="\n".join(current_guidelines.get('terminology', {}).get('prohibited', [
                'best in class', 'world\'s first', 'revolutionary',
                'game-changing', 'unbeatable'
            ])),
            height=150,
            key="prohibited_terms"
        )

    with col2:
        preferred_text = st.text_area(
            "Preferred Term Mappings (original: preferred, one per line)",
            value="\n".join([
                f"{k}: {v}"
                for k, v in current_guidelines.get('terminology', {}).get('preferred', {
                    'smartphone': 'device',
                    'buy': 'get yours',
                    'features': 'capabilities'
                }).items()
            ]),
            height=150,
            key="preferred_terms"
        )

    st.divider()

    # Style rules
    st.write("**Style Rules**")

    col1, col2, col3 = st.columns(3)

    with col1:
        max_sentence = st.number_input(
            "Max Sentence Length (words)",
            min_value=10,
            max_value=50,
            value=current_guidelines.get('style_rules', {}).get('sentence_length', {}).get('max', 25),
            key="max_sentence"
        )

    with col2:
        max_paragraph = st.number_input(
            "Max Paragraph Length (sentences)",
            min_value=1,
            max_value=10,
            value=current_guidelines.get('style_rules', {}).get('paragraph_length', {}).get('max', 4),
            key="max_paragraph"
        )

    with col3:
        capitalization = st.selectbox(
            "Capitalization Style",
            ["sentence case for descriptions", "title case", "lowercase"],
            key="capitalization"
        )

    # Save button
    if st.button("Save Brand Guidelines", type="primary"):
        # Parse prohibited terms
        prohibited = [t.strip() for t in prohibited_text.split('\n') if t.strip()]

        # Parse preferred terms
        preferred = {}
        for line in preferred_text.split('\n'):
            if ':' in line:
                parts = line.split(':', 1)
                preferred[parts[0].strip()] = parts[1].strip()

        new_guidelines = {
            'brand_name': brand_name,
            'voice_attributes': {
                'tone': tone,
                'personality': [p.strip() for p in personality.split(',')],
                'perspective': perspective
            },
            'terminology': {
                'prohibited': prohibited,
                'preferred': preferred
            },
            'style_rules': {
                'sentence_length': {'max': max_sentence, 'ideal': 15},
                'paragraph_length': {'max': max_paragraph, 'ideal': 2},
                'capitalization': capitalization
            }
        }

        st.session_state.brand_guidelines = new_guidelines
        st.success("Brand guidelines saved successfully!")


def render_routing_settings():
    """Render routing threshold configuration."""
    st.subheader("Review Routing Thresholds")

    st.info(
        "Configure the score thresholds for automatic routing decisions. "
        "Content is routed based on composite score and confidence level."
    )

    st.write("**Current Routing Rules:**")

    routing_data = [
        {
            'Route': 'Auto-Publish',
            'Min Score': ROUTING_THRESHOLDS['auto_publish']['score'],
            'Min Confidence': f"{ROUTING_THRESHOLDS['auto_publish']['confidence']:.0%}",
            'Action': 'Published without human review'
        },
        {
            'Route': 'Light Review',
            'Min Score': ROUTING_THRESHOLDS['light_review']['score'],
            'Min Confidence': f"{ROUTING_THRESHOLDS['light_review']['confidence']:.0%}",
            'Action': '5% audit sample reviewed'
        },
        {
            'Route': 'Standard Review',
            'Min Score': ROUTING_THRESHOLDS['standard_review']['score'],
            'Min Confidence': f"{ROUTING_THRESHOLDS['standard_review']['confidence']:.0%}",
            'Action': 'Full human review required'
        },
        {
            'Route': 'Priority Review',
            'Min Score': ROUTING_THRESHOLDS['priority_review']['score'],
            'Min Confidence': f"{ROUTING_THRESHOLDS['priority_review']['confidence']:.0%}",
            'Action': 'Expedited review by senior staff'
        },
        {
            'Route': 'Reject',
            'Min Score': '<40',
            'Min Confidence': '-',
            'Action': 'Regenerate content'
        },
    ]

    import pandas as pd
    st.dataframe(pd.DataFrame(routing_data), use_container_width=True, hide_index=True)

    st.write("**Quality Tiers:**")

    tier_data = [
        {
            'Tier': config['label'],
            'Score Range': f"{config['min']}-{config['max']}",
            'Color': config['color']
        }
        for config in QUALITY_TIERS.values()
    ]

    st.dataframe(pd.DataFrame(tier_data), use_container_width=True, hide_index=True)


def render_data_management():
    """Render data management options."""
    st.subheader("Data Management")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Sample Data**")

        if st.button("Generate New Sample Data", type="primary"):
            with st.spinner("Generating 100 sample products..."):
                from data.synthetic_generator import generate_sample_data
                import os
                data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sample_products.json')
                generate_sample_data(data_path, num_products=100)
                st.success("Sample data generated!")
                st.session_state.sample_data_loaded = False
                st.rerun()

        if st.session_state.get('sample_data_loaded'):
            st.success(f"✓ {len(st.session_state.get('products', []))} products loaded")
        else:
            st.warning("No sample data loaded")

    with col2:
        st.write("**Clear Data**")

        if st.button("Clear Evaluation History"):
            st.session_state.evaluation_history = []
            st.session_state.current_evaluation = None
            st.success("Evaluation history cleared!")

        if st.button("Clear Review Queue"):
            st.session_state.review_queue = []
            st.success("Review queue cleared!")

        if st.button("Reset All Settings"):
            st.session_state.weights = DEFAULT_WEIGHTS.copy()
            st.session_state.brand_guidelines = {}
            st.success("Settings reset to defaults!")
            st.rerun()

    st.divider()

    st.write("**Export/Import Configuration**")

    # Export configuration
    if st.button("Export Configuration"):
        config = {
            'weights': st.session_state.get('weights', DEFAULT_WEIGHTS),
            'brand_guidelines': st.session_state.get('brand_guidelines', {})
        }
        config_json = json.dumps(config, indent=2)
        st.download_button(
            "Download Configuration",
            data=config_json,
            file_name="evaluator_config.json",
            mime="application/json"
        )

    # Import configuration
    uploaded_config = st.file_uploader(
        "Import Configuration",
        type=['json'],
        key="config_upload"
    )

    if uploaded_config:
        try:
            config = json.load(uploaded_config)
            if 'weights' in config:
                st.session_state.weights = config['weights']
            if 'brand_guidelines' in config:
                st.session_state.brand_guidelines = config['brand_guidelines']
            st.success("Configuration imported successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error importing configuration: {e}")
