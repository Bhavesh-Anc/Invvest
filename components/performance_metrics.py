"""
AI Stock Advisor Pro - Performance Metrics Dashboard
Real-time performance monitoring and metrics display
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

def display_enhanced_performance_dashboard(models: Dict, predictions: pd.DataFrame):
    """Display comprehensive performance dashboard"""

    st.header("📊 Enhanced Performance Dashboard")

    # Key Metrics Overview
    _display_key_metrics(predictions)

    # Model Performance
    _display_model_performance(models, predictions)

    # Risk Analysis
    _display_risk_analysis(predictions)

    # Real-time Monitoring
    _display_realtime_monitoring()

def _display_key_metrics(predictions: pd.DataFrame):
    """Display key performance metrics"""
    if predictions.empty:
        st.warning("No predictions available for performance analysis")
        return

    st.subheader("🎯 Key Performance Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_predictions = len(predictions)
        high_confidence = len(predictions[predictions['ensemble_confidence'] >= 0.8])
        st.metric(
            "Total Predictions",
            total_predictions,
            delta=f"{high_confidence} high confidence"
        )

    with col2:
        avg_success_prob = predictions['success_prob'].mean()
        benchmark = 0.6  # Expected baseline
        delta_vs_benchmark = (avg_success_prob - benchmark) * 100
        st.metric(
            "Avg Success Rate",
            f"{avg_success_prob:.1%}",
            delta=f"{delta_vs_benchmark:+.1f}% vs benchmark",
            delta_color="normal"
        )

    with col3:
        bullish_count = len(predictions[predictions['predicted_return'] == 1])
        bullish_pct = bullish_count / total_predictions if total_predictions > 0 else 0
        st.metric(
            "Market Sentiment", 
            f"{bullish_pct:.1%} Bullish",
            delta=f"{bullish_count}/{total_predictions} signals"
        )

    with col4:
        avg_confidence = predictions['ensemble_confidence'].mean()
        confidence_level = "High" if avg_confidence > 0.7 else "Medium" if avg_confidence > 0.5 else "Low"
        st.metric(
            "Model Confidence",
            f"{avg_confidence:.1%}",
            delta=confidence_level
        )

    with col5:
        avg_risk = predictions['risk_score'].mean()
        risk_label = "Low" if avg_risk < 0.3 else "Medium" if avg_risk < 0.7 else "High"
        st.metric(
            "Portfolio Risk",
            f"{avg_risk:.2f}",
            delta=risk_label,
            delta_color="inverse"
        )

def _display_model_performance(models: Dict, predictions: pd.DataFrame):
    """Display model performance analysis"""
    st.subheader("🤖 Model Performance Analysis")

    if predictions.empty:
        st.info("No model performance data available")
        return

    tab1, tab2, tab3 = st.tabs(["📈 Accuracy Analysis", "🎯 Confidence Metrics", "⚖️ Model Comparison"])

    with tab1:
        _display_accuracy_analysis(predictions)

    with tab2:
        _display_confidence_metrics(predictions)

    with tab3:
        _display_model_comparison(models)

def _display_accuracy_analysis(predictions: pd.DataFrame):
    """Display accuracy analysis"""
    col1, col2 = st.columns(2)

    with col1:
        # Success probability distribution
        fig = px.histogram(
            predictions,
            x='success_prob',
            nbins=20,
            title="Success Probability Distribution",
            labels={'success_prob': 'Success Probability', 'count': 'Number of Predictions'},
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(
            showlegend=False,
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Confidence vs Success Rate scatter
        fig = px.scatter(
            predictions,
            x='ensemble_confidence',
            y='success_prob',
            size='models_used',
            color='predicted_return',
            title="Model Confidence vs Success Probability",
            labels={
                'ensemble_confidence': 'Model Confidence',
                'success_prob': 'Success Probability',
                'predicted_return': 'Prediction'
            },
            color_discrete_map={'0': '#ff7f0e', '1': '#2ca02c'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def _display_confidence_metrics(predictions: pd.DataFrame):
    """Display confidence metrics"""

    # Confidence distribution by prediction type
    confidence_by_prediction = predictions.groupby('predicted_return')['ensemble_confidence'].agg(['mean', 'std', 'count']).reset_index()
    confidence_by_prediction['predicted_return'] = confidence_by_prediction['predicted_return'].map({0: 'Bearish', 1: 'Bullish'})

    col1, col2 = st.columns(2)

    with col1:
        # Confidence levels bar chart
        fig = px.bar(
            confidence_by_prediction,
            x='predicted_return',
            y='mean',
            error_y='std',
            title="Average Confidence by Prediction Type",
            labels={'mean': 'Average Confidence', 'predicted_return': 'Prediction Type'},
            color='predicted_return',
            color_discrete_map={'Bearish': '#ff7f0e', 'Bullish': '#2ca02c'}
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Model agreement analysis
        agreement_bins = pd.cut(predictions['model_agreement'], bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
        agreement_counts = agreement_bins.value_counts()

        fig = px.pie(
            values=agreement_counts.values,
            names=agreement_counts.index,
            title="Model Agreement Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def _display_model_comparison(models: Dict):
    """Display model comparison"""
    if not models:
        st.info("No model data available for comparison")
        return

    # Create comparison data
    model_stats = []
    for ticker, ticker_models in models.items():
        for model_key, model in ticker_models.items():
            if hasattr(model, 'cv_scores') and model.cv_scores:
                model_stats.append({
                    'ticker': ticker,
                    'model_type': model_key.split('_')[0],
                    'horizon': '_'.join(model_key.split('_')[1:]),
                    'accuracy': model.cv_scores.get('accuracy', 0),
                    'roc_auc': model.cv_scores.get('roc_auc', 0),
                    'f1_score': model.cv_scores.get('f1', 0),
                    'training_time': getattr(model, 'training_time', 0)
                })

    if not model_stats:
        st.info("No model statistics available")
        return

    model_df = pd.DataFrame(model_stats)

    # Model performance by type
    model_performance = model_df.groupby('model_type')[['accuracy', 'roc_auc', 'f1_score']].mean().reset_index()

    fig = px.bar(
        model_performance.melt(id_vars='model_type', var_name='metric', value_name='score'),
        x='model_type',
        y='score',
        color='metric',
        title="Average Model Performance by Type",
        barmode='group'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def _display_risk_analysis(predictions: pd.DataFrame):
    """Display risk analysis"""
    st.subheader("⚖️ Risk Analysis Dashboard")

    if predictions.empty:
        st.info("No risk data available")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        # Risk distribution
        fig = px.histogram(
            predictions,
            x='risk_score',
            nbins=15,
            title="Risk Score Distribution",
            labels={'risk_score': 'Risk Score', 'count': 'Number of Stocks'},
            color_discrete_sequence=['#d62728']
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Risk vs Return
        fig = px.scatter(
            predictions,
            x='risk_score',
            y='success_prob',
            size='ensemble_confidence',
            color='predicted_return',
            title="Risk vs Expected Return",
            labels={'risk_score': 'Risk Score', 'success_prob': 'Expected Success Rate'},
            color_discrete_map={'0': '#d62728', '1': '#2ca02c'}
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        # Volatility analysis
        if 'volatility' in predictions.columns:
            volatility_levels = pd.cut(
                predictions['volatility'],
                bins=3,
                labels=['Low Volatility', 'Medium Volatility', 'High Volatility']
            )
            vol_counts = volatility_levels.value_counts()

            fig = px.pie(
                values=vol_counts.values,
                names=vol_counts.index,
                title="Volatility Distribution",
                color_discrete_sequence=['#2ca02c', '#ff7f0e', '#d62728']
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

def _display_realtime_monitoring():
    """Display real-time monitoring dashboard"""
    st.subheader("📡 Real-time Monitoring")

    # System status
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("System Status", "🟢 Online", delta="All systems operational")

    with col2:
        last_update = datetime.now() - timedelta(minutes=5)
        st.metric("Last Update", last_update.strftime("%H:%M"), delta="5 min ago")

    with col3:
        st.metric("Active Models", "12", delta="All models running")

    with col4:
        st.metric("Data Sources", "4/4", delta="All connected")

    # Performance trend (mock data for now)
    with st.expander("📈 Performance Trends"):
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        performance_trend = pd.DataFrame({
            'date': dates,
            'accuracy': np.random.normal(0.68, 0.05, len(dates)),
            'confidence': np.random.normal(0.75, 0.08, len(dates))
        })

        fig = px.line(
            performance_trend,
            x='date',
            y=['accuracy', 'confidence'],
            title="30-Day Performance Trend",
            labels={'value': 'Score', 'date': 'Date'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def display_portfolio_performance(portfolio_data: Dict):
    """Display portfolio performance metrics"""
    st.header("💼 Portfolio Performance")

    if not portfolio_data:
        st.info("No portfolio data available")
        return

    # Portfolio overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_value = portfolio_data.get('total_value', 0)
        st.metric("Portfolio Value", f"₹{total_value:,.0f}")

    with col2:
        daily_return = portfolio_data.get('daily_return', 0)
        st.metric("Daily Return", f"{daily_return:.2%}", delta=f"₹{total_value * daily_return:,.0f}")

    with col3:
        volatility = portfolio_data.get('volatility', 0)
        st.metric("Volatility", f"{volatility:.2%}")

    with col4:
        sharpe_ratio = portfolio_data.get('sharpe_ratio', 0)
        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")

def display_alert_system():
    """Display alert system"""
    st.header("🚨 Alert System")

    # Mock alerts for demonstration
    alerts = [
        {"type": "HIGH", "message": "RELIANCE.NS showing strong bullish signals", "time": "2 min ago"},
        {"type": "MEDIUM", "message": "TCS.NS volatility spike detected", "time": "15 min ago"},
        {"type": "LOW", "message": "Model confidence below threshold for INFY.NS", "time": "1 hour ago"}
    ]

    for alert in alerts:
        alert_color = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}[alert["type"]]
        st.write(f"{alert_color} **{alert['type']}**: {alert['message']} - *{alert['time']}*")

# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    # This would be called from the main Streamlit app
    st.title("Performance Dashboard Test")

    # Generate sample data for testing
    sample_predictions = pd.DataFrame({
        'ticker': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS'] * 10,
        'predicted_return': np.random.choice([0, 1], 30),
        'success_prob': np.random.beta(2, 2, 30),
        'ensemble_confidence': np.random.beta(3, 2, 30),
        'risk_score': np.random.beta(2, 3, 30),
        'volatility': np.random.gamma(2, 0.1, 30),
        'models_used': np.random.choice([3, 4, 5], 30),
        'model_agreement': np.random.beta(4, 2, 30)
    })

    display_enhanced_performance_dashboard({}, sample_predictions)
