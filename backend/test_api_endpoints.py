#!/usr/bin/env python3
"""
Automated API Endpoint Testing Script
Tests all 41 new institutional quant strategy endpoints
"""

import requests
import json
import time
from typing import Dict, List
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class APITester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> bool:
        """Test a single endpoint"""
        url = f"{BASE_URL}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            else:
                raise ValueError(f"Unknown method: {method}")

            if response.status_code in [200, 201]:
                print(f"{GREEN}✓{RESET} {method:4s} {endpoint}")
                self.passed += 1
                return True
            else:
                print(f"{RED}✗{RESET} {method:4s} {endpoint} - Status: {response.status_code}")
                self.errors.append({
                    'endpoint': endpoint,
                    'status': response.status_code,
                    'error': response.text[:200]
                })
                self.failed += 1
                return False

        except Exception as e:
            print(f"{RED}✗{RESET} {method:4s} {endpoint} - Error: {str(e)[:50]}")
            self.errors.append({
                'endpoint': endpoint,
                'error': str(e)
            })
            self.failed += 1
            return False

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print("\n" + "=" * 70)
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print("=" * 70)
        print(f"Total Tests:  {total}")
        print(f"{GREEN}Passed:       {self.passed}{RESET}")
        print(f"{RED}Failed:       {self.failed}{RESET}")
        print(f"Pass Rate:    {pass_rate:.1f}%")

        if self.errors:
            print(f"\n{YELLOW}ERRORS:{RESET}")
            for i, error in enumerate(self.errors[:5], 1):
                print(f"{i}. {error['endpoint']}")
                print(f"   {error.get('error', 'Unknown error')[:100]}")

        print("=" * 70)


def main():
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}QuantEdge Pro - API Endpoint Testing{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code == 200:
            print(f"{GREEN}✓ Server is running{RESET}\n")
        else:
            print(f"{RED}✗ Server returned status {response.status_code}{RESET}\n")
            return
    except Exception as e:
        print(f"{RED}✗ Server is not running. Start it with: python main.py{RESET}")
        print(f"   Error: {str(e)}\n")
        return

    tester = APITester()

    # Test Options Advanced Endpoints
    print(f"\n{YELLOW}Testing Options Advanced API (10 endpoints)...{RESET}")
    tester.test_endpoint("GET", "/api/options/volatility-arbitrage/opportunities",
                         params={"symbol": "RELIANCE", "forecasting_method": "ewma"})
    tester.test_endpoint("GET", "/api/options/volatility-arbitrage/forecast/RELIANCE",
                         params={"method": "ewma"})
    tester.test_endpoint("POST", "/api/options/volatility-arbitrage/position-size",
                         data={"capital": 1000000, "option_price": 250, "vega": 0.5, "max_vega_exposure": 50000})
    tester.test_endpoint("POST", "/api/options/gamma-scalping/hedge-ratio",
                         data=[{"delta": 0.5, "quantity": 10}, {"delta": -0.3, "quantity": 5}])
    tester.test_endpoint("POST", "/api/options/gamma-scalping/simulate",
                         data={"option_price": 250, "implied_vol": 0.15, "spot_prices": [22000, 22050, 22100],
                               "gamma": 0.002, "initial_delta": 0.5, "transaction_cost": 10})
    tester.test_endpoint("GET", "/api/options/gamma-scalping/optimize-rehedge",
                         params={"transaction_cost": 10, "gamma": 0.002, "realized_vol": 0.18})
    tester.test_endpoint("GET", "/api/options/dispersion/opportunity",
                         params={"index": "NIFTY", "threshold": 0.10})
    tester.test_endpoint("GET", "/api/options/dispersion/correlation",
                         params={"index": "NIFTY", "lookback_days": 30})
    tester.test_endpoint("GET", "/api/options/volatility-surface/skew",
                         params={"symbol": "RELIANCE", "expiry_date": "2024-03-28"})
    tester.test_endpoint("GET", "/api/options/volatility-surface/butterfly-arbitrage",
                         params={"symbol": "RELIANCE", "transaction_cost": 50})

    # Test ML Strategies Endpoints
    print(f"\n{YELLOW}Testing ML Strategies API (10 endpoints)...{RESET}")
    tester.test_endpoint("POST", "/api/ml/features/generate",
                         data={"symbol": "TCS", "start_date": "2024-01-01", "end_date": "2024-12-31"})
    tester.test_endpoint("GET", "/api/ml/features/importance/NIFTY",
                         params={"top_n": 10})
    tester.test_endpoint("POST", "/api/ml/lstm/train",
                         data={"symbol": "INFY", "sequence_length": 60, "epochs": 10, "hidden_size": 64})
    tester.test_endpoint("GET", "/api/ml/lstm/predict/RELIANCE",
                         params={"horizon": "5d"})
    tester.test_endpoint("POST", "/api/ml/xgboost/train",
                         data={"symbol": "TCS", "task": "regression", "n_estimators": 50})
    tester.test_endpoint("GET", "/api/ml/xgboost/signals/NIFTY",
                         params={"threshold": 0.002})
    tester.test_endpoint("POST", "/api/ml/sentiment/analyze",
                         data=[{"title": "NIFTY hits new high", "description": "Strong rally continues"}])
    tester.test_endpoint("GET", "/api/ml/sentiment/signal/RELIANCE")
    tester.test_endpoint("POST", "/api/ml/sentiment/divergence/TCS",
                         params={"lookback_days": 30})
    tester.test_endpoint("POST", "/api/ml/ensemble/predict",
                         data={"symbol": "INFY", "models": [{"name": "lstm", "weight": 0.5}, {"name": "xgboost", "weight": 0.5}]})

    # Test Execution Endpoints
    print(f"\n{YELLOW}Testing Optimal Execution API (10 endpoints)...{RESET}")
    tester.test_endpoint("POST", "/api/execution/vwap/schedule",
                         data={"symbol": "TCS", "total_quantity": 10000, "participation_rate": 0.10})
    tester.test_endpoint("POST", "/api/execution/vwap/evaluate",
                         data={"fills": [{"symbol": "TCS", "side": "buy", "quantity": 1000, "price": 3500}],
                               "vwap_benchmark": 3505})
    tester.test_endpoint("POST", "/api/execution/twap/schedule",
                         data={"symbol": "INFY", "total_quantity": 5000, "num_intervals": 10, "randomize": True})
    tester.test_endpoint("POST", "/api/execution/twap/evaluate",
                         data={"fills": [{"symbol": "INFY", "side": "buy", "quantity": 500, "price": 1450}],
                               "start_price": 1440, "end_price": 1460})
    tester.test_endpoint("POST", "/api/execution/impact/calculate",
                         data={"quantity": 100000, "adv": 5000000, "price": 2500, "execution_time": 0.5})
    tester.test_endpoint("POST", "/api/execution/impact/optimize-time",
                         data={"quantity": 100000, "adv": 5000000, "price": 2500, "max_time": 1.0})
    tester.test_endpoint("POST", "/api/execution/route",
                         data={"symbol": "RELIANCE", "side": "buy", "quantity": 1000, "price": 2500,
                               "venue_liquidity": {"NSE": 2000, "BSE": 800}})
    tester.test_endpoint("GET", "/api/execution/venues/evaluate",
                         params={"symbol": "RELIANCE", "quantity": 1000})
    tester.test_endpoint("POST", "/api/execution/adaptive/adjust-schedule",
                         data={"original_schedule": [{"interval": 0, "quantity": 1000}], "current_interval": 0,
                               "executed_quantity": 500, "target_quantity": 10000, "current_volume_pct": 0.15,
                               "expected_volume_pct": 0.10})
    tester.test_endpoint("GET", "/api/execution/adaptive/urgency",
                         params={"time_elapsed_pct": 50, "quantity_executed_pct": 30})

    # Test Market Making Endpoints
    print(f"\n{YELLOW}Testing Market Making API (11 endpoints)...{RESET}")
    tester.test_endpoint("POST", "/api/market-making/quotes/generate",
                         data={"symbol": "NIFTY", "fair_value": 22000, "volatility": 0.02, "order_flow_imbalance": 0.0})
    tester.test_endpoint("GET", "/api/market-making/quotes/spread-analysis",
                         params={"symbol": "NIFTY", "volatility": 0.02, "inventory_pct": 0.5})
    tester.test_endpoint("GET", "/api/market-making/inventory/position",
                         params={"symbol": "NIFTY"})
    tester.test_endpoint("POST", "/api/market-making/inventory/check-limit",
                         data={"symbol": "NIFTY", "current_position": 1000, "proposed_trade_size": 500, "side": "bid"})
    tester.test_endpoint("GET", "/api/market-making/inventory/urgency",
                         params={"symbol": "NIFTY", "current_position": 3000, "target_position": 0})
    tester.test_endpoint("POST", "/api/market-making/flow/imbalance",
                         data={"buy_volume": [1000, 1200, 1100], "sell_volume": [900, 950, 1000], "lookback": 3})
    tester.test_endpoint("POST", "/api/market-making/flow/adverse-selection",
                         data={"prices": [22000, 22010, 22005, 22015], "trade_directions": [1, 1, -1, 1]})
    tester.test_endpoint("POST", "/api/market-making/process-fill",
                         data={"symbol": "NIFTY", "side": "bid", "quantity": 100, "price": 21995})
    tester.test_endpoint("GET", "/api/market-making/pnl",
                         params={"symbol": "NIFTY", "current_price": 22000})
    tester.test_endpoint("GET", "/api/market-making/volatility/estimate",
                         params={"symbol": "RELIANCE", "lookback_days": 30})
    tester.test_endpoint("POST", "/api/market-making/reset/NIFTY")

    # Print summary
    tester.print_summary()

    print(f"\n{BLUE}Next Steps:{RESET}")
    print("1. Review any failed endpoints above")
    print("2. Check Swagger docs at http://localhost:8000/api/docs")
    print("3. Test WebSocket: ws://localhost:8000/api/market-making/ws/quotes/NIFTY")
    print()


if __name__ == "__main__":
    main()
