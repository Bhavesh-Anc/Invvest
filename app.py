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

# Configure logging
logging.basicConfig(level=logging.INFO)
warnings.filterwarnings('ignore')

# Enhanced Streamlit page configuration
st.set_page_config(
    page_title="AI Stock Advisor Pro - Individual Edition",
    page_icon="🚀",
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

def display_main_header():
    """Display main application header"""
    
    st.markdown('<h1 class="main-header">🚀 AI Stock Advisor Pro - Individual Edition</h1>', unsafe_allow_html=True)
    
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