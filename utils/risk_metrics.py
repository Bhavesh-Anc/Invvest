# utils/risk_metrics.py
import numpy as np

def var_historical(returns, alpha=0.05):
    return np.percentile(returns, 100*alpha)

def cvar_historical(returns, alpha=0.05):
    var = var_historical(returns, alpha)
    return returns[returns <= var].mean()

def stress_test_scenario(returns, volatility_shock=1.5):
    shocked = returns * volatility_shock
    return shocked
