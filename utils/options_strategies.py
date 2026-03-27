"""
Options Trading Strategies Builder
Pre-configured strategies with payoff diagrams and risk analysis
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

from .options_pricing import BlackScholesModel, GreeksCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptionLeg:
    """
    Single option leg in a strategy
    """

    def __init__(self, option_type: str, strike: float, position: str,
                 quantity: int = 1, premium: float = 0):
        """
        Initialize option leg

        Args:
            option_type: 'call' or 'put'
            strike: Strike price
            position: 'long' or 'short'
            quantity: Number of contracts
            premium: Option premium per contract
        """
        self.option_type = option_type.lower()
        self.strike = strike
        self.position = position.lower()
        self.quantity = quantity
        self.premium = premium

    def payoff(self, spot_prices: np.ndarray) -> np.ndarray:
        """
        Calculate payoff at expiration

        Args:
            spot_prices: Array of spot prices

        Returns:
            Array of payoffs
        """
        if self.option_type == 'call':
            intrinsic = np.maximum(spot_prices - self.strike, 0)
        else:  # put
            intrinsic = np.maximum(self.strike - spot_prices, 0)

        if self.position == 'long':
            payoff = (intrinsic - self.premium) * self.quantity
        else:  # short
            payoff = (self.premium - intrinsic) * self.quantity

        return payoff


class OptionsStrategy:
    """
    Options trading strategy builder
    """

    def __init__(self, strategy_name: str, spot_price: float):
        """
        Initialize strategy

        Args:
            strategy_name: Name of the strategy
            spot_price: Current spot price
        """
        self.strategy_name = strategy_name
        self.spot_price = spot_price
        self.legs: List[OptionLeg] = []
        self.bs_model = BlackScholesModel()
        self.greeks_calc = GreeksCalculator(self.bs_model)

    def add_leg(self, option_type: str, strike: float, position: str,
                quantity: int = 1, premium: float = 0):
        """Add an option leg to the strategy"""
        leg = OptionLeg(option_type, strike, position, quantity, premium)
        self.legs.append(leg)
        logger.info(f"Added {position} {quantity} {option_type} @ {strike} with premium {premium}")

    def calculate_total_payoff(self, spot_prices: np.ndarray) -> np.ndarray:
        """
        Calculate total strategy payoff

        Args:
            spot_prices: Array of spot prices

        Returns:
            Array of total payoffs
        """
        total_payoff = np.zeros_like(spot_prices)

        for leg in self.legs:
            total_payoff += leg.payoff(spot_prices)

        return total_payoff

    def calculate_breakeven_points(self) -> List[float]:
        """
        Calculate breakeven points

        Returns:
            List of breakeven prices
        """
        spot_prices = np.linspace(
            self.spot_price * 0.5,
            self.spot_price * 1.5,
            1000
        )
        payoffs = self.calculate_total_payoff(spot_prices)

        # Find where payoff crosses zero
        breakeven_points = []
        for i in range(len(payoffs) - 1):
            if payoffs[i] * payoffs[i + 1] < 0:  # Sign change
                # Linear interpolation
                be = spot_prices[i] + (spot_prices[i + 1] - spot_prices[i]) * \
                     (-payoffs[i] / (payoffs[i + 1] - payoffs[i]))
                breakeven_points.append(be)

        return breakeven_points

    def calculate_max_profit_loss(self) -> Dict:
        """
        Calculate maximum profit and loss

        Returns:
            Dictionary with max profit and loss
        """
        spot_prices = np.linspace(
            self.spot_price * 0.3,
            self.spot_price * 1.7,
            10000
        )
        payoffs = self.calculate_total_payoff(spot_prices)

        max_profit = np.max(payoffs)
        max_loss = np.min(payoffs)

        # Check if unlimited
        max_profit_unlimited = max_profit > self.spot_price * 10
        max_loss_unlimited = max_loss < -self.spot_price * 10

        return {
            'max_profit': max_profit if not max_profit_unlimited else np.inf,
            'max_loss': max_loss if not max_loss_unlimited else -np.inf,
            'max_profit_unlimited': max_profit_unlimited,
            'max_loss_unlimited': max_loss_unlimited
        }

    def calculate_initial_cost(self) -> float:
        """
        Calculate initial cost/credit of strategy

        Returns:
            Net cost (positive) or credit (negative)
        """
        total_cost = 0

        for leg in self.legs:
            if leg.position == 'long':
                total_cost += leg.premium * leg.quantity
            else:  # short
                total_cost -= leg.premium * leg.quantity

        return total_cost

    def plot_payoff_diagram(self, show_current_price: bool = True) -> go.Figure:
        """
        Create interactive payoff diagram

        Args:
            show_current_price: Show vertical line at current spot price

        Returns:
            Plotly figure
        """
        # Generate spot prices
        spot_prices = np.linspace(
            self.spot_price * 0.6,
            self.spot_price * 1.4,
            500
        )

        # Calculate payoffs for each leg
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=[f"{self.strategy_name} Payoff Diagram"]
        )

        # Individual legs
        for i, leg in enumerate(self.legs):
            payoff = leg.payoff(spot_prices)
            fig.add_trace(go.Scatter(
                x=spot_prices,
                y=payoff,
                name=f"{leg.position.upper()} {leg.quantity} {leg.option_type.upper()} {leg.strike}",
                line=dict(width=1, dash='dash'),
                opacity=0.5
            ))

        # Total payoff
        total_payoff = self.calculate_total_payoff(spot_prices)
        fig.add_trace(go.Scatter(
            x=spot_prices,
            y=total_payoff,
            name='Total Payoff',
            line=dict(width=3, color='blue'),
            fill='tozeroy',
            fillcolor='rgba(0,100,200,0.2)'
        ))

        # Zero line
        fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)

        # Current price line
        if show_current_price:
            fig.add_vline(
                x=self.spot_price,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Current: ₹{self.spot_price:.2f}",
                annotation_position="top"
            )

        # Breakeven points
        breakeven_points = self.calculate_breakeven_points()
        for be in breakeven_points:
            fig.add_vline(
                x=be,
                line_dash="dot",
                line_color="green",
                annotation_text=f"BE: ₹{be:.2f}",
                annotation_position="bottom"
            )

        # Update layout
        fig.update_layout(
            xaxis_title="Spot Price at Expiration (₹)",
            yaxis_title="Profit/Loss (₹)",
            hovermode='x unified',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        # Add annotations for max profit/loss
        max_pl = self.calculate_max_profit_loss()
        annotation_text = f"<b>Strategy: {self.strategy_name}</b><br>"
        annotation_text += f"Initial Cost: ₹{self.calculate_initial_cost():.2f}<br>"
        annotation_text += f"Max Profit: ₹{max_pl['max_profit']:.2f}" + \
                          (" (Unlimited)" if max_pl['max_profit_unlimited'] else "") + "<br>"
        annotation_text += f"Max Loss: ₹{abs(max_pl['max_loss']):.2f}" + \
                          (" (Unlimited)" if max_pl['max_loss_unlimited'] else "")

        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.98,
            y=0.98,
            text=annotation_text,
            showarrow=False,
            bgcolor="white",
            bordercolor="black",
            borderwidth=1,
            align="left",
            xanchor="right",
            yanchor="top"
        )

        return fig

    def get_strategy_summary(self) -> Dict:
        """
        Get comprehensive strategy summary

        Returns:
            Dictionary with strategy details
        """
        max_pl = self.calculate_max_profit_loss()
        breakevens = self.calculate_breakeven_points()
        initial_cost = self.calculate_initial_cost()

        return {
            'strategy_name': self.strategy_name,
            'spot_price': self.spot_price,
            'num_legs': len(self.legs),
            'initial_cost': initial_cost,
            'strategy_type': 'Debit' if initial_cost > 0 else 'Credit',
            'max_profit': max_pl['max_profit'],
            'max_loss': max_pl['max_loss'],
            'breakeven_points': breakevens,
            'legs': [
                {
                    'type': leg.option_type,
                    'strike': leg.strike,
                    'position': leg.position,
                    'quantity': leg.quantity,
                    'premium': leg.premium
                }
                for leg in self.legs
            ]
        }


class StrategyBuilder:
    """
    Pre-configured popular options strategies
    """

    @staticmethod
    def bull_call_spread(spot_price: float, lower_strike: float,
                        upper_strike: float, lower_premium: float,
                        upper_premium: float) -> OptionsStrategy:
        """
        Bull Call Spread: Buy lower strike call, Sell higher strike call
        Bullish strategy with limited profit and loss
        """
        strategy = OptionsStrategy("Bull Call Spread", spot_price)
        strategy.add_leg('call', lower_strike, 'long', 1, lower_premium)
        strategy.add_leg('call', upper_strike, 'short', 1, upper_premium)
        return strategy

    @staticmethod
    def bear_put_spread(spot_price: float, lower_strike: float,
                       upper_strike: float, lower_premium: float,
                       upper_premium: float) -> OptionsStrategy:
        """
        Bear Put Spread: Buy higher strike put, Sell lower strike put
        Bearish strategy with limited profit and loss
        """
        strategy = OptionsStrategy("Bear Put Spread", spot_price)
        strategy.add_leg('put', upper_strike, 'long', 1, upper_premium)
        strategy.add_leg('put', lower_strike, 'short', 1, lower_premium)
        return strategy

    @staticmethod
    def long_straddle(spot_price: float, strike: float,
                     call_premium: float, put_premium: float) -> OptionsStrategy:
        """
        Long Straddle: Buy ATM call and ATM put
        Profits from large moves in either direction
        """
        strategy = OptionsStrategy("Long Straddle", spot_price)
        strategy.add_leg('call', strike, 'long', 1, call_premium)
        strategy.add_leg('put', strike, 'long', 1, put_premium)
        return strategy

    @staticmethod
    def short_straddle(spot_price: float, strike: float,
                      call_premium: float, put_premium: float) -> OptionsStrategy:
        """
        Short Straddle: Sell ATM call and ATM put
        Profits from low volatility (stock staying near strike)
        """
        strategy = OptionsStrategy("Short Straddle", spot_price)
        strategy.add_leg('call', strike, 'short', 1, call_premium)
        strategy.add_leg('put', strike, 'short', 1, put_premium)
        return strategy

    @staticmethod
    def long_strangle(spot_price: float, call_strike: float, put_strike: float,
                     call_premium: float, put_premium: float) -> OptionsStrategy:
        """
        Long Strangle: Buy OTM call and OTM put
        Similar to straddle but cheaper, needs bigger move
        """
        strategy = OptionsStrategy("Long Strangle", spot_price)
        strategy.add_leg('call', call_strike, 'long', 1, call_premium)
        strategy.add_leg('put', put_strike, 'long', 1, put_premium)
        return strategy

    @staticmethod
    def iron_condor(spot_price: float, put_long_strike: float, put_short_strike: float,
                   call_short_strike: float, call_long_strike: float,
                   put_long_premium: float, put_short_premium: float,
                   call_short_premium: float, call_long_premium: float) -> OptionsStrategy:
        """
        Iron Condor: Combination of bull put spread and bear call spread
        Profits from low volatility, limited risk and reward
        """
        strategy = OptionsStrategy("Iron Condor", spot_price)
        # Bull put spread
        strategy.add_leg('put', put_long_strike, 'long', 1, put_long_premium)
        strategy.add_leg('put', put_short_strike, 'short', 1, put_short_premium)
        # Bear call spread
        strategy.add_leg('call', call_short_strike, 'short', 1, call_short_premium)
        strategy.add_leg('call', call_long_strike, 'long', 1, call_long_premium)
        return strategy

    @staticmethod
    def butterfly_spread(spot_price: float, lower_strike: float,
                        middle_strike: float, upper_strike: float,
                        lower_premium: float, middle_premium: float,
                        upper_premium: float, option_type: str = 'call') -> OptionsStrategy:
        """
        Butterfly Spread: Buy 1 ITM, Sell 2 ATM, Buy 1 OTM
        Profits if stock stays near middle strike
        """
        strategy = OptionsStrategy(f"Butterfly Spread ({option_type.upper()})", spot_price)
        strategy.add_leg(option_type, lower_strike, 'long', 1, lower_premium)
        strategy.add_leg(option_type, middle_strike, 'short', 2, middle_premium)
        strategy.add_leg(option_type, upper_strike, 'long', 1, upper_premium)
        return strategy

    @staticmethod
    def covered_call(spot_price: float, call_strike: float,
                    call_premium: float, stock_quantity: int = 100) -> OptionsStrategy:
        """
        Covered Call: Own stock + Sell call
        Generate income on existing stock position
        Note: This is simplified - doesn't include stock position in payoff
        """
        strategy = OptionsStrategy("Covered Call", spot_price)
        strategy.add_leg('call', call_strike, 'short', 1, call_premium)
        return strategy

    @staticmethod
    def protective_put(spot_price: float, put_strike: float,
                      put_premium: float) -> OptionsStrategy:
        """
        Protective Put: Own stock + Buy put
        Insurance against downside
        Note: This is simplified - doesn't include stock position in payoff
        """
        strategy = OptionsStrategy("Protective Put", spot_price)
        strategy.add_leg('put', put_strike, 'long', 1, put_premium)
        return strategy

    @staticmethod
    def collar(spot_price: float, put_strike: float, call_strike: float,
              put_premium: float, call_premium: float) -> OptionsStrategy:
        """
        Collar: Own stock + Buy put + Sell call
        Limited protection with capped upside
        """
        strategy = OptionsStrategy("Collar", spot_price)
        strategy.add_leg('put', put_strike, 'long', 1, put_premium)
        strategy.add_leg('call', call_strike, 'short', 1, call_premium)
        return strategy

    @staticmethod
    def ratio_spread(spot_price: float, long_strike: float, short_strike: float,
                    long_premium: float, short_premium: float,
                    option_type: str = 'call', ratio: int = 2) -> OptionsStrategy:
        """
        Ratio Spread: Buy 1 option, Sell multiple options at different strike
        Can be used for various market views
        """
        strategy = OptionsStrategy(f"Ratio Spread ({option_type.upper()} 1:{ratio})", spot_price)
        strategy.add_leg(option_type, long_strike, 'long', 1, long_premium)
        strategy.add_leg(option_type, short_strike, 'short', ratio, short_premium)
        return strategy


def calculate_strategy_greeks(strategy: OptionsStrategy, T: float,
                              sigma: float, r: float = 0.065) -> Dict:
    """
    Calculate total Greeks for an options strategy

    Args:
        strategy: OptionsStrategy instance
        T: Time to expiration (years)
        sigma: Volatility
        r: Risk-free rate

    Returns:
        Dictionary with total Greeks
    """
    total_greeks = {
        'delta': 0,
        'gamma': 0,
        'theta': 0,
        'vega': 0,
        'rho': 0
    }

    greeks_calc = GreeksCalculator()

    for leg in strategy.legs:
        greeks = greeks_calc.calculate_all_greeks(
            strategy.spot_price, leg.strike, T, sigma, leg.option_type, r
        )

        multiplier = leg.quantity * (1 if leg.position == 'long' else -1)

        for greek in total_greeks:
            total_greeks[greek] += greeks[greek] * multiplier

    return total_greeks


if __name__ == "__main__":
    # Example: Bull Call Spread on Nifty
    spot = 18500
    strategy = StrategyBuilder.bull_call_spread(
        spot_price=spot,
        lower_strike=18400,
        upper_strike=18600,
        lower_premium=150,
        upper_premium=75
    )

    # Print summary
    summary = strategy.get_strategy_summary()
    print(f"Strategy: {summary['strategy_name']}")
    print(f"Initial Cost: ₹{summary['initial_cost']:.2f}")
    print(f"Max Profit: ₹{summary['max_profit']:.2f}")
    print(f"Max Loss: ₹{summary['max_loss']:.2f}")
    print(f"Breakeven Points: {[f'₹{be:.2f}' for be in summary['breakeven_points']]}")

    # Plot payoff diagram
    fig = strategy.plot_payoff_diagram()
    # fig.show()  # Uncomment to display
