"""
Content input component for LLM Content Quality Evaluator.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional, Tuple

from config import PRODUCT_CATEGORIES


def render_content_input() -> Tuple[Optional[Dict], Optional[Dict], str]:
    """
    Render content input interface.

    Returns:
        Tuple of (content_dict, specifications_dict, category)
    """
    content = None
    specifications = None

    # Input method tabs
    tab1, tab2, tab3 = st.tabs(["Manual Entry", "Upload JSON", "Select from Database"])

    with tab1:
        content, specifications, category = render_manual_entry()

    with tab2:
        uploaded_content, uploaded_specs, uploaded_category = render_json_upload()
        if uploaded_content:
            content = uploaded_content
            specifications = uploaded_specs
            category = uploaded_category

    with tab3:
        selected_content, selected_specs, selected_category = render_database_select()
        if selected_content:
            content = selected_content
            specifications = selected_specs
            category = selected_category

    # Return the active input
    return content, specifications, category if 'category' in dir() else "Consumer Electronics"


def render_manual_entry() -> Tuple[Optional[Dict], Optional[Dict], str]:
    """Render manual entry form."""
    col1, col2 = st.columns(2)

    with col1:
        category = st.selectbox(
            "Product Category",
            PRODUCT_CATEGORIES,
            key="manual_category"
        )

    with col2:
        subcategory = st.text_input(
            "Subcategory (optional)",
            key="manual_subcategory"
        )

    st.subheader("Source Specifications (Ground Truth)")

    spec_col1, spec_col2 = st.columns(2)

    with spec_col1:
        product_name = st.text_input("Product Name", key="spec_name")
        brand = st.text_input("Brand", key="spec_brand")
        price = st.number_input("Price ($)", min_value=0.0, step=0.01, key="spec_price")

    with spec_col2:
        warranty = st.text_input("Warranty", key="spec_warranty")
        materials = st.text_input("Materials (comma-separated)", key="spec_materials")
        colors = st.text_input("Available Colors (comma-separated)", key="spec_colors")

    features = st.text_area(
        "Features (one per line)",
        height=100,
        key="spec_features"
    )

    st.subheader("Generated Content (To Evaluate)")

    description = st.text_area(
        "Product Description",
        height=150,
        key="content_description",
        placeholder="Enter the LLM-generated product description..."
    )

    marketing_copy = st.text_area(
        "Marketing Copy",
        height=100,
        key="content_marketing",
        placeholder="Enter the marketing copy..."
    )

    feature_bullets = st.text_area(
        "Feature Bullets (one per line)",
        height=100,
        key="content_bullets",
        placeholder="Enter feature bullet points..."
    )

    meta_description = st.text_input(
        "Meta Description",
        key="content_meta",
        placeholder="SEO meta description..."
    )

    with st.expander("Advanced Options"):
        prompt_used = st.text_area(
            "Prompt Used (optional)",
            height=100,
            key="content_prompt"
        )
        model_version = st.text_input(
            "Model Version (optional)",
            key="content_model"
        )

    # Build content and specs if enough data provided
    if product_name and description:
        specifications = {
            "name": product_name,
            "brand": brand,
            "price": price if price > 0 else None,
            "warranty": warranty,
            "materials": [m.strip() for m in materials.split(",")] if materials else [],
            "colors": [c.strip() for c in colors.split(",")] if colors else [],
            "features": [f.strip() for f in features.split("\n") if f.strip()]
        }

        content = {
            "description": description,
            "marketing_copy": marketing_copy,
            "feature_bullets": [b.strip() for b in feature_bullets.split("\n") if b.strip()],
            "meta_description": meta_description
        }

        return content, specifications, category

    return None, None, category


def render_json_upload() -> Tuple[Optional[Dict], Optional[Dict], str]:
    """Render JSON upload interface."""
    st.write("Upload a JSON file containing product specifications and generated content.")

    uploaded_file = st.file_uploader(
        "Upload JSON",
        type=['json'],
        key="json_upload"
    )

    if uploaded_file:
        try:
            data = json.load(uploaded_file)

            # Display preview
            st.write("**Preview:**")

            # Extract specifications
            specifications = data.get('specifications', {})
            if not specifications and 'name' in data:
                specifications = {k: v for k, v in data.items()
                                  if k not in ['generated_content', 'category', 'product_id']}

            # Extract content
            content = data.get('generated_content', {})
            if isinstance(content, dict) and 'version_1' in content:
                content = content['version_1']

            # Extract content fields
            content_dict = {
                'description': content.get('description', ''),
                'marketing_copy': content.get('marketing_copy', ''),
                'feature_bullets': content.get('feature_bullets', []),
                'meta_description': content.get('meta_description', '')
            }

            category = data.get('category', 'Consumer Electronics')

            # Show preview
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Specifications:**")
                st.json(specifications)
            with col2:
                st.write("**Content:**")
                st.json(content_dict)

            return content_dict, specifications, category

        except json.JSONDecodeError:
            st.error("Invalid JSON file")
        except Exception as e:
            st.error(f"Error parsing file: {e}")

    return None, None, "Consumer Electronics"


def render_database_select() -> Tuple[Optional[Dict], Optional[Dict], str]:
    """Render database selection interface."""
    products = st.session_state.get('products', [])

    if not products:
        st.info("No products loaded. Generate sample data from the Dashboard or upload a JSON file.")
        return None, None, "Consumer Electronics"

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        categories = list(set(p.get('category', 'Unknown') for p in products))
        selected_category = st.selectbox(
            "Filter by Category",
            ["All"] + categories,
            key="db_category_filter"
        )

    with col2:
        brands = list(set(p.get('brand', 'Unknown') for p in products))
        selected_brand = st.selectbox(
            "Filter by Brand",
            ["All"] + brands,
            key="db_brand_filter"
        )

    # Filter products
    filtered = products
    if selected_category != "All":
        filtered = [p for p in filtered if p.get('category') == selected_category]
    if selected_brand != "All":
        filtered = [p for p in filtered if p.get('brand') == selected_brand]

    # Product selector
    product_options = {
        f"{p.get('specifications', {}).get('name', 'Unknown')} ({p.get('product_id', 'N/A')})": p
        for p in filtered
    }

    if not product_options:
        st.warning("No products match the selected filters.")
        return None, None, "Consumer Electronics"

    selected_name = st.selectbox(
        "Select Product",
        list(product_options.keys()),
        key="db_product_select"
    )

    selected_product = product_options.get(selected_name)

    if selected_product:
        st.session_state.selected_product = selected_product

        # Version selector
        content_versions = selected_product.get('generated_content', {})
        version_names = list(content_versions.keys())

        if version_names:
            selected_version = st.selectbox(
                "Select Content Version",
                version_names,
                key="db_version_select"
            )

            version_content = content_versions[selected_version]

            # Display preview
            with st.expander("Preview Selected Content", expanded=True):
                st.write(f"**Quality Level:** {version_content.get('quality_level', 'Unknown')}")
                st.write(f"**Model:** {version_content.get('model', 'Unknown')}")
                st.write("**Description:**")
                st.write(version_content.get('description', '')[:500] + "...")

            # Build return values
            content = {
                'description': version_content.get('description', ''),
                'marketing_copy': version_content.get('marketing_copy', ''),
                'feature_bullets': version_content.get('feature_bullets', []),
                'meta_description': version_content.get('meta_description', '')
            }

            specifications = selected_product.get('specifications', {})
            category = selected_product.get('category', 'Consumer Electronics')

            return content, specifications, category

    return None, None, "Consumer Electronics"
