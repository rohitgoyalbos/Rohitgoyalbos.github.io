"""
Analytics dashboard component for LLM Content Quality Evaluator.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random


def render_analytics_dashboard():
    """Render the analytics dashboard page."""
    st.title("Performance Analytics")

    # Time period selector
    col1, col2 = st.columns([2, 1])

    with col1:
        time_period = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            key="analytics_period"
        )

    with col2:
        category_filter = st.selectbox(
            "Category",
            ["All Categories", "Consumer Electronics", "Fashion/Apparel",
             "Home & Garden", "Beauty & Personal Care", "Sports & Outdoors"],
            key="analytics_category"
        )

    st.divider()

    # Generate or load analytics data
    analytics_data = generate_analytics_data(time_period, category_filter)

    # Key metrics row
    render_key_metrics(analytics_data)

    st.divider()

    # Two-column layout for charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Quality Score vs Conversion Rate")
        render_correlation_chart(analytics_data)

    with col_right:
        st.subheader("Dimension Impact on Conversion")
        render_dimension_impact_chart(analytics_data)

    st.divider()

    # Trend charts
    st.subheader("Quality Trends Over Time")
    render_trend_chart(analytics_data)

    st.divider()

    # Detailed breakdown
    st.subheader("Detailed Performance Data")
    render_performance_table(analytics_data)


def generate_analytics_data(time_period: str, category: str) -> Dict[str, Any]:
    """Generate simulated analytics data for demonstration."""
    # Set seed for reproducibility
    np.random.seed(42)

    # Determine number of data points based on time period
    days_map = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "All time": 180
    }
    num_days = days_map.get(time_period, 30)

    # Generate product-level data
    num_products = 50
    products = []

    for i in range(num_products):
        quality_score = np.random.normal(72, 15)
        quality_score = max(30, min(100, quality_score))

        # Conversion rate correlates with quality score
        base_conversion = 2 + (quality_score - 50) * 0.08
        conversion_rate = max(0.5, base_conversion + np.random.normal(0, 0.8))

        # Other metrics also correlate
        products.append({
            'product_id': f'SKU-{10000 + i}',
            'quality_score': round(quality_score, 1),
            'conversion_rate': round(conversion_rate, 2),
            'impressions': np.random.randint(5000, 50000),
            'clicks': np.random.randint(200, 5000),
            'revenue': round(np.random.uniform(1000, 50000), 2),
            'accuracy_score': round(quality_score + np.random.normal(0, 5), 1),
            'completeness_score': round(quality_score + np.random.normal(0, 8), 1),
            'brand_voice_score': round(quality_score + np.random.normal(0, 10), 1),
            'seo_score': round(quality_score + np.random.normal(0, 7), 1),
            'readability_score': round(quality_score + np.random.normal(0, 6), 1),
            'style_score': round(quality_score + np.random.normal(0, 9), 1),
        })

    # Generate daily trend data
    daily_data = []
    start_date = datetime.now() - timedelta(days=num_days)

    for day in range(num_days):
        date = start_date + timedelta(days=day)
        # Slight upward trend with noise
        trend_factor = 1 + (day / num_days) * 0.1
        daily_data.append({
            'date': date,
            'avg_score': round(70 * trend_factor + np.random.normal(0, 3), 1),
            'evaluations': np.random.randint(10, 100),
            'excellent_rate': round(20 * trend_factor + np.random.normal(0, 5), 1),
            'conversion_rate': round(3.5 * trend_factor + np.random.normal(0, 0.5), 2)
        })

    # Calculate dimension correlations
    dimension_correlations = {
        'accuracy': 0.68 + np.random.uniform(-0.05, 0.05),
        'completeness': 0.61 + np.random.uniform(-0.05, 0.05),
        'seo': 0.54 + np.random.uniform(-0.05, 0.05),
        'readability': 0.48 + np.random.uniform(-0.05, 0.05),
        'brand_voice': 0.42 + np.random.uniform(-0.05, 0.05),
        'style': 0.35 + np.random.uniform(-0.05, 0.05),
    }

    # Calculate summary statistics
    product_df = pd.DataFrame(products)
    avg_score = product_df['quality_score'].mean()
    avg_conversion = product_df['conversion_rate'].mean()

    # Calculate correlation
    correlation = product_df['quality_score'].corr(product_df['conversion_rate'])

    return {
        'products': products,
        'daily_data': daily_data,
        'dimension_correlations': dimension_correlations,
        'summary': {
            'avg_score': round(avg_score, 1),
            'avg_conversion': round(avg_conversion, 2),
            'correlation': round(correlation, 2),
            'excellent_rate': round(len([p for p in products if p['quality_score'] >= 90]) / len(products) * 100, 0),
            'total_evaluations': sum(d['evaluations'] for d in daily_data),
            'total_revenue': round(product_df['revenue'].sum(), 2)
        }
    }


def render_key_metrics(data: Dict[str, Any]):
    """Render key metrics row."""
    summary = data['summary']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Avg Quality Score",
            f"{summary['avg_score']:.1f}",
            delta="+3.2 vs last period"
        )

    with col2:
        st.metric(
            "Avg Conversion",
            f"{summary['avg_conversion']:.1f}%",
            delta="+0.4%"
        )

    with col3:
        st.metric(
            "Score-Conversion Correlation",
            f"r={summary['correlation']:.2f}",
            delta="Strong positive"
        )

    with col4:
        st.metric(
            "Excellence Rate",
            f"{summary['excellent_rate']:.0f}%",
            delta="+5%"
        )


def render_correlation_chart(data: Dict[str, Any]):
    """Render quality score vs conversion rate scatter plot."""
    products = data['products']
    df = pd.DataFrame(products)

    fig = px.scatter(
        df,
        x='quality_score',
        y='conversion_rate',
        size='revenue',
        color='quality_score',
        color_continuous_scale='RdYlGn',
        hover_data=['product_id', 'impressions'],
        labels={
            'quality_score': 'Quality Score',
            'conversion_rate': 'Conversion Rate (%)',
            'revenue': 'Revenue'
        }
    )

    # Add trend line
    z = np.polyfit(df['quality_score'], df['conversion_rate'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df['quality_score'].min(), df['quality_score'].max(), 100)

    fig.add_trace(go.Scatter(
        x=x_line,
        y=p(x_line),
        mode='lines',
        name='Trend',
        line=dict(color='rgba(0,0,0,0.5)', dash='dash')
    ))

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_dimension_impact_chart(data: Dict[str, Any]):
    """Render dimension impact on conversion bar chart."""
    correlations = data['dimension_correlations']

    df = pd.DataFrame([
        {'Dimension': k.replace('_', ' ').title(), 'Correlation': v}
        for k, v in sorted(correlations.items(), key=lambda x: x[1], reverse=True)
    ])

    fig = px.bar(
        df,
        x='Correlation',
        y='Dimension',
        orientation='h',
        color='Correlation',
        color_continuous_scale='RdYlGn',
        labels={'Correlation': 'Correlation with Conversion'}
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )

    st.plotly_chart(fig, use_container_width=True)


def render_trend_chart(data: Dict[str, Any]):
    """Render quality score trend over time."""
    daily_data = data['daily_data']
    df = pd.DataFrame(daily_data)

    fig = go.Figure()

    # Quality score trend
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['avg_score'],
        mode='lines+markers',
        name='Avg Quality Score',
        line=dict(color='#3b82f6', width=2)
    ))

    # Excellence rate (secondary axis)
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['excellent_rate'],
        mode='lines',
        name='Excellence Rate (%)',
        line=dict(color='#22c55e', width=2, dash='dot'),
        yaxis='y2'
    ))

    fig.update_layout(
        height=400,
        xaxis_title='Date',
        yaxis_title='Quality Score',
        yaxis2=dict(
            title='Excellence Rate (%)',
            overlaying='y',
            side='right'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)


def render_performance_table(data: Dict[str, Any]):
    """Render detailed performance data table."""
    products = data['products']
    df = pd.DataFrame(products)

    # Select and rename columns for display
    display_df = df[[
        'product_id', 'quality_score', 'conversion_rate',
        'impressions', 'clicks', 'revenue'
    ]].copy()

    display_df.columns = [
        'Product ID', 'Quality Score', 'Conversion Rate (%)',
        'Impressions', 'Clicks', 'Revenue ($)'
    ]

    # Sort by quality score
    display_df = display_df.sort_values('Quality Score', ascending=False)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # Export button
    csv = display_df.to_csv(index=False)
    st.download_button(
        "Download Data (CSV)",
        data=csv,
        file_name="analytics_data.csv",
        mime="text/csv"
    )
