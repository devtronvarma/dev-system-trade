"""
Custom Backtest Configurations

Use this file to define and run your own backtest experiments.
"""

from backtest_framework import (
    BacktestConfig,
    BacktestRunner,
    # All available rule creators:
    create_ewmac_rule,
    create_mr_wings_rule,
    create_breakout_rule,
    create_carry_rule,
    create_accel_rule,
)


# ============================================================================
# YOUR BACKTEST CONFIGURATIONS
# ============================================================================

def run_trend_mr_portfolio():
    """
    Backtest: Trend-following + Mean Reversion on US Equities & Bonds
    """
    print("\n" + "=" * 70)
    print("BACKTEST: TREND + MEAN REVERSION PORTFOLIO")
    print("=" * 70)

    rules = {
        'ewmac_64_256': create_ewmac_rule(64, 256),
        'mr_wings_4': create_mr_wings_rule(4),
    }

    config = BacktestConfig(
        instruments=['SP500', 'NASDAQ', 'US10'],
        trading_rules=rules,
        start_date="2000-01-01",
        percentage_vol_target=15,
        notional_trading_capital=1_000_000,
        base_currency="USD",
    )

    runner = BacktestRunner(config)
    runner.build_system()
    results = runner.run()
    runner.print_results(results)
    runner.plot_results(results, save_path='outputs/trend_mr_portfolio.png')

    return runner, results


def run_multi_timeframe_trend():
    """
    Backtest: Multiple EWMAC timeframes on equities and bonds
    """
    print("\n" + "=" * 70)
    print("BACKTEST: MULTI-TIMEFRAME TREND FOLLOWING")
    print("=" * 70)

    rules = {
        'ewmac_8_32': create_ewmac_rule(8, 32),      # Fast
        'ewmac_16_64': create_ewmac_rule(16, 64),    # Medium
        'ewmac_32_128': create_ewmac_rule(32, 128),  # Slow
        'ewmac_64_256': create_ewmac_rule(64, 256),  # Very slow
    }

    config = BacktestConfig(
        instruments=['SP500', 'US10'],
        trading_rules=rules,
        start_date="2000-01-01",
        percentage_vol_target=20,
        notional_trading_capital=500_000,
        base_currency="USD",
    )

    runner = BacktestRunner(config)
    runner.build_system()
    results = runner.run()
    runner.print_results(results)
    runner.plot_results(results, save_path='outputs/multi_timeframe_trend.png')

    return runner, results


def run_equal_weights_backtest():
    """
    Backtest: Same as first but with equal weights (no optimization)
    """
    print("\n" + "=" * 70)
    print("BACKTEST: EQUAL WEIGHTS (NO ESTIMATION)")
    print("=" * 70)

    rules = {
        'ewmac_64_256': create_ewmac_rule(64, 256),
        'mr_wings_4': create_mr_wings_rule(4),
    }

    config = BacktestConfig(
        instruments=['SP500', 'NASDAQ', 'US10'],
        trading_rules=rules,
        start_date="2000-01-01",
        percentage_vol_target=15,
        notional_trading_capital=1_000_000,
        base_currency="USD",
        use_estimations=False  # Use equal weights everywhere
    )

    runner = BacktestRunner(config)
    runner.build_system()
    results = runner.run()
    runner.print_results(results)
    runner.plot_results(results, save_path='outputs/equal_weights.png')

    return runner, results


def run_custom_date_range():
    """
    Backtest: Custom date range to test specific period
    """
    print("\n" + "=" * 70)
    print("BACKTEST: POST-FINANCIAL CRISIS (2010-2020)")
    print("=" * 70)

    rules = {
        'ewmac_32_128': create_ewmac_rule(32, 128),
        'mr_wings_4': create_mr_wings_rule(4),
    }

    config = BacktestConfig(
        instruments=['SP500', 'US10'],
        trading_rules=rules,
        start_date="2010-01-01",
        end_date="2020-12-31",
        percentage_vol_target=12,
        notional_trading_capital=250_000,
        base_currency="USD",
    )

    runner = BacktestRunner(config)
    runner.build_system()
    results = runner.run()
    runner.print_results(results)
    runner.plot_results(results, save_path='outputs/post_crisis.png')

    return runner, results


def run_mixed_rule_types():
    """
    Backtest: Mix different rule types - trend, breakout, mean reversion, acceleration
    """
    print("\n" + "=" * 70)
    print("BACKTEST: MIXED STRATEGY TYPES")
    print("=" * 70)

    rules = {
        'ewmac_64_256': create_ewmac_rule(64, 256),    # Trend following
        'breakout_80': create_breakout_rule(80),        # Breakout
        'mr_wings_4': create_mr_wings_rule(4),          # Mean reversion
        'accel_4': create_accel_rule(4),                # Acceleration
    }

    config = BacktestConfig(
        instruments=['SP500', 'NASDAQ', 'US10'],
        trading_rules=rules,
        start_date="2000-01-01",
        percentage_vol_target=18,
        notional_trading_capital=1_000_000,
        base_currency="USD",
    )

    runner = BacktestRunner(config)
    runner.build_system()
    results = runner.run()
    runner.print_results(results)
    runner.plot_results(results, save_path='outputs/mixed_strategies.png')

    return runner, results


# ============================================================================
# RUN YOUR BACKTESTS
# ============================================================================

if __name__ == "__main__":
    # Uncomment the backtests you want to run:

    # Run the trend + mean reversion portfolio
    runner1, results1 = run_trend_mr_portfolio()

    # Run multi-timeframe trend following
    # runner2, results2 = run_multi_timeframe_trend()

    # Run with equal weights instead of optimization
    # runner3, results3 = run_equal_weights_backtest()

    # Run for specific date range
    # runner4, results4 = run_custom_date_range()

    print("\n" + "=" * 70)
    print("BACKTESTS COMPLETED")
    print("=" * 70)