"""
Generalized Backtesting Framework for pysystemtrade

This module provides a flexible framework for backtesting trading strategies
with multiple instruments and rules.

IMPORTANT: Configuration System
================================
This framework properly handles pysystemtrade's configuration inheritance.
When you create a Config() object, it automatically loads all default settings
from sysdata/config/defaults.yaml, including:
- Optimizer functions (func parameter)
- Cost constraints (ceiling_cost_SR, cost_multiplier)
- Estimator configurations (correlation, mean, volatility)

The framework MODIFIES these defaults rather than REPLACING them. This is
critical - replacing config dicts will cause KeyError: 'func' and similar errors.

Correct approach (used here):
    my_config.instrument_weight_estimate["method"] = "shrinkage"

Incorrect approach (will break):
    my_config.instrument_weight_estimate = dict(method="shrinkage")
"""

import matplotlib.pyplot as plt
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from sysdata.config.configdata import Config
from systems.basesystem import System
from systems.rawdata import RawData
from systems.forecasting import Rules
from systems.forecast_scale_cap import ForecastScaleCap
from systems.forecast_combine import ForecastCombine
from systems.positionsizing import PositionSizing
from systems.portfolio import Portfolios
from systems.accounts.accounts_stage import Account
from systems.trading_rules import TradingRule

# Import all provided rules
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults as ewmac
from systems.provided.rules.mr_wings import mr_wings
from systems.provided.rules.carry import carry
from systems.provided.rules.breakout import breakout
from systems.provided.rules.accel import accel
from systems.provided.rules.rel_mom import relative_momentum
from systems.provided.rules.cs_mr import cross_sectional_mean_reversion
from systems.provided.rules.factors import factor_trading_rule, conditioned_factor_trading_rule


class BacktestConfig:
    """
    Configuration class for backtest parameters.

    This makes it easy to modify backtest settings without changing the core logic.
    """

    def __init__(
        self,
        instruments,
        trading_rules,
        start_date="2000-01-01",
        end_date=None,
        percentage_vol_target=15,
        notional_trading_capital=1_000_000,
        base_currency="USD",
        forecast_scalar_pooling=False,
        forecast_weight_method="shrinkage",
        instrument_weight_method="shrinkage",
        use_estimations=True
    ):
        """
        Initialize backtest configuration.

        Args:
            instruments: List of instrument codes (e.g., ['SP500', 'US10'])
            trading_rules: Dict of {rule_name: TradingRule} objects
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD), None = use all available
            percentage_vol_target: Annual volatility target (%)
            notional_trading_capital: Starting capital
            base_currency: Currency code (USD, GBP, etc.)
            forecast_scalar_pooling: Whether to pool forecast scalars across instruments
            forecast_weight_method: Method for forecast weight estimation
            instrument_weight_method: Method for instrument weight estimation
            use_estimations: If False, uses equal weights everywhere
        """
        self.instruments = instruments
        self.trading_rules = trading_rules
        self.start_date = start_date
        self.end_date = end_date
        self.percentage_vol_target = percentage_vol_target
        self.notional_trading_capital = notional_trading_capital
        self.base_currency = base_currency
        self.forecast_scalar_pooling = forecast_scalar_pooling
        self.forecast_weight_method = forecast_weight_method
        self.instrument_weight_method = instrument_weight_method
        self.use_estimations = use_estimations


class BacktestRunner:
    """
    Main class for running backtests with the configured parameters.
    """

    def __init__(self, config: BacktestConfig):
        """
        Initialize the backtest runner.

        Args:
            config: BacktestConfig object with all settings
        """
        self.config = config
        self.data = csvFuturesSimData()
        self.system = None

    def build_system(self):
        """
        Build the complete trading system with all stages.

        Returns:
            Configured System object
        """
        # Create config object
        my_config = Config()
        my_config.instruments = self.config.instruments
        my_config.start_date = self.config.start_date
        if self.config.end_date:
            my_config.end_date = self.config.end_date

        # Add trading rules
        my_config.trading_rules = self.config.trading_rules

        # Position sizing parameters
        my_config.percentage_vol_target = self.config.percentage_vol_target
        my_config.notional_trading_capital = self.config.notional_trading_capital
        my_config.base_currency = self.config.base_currency

        # Instantiate stages
        raw_data = RawData()
        rules = Rules()
        forecast_scale_cap = ForecastScaleCap()
        forecast_combine = ForecastCombine()
        position_sizing = PositionSizing()
        portfolio = Portfolios()
        account = Account()

        # Create initial system to populate config
        self.system = System(
            [account, portfolio, position_sizing, forecast_combine,
             forecast_scale_cap, rules, raw_data],
            self.data,
            my_config
        )

        # Configure estimation settings
        if self.config.use_estimations:
            # Forecast scaling
            my_config.use_forecast_scale_estimates = True
            my_config.forecast_scalar_estimate["pool_instruments"] = self.config.forecast_scalar_pooling

            # Forecast combining - use full optimizer configuration
            my_config.use_forecast_weight_estimates = True
            # Start with defaults from config, then override method
            my_config.forecast_weight_estimate["method"] = self.config.forecast_weight_method
            # Keep the default date_method from defaults.yaml (expanding)
            my_config.use_forecast_div_mult_estimates = True

            # Portfolio/Instrument level - use full optimizer configuration
            my_config.use_instrument_weight_estimates = True
            # Start with defaults from config, then override method
            my_config.instrument_weight_estimate["method"] = self.config.instrument_weight_method
            # Keep the default date_method from defaults.yaml (expanding)
            my_config.use_instrument_div_mult_estimates = True
        else:
            # Use equal weights everywhere
            my_config.use_forecast_scale_estimates = True
            my_config.forecast_scalar_estimate["pool_instruments"] = True

            my_config.use_forecast_weight_estimates = True
            my_config.forecast_weight_estimate["method"] = "equal_weights"
            my_config.use_forecast_div_mult_estimates = False
            my_config.forecast_div_multiplier = 1.0

            my_config.use_instrument_weight_estimates = True
            my_config.instrument_weight_estimate["method"] = "equal_weights"
            my_config.use_instrument_div_mult_estimates = False
            my_config.instrument_div_multiplier = 1.0

        return self.system

    def run(self):
        """
        Run the backtest and return results.

        Returns:
            Portfolio returns object
        """
        if self.system is None:
            self.build_system()

        return self.system.accounts.portfolio()

    def print_results(self, portfolio_returns):
        """
        Print formatted backtest results.

        Args:
            portfolio_returns: Returns object from system.accounts.portfolio()
        """
        print("=" * 70)
        print("BACKTEST CONFIGURATION")
        print("=" * 70)
        print(f"Instruments: {', '.join(self.config.instruments)}")
        print(f"Trading Rules: {', '.join(self.config.trading_rules.keys())}")
        print(f"Period: {self.config.start_date} to {self.config.end_date or 'latest'}")
        print(f"Vol Target: {self.config.percentage_vol_target}%")
        print(f"Capital: ${self.config.notional_trading_capital:,.0f} {self.config.base_currency}")

        print("\n" + "=" * 70)
        print("PORTFOLIO PERFORMANCE (GROSS - before costs)")
        print("=" * 70)
        print(portfolio_returns.gross.percent.stats())

        print("\n" + "=" * 70)
        print("PORTFOLIO PERFORMANCE (NET - after costs)")
        print("=" * 70)
        print(portfolio_returns.net.percent.stats())

        print("\n" + "=" * 70)
        print("PER-INSTRUMENT PERFORMANCE (NET)")
        print("=" * 70)
        for instrument in self.config.instruments:
            print(f"\n{instrument}:")
            inst_returns = self.system.accounts.pandl_for_instrument(instrument)
            print(inst_returns.percent.stats())

    def plot_results(self, portfolio_returns, save_path=None):
        """
        Plot backtest results.

        Args:
            portfolio_returns: Returns object from system.accounts.portfolio()
            save_path: Optional path to save figure (e.g., 'backtest_results.png')
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Cumulative returns
        portfolio_returns.gross.percent.curve().plot(
            ax=ax1, label='Gross Returns', linewidth=2
        )
        portfolio_returns.net.percent.curve().plot(
            ax=ax1, label='Net Returns', linewidth=2
        )
        ax1.set_title(
            f'Portfolio Cumulative Returns\n'
            f'{", ".join(self.config.instruments)} | '
            f'{", ".join(self.config.trading_rules.keys())}',
            fontsize=12, fontweight='bold'
        )
        ax1.set_ylabel('Cumulative Return (%)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Drawdown
        drawdown = portfolio_returns.net.percent.drawdown()
        drawdown.plot(ax=ax2, color='red', linewidth=2)
        ax2.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)
        ax2.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\nPlot saved to: {save_path}")

        plt.show()


# ============================================================================
# HELPER FUNCTIONS FOR CREATING TRADING RULES
# ============================================================================

def create_ewmac_rule(Lfast, Lslow):
    """
    Create an EWMAC (Exponentially Weighted Moving Average Crossover) trading rule.

    This is a trend-following rule that generates buy signals when fast MA > slow MA.

    Args:
        Lfast: Fast moving average period (e.g., 8, 16, 32, 64)
        Lslow: Slow moving average period (e.g., 32, 64, 128, 256)

    Returns:
        TradingRule object

    Common configurations:
        - Fast: (8, 32) or (16, 64)
        - Medium: (32, 128)
        - Slow: (64, 256)
    """
    return TradingRule(dict(
        function=ewmac,
        other_args=dict(Lfast=Lfast, Lslow=Lslow)
    ))


def create_mr_wings_rule(Lfast=4):
    """
    Create a Mean Reversion Wings rule.

    This rule fades extreme moves (buys dips, sells rallies) based on EWMAC extremes.

    Args:
        Lfast: Fast period (slow = Lfast * 4). Default is 4.

    Returns:
        TradingRule object

    Common configurations:
        - Aggressive: Lfast=2
        - Standard: Lfast=4
        - Conservative: Lfast=8
    """
    return TradingRule(dict(
        function=mr_wings,
        data=["data.daily_prices", "rawdata.daily_returns_volatility"],
        other_args=dict(Lfast=Lfast)
    ))


def create_breakout_rule(lookback=20, smooth=None):
    """
    Create a Breakout trading rule (Donchian Channel style).

    Goes long when price breaks above recent highs, short when below recent lows.

    Args:
        lookback: Lookback period for high/low (e.g., 10, 20, 40, 80, 160, 320)
        smooth: Smoothing period (default: lookback/4)

    Returns:
        TradingRule object

    Common configurations:
        - Fast: lookback=20
        - Medium: lookback=40 or 80
        - Slow: lookback=160 or 320
    """
    other_args = dict(lookback=lookback)
    if smooth is not None:
        other_args['smooth'] = smooth

    return TradingRule(dict(
        function=breakout,
        data=["data.daily_prices"],
        other_args=other_args
    ))


def create_carry_rule(smooth_days=90):
    """
    Create a Carry trading rule.

    Buys high carry (positive roll yield), sells low carry.
    Only works for futures with roll data.

    Args:
        smooth_days: Smoothing period for carry signal (default: 90)

    Returns:
        TradingRule object

    Note: Requires raw_carry data - only applicable to futures contracts
    """
    return TradingRule(dict(
        function=carry,
        data=["rawdata.raw_carry"],
        other_args=dict(smooth_days=smooth_days)
    ))


def create_accel_rule(Lfast=4):
    """
    Create an Acceleration rule.

    Measures the change in trend (acceleration/deceleration of price momentum).

    Args:
        Lfast: Fast period (slow = Lfast * 4). Default is 4.

    Returns:
        TradingRule object

    Common configurations:
        - Fast: Lfast=2
        - Standard: Lfast=4
        - Slow: Lfast=8
    """
    return TradingRule(dict(
        function=accel,
        data=["data.daily_prices", "rawdata.daily_returns_volatility"],
        other_args=dict(Lfast=Lfast)
    ))


def create_instrument_specific_rules(instruments, rule_configs):
    """
    Create rules that apply only to specific instruments.

    Args:
        instruments: List of instrument codes
        rule_configs: Dict of {instrument: {rule_name: TradingRule}}

    Returns:
        Dict of combined rules with instrument-specific naming

    Example:
        rule_configs = {
            'SP500': {'ewmac_fast': create_ewmac_rule(16, 64)},
            'US10': {'ewmac_slow': create_ewmac_rule(64, 256)}
        }
    """
    combined_rules = {}

    for instrument, rules in rule_configs.items():
        for rule_name, rule in rules.items():
            # Create instrument-specific rule name
            specific_name = f"{instrument}_{rule_name}"
            combined_rules[specific_name] = rule

    return combined_rules


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Simple multi-strategy backtest
    print("=" * 70)
    print("EXAMPLE 1: TREND + MEAN REVERSION ON EQUITIES & BONDS")
    print("=" * 70)

    # Define trading rules
    rules = {
        'ewmac_64_256': create_ewmac_rule(64, 256),
        'mr_wings_4': create_mr_wings_rule(4),
    }

    # Create configuration
    config = BacktestConfig(
        instruments=['SP500', 'NASDAQ', 'US10'],
        trading_rules=rules,
        start_date="2000-01-01",
        percentage_vol_target=15,
        notional_trading_capital=1_000_000,
        base_currency="USD",
        use_estimations=True
    )

    # Run backtest
    runner = BacktestRunner(config)
    runner.build_system()
    results = runner.run()

    # Display results
    runner.print_results(results)
    runner.plot_results(results, save_path='example1_results.png')

    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: MULTIPLE EWMAC VARIATIONS")
    print("=" * 70)

    # Multiple variations of same rule
    rules2 = {
        'ewmac_8_32': create_ewmac_rule(8, 32),
        'ewmac_16_64': create_ewmac_rule(16, 64),
        'ewmac_32_128': create_ewmac_rule(32, 128),
        'ewmac_64_256': create_ewmac_rule(64, 256),
    }

    config2 = BacktestConfig(
        instruments=['SP500', 'US10'],
        trading_rules=rules2,
        start_date="2000-01-01",
        percentage_vol_target=20,
        notional_trading_capital=500_000,
        base_currency="USD"
    )

    runner2 = BacktestRunner(config2)
    runner2.build_system()
    results2 = runner2.run()

    runner2.print_results(results2)
    runner2.plot_results(results2, save_path='example2_results.png')
