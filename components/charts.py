import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)

def display_advanced_charts(data: Dict, chart_type: str = "comprehensive"):
    """Display advanced chart suite"""
    if chart_type == "comprehensive":
        _display_comprehensive_charts(data)
    elif chart_type == "technical":
        _display_technical_charts(data)
    elif chart_type == "portfolio":
        _display_portfolio_charts(data)
    elif chart_type == "risk":
        _display_risk_charts(data)

def _display_comprehensive_charts(data: Dict):
    """Display comprehensive chart dashboard"""
    st.header("📊 Advanced Market Analysis")
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Performance Analysis",
        "📈 Technical Analysis",
        "💼 Portfolio Analysis",
        "⚖️ Risk Analysis"
    ])
    with tab1:
        _display_performance_charts(data)
    with tab2:
        _display_technical_charts(data)
    with tab3:
        _display_portfolio_charts(data)
    with tab4:
        _display_risk_charts(data)

def _display_performance_charts(data: Dict):
    predictions = data.get('predictions', pd.DataFrame())
    if predictions.empty:
        st.warning("No prediction data available for performance charts")
        return

    col1, col2 = st.columns(2)
    with col1:
        if len(predictions) > 5:
            fig = create_prediction_heatmap(predictions)
            st.plotly_chart(fig, width="stretch")
        fig = create_confidence_distribution(predictions)
        st.plotly_chart(fig, width="stretch")
    with col2:
        fig = create_risk_return_scatter(predictions)
        st.plotly_chart(fig, width="stretch")
        fig = create_sentiment_gauge(predictions)
        st.plotly_chart(fig, width="stretch")

def _display_technical_charts(data: Dict):
    raw_data = data.get('raw_data', {})
    if not raw_data:
        st.warning("No raw data available for technical charts")
        return

    selected_stock = st.selectbox(
        "Select Stock for Technical Analysis",
        options=list(raw_data.keys()),
        key="tech_analysis_stock"
    )
    if selected_stock and selected_stock in raw_data:
        stock_data = raw_data[selected_stock]
        if not stock_data.empty:
            fig = create_technical_analysis_chart(stock_data, selected_stock)
            st.plotly_chart(fig, width="stretch", height=600)
            col1, col2 = st.columns(2)
            with col1:
                fig = create_volume_analysis_chart(stock_data)
                st.plotly_chart(fig, width="stretch")
            with col2:
                fig = create_volatility_chart(stock_data)
                st.plotly_chart(fig, width="stretch")

def _display_portfolio_charts(data: Dict):
    predictions = data.get('predictions', pd.DataFrame())
    portfolio_data = data.get('portfolio', {})

    col1, col2 = st.columns(2)
    with col1:
        if not predictions.empty:
            fig = create_portfolio_composition_chart(predictions)
            st.plotly_chart(fig, width="stretch")
        if 'sector_data' in data:
            fig = create_sector_allocation_chart(data['sector_data'])
            st.plotly_chart(fig, width="stretch")
    with col2:
        if portfolio_data:
            fig = create_portfolio_performance_chart(portfolio_data)
            st.plotly_chart(fig, width="stretch")
        if not predictions.empty and len(predictions) > 3:
            fig = create_correlation_heatmap(predictions)
            st.plotly_chart(fig, width="stretch")

def _display_risk_charts(data: Dict):
    predictions = data.get('predictions', pd.DataFrame())
    if predictions.empty:
        st.warning("No data available for risk analysis")
        return

    col1, col2 = st.columns(2)
    with col1:
        fig = create_risk_distribution_chart(predictions)
        st.plotly_chart(fig, width="stretch")
        fig = create_var_analysis_chart(predictions)
        st.plotly_chart(fig, width="stretch")
    with col2:
        fig = create_risk_adjusted_returns_chart(predictions)
        st.plotly_chart(fig, width="stretch")
        fig = create_monte_carlo_chart(predictions)
        st.plotly_chart(fig, width="stretch")

# ==================== CHART CREATION FUNCTIONS ====================

def create_prediction_heatmap(predictions: pd.DataFrame) -> go.Figure:
    """Create prediction confidence heatmap"""
    try:
        # Create a matrix of predictions vs confidence
        pivot_data = predictions.pivot_table(
            values='ensemble_confidence',
            index='ticker',
            columns='predicted_return',
            aggfunc='mean'
        ).fillna(0)

        fig = px.imshow(
            pivot_data,
            title="Prediction Confidence Heatmap",
            labels={'color': 'Confidence', 'x': 'Prediction (0=Sell, 1=Buy)', 'y': 'Stock'},
            color_continuous_scale='RdYlGn'
        )

        fig.update_layout(height=400)
        return fig
    except:
        # Fallback simple chart
        return create_simple_confidence_chart(predictions)

def create_confidence_distribution(predictions: pd.DataFrame) -> go.Figure:
    """Create confidence distribution chart"""
    fig = px.histogram(
        predictions,
        x='ensemble_confidence',
        nbins=20,
        title="Model Confidence Distribution",
        labels={'ensemble_confidence': 'Confidence Level', 'count': 'Number of Predictions'},
        color_discrete_sequence=['#1f77b4']
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def create_risk_return_scatter(predictions: pd.DataFrame) -> go.Figure:
    """Create risk vs return scatter plot"""
    fig = px.scatter(
        predictions,
        x='risk_score',
        y='success_prob',
        size='ensemble_confidence',
        color='predicted_return',
        hover_data=['ticker'],
        title="Risk vs Expected Return Analysis",
        labels={
            'risk_score': 'Risk Score',
            'success_prob': 'Expected Success Rate',
            'predicted_return': 'Prediction'
        },
        color_discrete_map={0: '#ff7f0e', 1: '#2ca02c'}
    )

    fig.update_layout(height=400)
    return fig

def create_sentiment_gauge(predictions: pd.DataFrame) -> go.Figure:
    """Create market sentiment gauge"""
    if predictions.empty:
        bullish_pct = 50
    else:
        bullish_count = len(predictions[predictions['predicted_return'] == 1])
        bullish_pct = (bullish_count / len(predictions)) * 100

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=bullish_pct,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Market Sentiment (% Bullish)"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "lightgray"},
                {'range': [25, 50], 'color': "gray"},
                {'range': [50, 75], 'color': "lightgreen"},
                {'range': [75, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))

    fig.update_layout(height=400)
    return fig

def create_technical_analysis_chart(stock_data: pd.DataFrame, symbol: str) -> go.Figure:
    """Create comprehensive technical analysis chart"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('Price & Moving Averages', 'Volume', 'RSI'),
        row_heights=[0.6, 0.2, 0.2]
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=stock_data.index,
            open=stock_data['Open'],
            high=stock_data['High'],
            low=stock_data['Low'],
            close=stock_data['Close'],
            name="OHLC"
        ),
        row=1, col=1
    )

    # Moving averages
    if len(stock_data) > 20:
        ma_20 = stock_data['Close'].rolling(20).mean()
        ma_50 = stock_data['Close'].rolling(50).mean() if len(stock_data) > 50 else None

        fig.add_trace(
            go.Scatter(x=stock_data.index, y=ma_20, name="MA20", line={'color': 'orange'}),
            row=1, col=1
        )

        if ma_50 is not None:
            fig.add_trace(
                go.Scatter(x=stock_data.index, y=ma_50, name="MA50", line={'color': 'blue'}),
                row=1, col=1
            )

    # Volume
    fig.add_trace(
        go.Bar(x=stock_data.index, y=stock_data['Volume'], name="Volume", marker_color='lightblue'),
        row=2, col=1
    )

    # RSI (simplified calculation)
    if len(stock_data) > 14:
        delta = stock_data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        fig.add_trace(
            go.Scatter(x=stock_data.index, y=rsi, name="RSI", line={'color': 'purple'}),
            row=3, col=1
        )

        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(
        title=f"{symbol} - Technical Analysis",
        height=600,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )

    return fig

def create_volume_analysis_chart(stock_data: pd.DataFrame) -> go.Figure:
    """Create volume analysis chart"""
    volume_ma = stock_data['Volume'].rolling(20).mean()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=stock_data.index,
        y=stock_data['Volume'],
        name="Volume",
        marker_color='lightblue'
    ))

    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=volume_ma,
        name="Volume MA20",
        line={'color': 'red'}
    ))

    fig.update_layout(
        title="Volume Analysis",
        height=300,
        showlegend=True
    )

    return fig

def create_volatility_chart(stock_data: pd.DataFrame) -> go.Figure:
    """Create volatility analysis chart"""
    returns = stock_data['Close'].pct_change().dropna()
    rolling_vol = returns.rolling(20).std() * np.sqrt(252) * 100  # Annualized %

    fig = px.line(
        x=rolling_vol.index,
        y=rolling_vol.values,
        title="20-Day Rolling Volatility (%)",
        labels={'x': 'Date', 'y': 'Volatility (%)'}
    )

    fig.update_layout(height=300)
    return fig

def create_portfolio_composition_chart(predictions: pd.DataFrame) -> go.Figure:
    """Create portfolio composition pie chart"""
    if 'weight' in predictions.columns:
        # Use actual weights if available
        composition_data = predictions.nlargest(10, 'weight')
        values = composition_data['weight']
        names = composition_data['ticker']
    else:
        # Use success probability as proxy
        composition_data = predictions.nlargest(10, 'success_prob')
        values = composition_data['success_prob']
        names = composition_data['ticker']

    fig = px.pie(
        values=values,
        names=names,
        title="Top 10 Portfolio Holdings"
    )

    fig.update_layout(height=400)
    return fig

def create_risk_distribution_chart(predictions: pd.DataFrame) -> go.Figure:
    """Create risk distribution chart"""
    fig = px.histogram(
        predictions,
        x='risk_score',
        nbins=15,
        title="Risk Score Distribution",
        labels={'risk_score': 'Risk Score', 'count': 'Number of Stocks'},
        color_discrete_sequence=['#d62728']
    )

    fig.update_layout(height=350)
    return fig

def create_simple_confidence_chart(predictions: pd.DataFrame) -> go.Figure:
    """Create simple confidence chart as fallback"""
    avg_confidence = predictions.groupby('ticker')['ensemble_confidence'].mean().reset_index()

    fig = px.bar(
        avg_confidence,
        x='ticker',
        y='ensemble_confidence',
        title="Average Confidence by Stock"
    )

    fig.update_layout(height=400)
    return fig

def create_correlation_heatmap(predictions: pd.DataFrame) -> go.Figure:
    """Create correlation heatmap"""
    # Simple version using available numerical columns
    numeric_cols = ['success_prob', 'ensemble_confidence', 'risk_score']
    available_cols = [col for col in numeric_cols if col in predictions.columns]

    if len(available_cols) < 2:
        # Fallback chart
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data for correlation analysis", 
                          xref="paper", yref="paper", x=0.5, y=0.5)
        fig.update_layout(title="Correlation Analysis", height=300)
        return fig

    corr_matrix = predictions[available_cols].corr()

    fig = px.imshow(
        corr_matrix,
        title="Feature Correlation Matrix",
        color_continuous_scale='RdBu_r'
    )

    fig.update_layout(height=300)
    return fig

# ==================== ADDITIONAL CHART FUNCTIONS ====================

def create_sector_allocation_chart(sector_data: Dict) -> go.Figure:
    """Create sector allocation chart"""
    fig = px.pie(
        values=list(sector_data.values()),
        names=list(sector_data.keys()),
        title="Sector Allocation"
    )

    fig.update_layout(height=400)
    return fig

def create_portfolio_performance_chart(portfolio_data: Dict) -> go.Figure:
    """Create portfolio performance chart"""
    # Mock data for demonstration
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    performance = np.cumsum(np.random.normal(0.001, 0.02, len(dates))) + 1

    fig = px.line(
        x=dates,
        y=performance,
        title="Portfolio Performance (30 Days)",
        labels={'x': 'Date', 'y': 'Cumulative Return'}
    )

    fig.update_layout(height=400)
    return fig

def create_var_analysis_chart(predictions: pd.DataFrame) -> go.Figure:
    """Create VaR analysis chart"""
    # Simplified VaR calculation
    if 'expected_return' in predictions.columns:
        returns = predictions['expected_return']
    else:
        returns = (predictions['success_prob'] - 0.5) * 0.2  # Proxy returns

    var_95 = np.percentile(returns, 5)
    var_99 = np.percentile(returns, 1)

    fig = px.histogram(
        returns,
        nbins=20,
        title=f"Value at Risk Analysis (VaR 95%: {var_95:.2%}, VaR 99%: {var_99:.2%})"
    )

    fig.add_vline(x=var_95, line_dash="dash", line_color="orange", annotation_text="VaR 95%")
    fig.add_vline(x=var_99, line_dash="dash", line_color="red", annotation_text="VaR 99%")

    fig.update_layout(height=300)
    return fig

def create_risk_adjusted_returns_chart(predictions: pd.DataFrame) -> go.Figure:
    """Create risk-adjusted returns chart"""
    # Calculate Sharpe ratio proxy
    expected_returns = predictions['success_prob'] - 0.5
    risk_adjusted = expected_returns / (predictions['risk_score'] + 0.01)

    fig = px.scatter(
        x=predictions['risk_score'],
        y=risk_adjusted,
        color=predictions['predicted_return'],
        title="Risk-Adjusted Returns (Sharpe Ratio Proxy)",
        labels={'x': 'Risk Score', 'y': 'Risk-Adjusted Return'},
        color_discrete_map={0: '#ff7f0e', 1: '#2ca02c'}
    )

    fig.update_layout(height=300)
    return fig

def create_monte_carlo_chart(predictions: pd.DataFrame) -> go.Figure:
    """Create Monte Carlo simulation chart"""
    # Simplified Monte Carlo
    n_simulations = 1000
    time_steps = 30

    # Use average risk and return from predictions
    avg_return = predictions['success_prob'].mean() - 0.5
    avg_risk = predictions['risk_score'].mean()

    # Generate random paths
    paths = []
    for _ in range(min(n_simulations, 100)):  # Limit for performance
        random_returns = np.random.normal(avg_return * 0.01, avg_risk * 0.02, time_steps)
        path = np.cumsum(random_returns) + 1
        paths.append(path)

    fig = go.Figure()

    for i, path in enumerate(paths):
        fig.add_trace(go.Scatter(
            y=path,
            mode='lines',
            line={'width': 1, 'color': 'rgba(0,100,80,0.1)'},
            showlegend=False
        ))

    fig.update_layout(
        title="Monte Carlo Simulation (100 paths)",
        height=300,
        xaxis_title="Days",
        yaxis_title="Cumulative Return"
    )

    return fig

# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    st.title("Advanced Charts Test")

    # Generate sample data
    sample_data = {
        'predictions': pd.DataFrame({
            'ticker': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS'] * 10,
            'predicted_return': np.random.choice([0, 1], 30),
            'success_prob': np.random.beta(2, 2, 30),
            'ensemble_confidence': np.random.beta(3, 2, 30),
            'risk_score': np.random.beta(2, 3, 30),
            'models_used': np.random.choice([3, 4, 5], 30)
        })
    }

    display_advanced_charts(sample_data)
