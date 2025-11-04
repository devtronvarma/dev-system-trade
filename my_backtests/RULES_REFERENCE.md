# Trading Rules Reference

All of Rob Carver's provided trading rules are now available in the backtesting framework.

## Available Rules

### 1. EWMAC - Exponentially Weighted Moving Average Crossover
**Type:** Trend Following
**Function:** `create_ewmac_rule(Lfast, Lslow)`

Goes long when fast MA > slow MA, short when fast MA < slow MA.

**Parameters:**
- `Lfast`: Fast moving average period
- `Lslow`: Slow moving average period (should be > Lfast)

**Common Configurations:**
```python
create_ewmac_rule(8, 32)      # Very fast - catches short-term trends
create_ewmac_rule(16, 64)     # Fast
create_ewmac_rule(32, 128)    # Medium speed
create_ewmac_rule(64, 256)    # Slow - long-term trends only
```

**Best For:** All instruments, especially trending markets

---

### 2. MR Wings - Mean Reversion Wings
**Type:** Mean Reversion
**Function:** `create_mr_wings_rule(Lfast=4)`

Fades extreme moves by going long after big drops, short after big rallies.

**Parameters:**
- `Lfast`: Fast period (slow automatically = Lfast * 4)

**Common Configurations:**
```python
create_mr_wings_rule(2)       # Aggressive - fades smaller moves
create_mr_wings_rule(4)       # Standard (default)
create_mr_wings_rule(8)       # Conservative - only fades major extremes
```

**Best For:** Range-bound markets, pairs well with trend following

---

### 3. Breakout - Donchian Channel
**Type:** Trend Following / Momentum
**Function:** `create_breakout_rule(lookback=20, smooth=None)`

Goes long when price breaks above recent high, short when below recent low.

**Parameters:**
- `lookback`: Lookback period for high/low calculation
- `smooth`: Smoothing period (default: lookback/4)

**Common Configurations:**
```python
create_breakout_rule(20)      # Fast - 1 month lookback
create_breakout_rule(40)      # Medium - 2 months
create_breakout_rule(80)      # Standard - ~4 months
create_breakout_rule(160)     # Slow - ~8 months
create_breakout_rule(320)     # Very slow - ~16 months
```

**Best For:** Strongly trending markets, good complement to EWMAC

---

### 4. Carry
**Type:** Fundamental / Yield
**Function:** `create_carry_rule(smooth_days=90)`

Buys assets with high positive roll yield, sells those with negative roll yield.

**Parameters:**
- `smooth_days`: Smoothing period for carry signal

**Common Configurations:**
```python
create_carry_rule(30)         # Fast - responds quickly to carry changes
create_carry_rule(90)         # Standard (default)
create_carry_rule(180)        # Slow - very stable carry signal
```

**Best For:** Futures contracts with roll data (bonds, commodities, FX)
**Note:** Requires `raw_carry` data - NOT applicable to equity indices like SP500

---

### 5. Acceleration
**Type:** Momentum / Trend Change
**Function:** `create_accel_rule(Lfast=4)`

Measures the change in momentum (acceleration/deceleration of trends).

**Parameters:**
- `Lfast`: Fast period (slow automatically = Lfast * 4)

**Common Configurations:**
```python
create_accel_rule(2)          # Fast - catches quick changes
create_accel_rule(4)          # Standard (default)
create_accel_rule(8)          # Slow - only major accelerations
```

**Best For:** Markets entering or exiting trends, pairs well with EWMAC

---

## Rules NOT Yet Implemented in Helper Functions

The following rules are available but require more complex data inputs. You'll need to create TradingRule objects manually:

### 6. Relative Momentum
Cross-sectional momentum - buys instruments outperforming their asset class.

**Requires:** Normalized prices for instrument AND asset class average

### 7. Cross-Sectional Mean Reversion
Fades relative outperformance within an asset class.

**Requires:** Normalized prices for instrument AND asset class average

### 8. Factor Trading
Generic factor-based trading (value, momentum, quality factors).

**Requires:** Pre-calculated factor values

---

## Combining Rules

### Strategy Types

**Pure Trend Following:**
```python
rules = {
    'ewmac_fast': create_ewmac_rule(16, 64),
    'ewmac_slow': create_ewmac_rule(64, 256),
    'breakout_80': create_breakout_rule(80),
}
```

**Trend + Mean Reversion (Balanced):**
```python
rules = {
    'ewmac_64_256': create_ewmac_rule(64, 256),
    'mr_wings_4': create_mr_wings_rule(4),
}
```

**Multi-Timeframe Trend:**
```python
rules = {
    'ewmac_8_32': create_ewmac_rule(8, 32),
    'ewmac_16_64': create_ewmac_rule(16, 64),
    'ewmac_32_128': create_ewmac_rule(32, 128),
    'ewmac_64_256': create_ewmac_rule(64, 256),
}
```

**Mixed Strategies:**
```python
rules = {
    'ewmac_64_256': create_ewmac_rule(64, 256),     # Trend
    'breakout_80': create_breakout_rule(80),         # Breakout
    'mr_wings_4': create_mr_wings_rule(4),           # Mean reversion
    'accel_4': create_accel_rule(4),                 # Acceleration
}
```

---

## Rule Characteristics

| Rule | Type | Speed | Works Best In | Pairs Well With |
|------|------|-------|---------------|-----------------|
| EWMAC | Trend | Variable | Trending markets | MR Wings, Breakout |
| MR Wings | Mean Rev | Fast | Range-bound | EWMAC, Accel |
| Breakout | Momentum | Variable | Strong trends | EWMAC, Carry |
| Carry | Fundamental | Slow | Stable markets | EWMAC, Breakout |
| Accel | Momentum | Fast | Trend changes | EWMAC, MR Wings |

---

## Tips for Rule Selection

1. **Diversify Strategy Types**: Mix trend-following with mean-reversion
2. **Diversify Speeds**: Use fast and slow versions of the same rule
3. **Consider Market Regime**: Trend rules for trending markets, MR for choppy markets
4. **Don't Over-fit**: More rules isn't always better - stick to 2-5 well-chosen rules
5. **Check Correlation**: Rules that behave similarly won't add much diversification

---

## Example Usage

```python
from backtest_framework import (
    BacktestConfig,
    BacktestRunner,
    create_ewmac_rule,
    create_mr_wings_rule,
    create_breakout_rule,
    create_accel_rule,
)

# Define your rules
rules = {
    'trend_slow': create_ewmac_rule(64, 256),
    'breakout': create_breakout_rule(80),
    'mean_rev': create_mr_wings_rule(4),
}

# Configure backtest
config = BacktestConfig(
    instruments=['SP500', 'US10'],
    trading_rules=rules,
    start_date="2000-01-01",
    percentage_vol_target=15,
    notional_trading_capital=1_000_000,
    base_currency="USD",
)

# Run it
runner = BacktestRunner(config)
runner.build_system()
results = runner.run()
runner.print_results(results)
runner.plot_results(results)
```

---

## Data Requirements

Different rules need different data:

- **Price Only**: EWMAC, Breakout
- **Price + Volatility**: MR Wings, Acceleration
- **Carry Data**: Carry rule (futures only)
- **Cross-Sectional Data**: Relative Momentum, CS Mean Reversion (requires asset class averages)

The framework automatically handles data routing for the implemented helper functions.
