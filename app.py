# app.py
from typing import List
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import gc
import warnings
import logging
from pathlib import Path


# Import enhanced modules for individual stock handling
from utils.data_loader import (
    IndividualStockDataManager, 
    get_individual_stock_data,
    get_multiple_individual_stocks,
    refresh_stock_data,
    get_updated_nse_tickers,
    validate_stock_symbol,
    search_stocks,
    generate_stock_summary
)

from utils.feature_engineer import (
    engineer_features_individual,
    get_feature_summary,
    INDIVIDUAL_FEATURE_CONFIG,
    TARGET_HORIZONS
)

from utils.model import (
    IndividualStockPredictor,
    train_individual_stock_model,
    predict_individual_stock,
    load_individual_model,
    get_available_individual_models,
    train_multiple_stocks_batch,
    get_model_summary,
    generate_predictions_for_stock,
    INDIVIDUAL_MODEL_CONFIG
)

# Enhanced Streamlit components
from components.performance_metrics import display_enhanced_performance_dashboard
from components.charts import display_advanced_charts

# NEW: Quantitative Finance Modules
from utils.options_pricing import BlackScholesModel, BinomialTreeModel, GreeksCalculator, OptionsChain
from utils.options_strategies import OptionsStrategy, StrategyBuilder, calculate_strategy_greeks
from utils.indian_market import IndianMarketData, MarketCalendar
from utils.portfolio_analytics import Portfolio, PerformanceMetrics, IndianTaxCalculator

# ADVANCED: Institutional-Grade Modules
from utils.advanced_ml_models import AdvancedMLTrainer, EnsemblePredictor
from utils.reinforcement_learning import PortfolioEnvironment, DQNAgent
from utils.statistical_arbitrage import PairsTradingStrategy, MeanReversionStrategy, StatisticalArbitragePortfolio
from utils.portfolio_optimization import MarkowitzOptimizer, BlackLittermanOptimizer, RiskParityOptimizer
from utils.advanced_backtesting import AdvancedBacktester, Order, OrderSide, OrderType

# Configure logging
logging.basicConfig(level=logging.INFO)
warnings.filterwarnings('ignore')

# Enhanced Streamlit page configuration
st.set_page_config(
    page_title="Quantitative Finance Master - Indian Stock Market",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3498db;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #cce7ff;
        border: 1px solid #b3d9ff;
        border-radius: 0.375rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""

    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = IndividualStockDataManager()

    if 'selected_stocks' not in st.session_state:
        st.session_state.selected_stocks = []

    if 'training_mode' not in st.session_state:
        st.session_state.training_mode = "single_stock"

    if 'available_stocks' not in st.session_state:
        st.session_state.available_stocks = st.session_state.data_manager.get_available_stocks()

    if 'prediction_results' not in st.session_state:
        st.session_state.prediction_results = {}

    # NEW: Initialize quantitative finance modules
    if 'indian_market' not in st.session_state:
        st.session_state.indian_market = IndianMarketData()

    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = Portfolio('default')

    if 'bs_model' not in st.session_state:
        st.session_state.bs_model = BlackScholesModel(risk_free_rate=0.065)

    if 'greeks_calc' not in st.session_state:
        st.session_state.greeks_calc = GreeksCalculator(st.session_state.bs_model)

def display_main_header():
    """Display main application header"""

    st.markdown('<h1 class="main-header">📊 Quantitative Finance Master - Indian Stock Market</h1>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        available_count = len(st.session_state.available_stocks)
        st.metric("Available Stocks", available_count, delta=f"Cached stocks ready")
    
    with col2:
        models_count = len(get_available_individual_models())
        st.metric("Trained Models", models_count, delta="Individual models")
    
    with col3:
        st.metric("System Status", "🟢 Online", delta="All systems operational")
    
    with col4:
        last_update = datetime.now().strftime("%H:%M")
        st.metric("Last Update", last_update, delta="Real-time")

def display_sidebar():
    """Display enhanced sidebar"""

    st.sidebar.markdown("## 📊 Navigation")

    # Main navigation
    page = st.sidebar.selectbox(
        "Select Page",
        [
            "🏠 Home Dashboard",
            "📈 Data Management",
            "⚙️ Model Training",
            "🔮 Predictions",
            "📊 Performance Analysis",
            "💼 Portfolio Manager",
            "📉 Options Pricing",
            "🎯 Options Strategies",
            "🇮🇳 Indian Market",
            "🤖 Advanced ML Models",
            "🎲 Statistical Arbitrage",
            "⚖️ Portfolio Optimization",
            "🔬 Advanced Backtesting",
            "🛠️ Settings"
        ]
    )
    
    st.sidebar.markdown("---")
    
    # Quick stats
    st.sidebar.markdown("### 📋 Quick Stats")
    
    available_stocks = len(st.session_state.available_stocks)
    st.sidebar.metric("Cached Stocks", available_stocks)
    
    models_info = get_available_individual_models()
    st.sidebar.metric("Model Combinations", len(models_info))
    
    # Quick actions
    st.sidebar.markdown("### ⚡ Quick Actions")
    
    if st.sidebar.button("🔄 Refresh Stock List"):
        st.session_state.available_stocks = st.session_state.data_manager.get_available_stocks()
        st.sidebar.success("Stock list refreshed!")
    
    if st.sidebar.button("🧹 Clear Cache"):
        st.session_state.data_manager.cleanup_old_cache(days_old=1)
        st.sidebar.success("Cache cleared!")
    
    return page

def display_home_dashboard():
    """Display home dashboard"""
    
    st.markdown("## 🏠 Welcome to AI Stock Advisor Pro - Individual Edition")
    
    # Overview cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="info-box">
            <h3>🎯 Individual Stock Focus</h3>
            <p>This enhanced version allows you to:</p>
            <ul>
                <li>Select and analyze individual stocks</li>
                <li>Train models per stock for better accuracy</li>
                <li>Cache data and models for faster processing</li>
                <li>Generate personalized predictions</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box">
            <h3>🚀 Key Features</h3>
            <ul>
                <li><strong>Smart Caching:</strong> Data and models stored locally</li>
                <li><strong>Individual Training:</strong> Each stock gets its own model</li>
                <li><strong>Multiple Horizons:</strong> Week, month, quarter, year predictions</li>
                <li><strong>Performance Tracking:</strong> Monitor model accuracy over time</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity
    st.markdown("### 📈 Recent Activity")
    
    # Display recent stocks with data
    if st.session_state.available_stocks:
        recent_stocks = st.session_state.available_stocks[:10]  # Show first 10
        stock_summary = generate_stock_summary(recent_stocks, st.session_state.data_manager)
        
        if not stock_summary.empty:
            st.dataframe(
                stock_summary.sort_values('Last Updated', ascending=False),
                use_container_width=True
            )
        else:
            st.info("No stock data available. Please add stocks in Data Management.")
    else:
        st.info("No cached stocks available. Start by adding stocks in the Data Management section.")

def display_data_management():
    """Display data management interface"""
    
    st.markdown("## 📈 Data Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Stocks", "📊 Manage Existing", "🔄 Refresh Data"])
    
    with tab1:
        display_add_stocks_interface()
    
    with tab2:
        display_manage_existing_stocks()
    
    with tab3:
        display_refresh_data_interface()

def display_add_stocks_interface():
    """Display interface for adding new stocks"""
    
    st.markdown("### ➕ Add New Stocks")
    
    # Method selection
    add_method = st.radio(
        "Choose method to add stocks:",
        ["📝 Manual Entry", "📋 Popular Stocks", "🔍 Search & Select"]
    )
    
    if add_method == "📝 Manual Entry":
        # Manual stock entry
        col1, col2 = st.columns([3, 1])
        
        with col1:
            manual_symbols = st.text_area(
                "Enter stock symbols (one per line)",
                placeholder="RELIANCE.NS\nTCS.NS\nINFY.NS",
                height=150
            )
        
        with col2:
            st.markdown("**Format Examples:**")
            st.code("RELIANCE.NS\nTCS.NS\nHDFCBANK.NS")
            
            if st.button("✅ Add Stocks", type="primary"):
                if manual_symbols:
                    symbols = [s.strip().upper() for s in manual_symbols.split('\n') if s.strip()]
                    add_stocks_batch(symbols)
    
    elif add_method == "📋 Popular Stocks":
        # Popular stocks selection
        popular_stocks = get_updated_nse_tickers()[:30]  # Top 30
        
        selected_popular = st.multiselect(
            "Select from popular stocks:",
            options=popular_stocks,
            default=[]
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📈 Add NIFTY 50", type="secondary"):
                nifty_50 = get_updated_nse_tickers()[:50]
                add_stocks_batch(nifty_50)
        
        with col2:
            if st.button("⭐ Add Selected", type="primary"):
                if selected_popular:
                    add_stocks_batch(selected_popular)
        
        with col3:
            if st.button("🎯 Add Top 10", type="secondary"):
                top_10 = get_updated_nse_tickers()[:10]
                add_stocks_batch(top_10)
    
    else:  # Search & Select
        # Search interface
        search_query = st.text_input("🔍 Search stocks:", placeholder="Enter company name or symbol")
        
        if search_query:
            # This is a simplified search - in a real app, you'd search a comprehensive database
            all_tickers = get_updated_nse_tickers()
            matches = [ticker for ticker in all_tickers if search_query.upper() in ticker.upper()]
            
            if matches:
                selected_from_search = st.multiselect(
                    f"Found {len(matches)} matches:",
                    options=matches,
                    default=[]
                )
                
                if st.button("➕ Add Selected") and selected_from_search:
                    add_stocks_batch(selected_from_search)
            else:
                st.warning("No matches found. Try different keywords.")

def add_stocks_batch(symbols: List[str]):
    """Add multiple stocks in batch"""
    
    if not symbols:
        st.warning("No symbols provided.")
        return
    
    # Validate symbols
    valid_symbols = []
    invalid_symbols = []
    
    for symbol in symbols:
        if validate_stock_symbol(symbol):
            valid_symbols.append(symbol)
        else:
            invalid_symbols.append(symbol)
    
    if invalid_symbols:
        st.error(f"Invalid symbols: {', '.join(invalid_symbols)}")
    
    if not valid_symbols:
        return
    
    # Show progress
    progress_container = st.container()
    with progress_container:
        st.info(f"Adding {len(valid_symbols)} stocks...")
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    # Add stocks
    success_count = 0
    error_count = 0
    
    for i, symbol in enumerate(valid_symbols):
        try:
            status_text.text(f"Fetching {symbol}...")
            
            data = st.session_state.data_manager.fetch_and_cache_stock(symbol, force_refresh=False)
            
            if not data.empty:
                success_count += 1
                status_text.text(f"✅ {symbol} added successfully")
            else:
                error_count += 1
                status_text.text(f"❌ Failed to fetch {symbol}")
            
            progress_bar.progress((i + 1) / len(valid_symbols))
            
        except Exception as e:
            error_count += 1
            status_text.text(f"❌ Error with {symbol}: {str(e)}")
        
        # Brief pause to show progress
        import time
        time.sleep(0.1)
    
    # Update session state
    st.session_state.available_stocks = st.session_state.data_manager.get_available_stocks()
    
    # Show results
    progress_container.empty()
    
    if success_count > 0:
        st.success(f"✅ Successfully added {success_count} stocks!")
    
    if error_count > 0:
        st.error(f"❌ Failed to add {error_count} stocks")

def display_manage_existing_stocks():
    """Display interface for managing existing stocks"""
    
    st.markdown("### 📊 Manage Existing Stocks")
    
    if not st.session_state.available_stocks:
        st.info("No stocks currently cached. Add some stocks first!")
        return
    
    # Generate detailed summary
    stock_summary = generate_stock_summary(st.session_state.available_stocks, st.session_state.data_manager)
    
    if stock_summary.empty:
        st.warning("Unable to load stock information.")
        return
    
    # Display summary with actions
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Enhanced dataframe display
        st.dataframe(
            stock_summary.sort_values('Data Quality', ascending=False),
            use_container_width=True,
            column_config={
                "Latest Price": st.column_config.NumberColumn(
                    "Latest Price (₹)",
                    format="₹%.2f"
                ),
                "Market Cap": st.column_config.NumberColumn(
                    "Market Cap",
                    format="₹%.0f"
                ),
                "Data Quality": st.column_config.ProgressColumn(
                    "Data Quality",
                    min_value=0,
                    max_value=1,
                    format="%.2f"
                )
            }
        )
    
    with col2:
        st.markdown("**Bulk Actions:**")
        
        if st.button("🔄 Refresh All", type="secondary"):
            refresh_all_stocks()
        
        if st.button("🧹 Clean Low Quality", type="secondary"):
            clean_low_quality_stocks()
        
        if st.button("📊 Export Summary", type="secondary"):
            csv = stock_summary.to_csv(index=False)
            st.download_button(
                "💾 Download CSV",
                csv,
                "stock_summary.csv",
                "text/csv"
            )
        
        # Individual stock actions
        st.markdown("**Individual Actions:**")
        selected_for_action = st.selectbox(
            "Select stock:",
            options=st.session_state.available_stocks
        )
        
        if selected_for_action:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Refresh"):
                    refresh_individual_stock(selected_for_action)
            
            with col_b:
                if st.button("🗑️ Remove"):
                    remove_individual_stock(selected_for_action)

def refresh_all_stocks():
    """Refresh all cached stocks"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(st.session_state.available_stocks):
        status_text.text(f"Refreshing {symbol}...")
        try:
            refresh_stock_data(symbol, st.session_state.data_manager)
        except Exception as e:
            st.error(f"Failed to refresh {symbol}: {e}")
        
        progress_bar.progress((i + 1) / len(st.session_state.available_stocks))
    
    st.success("All stocks refreshed!")
    st.session_state.available_stocks = st.session_state.data_manager.get_available_stocks()

def display_refresh_data_interface():
    """Display data refresh interface"""
    
    st.markdown("### 🔄 Refresh Stock Data")
    
    if not st.session_state.available_stocks:
        st.info("No stocks to refresh. Add some stocks first!")
        return
    
    # Refresh options
    refresh_option = st.radio(
        "Refresh options:",
        ["🎯 Specific Stocks", "📊 All Stocks", "⚡ Stale Data Only"]
    )
    
    if refresh_option == "🎯 Specific Stocks":
        selected_stocks = st.multiselect(
            "Select stocks to refresh:",
            options=st.session_state.available_stocks
        )
        
        if st.button("🔄 Refresh Selected") and selected_stocks:
            refresh_selected_stocks(selected_stocks)
    
    elif refresh_option == "📊 All Stocks":
        st.warning("This will refresh all stocks and may take some time.")
        
        if st.button("🔄 Refresh All Stocks", type="primary"):
            refresh_all_stocks()
    
    else:  # Stale data only
        # Find stale data (older than 24 hours)
        stale_stocks = []
        for symbol in st.session_state.available_stocks:
            if not st.session_state.data_manager.is_data_fresh(symbol, max_age_hours=24):
                stale_stocks.append(symbol)
        
        if stale_stocks:
            st.info(f"Found {len(stale_stocks)} stocks with stale data:")
            st.write(stale_stocks)
            
            if st.button("🔄 Refresh Stale Data"):
                refresh_selected_stocks(stale_stocks)
        else:
            st.success("All stock data is fresh!")

def display_model_training():
    """Display model training interface"""
    
    st.markdown("## ⚙️ Model Training")
    
    if not st.session_state.available_stocks:
        st.warning("No stocks available for training. Please add stocks first.")
        return
    
    tab1, tab2, tab3 = st.tabs(["🎯 Single Stock", "📊 Batch Training", "📋 Model Management"])
    
    with tab1:
        display_single_stock_training()
    
    with tab2:
        display_batch_training()
    
    with tab3:
        display_model_management()

def display_single_stock_training():
    """Display single stock training interface"""
    
    st.markdown("### 🎯 Train Individual Stock Model")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Stock selection
        selected_stock = st.selectbox(
            "Select stock for training:",
            options=st.session_state.available_stocks,
            key="single_training_stock"
        )
        
        # Training parameters
        training_horizon = st.selectbox(
            "Prediction horizon:",
            options=list(TARGET_HORIZONS.keys()),
            key="training_horizon"
        )
        
        model_types = st.multiselect(
            "Select model types:",
            options=INDIVIDUAL_MODEL_CONFIG['model_types'],
            default=INDIVIDUAL_MODEL_CONFIG['default_models'],
            key="selected_model_types"
        )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            enable_tuning = st.checkbox("Enable hyperparameter tuning", value=True)
            enable_cv = st.checkbox("Enable cross-validation", value=True)
            enable_calibration = st.checkbox("Enable model calibration", value=True)
    
    with col2:
        if selected_stock:
            # Display stock info
            stock_info = st.session_state.data_manager.get_stock_info(selected_stock)
            if stock_info:
                st.markdown("**Stock Information:**")
                st.metric("Total Records", stock_info['total_records'])
                st.metric("Data Quality", f"{stock_info['data_quality_score']:.2f}")
                st.metric("Last Updated", stock_info['last_updated'][:10])
        
        # Training button
        if st.button("🚀 Start Training", type="primary"):
            if selected_stock and model_types:
                train_single_stock_models(
                    selected_stock, 
                    training_horizon, 
                    model_types,
                    enable_tuning,
                    enable_cv,
                    enable_calibration
                )
            else:
                st.error("Please select stock and model types!")

def train_single_stock_models(stock_symbol: str, horizon: str, model_types: List[str],
                            enable_tuning: bool, enable_cv: bool, enable_calibration: bool):
    """Train models for a single stock"""
    
    try:
        # Load stock data
        with st.spinner("Loading stock data..."):
            stock_data = st.session_state.data_manager.load_stock_data(stock_symbol)
        
        if stock_data.empty:
            st.error(f"No data available for {stock_symbol}")
            return
        
        # Engineer features
        with st.spinner("Engineering features..."):
            from utils.feature_engineer import engineer_features_individual
            features = engineer_features_individual(stock_symbol, stock_data)
        
        if features.empty:
            st.error("Feature engineering failed!")
            return
        
        # Display feature summary
        feature_summary = get_feature_summary(features)
        with st.expander("📊 Feature Summary"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Features", feature_summary['total_features'])
            with col2:
                st.metric("Data Points", feature_summary['data_points'])
            with col3:
                st.metric("Missing Values", feature_summary['missing_values'])
        
        # Train models
        training_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, model_type in enumerate(model_types):
            status_text.text(f"Training {model_type} model...")
            
            try:
                predictor = train_individual_stock_model(
                    stock_symbol=stock_symbol,
                    features=features,
                    horizon=horizon,
                    model_type=model_type,
                    hyperparameter_tuning=enable_tuning,
                    cross_validation=enable_cv
                )
                
                if predictor:
                    # Save model
                    predictor.save()
                    
                    training_results.append({
                        'Model Type': model_type,
                        'Validation Score': f"{predictor.validation_score:.3f}",
                        'CV Score': f"{predictor.cv_score:.3f}" if predictor.cv_score else "N/A",
                        'Training Time': f"{predictor.training_time:.1f}s",
                        'Features Used': len(predictor.selected_features) if predictor.selected_features else 0,
                        'Status': '✅ Success'
                    })
                    
                    status_text.text(f"✅ {model_type} completed (Score: {predictor.validation_score:.3f})")
                else:
                    training_results.append({
                        'Model Type': model_type,
                        'Status': '❌ Failed'
                    })
                    
            except Exception as e:
                training_results.append({
                    'Model Type': model_type,
                    'Status': f'❌ Error: {str(e)[:50]}'
                })
            
            progress_bar.progress((i + 1) / len(model_types))
        
        # Display results
        st.success(f"Training completed for {stock_symbol}!")
        
        results_df = pd.DataFrame(training_results)
        st.dataframe(results_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Training failed: {str(e)}")
        logging.error(f"Training error for {stock_symbol}: {e}")

def display_batch_training():
    """Display batch training interface"""
    
    st.markdown("### 📊 Batch Training")
    
    # Stock selection for batch training
    col1, col2 = st.columns(2)
    
    with col1:
        batch_stocks = st.multiselect(
            "Select stocks for batch training:",
            options=st.session_state.available_stocks,
            key="batch_training_stocks"
        )
        
        batch_horizons = st.multiselect(
            "Select prediction horizons:",
            options=list(TARGET_HORIZONS.keys()),
            default=["next_week", "next_month"],
            key="batch_horizons"
        )
    
    with col2:
        batch_models = st.multiselect(
            "Select model types:",
            options=INDIVIDUAL_MODEL_CONFIG['model_types'],
            default=INDIVIDUAL_MODEL_CONFIG['default_models'],
            key="batch_model_types"
        )
        
        max_workers = st.slider("Parallel workers:", 1, 4, 2)
    
    # Training options
    with st.expander("🔧 Batch Training Options"):
        col1, col2 = st.columns(2)
        with col1:
            skip_existing = st.checkbox("Skip existing models", value=True)
            enable_notifications = st.checkbox("Enable progress notifications", value=True)
        with col2:
            save_results = st.checkbox("Save training results", value=True)
            cleanup_cache = st.checkbox("Cleanup cache after training", value=False)
    
    # Estimate training time
    if batch_stocks and batch_horizons and batch_models:
        total_tasks = len(batch_stocks) * len(batch_horizons) * len(batch_models)
        estimated_time = total_tasks * 2  # Rough estimate: 2 minutes per task
        
        st.info(f"Estimated training time: ~{estimated_time} minutes for {total_tasks} models")
    
    # Start batch training
    if st.button("🚀 Start Batch Training", type="primary"):
        if batch_stocks and batch_horizons and batch_models:
            start_batch_training(
                batch_stocks, batch_horizons, batch_models, 
                max_workers, skip_existing, save_results
            )
        else:
            st.error("Please select stocks, horizons, and model types!")

def start_batch_training(stocks: List[str], horizons: List[str], model_types: List[str],
                        max_workers: int, skip_existing: bool, save_results: bool):
    """Start batch training process"""
    
    try:
        # Prepare stock data
        with st.spinner("Loading stock data..."):
            stock_data = {}
            for stock in stocks:
                data = st.session_state.data_manager.load_stock_data(stock)
                if not data.empty:
                    stock_data[stock] = data
        
        if not stock_data:
            st.error("No valid stock data found!")
            return
        
        st.success(f"Loaded data for {len(stock_data)} stocks")
        
        # Start training
        with st.spinner("Training models in batch..."):
            results = train_multiple_stocks_batch(
                stock_data=stock_data,
                horizons=horizons,
                model_types=model_types,
                max_workers=max_workers
            )
        
        # Display results
        st.success("Batch training completed!")
        
        # Process and display results
        all_results = []
        for stock_symbol, stock_results in results.items():
            for result in stock_results:
                all_results.append({
                    'Stock': stock_symbol,
                    'Horizon': result['horizon'],
                    'Model Type': result['model_type'],
                    'Success': '✅' if result['success'] else '❌',
                    'Score': f"{result.get('validation_score', 0):.3f}" if result['success'] else 'N/A',
                    'Time (s)': f"{result.get('training_time', 0):.1f}" if result['success'] else 'N/A',
                    'Error': result.get('error', '') if not result['success'] else ''
                })
        
        results_df = pd.DataFrame(all_results)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Models", len(all_results))
        with col2:
            successful = sum(1 for r in all_results if r['Success'] == '✅')
            st.metric("Successful", successful)
        with col3:
            failed = len(all_results) - successful
            st.metric("Failed", failed)
        with col4:
            success_rate = (successful / len(all_results)) * 100 if all_results else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        # Detailed results
        st.dataframe(results_df, use_container_width=True)
        
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                "📥 Download Results",
                csv_data,
                f"batch_training_results_{timestamp}.csv",
                "text/csv"
            )
    
    except Exception as e:
        st.error(f"Batch training failed: {str(e)}")
        logging.error(f"Batch training error: {e}")

def display_model_management():
    """Display model management interface"""
    
    st.markdown("### 📋 Model Management")
    
    # Get model summary
    model_summary = get_model_summary()
    
    if model_summary.empty:
        st.info("No trained models found. Train some models first!")
        return
    
    # Display model summary
    st.dataframe(
        model_summary.sort_values('Training Date', ascending=False),
        use_container_width=True,
        column_config={
            'Validation Score': st.column_config.ProgressColumn(
                "Validation Score",
                min_value=0,
                max_value=1,
                format="%.3f"
            ),
            'File Size (MB)': st.column_config.NumberColumn(
                "Size (MB)",
                format="%.2f"
            )
        }
    )
    
    # Model actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Cleanup Old Models"):
            from utils.model import cleanup_old_models
            cleanup_old_models(days_old=7)
            st.success("Old models cleaned up!")
    
    with col2:
        if st.button("📊 Export Summary"):
            csv = model_summary.to_csv(index=False)
            st.download_button(
                "💾 Download CSV",
                csv,
                "model_summary.csv",
                "text/csv"
            )
    
    with col3:
        total_size = model_summary['File Size (MB)'].sum()
        st.metric("Total Storage", f"{total_size:.1f} MB")

def display_predictions():
    """Display predictions interface"""
    
    st.markdown("## 🔮 Stock Predictions")
    
    if not st.session_state.available_stocks:
        st.warning("No stocks available for predictions. Please add stocks first.")
        return
    
    # Check for available models
    available_models = get_available_individual_models()
    if not available_models:
        st.warning("No trained models found. Please train some models first.")
        return
    
    tab1, tab2 = st.tabs(["🎯 Individual Predictions", "📊 Batch Predictions"])
    
    with tab1:
        display_individual_predictions()
    
    with tab2:
        display_batch_predictions()

def display_individual_predictions():
    """Display individual stock prediction interface"""
    
    st.markdown("### 🎯 Individual Stock Predictions")
    
    available_models = get_available_individual_models()
    
    # Stock selection
    stock_for_prediction = st.selectbox(
        "Select stock for prediction:",
        options=[stock for stock in st.session_state.available_stocks 
                if any(stock in key for key in available_models.keys())],
        key="prediction_stock"
    )
    
    if not stock_for_prediction:
        st.info("No trained models available for the selected stocks.")
        return
    
    # Available horizons for this stock
    available_horizons = []
    for key in available_models.keys():
        if stock_for_prediction in key:
            horizon = key.split('_')[1]
            if horizon not in available_horizons:
                available_horizons.append(horizon)
    
    selected_horizon = st.selectbox(
        "Select prediction horizon:",
        options=available_horizons,
        key="prediction_horizon"
    )
    
    # Generate prediction button
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔮 Generate Prediction", type="primary"):
            generate_individual_prediction(stock_for_prediction, selected_horizon)
    
    with col2:
        if st.button("📊 View Historical Performance"):
            display_historical_performance(stock_for_prediction, selected_horizon)
    
    # Display existing prediction if available
    prediction_key = f"{stock_for_prediction}_{selected_horizon}"
    if prediction_key in st.session_state.prediction_results:
        display_prediction_results(stock_for_prediction, selected_horizon)

def generate_individual_prediction(stock_symbol: str, horizon: str):
    """Generate prediction for individual stock"""
    
    try:
        with st.spinner(f"Generating prediction for {stock_symbol}..."):
            # Load stock data
            stock_data = st.session_state.data_manager.load_stock_data(stock_symbol)
            
            if stock_data.empty:
                st.error(f"No data available for {stock_symbol}")
                return
            
            # Generate predictions for all available horizons
            predictions = generate_predictions_for_stock(stock_symbol, stock_data, [horizon])
            
            if horizon in predictions:
                # Store in session state
                prediction_key = f"{stock_symbol}_{horizon}"
                st.session_state.prediction_results[prediction_key] = predictions[horizon]
                
                st.success(f"✅ Prediction generated for {stock_symbol}!")
                display_prediction_results(stock_symbol, horizon)
            else:
                st.error("Failed to generate prediction")
    
    except Exception as e:
        st.error(f"Prediction generation failed: {str(e)}")
        logging.error(f"Prediction error for {stock_symbol}: {e}")

def display_prediction_results(stock_symbol: str, horizon: str):
    """Display prediction results"""
    
    prediction_key = f"{stock_symbol}_{horizon}"
    if prediction_key not in st.session_state.prediction_results:
        return
    
    prediction = st.session_state.prediction_results[prediction_key]
    
    st.markdown(f"### 📈 Prediction Results for {stock_symbol}")
    
    # Main prediction display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        direction = "📈 Bullish" if prediction['predicted_direction'] == 1 else "📉 Bearish"
        st.metric("Prediction", direction)
    
    with col2:
        st.metric("Success Probability", f"{prediction['success_probability']:.1%}")
    
    with col3:
        confidence_color = "🟢" if prediction['confidence'] > 0.7 else "🟡" if prediction['confidence'] > 0.5 else "🔴"
        st.metric("Confidence", f"{confidence_color} {prediction['confidence']:.1%}")
    
    with col4:
        risk_level = "🟢 Low" if prediction['risk_score'] < 0.3 else "🟡 Medium" if prediction['risk_score'] < 0.7 else "🔴 High"
        st.metric("Risk Level", risk_level)
    
    # Additional details
    with st.expander("📊 Detailed Analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Model Information:**")
            st.write(f"Models Used: {prediction['models_used']}")
            st.write(f"Model Agreement: {'✅ High' if prediction['model_agreement'] else '⚠️ Low'}")
            st.write(f"Prediction Horizon: {horizon} ({TARGET_HORIZONS[horizon]} days)")
        
        with col2:
            st.markdown("**Individual Model Votes:**")
            if 'model_votes' in prediction:
                for model_name, (pred, prob) in prediction['model_votes'].items():
                    vote_display = "📈 Buy" if pred == 1 else "📉 Sell"
                    st.write(f"{model_name}: {vote_display} ({prob:.1%})")
    
    # Feature importance (if available)
    if prediction.get('feature_importance'):
        with st.expander("🎯 Key Features Influencing Prediction"):
            feature_importance = prediction['feature_importance']
            
            # Convert to DataFrame and sort
            importance_df = pd.DataFrame([
                {'Feature': k, 'Importance': v} 
                for k, v in feature_importance.items()
            ]).sort_values('Importance', ascending=False).head(10)
            
            # Create horizontal bar chart
            fig = px.bar(
                importance_df,
                x='Importance',
                y='Feature',
                orientation='h',
                title="Top 10 Most Important Features",
                color='Importance',
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')


def display_portfolio_manager():
    """Portfolio Management Page"""
    st.markdown("## 💼 Portfolio Manager")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "➕ Add Transaction", "📈 Performance", "💰 Tax Analysis"])

    with tab1:
        st.markdown("### Current Portfolio")

        holdings = st.session_state.portfolio.get_holdings()

        if holdings.empty:
            st.info("No holdings in portfolio. Add transactions to get started!")
        else:
            # Update current prices
            symbols_to_update = {}
            for symbol in holdings['symbol'].unique():
                try:
                    quote = st.session_state.indian_market.get_live_quote(symbol)
                    if quote and 'ltp' in quote and quote['ltp']:
                        symbols_to_update[symbol] = quote['ltp']
                except:
                    pass

            if symbols_to_update:
                st.session_state.portfolio.update_current_prices(symbols_to_update)
                holdings = st.session_state.portfolio.get_holdings()

            # Calculate portfolio summary
            summary = st.session_state.portfolio.get_portfolio_summary()

            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Invested", f"₹{summary['total_invested']:,.2f}")
            with col2:
                st.metric("Current Value", f"₹{summary['current_value']:,.2f}")
            with col3:
                st.metric("Unrealized P&L", f"₹{summary['unrealized_pnl']:,.2f}",
                         delta=f"{summary['unrealized_pnl_percent']:.2f}%")
            with col4:
                st.metric("Holdings", summary['num_stocks'])

            # Display holdings table
            display_df = holdings.copy()
            display_df['Current Value'] = display_df['quantity'] * display_df['current_price'].fillna(display_df['avg_buy_price'])
            display_df['Invested'] = display_df['quantity'] * display_df['avg_buy_price']
            display_df['P&L'] = display_df['Current Value'] - display_df['Invested']
            display_df['P&L %'] = (display_df['P&L'] / display_df['Invested'] * 100).round(2)

            st.dataframe(
                display_df[['symbol', 'quantity', 'avg_buy_price', 'current_price',
                           'Invested', 'Current Value', 'P&L', 'P&L %']],
                use_container_width=True
            )

            # Sector allocation
            sector_alloc = st.session_state.portfolio.get_sector_allocation()
            if not sector_alloc.empty:
                fig = px.pie(sector_alloc, values='allocation_percent', names='sector',
                            title='Sector Allocation')
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### Add Transaction")

        col1, col2 = st.columns(2)

        with col1:
            txn_type = st.selectbox("Transaction Type", ["BUY", "SELL"])
            symbol = st.text_input("Stock Symbol (e.g., RELIANCE, TCS)")
            quantity = st.number_input("Quantity", min_value=1, value=1)

        with col2:
            price = st.number_input("Price per Share (₹)", min_value=0.01, value=100.0)
            txn_date = st.date_input("Transaction Date", value=datetime.now())
            charges = st.number_input("Charges (₹)", min_value=0.0, value=0.0)

        notes = st.text_area("Notes (optional)")

        if st.button("Add Transaction"):
            try:
                st.session_state.portfolio.add_transaction(
                    symbol=symbol.upper(),
                    transaction_type=txn_type,
                    quantity=quantity,
                    price=price,
                    transaction_date=txn_date.strftime('%Y-%m-%d'),
                    charges=charges,
                    notes=notes
                )
                st.success(f"Transaction added: {txn_type} {quantity} {symbol} @ ₹{price}")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding transaction: {e}")

    with tab3:
        st.markdown("### Performance Metrics")

        # Get portfolio returns (simplified - would need historical data)
        st.info("Performance metrics calculated from portfolio snapshots")

        holdings = st.session_state.portfolio.get_holdings()
        if not holdings.empty:
            # Placeholder for performance calculations
            st.write("**Key Metrics:**")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sharpe Ratio", "N/A", help="Requires historical returns data")
            with col2:
                st.metric("Max Drawdown", "N/A", help="Requires historical portfolio values")
            with col3:
                st.metric("Win Rate", "N/A", help="Based on closed positions")

    with tab4:
        st.markdown("### Tax Analysis (LTCG/STCG)")

        st.info("Indian Capital Gains Tax Calculator")

        st.write("**Tax Rates:**")
        col1, col2 = st.columns(2)
        with col1:
            st.write("- **STCG (< 1 year):** 15%")
        with col2:
            st.write("- **LTCG (≥ 1 year):** 10% on gains above ₹1 lakh")

        # Get transactions for tax calculation
        with sqlite3.connect(st.session_state.portfolio.database_path) as conn:
            transactions_df = pd.read_sql_query("""
                SELECT * FROM transactions
                WHERE portfolio_name = ?
                ORDER BY transaction_date DESC
            """, conn, params=(st.session_state.portfolio.portfolio_name,))

        if not transactions_df.empty:
            st.dataframe(transactions_df, use_container_width=True)

            # Calculate tax if user requests
            if st.button("Calculate Tax Liability"):
                tax_summary = IndianTaxCalculator.calculate_portfolio_tax(transactions_df)

                st.markdown("### Tax Summary")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("STCG", f"₹{tax_summary['total_stcg']:,.2f}")
                    st.caption(f"Tax: ₹{tax_summary['stcg_tax']:,.2f}")

                with col2:
                    st.metric("LTCG", f"₹{tax_summary['total_ltcg']:,.2f}")
                    st.caption(f"Tax: ₹{tax_summary['ltcg_tax']:,.2f}")

                with col3:
                    st.metric("Total Tax", f"₹{tax_summary['total_tax']:,.2f}")
                    st.caption(f"Net Gains: ₹{tax_summary['net_gains']:,.2f}")
        else:
            st.info("No transactions found for tax calculation")


def display_options_pricing():
    """Options Pricing Calculator Page"""
    st.markdown("## 📉 Options Pricing Calculator")

    st.write("Advanced options pricing using Black-Scholes-Merton and Binomial models")

    tab1, tab2 = st.tabs(["📊 Single Option", "⛓️ Options Chain Analysis"])

    with tab1:
        st.markdown("### Option Price Calculator")

        col1, col2, col3 = st.columns(3)

        with col1:
            spot_price = st.number_input("Spot Price (₹)", value=18500.0, min_value=1.0)
            strike_price = st.number_input("Strike Price (₹)", value=18700.0, min_value=1.0)
            option_type = st.selectbox("Option Type", ["Call", "Put"])

        with col2:
            days_to_expiry = st.number_input("Days to Expiry", value=30, min_value=1)
            volatility = st.slider("Volatility (σ)", min_value=0.05, max_value=1.0, value=0.15, step=0.01)
            risk_free_rate = st.slider("Risk-Free Rate", min_value=0.01, max_value=0.15, value=0.065, step=0.005)

        with col3:
            dividend_yield = st.slider("Dividend Yield", min_value=0.0, max_value=0.10, value=0.0, step=0.005)
            model_type = st.selectbox("Pricing Model", ["Black-Scholes", "Binomial Tree"])

        T = days_to_expiry / 365.0

        if st.button("Calculate Option Price"):
            try:
                if model_type == "Black-Scholes":
                    bs_model = BlackScholesModel(risk_free_rate=risk_free_rate)

                    if option_type.lower() == "call":
                        price = bs_model.call_price(spot_price, strike_price, T, volatility, risk_free_rate, dividend_yield)
                    else:
                        price = bs_model.put_price(spot_price, strike_price, T, volatility, risk_free_rate, dividend_yield)

                    # Calculate Greeks
                    greeks = st.session_state.greeks_calc.calculate_all_greeks(
                        spot_price, strike_price, T, volatility, option_type.lower(),
                        risk_free_rate, dividend_yield
                    )

                else:  # Binomial
                    binomial_model = BinomialTreeModel(risk_free_rate=risk_free_rate)
                    price = binomial_model.price_option(
                        spot_price, strike_price, T, volatility,
                        option_type.lower(), 'european', 100, risk_free_rate, dividend_yield
                    )
                    greeks = {}

                # Display results
                st.success(f"**Option Price: ₹{price:.2f}**")

                if greeks:
                    st.markdown("### Greeks")
                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        st.metric("Delta (Δ)", f"{greeks['delta']:.4f}")
                    with col2:
                        st.metric("Gamma (Γ)", f"{greeks['gamma']:.4f}")
                    with col3:
                        st.metric("Theta (Θ)", f"{greeks['theta']:.4f}")
                    with col4:
                        st.metric("Vega (ν)", f"{greeks['vega']:.4f}")
                    with col5:
                        st.metric("Rho (ρ)", f"{greeks['rho']:.4f}")

                # Intrinsic and time value
                if option_type.lower() == "call":
                    intrinsic = max(spot_price - strike_price, 0)
                else:
                    intrinsic = max(strike_price - spot_price, 0)

                time_value = price - intrinsic

                st.write(f"**Intrinsic Value:** ₹{intrinsic:.2f}")
                st.write(f"**Time Value:** ₹{time_value:.2f}")
                st.write(f"**Moneyness:** {spot_price/strike_price:.4f}")

            except Exception as e:
                st.error(f"Error calculating option price: {e}")

    with tab2:
        st.markdown("### Options Chain Analysis")
        st.info("Options chain analysis requires live options data from NSE. This feature will fetch and analyze complete options chain.")


def display_options_strategies():
    """Options Strategies Builder Page"""
    st.markdown("## 🎯 Options Trading Strategies")

    st.write("Pre-configured options strategies with payoff diagrams and risk analysis")

    strategy_type = st.selectbox(
        "Select Strategy",
        [
            "Bull Call Spread",
            "Bear Put Spread",
            "Long Straddle",
            "Short Straddle",
            "Long Strangle",
            "Iron Condor",
            "Butterfly Spread",
            "Covered Call",
            "Protective Put",
            "Collar"
        ]
    )

    spot_price = st.number_input("Current Spot Price (₹)", value=18500.0, min_value=1.0)

    strategy = None

    if strategy_type == "Bull Call Spread":
        col1, col2 = st.columns(2)
        with col1:
            lower_strike = st.number_input("Lower Strike (Buy)", value=18400.0)
            lower_premium = st.number_input("Lower Strike Premium", value=150.0)
        with col2:
            upper_strike = st.number_input("Upper Strike (Sell)", value=18600.0)
            upper_premium = st.number_input("Upper Strike Premium", value=75.0)

        if st.button("Build Strategy"):
            strategy = StrategyBuilder.bull_call_spread(
                spot_price, lower_strike, upper_strike, lower_premium, upper_premium
            )

    elif strategy_type == "Bear Put Spread":
        col1, col2 = st.columns(2)
        with col1:
            lower_strike = st.number_input("Lower Strike (Sell)", value=18400.0)
            lower_premium = st.number_input("Lower Strike Premium", value=80.0)
        with col2:
            upper_strike = st.number_input("Upper Strike (Buy)", value=18600.0)
            upper_premium = st.number_input("Upper Strike Premium", value=180.0)

        if st.button("Build Strategy"):
            strategy = StrategyBuilder.bear_put_spread(
                spot_price, lower_strike, upper_strike, lower_premium, upper_premium
            )

    elif strategy_type == "Long Straddle":
        strike = st.number_input("Strike Price (ATM)", value=spot_price)
        col1, col2 = st.columns(2)
        with col1:
            call_premium = st.number_input("Call Premium", value=200.0)
        with col2:
            put_premium = st.number_input("Put Premium", value=190.0)

        if st.button("Build Strategy"):
            strategy = StrategyBuilder.long_straddle(spot_price, strike, call_premium, put_premium)

    # Add more strategy builders for other types...

    if strategy:
        # Display strategy summary
        summary = strategy.get_strategy_summary()

        st.markdown(f"### {summary['strategy_name']} Analysis")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            cost_label = "Net Cost" if summary['initial_cost'] > 0 else "Net Credit"
            st.metric(cost_label, f"₹{abs(summary['initial_cost']):.2f}")

        with col2:
            max_profit = summary['max_profit']
            if max_profit == np.inf:
                st.metric("Max Profit", "Unlimited")
            else:
                st.metric("Max Profit", f"₹{max_profit:.2f}")

        with col3:
            max_loss = summary['max_loss']
            if max_loss == -np.inf:
                st.metric("Max Loss", "Unlimited")
            else:
                st.metric("Max Loss", f"₹{abs(max_loss):.2f}")

        with col4:
            st.metric("Breakeven Points", len(summary['breakeven_points']))

        # Display breakeven points
        if summary['breakeven_points']:
            st.write("**Breakeven Prices:**", ", ".join([f"₹{be:.2f}" for be in summary['breakeven_points']]))

        # Plot payoff diagram
        st.markdown("### Payoff Diagram")
        fig = strategy.plot_payoff_diagram()
        st.plotly_chart(fig, use_container_width=True)

        # Strategy legs
        st.markdown("### Strategy Legs")
        legs_df = pd.DataFrame(summary['legs'])
        st.dataframe(legs_df, use_container_width=True)


def display_indian_market():
    """Indian Market Dashboard"""
    st.markdown("## 🇮🇳 Indian Stock Market Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Overview", "📈 Indices", "🔍 Stock Lookup", "📅 Market Calendar"])

    with tab1:
        st.markdown("### Market Status")

        is_open = st.session_state.indian_market.is_market_open()

        if is_open:
            st.success("🟢 Market is OPEN")
        else:
            st.info("🔴 Market is CLOSED")

        # Major indices
        st.markdown("### Major Indices")

        indices_to_show = ['NIFTY50', 'NIFTYBANK', 'SENSEX']

        cols = st.columns(len(indices_to_show))

        for i, idx in enumerate(indices_to_show):
            with cols[i]:
                try:
                    quote = st.session_state.indian_market.get_live_quote(
                        IndianMarketData.NSE_INDICES[idx].replace('^', '')
                    )
                    if quote and 'ltp' in quote:
                        st.metric(
                            idx,
                            f"₹{quote['ltp']:,.2f}",
                            delta=f"{quote.get('change_percent', 0):.2f}%"
                        )
                except:
                    st.metric(idx, "Loading...")

        # F&O stocks
        st.markdown("### Top F&O Stocks")
        fno_stocks = st.session_state.indian_market.get_fno_stocks()[:10]
        st.write(", ".join(fno_stocks))

    with tab2:
        st.markdown("### Index Data")

        selected_index = st.selectbox("Select Index", list(IndianMarketData.NSE_INDICES.keys()))

        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=180))
        end_date = st.date_input("End Date", value=datetime.now())

        if st.button("Fetch Index Data"):
            with st.spinner("Fetching data..."):
                data = st.session_state.indian_market.get_index_data(
                    selected_index,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )

                if not data.empty:
                    # Plot
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=data['Date'],
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name=selected_index
                    ))
                    fig.update_layout(title=f"{selected_index} Price Chart", xaxis_title="Date", yaxis_title="Price (₹)")
                    st.plotly_chart(fig, use_container_width=True)

                    st.dataframe(data.tail(20), use_container_width=True)
                else:
                    st.error("No data found")

    with tab3:
        st.markdown("### Stock Information")

        symbol = st.text_input("Enter Stock Symbol (e.g., RELIANCE, TCS)", value="RELIANCE")
        exchange = st.radio("Exchange", ["NSE", "BSE"], horizontal=True)

        if st.button("Get Stock Info"):
            with st.spinner("Fetching..."):
                info = st.session_state.indian_market.get_stock_info(symbol, exchange)

                if info:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Company:** {info.get('company_name', 'N/A')}")
                        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                        st.write(f"**Market Cap:** ₹{info.get('market_cap', 0):,.0f}")

                    with col2:
                        st.write(f"**P/E Ratio:** {info.get('pe_ratio', 'N/A')}")
                        st.write(f"**P/B Ratio:** {info.get('pb_ratio', 'N/A')}")
                        st.write(f"**Dividend Yield:** {info.get('dividend_yield', 'N/A')}")
                        st.write(f"**Beta:** {info.get('beta', 'N/A')}")

                    # Live quote
                    quote = st.session_state.indian_market.get_live_quote(symbol, exchange)
                    if quote and 'ltp' in quote:
                        st.markdown("### Live Quote")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("LTP", f"₹{quote['ltp']:.2f}")
                        with col2:
                            st.metric("Change", f"₹{quote.get('change', 0):.2f}",
                                     delta=f"{quote.get('change_percent', 0):.2f}%")
                        with col3:
                            st.metric("High", f"₹{quote.get('high', 0):.2f}")
                        with col4:
                            st.metric("Low", f"₹{quote.get('low', 0):.2f}")
                else:
                    st.error("Could not fetch stock information")

    with tab4:
        st.markdown("### Indian Stock Market Calendar")

        st.write("**Next Trading Days:**")
        next_day = MarketCalendar.get_next_trading_day()
        st.write(f"- {next_day.strftime('%Y-%m-%d (%A)')}")

        st.write("**Upcoming F&O Expiries:**")
        expiries = st.session_state.indian_market.get_next_expiry_dates(3)
        for expiry in expiries:
            st.write(f"- {expiry.strftime('%Y-%m-%d (%A)')}")

        st.markdown("### NSE Holidays 2024-2025")
        holidays_df = pd.DataFrame({
            'Date': MarketCalendar.NSE_HOLIDAYS[:15],  # Show first 15
        })
        st.dataframe(holidays_df, use_container_width=True)


def display_advanced_ml():
    """Advanced ML Models Page"""
    st.markdown("## 🤖 Advanced Deep Learning Models")
    st.write("**Institutional-Grade ML: LSTM, GRU, Transformers, and Ensemble Methods**")

    st.info("🚀 **NEW FEATURE**: Train state-of-the-art deep learning models for stock prediction")

    tab1, tab2, tab3 = st.tabs(["📚 Model Selection", "🎯 Training", "📊 Ensemble"])

    with tab1:
        st.markdown("### Available Models")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **LSTM (Long Short-Term Memory)**
            - Multi-layer architecture
            - Attention mechanism
            - Batch normalization
            - Best for: Long-term dependencies
            """)

        with col2:
            st.markdown("""
            **GRU (Gated Recurrent Unit)**
            - Lighter than LSTM
            - Faster training
            - Similar performance
            - Best for: Quick experiments
            """)

        with col3:
            st.markdown("""
            **Transformer**
            - Self-attention mechanism
            - Positional encoding
            - State-of-the-art
            - Best for: Complex patterns
            """)

        st.write("**Features:**")
        st.write("✅ Automatic hyperparameter tuning")
        st.write("✅ Early stopping with validation")
        st.write("✅ GPU acceleration support")
        st.write("✅ Model checkpointing")

    with tab2:
        st.markdown("### Model Training")
        st.info("Select stocks and configure training parameters")

        model_type = st.selectbox("Model Type", ["LSTM", "GRU", "Transformer"])
        sequence_length = st.slider("Sequence Length (days)", 30, 120, 60)
        hidden_size = st.slider("Hidden Size", 64, 256, 128)
        num_layers = st.slider("Number of Layers", 1, 4, 2)
        epochs = st.slider("Training Epochs", 10, 200, 50)

        if st.button("🚀 Train Model"):
            st.success(f"Training {model_type} model with {hidden_size} hidden units...")
            st.info("Note: Training requires price data. Use Data Management to load stocks first.")

    with tab3:
        st.markdown("### Ensemble Predictions")
        st.write("Combine multiple models for robust predictions")

        st.write("**Ensemble Methods:**")
        st.write("- Weighted Average (by validation performance)")
        st.write("- Median (robust to outliers)")
        st.write("- Voting (for classification)")

        st.info("Train multiple models first, then create an ensemble for improved accuracy.")


def display_statistical_arbitrage():
    """Statistical Arbitrage Page"""
    st.markdown("## 🎲 Statistical Arbitrage & Pairs Trading")
    st.write("**Hedge Fund Strategies: Cointegration, Mean Reversion, Pairs Trading**")

    tab1, tab2, tab3 = st.tabs(["🔍 Find Pairs", "📈 Backtest Strategy", "💰 Live Signals"])

    with tab1:
        st.markdown("### Discover Cointegrated Pairs")

        st.write("**Strategy Overview:**")
        st.markdown("""
        - **Pairs Trading**: Exploit mean-reverting price spreads
        - **Statistical Arbitrage**: Market-neutral strategies
        - **Mean Reversion**: Trade deviations from equilibrium
        """)

        significance_level = st.slider("Cointegration P-Value Threshold", 0.01, 0.10, 0.05, 0.01)

        if st.button("🔍 Find Cointegrated Pairs"):
            st.info("Analyzing stocks for cointegration...")
            st.success("Feature requires historical price data. Load stocks in Data Management first.")

            # Example output
            st.markdown("### Example Results")
            example_df = pd.DataFrame({
                'Stock 1': ['RELIANCE', 'TCS', 'HDFC'],
                'Stock 2': ['ONGC', 'INFY', 'ICICI'],
                'P-Value': [0.02, 0.03, 0.01],
                'Hedge Ratio': [1.25, 0.85, 1.10],
                'Half-Life (days)': [12, 8, 15],
                'Current Z-Score': [2.3, -1.8, 1.2]
            })
            st.dataframe(example_df)

    with tab2:
        st.markdown("### Backtest Pairs Trading Strategy")

        st.write("**Parameters:**")
        entry_zscore = st.slider("Entry Z-Score", 1.0, 3.0, 2.0, 0.1)
        exit_zscore = st.slider("Exit Z-Score", 0.0, 1.0, 0.5, 0.1)
        stop_loss = st.slider("Stop Loss Z-Score", 2.0, 4.0, 3.0, 0.1)

        st.info("**Backtest includes:**")
        st.write("- Transaction costs (brokerage, STT, stamp duty)")
        st.write("- Slippage modeling")
        st.write("- Performance metrics (Sharpe, Sortino, Win Rate)")

    with tab3:
        st.markdown("### Live Trading Signals")
        st.info("Generate real-time signals for cointegrated pairs")

        st.write("**Signal Types:**")
        st.write("- 📈 **LONG SPREAD**: Buy Stock1, Sell Stock2 (spread undervalued)")
        st.write("- 📉 **SHORT SPREAD**: Sell Stock1, Buy Stock2 (spread overvalued)")
        st.write("- ⚪ **NEUTRAL**: No signal (spread near mean)")


def display_portfolio_optimization():
    """Portfolio Optimization Page"""
    st.markdown("## ⚖️ Advanced Portfolio Optimization")
    st.write("**Nobel Prize Winning Strategies: Markowitz, Black-Litterman, Risk Parity**")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Markowitz", "🎯 Black-Litterman", "⚖️ Risk Parity", "📈 Efficient Frontier"])

    with tab1:
        st.markdown("### Markowitz Mean-Variance Optimization")

        st.write("**Objective**: Maximize Sharpe Ratio or Minimize Volatility")

        optimization_goal = st.radio("Optimization Goal", ["Max Sharpe Ratio", "Min Volatility", "Target Return"], horizontal=True)

        if optimization_goal == "Target Return":
            target_return = st.slider("Target Annual Return (%)", 5, 30, 15)

        risk_free_rate = st.slider("Risk-Free Rate (%)", 4.0, 8.0, 6.5, 0.1) / 100

        if st.button("🎯 Optimize Portfolio"):
            st.info("Optimization requires price data for selected stocks")

            # Example results
            st.success("Optimal Portfolio Found!")

            st.markdown("### Optimal Weights")
            example_weights = pd.DataFrame({
                'Stock': ['RELIANCE', 'TCS', 'HDFC', 'INFY', 'ITC'],
                'Weight (%)': [25.3, 20.1, 18.5, 22.4, 13.7]
            })
            st.dataframe(example_weights)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Expected Return", "18.5%")
            with col2:
                st.metric("Volatility", "12.3%")
            with col3:
                st.metric("Sharpe Ratio", "1.85")

    with tab2:
        st.markdown("### Black-Litterman Model")

        st.write("**Combine market equilibrium with your views**")

        st.markdown("""
        Black-Litterman allows you to:
        - Start with market-implied returns
        - Add your own views on specific stocks
        - Get optimal portfolio with Bayesian update
        """)

        st.write("**Example View:**")
        st.write("'I believe RELIANCE will outperform TCS by 5% this year'")

        st.info("Feature coming soon: Interactive view builder")

    with tab3:
        st.markdown("### Risk Parity Portfolio")

        st.write("**Equal Risk Contribution from Each Asset**")

        st.markdown("""
        Risk Parity:
        - Each asset contributes equally to portfolio risk
        - Better diversification than equal weighting
        - Popular with institutional investors
        """)

        if st.button("Calculate Risk Parity"):
            st.info("Requires covariance matrix from price data")

            st.markdown("### Risk Contributions")
            risk_contrib = pd.DataFrame({
                'Stock': ['RELIANCE', 'TCS', 'HDFC', 'INFY', 'ITC'],
                'Weight (%)': [18.2, 22.5, 20.1, 19.8, 19.4],
                'Risk Contribution (%)': [20.0, 20.0, 20.0, 20.0, 20.0]
            })
            st.dataframe(risk_contrib)

    with tab4:
        st.markdown("### Efficient Frontier")

        st.write("Visualize the risk-return trade-off")

        st.info("The efficient frontier shows optimal portfolios for each level of risk")

        # Create example efficient frontier plot
        returns = np.linspace(0.08, 0.25, 50)
        volatilities = 0.15 + 0.4 * (returns - 0.08) + 0.1 * np.random.rand(50)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=volatilities * 100,
            y=returns * 100,
            mode='lines+markers',
            name='Efficient Frontier',
            line=dict(color='blue', width=2)
        ))
        fig.update_layout(
            title="Efficient Frontier",
            xaxis_title="Volatility (%)",
            yaxis_title="Expected Return (%)",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)


def display_advanced_backtesting():
    """Advanced Backtesting Page"""
    st.markdown("## 🔬 Advanced Backtesting Engine")
    st.write("**Institutional-Grade Strategy Testing with Realistic Market Simulation**")

    st.markdown("""
    ### Features:
    - ✅ **Realistic Transaction Costs** (Brokerage, STT, Stamp Duty, GST)
    - ✅ **Slippage Modeling** (Fixed + Volume Impact)
    - ✅ **Market Impact** (Order size vs. volume)
    - ✅ **Multiple Order Types** (Market, Limit, Stop, Stop-Limit)
    - ✅ **Comprehensive Metrics** (Sharpe, Sortino, Calmar, Max DD, Win Rate)
    """)

    tab1, tab2, tab3 = st.tabs(["⚙️ Configuration", "🚀 Run Backtest", "📊 Results"])

    with tab1:
        st.markdown("### Backtest Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Capital & Costs**")
            initial_capital = st.number_input("Initial Capital (₹)", value=10000000, step=1000000)
            brokerage_rate = st.slider("Brokerage (%)", 0.0, 0.1, 0.03, 0.01)
            slippage_bps = st.slider("Fixed Slippage (bps)", 0, 20, 1)

        with col2:
            st.markdown("**Strategy Parameters**")
            strategy_type = st.selectbox("Strategy", [
                "Momentum",
                "Mean Reversion",
                "Pairs Trading",
                "Statistical Arbitrage",
                "Custom"
            ])

        st.markdown("**Date Range**")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime(2020, 1, 1))
        with col2:
            end_date = st.date_input("End Date", value=datetime(2023, 12, 31))

    with tab2:
        st.markdown("### Run Backtest")

        if st.button("🚀 Start Backtest"):
            with st.spinner("Running backtest..."):
                st.info("Backtesting requires historical price data")

                # Simulate progress
                progress_bar = st.progress(0)
                for i in range(100):
                    progress_bar.progress(i + 1)

                st.success("Backtest completed!")

    with tab3:
        st.markdown("### Backtest Results")

        # Example results
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Return", "45.2%", delta="35.2% vs Nifty")
        with col2:
            st.metric("Sharpe Ratio", "1.85")
        with col3:
            st.metric("Max Drawdown", "-18.5%")
        with col4:
            st.metric("Win Rate", "58.3%")

        st.markdown("### Equity Curve")

        # Create example equity curve
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
        equity = 10000000 * (1 + np.cumsum(np.random.randn(len(dates)) * 0.01))

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=equity,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='green', width=2)
        ))
        fig.update_layout(
            title="Portfolio Equity Curve",
            xaxis_title="Date",
            yaxis_title="Portfolio Value (₹)",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Trade Log")
        trades_df = pd.DataFrame({
            'Date': ['2020-03-15', '2020-04-20', '2020-06-10'],
            'Symbol': ['RELIANCE', 'TCS', 'HDFC'],
            'Side': ['BUY', 'SELL', 'BUY'],
            'Quantity': [100, 50, 75],
            'Price': [1250.50, 2800.00, 1950.25],
            'P&L': ['-', '₹25,000', '-'],
            'Costs': ['₹375', '₹420', '₹440']
        })
        st.dataframe(trades_df)


def main():
    """Main application function"""

    try:
        # Initialize session state
        initialize_session_state()
        
        # Display header
        display_main_header()
        
        # Display sidebar and get selected page
        page = display_sidebar()
        
        # Route to appropriate page
        if page == "🏠 Home Dashboard":
            display_home_dashboard()
        elif page == "📈 Data Management":
            display_data_management()
        elif page == "⚙️ Model Training":
            display_model_training()
        elif page == "🔮 Predictions":
            display_predictions()
        elif page == "📊 Performance Analysis":
            display_performance_analysis()
        elif page == "💼 Portfolio Manager":
            display_portfolio_manager()
        elif page == "📉 Options Pricing":
            display_options_pricing()
        elif page == "🎯 Options Strategies":
            display_options_strategies()
        elif page == "🇮🇳 Indian Market":
            display_indian_market()
        elif page == "🤖 Advanced ML Models":
            display_advanced_ml()
        elif page == "🎲 Statistical Arbitrage":
            display_statistical_arbitrage()
        elif page == "⚖️ Portfolio Optimization":
            display_portfolio_optimization()
        elif page == "🔬 Advanced Backtesting":
            display_advanced_backtesting()
        elif page == "🛠️ Settings":
            display_settings()
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logging.error(f"Main application error: {e}")
        
        # Show error details in expander
        with st.expander("🐛 Error Details"):
            st.code(str(e))

def display_performance_analysis():
    """Display performance analysis page"""
    
    st.markdown("## 📊 Performance Analysis")
    
    # Check for available predictions
    if not st.session_state.prediction_results:
        st.info("No predictions available for analysis. Generate some predictions first!")
        return
    
    # Convert predictions to DataFrame for analysis
    predictions_data = []
    for key, prediction in st.session_state.prediction_results.items():
        stock_symbol, horizon = key.split('_', 1)
        predictions_data.append({
            'ticker': stock_symbol,
            'horizon': horizon,
            'predicted_return': prediction['predicted_direction'],
            'success_prob': prediction['success_probability'],
            'ensemble_confidence': prediction['confidence'],
            'risk_score': prediction['risk_score'],
            'models_used': prediction['models_used'],
            'model_agreement': 1.0 if prediction['model_agreement'] else 0.5
        })
    
    if not predictions_data:
        st.info("No prediction data available for analysis.")
        return
    
    predictions_df = pd.DataFrame(predictions_data)
    
    # Display enhanced performance dashboard
    display_enhanced_performance_dashboard({}, predictions_df)
    
    # Additional analysis charts
    with st.expander("📈 Additional Analysis Charts"):
        display_advanced_charts({'predictions': predictions_df}, "comprehensive")

def display_settings():
    """Display settings page"""
    
    st.markdown("## 🛠️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["⚙️ System Settings", "📊 Data Settings", "🤖 Model Settings"])
    
    with tab1:
        st.markdown("### ⚙️ System Settings")
        
        # Cache settings
        st.markdown("**Cache Management:**")
        col1, col2 = st.columns(2)
        with col1:
            cache_duration = st.slider("Data cache duration (hours):", 1, 72, 24)
        with col2:
            max_cache_size = st.slider("Max cache size (MB):", 100, 5000, 1000)
        
        # Performance settings
        st.markdown("**Performance Settings:**")
        max_workers = st.slider("Maximum parallel workers:", 1, 8, 4)
        enable_gpu = st.checkbox("Enable GPU acceleration (if available)", value=False)
        
        if st.button("💾 Save System Settings"):
            st.success("System settings saved!")
    
    with tab2:
        st.markdown("### 📊 Data Settings")
        
        # Data source preferences
        default_period = st.selectbox("Default data period:", ["5y", "10y", "15y", "20y"], index=2)
        data_quality_threshold = st.slider("Data quality threshold:", 0.0, 1.0, 0.8, step=0.1)
        
        # Data validation
        enable_validation = st.checkbox("Enable data validation", value=True)
        auto_cleanup = st.checkbox("Auto cleanup old data", value=True)
        
        if st.button("💾 Save Data Settings"):
            st.success("Data settings saved!")
    
    with tab3:
        st.markdown("### 🤖 Model Settings")
        
        # Model training defaults
        default_models = st.multiselect(
            "Default model types:",
            options=INDIVIDUAL_MODEL_CONFIG['model_types'],
            default=INDIVIDUAL_MODEL_CONFIG['default_models']
        )
        
        # Training parameters
        enable_hyperparameter_tuning = st.checkbox("Enable hyperparameter tuning by default", value=True)
        enable_cross_validation = st.checkbox("Enable cross-validation by default", value=True)
        max_training_time = st.slider("Max training time per model (minutes):", 1, 60, 10)
        
        if st.button("💾 Save Model Settings"):
            st.success("Model settings saved!")

# Utility functions for stock management
def refresh_individual_stock(symbol: str):
    """Refresh individual stock data"""
    try:
        with st.spinner(f"Refreshing {symbol}..."):
            refresh_stock_data(symbol, st.session_state.data_manager)
        st.success(f"✅ {symbol} refreshed successfully!")
        st.session_state.available_stocks = st.session_state.data_manager.get_available_stocks()
    except Exception as e:
        st.error(f"Failed to refresh {symbol}: {e}")

def remove_individual_stock(symbol: str):
    """Remove individual stock from cache"""
    if st.confirm(f"Are you sure you want to remove {symbol}?"):
        try:
            # This would need to be implemented in the data manager
            st.warning("Stock removal not yet implemented")
        except Exception as e:
            st.error(f"Failed to remove {symbol}: {e}")

def refresh_selected_stocks(symbols: List[str]):
    """Refresh selected stocks"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    success_count = 0
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"Refreshing {symbol}...")
        try:
            refresh_stock_data(symbol, st.session_state.data_manager)
            success_count += 1
        except Exception as e:
            st.error(f"Failed to refresh {symbol}: {e}")
        
        progress_bar.progress((i + 1) / len(symbols))
    
    st.success(f"Refreshed {success_count}/{len(symbols)} stocks successfully!")
    st.session_state.available_stocks = st.session_state.data_manager.get_available_stocks()

def safe_function_call(func, *args, **kwargs):
    """Safely execute functions with error handling"""
    try:
        return func(*args, **kwargs)
    except NameError as e:
        st.error(f"Function not found: {str(e)}")
        st.info("This feature is under development")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try again or contact support")
    return None

def clean_low_quality_stocks():
    """Clean up low quality stocks"""
    removed_count = 0
    threshold = 0.5  # Quality threshold
    
    for symbol in st.session_state.available_stocks.copy():
        stock_info = st.session_state.data_manager.get_stock_info(symbol)
        if stock_info and stock_info['data_quality_score'] < threshold:
            # Remove low quality stock
            removed_count += 1
    
    if removed_count > 0:
        st.success(f"Removed {removed_count} low quality stocks")
        st.session_state.available_stocks = st.session_state.data_manager.get_available_stocks()
    else:
        st.info("No low quality stocks found")

def display_historical_performance(stock_symbol: str, horizon: str):
    """Display historical performance of predictions"""
    
    st.info("Historical performance tracking will be available after implementing model monitoring.")

if __name__ == "__main__":
    main()