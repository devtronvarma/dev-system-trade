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
import pandas as pd
from pathlib import Path
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

try:
    import quantstats as qs
    QUANTSTATS_AVAILABLE = True

    # Monkey-patch QuantStats to fix pandas 2.x compatibility issues
    # Replace 'ME' with 'M' in the stats module
    import quantstats.stats as qs_stats
    if hasattr(qs_stats, 'gain_to_pain_ratio'):
        _original_gain_to_pain = qs_stats.gain_to_pain_ratio

        def _patched_gain_to_pain(returns, rf=0, resolution='M'):
            """Patched version that uses 'M' instead of 'ME' for pandas 2.x"""
            # Convert ME to M for compatibility
            if resolution == 'ME':
                resolution = 'MS'  # Month Start is more compatible
            return _original_gain_to_pain(returns, rf, resolution)

        qs_stats.gain_to_pain_ratio = _patched_gain_to_pain

except ImportError:
    QUANTSTATS_AVAILABLE = False

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
        use_estimations=True,
        forecast_weights=None,
        instrument_weights=None,
        forecast_cap=20.0,
        forecast_div_multiplier=None,
        instrument_div_multiplier=None
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
            forecast_weights: Dict of forecast weights (nested: {instrument: {rule: weight}} or flat: {rule: weight})
            instrument_weights: Dict of instrument weights {instrument: weight}
            forecast_cap: Maximum forecast value (default 20.0, per Rob Carver)
            forecast_div_multiplier: Fixed FDM value (None = estimate from data)
            instrument_div_multiplier: Fixed IDM value (None = estimate from data)
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
        self.forecast_weights = forecast_weights
        self.instrument_weights = instrument_weights
        self.forecast_cap = forecast_cap
        self.forecast_div_multiplier = forecast_div_multiplier
        self.instrument_div_multiplier = instrument_div_multiplier


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

        # Add forecast_weights and instrument_weights if provided
        if self.config.forecast_weights is not None:
            my_config.forecast_weights = self.config.forecast_weights
        if self.config.instrument_weights is not None:
            my_config.instrument_weights = self.config.instrument_weights

        # Forecast cap (Rob Carver uses 20)
        my_config.forecast_cap = self.config.forecast_cap

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

            # FDM (Forecast Diversification Multiplier)
            if self.config.forecast_div_multiplier is not None:
                # User provided a fixed FDM value
                my_config.use_forecast_div_mult_estimates = False
                my_config.forecast_div_multiplier = self.config.forecast_div_multiplier
            else:
                # Estimate FDM from data
                my_config.use_forecast_div_mult_estimates = True

            # Portfolio/Instrument level - use full optimizer configuration
            my_config.use_instrument_weight_estimates = True
            # Start with defaults from config, then override method
            my_config.instrument_weight_estimate["method"] = self.config.instrument_weight_method
            # Keep the default date_method from defaults.yaml (expanding)

            # IDM (Instrument Diversification Multiplier)
            if self.config.instrument_div_multiplier is not None:
                # User provided a fixed IDM value
                my_config.use_instrument_div_mult_estimates = False
                my_config.instrument_div_multiplier = self.config.instrument_div_multiplier
            else:
                # Estimate IDM from data
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

    def plot_results(self, portfolio_returns, save_path=None, show_plot=True):
        """
        Plot backtest results.

        Args:
            portfolio_returns: Returns object from system.accounts.portfolio()
            save_path: Optional path to save figure (e.g., 'backtest_results.png')
            show_plot: Whether to display the plot interactively (default: True)
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

        if show_plot:
            plt.show()
        else:
            plt.close(fig)

    def export_stats_to_csv(self, portfolio_returns, csv_path):
        """
        Export backtest statistics to CSV file.

        Args:
            portfolio_returns: Returns object from system.accounts.portfolio()
            csv_path: Path to save CSV file
        """
        # Create output directory if it doesn't exist
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

        # Get stats for portfolio
        stats_dict = portfolio_returns.net.percent.stats()

        # Convert to DataFrame
        stats_df = pd.DataFrame({
            'Portfolio_Net': stats_dict
        })

        # Add per-instrument stats
        for instrument in self.config.instruments:
            inst_returns = self.system.accounts.pandl_for_instrument(instrument)
            inst_stats = inst_returns.percent.stats()
            stats_df[f'{instrument}_Net'] = inst_stats

        # Transpose so metrics are rows
        stats_df = stats_df.T

        # Save to CSV
        stats_df.to_csv(csv_path)
        print(f"Stats exported to: {csv_path}")

    def _get_returns_series(self, portfolio_returns):
        """
        Extract returns as a pandas Series for QuantStats.

        Args:
            portfolio_returns: Returns object from system.accounts.portfolio()

        Returns:
            pandas Series of net percentage returns
        """
        # The percent object is already a pandas Series-like object
        # It contains percentage returns (not cumulative)
        returns_pct = portfolio_returns.net.percent

        # Convert to pandas Series if needed and convert from percentage to decimal
        if hasattr(returns_pct, 'to_frame'):
            returns = pd.Series(returns_pct.values, index=returns_pct.index)
        else:
            returns = pd.Series(returns_pct)

        # Returns are in percentage form, convert to decimal
        returns = returns / 100.0

        return returns

    def generate_quantstats_report(
        self,
        portfolio_returns,
        output_path,
        benchmark=None,
        title=None
    ):
        """
        Generate a comprehensive QuantStats HTML report.

        Args:
            portfolio_returns: Returns object from system.accounts.portfolio()
            output_path: Path to save HTML report
            benchmark: Optional benchmark returns (pandas Series)
            title: Optional custom title for the report

        Returns:
            Path to generated report
        """
        if not QUANTSTATS_AVAILABLE:
            print("⚠️  QuantStats not available. Install with: pip install quantstats")
            return None

        # Create output directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Get returns series
        returns = self._get_returns_series(portfolio_returns)

        # Set title
        if title is None:
            title = f"Backtest Report: {', '.join(self.config.instruments)}"

        print(f"\nGenerating QuantStats HTML report...")

        try:
            # Try to generate the report using basic mode (fewer metrics, no problematic frequencies)
            qs.reports.html(
                returns,
                benchmark=benchmark,
                output=output_path,
                title=title,
                download_filename=Path(output_path).name,
                periods_per_year=252  # Daily data
            )
            print(f"✓ QuantStats report saved to: {output_path}")
            return output_path

        except (ValueError, KeyError) as e:
            if 'ME' in str(e) or 'frequency' in str(e).lower():
                print(f"⚠️  QuantStats pandas compatibility issue detected.")
                print(f"    Creating simplified HTML report instead...")

                # Generate a simplified report using QuantStats plots
                self._generate_simplified_html_report(
                    returns,
                    output_path,
                    title,
                    benchmark
                )
                return output_path
            else:
                raise

    def _generate_simplified_html_report(
        self,
        returns,
        output_path,
        title,
        benchmark=None
    ):
        """
        Generate a simplified HTML report with key metrics and charts.
        Used as a fallback when QuantStats has pandas compatibility issues.

        Args:
            returns: Decimal returns series (already divided by 100)
            output_path: Path to save HTML
            title: Report title
            benchmark: Optional benchmark returns
        """
        import base64
        from io import BytesIO

        # Get the portfolio_returns object from the runner
        # We need this to use pysystemtrade's built-in calculations
        # Note: This is a bit hacky, but necessary to get accurate stats

        # Convert returns back to percentage for pysystemtrade
        returns_pct = returns * 100

        # Use cumsum for cumulative returns (matches pysystemtrade .curve())
        cum_returns_pct = returns_pct.cumsum()
        total_return_pct = cum_returns_pct.iloc[-1]

        # Calculate drawdown the pysystemtrade way
        # Drawdown = (current cumulative - running max cumulative)
        running_max_pct = cum_returns_pct.expanding().max()
        drawdown_pct = cum_returns_pct - running_max_pct
        max_dd_pct = drawdown_pct.min()

        # Calculate annualized metrics using pysystemtrade's formulas
        # Annual mean = mean of daily returns * 252
        ann_return_pct = returns_pct.mean() * 252

        # Annual std = std of daily returns * sqrt(252)
        ann_vol_pct = returns_pct.std() * (252 ** 0.5)

        # Sharpe = ann_return / ann_vol
        sharpe = ann_return_pct / ann_vol_pct if ann_vol_pct > 0 else 0

        # Create plots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Plot 1: Cumulative returns (using cumsum to match pysystemtrade)
        ax1 = axes[0, 0]
        cum_returns_pct.plot(ax=ax1, label='Strategy')
        if benchmark is not None:
            bench_cum_pct = (benchmark * 100).cumsum()
            bench_cum_pct.plot(ax=ax1, label='Benchmark', alpha=0.7)
        ax1.set_title('Cumulative Returns')
        ax1.set_ylabel('Return (%)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Drawdown
        ax2 = axes[0, 1]
        drawdown_pct.plot(ax=ax2, color='red')
        ax2.set_title('Drawdown')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)
        ax2.fill_between(drawdown_pct.index, drawdown_pct.values, 0, alpha=0.3, color='red')

        # Plot 3: Monthly returns heatmap (simplified)
        ax3 = axes[1, 0]
        monthly = returns.resample('MS').sum()
        monthly.plot(kind='bar', ax=ax3, width=0.8)
        ax3.set_title('Monthly Returns')
        ax3.set_ylabel('Return')
        ax3.grid(True, alpha=0.3, axis='y')

        # Plot 4: Rolling Sharpe
        ax4 = axes[1, 1]
        rolling_sharpe = (returns.rolling(252).mean() / returns.rolling(252).std()) * (252 ** 0.5)
        rolling_sharpe.plot(ax=ax4)
        ax4.axhline(y=0, color='black', linestyle='--', alpha=0.3)
        ax4.set_title('Rolling 252-Day Sharpe Ratio')
        ax4.set_ylabel('Sharpe Ratio')
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)

        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric {{ background: #f9f9f9; padding: 20px; border-radius: 5px; border-left: 4px solid #4CAF50; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .metric-label {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .charts {{ margin-top: 30px; }}
        img {{ max-width: 100%; height: auto; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{total_return_pct:.2f}%</div>
                <div class="metric-label">Total Return</div>
            </div>
            <div class="metric">
                <div class="metric-value">{ann_return_pct:.2f}%</div>
                <div class="metric-label">Annual Return</div>
            </div>
            <div class="metric">
                <div class="metric-value">{ann_vol_pct:.2f}%</div>
                <div class="metric-label">Annual Volatility</div>
            </div>
            <div class="metric">
                <div class="metric-value">{sharpe:.2f}</div>
                <div class="metric-label">Sharpe Ratio</div>
            </div>
            <div class="metric">
                <div class="metric-value">{max_dd_pct:.2f}%</div>
                <div class="metric-label">Max Drawdown</div>
            </div>
        </div>

        <div class="charts">
            <img src="data:image/png;base64,{img_base64}" alt="Performance Charts">
        </div>

        <div class="footer">
            Generated with pysystemtrade YAML Backtesting Framework<br>
            Report created: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

        # Write HTML file
        with open(output_path, 'w') as f:
            f.write(html)

        print(f"✓ Simplified HTML report saved to: {output_path}")

    def generate_quantstats_tearsheet(self, portfolio_returns, benchmark=None):
        """
        Display an interactive QuantStats tearsheet (for Jupyter notebooks).

        Args:
            portfolio_returns: Returns object from system.accounts.portfolio()
            benchmark: Optional benchmark returns (pandas Series)
        """
        if not QUANTSTATS_AVAILABLE:
            print("⚠️  QuantStats not available. Install with: pip install quantstats")
            return

        returns = self._get_returns_series(portfolio_returns)

        # Display interactive tearsheet
        qs.reports.full(returns, benchmark=benchmark)


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
