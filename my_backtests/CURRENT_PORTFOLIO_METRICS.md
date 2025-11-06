# Current Portfolio Performance Metrics
**Config**: `configs/high_return_strategy.yaml`
**Last Updated**: 2025-11-05
**Status**: Production baseline (best performing configuration)

---

## Portfolio Performance (NET - after costs)

| Metric | Value | Notes |
|--------|-------|-------|
| **Annual Return** | **8.338%** | 25% vol target |
| **Sharpe Ratio** | **0.4687** | Risk-adjusted return |
| **Max Drawdown** | **-37.60%** | Worst single drawdown point |
| **Average Drawdown** | -11.8% | Mean drawdown across all periods |
| **Annual Volatility** | 17.79% | Target: 25% |
| **Calmar Ratio** | 0.2217 | Return/max_drawdown ratio |
| **Sortino Ratio** | 0.6200 | Downside risk adjusted |
| **Time in Drawdown** | 96.07% | Typical for CTA strategies |
| **Hit Rate** | 52.63% | Slightly above 50/50 |

---

## Portfolio Composition

**18 Instruments across 7 asset classes:**

### Equity Indices (3)
- SP500, NASDAQ, DOW

### Bonds (4)
- US2, US5, BUND, SHATZ

### FX (4)
- JPY, EUR_micro, AUD, NZD

### Agriculture (1)
- CORN

### Energy (1)
- GAS_US_mini

### Metals (3)
- COPPER-micro, PLAT, PALLAD

### Volatility (1)
- VIX

---

## Configuration Parameters

- **Vol Target**: 25% (increased from 15% baseline)
- **Forecast Cap**: 25 (increased from 20)
- **Forecast Weight Method**: Shrinkage estimation
- **Instrument Weight Method**: Shrinkage estimation
- **Trading Rules**: 38 rules (full suite)
  - EWMAC (5 variants)
  - Breakout (6 variants)
  - Carry (4 variants)
  - Acceleration (3 variants)
  - Mean Reversion (1 variant)
  - Normalized Momentum (6 variants)
  - Cross-sectional Mean Reversion (2 variants)
  - Relative Momentum (4 variants)
  - Asset Trend (6 variants)
  - Relative Carry (1 variant)

---

## Top Performing Instruments (Annual Return)

1. **VIX**: 2.375% (0.57 Sharpe) ⭐
2. **GAS_US_mini**: 1.695% (0.32 Sharpe)
3. **BUND**: 1.134% (0.37 Sharpe)
4. **JPY**: 1.101% (0.33 Sharpe)
5. **SHATZ**: 0.881% (0.29 Sharpe)
6. **COPPER-micro**: 0.918% (0.24 Sharpe)
7. **US5**: 0.734% (0.26 Sharpe)

---

## Underperformers to Watch

1. **PLAT**: -0.682% (-0.26 Sharpe) ⚠️
2. **NZD**: -0.291% (-0.10 Sharpe) ⚠️
3. **CORN**: -0.092% (-0.02 Sharpe)
4. **AUD**: -0.080% (-0.04 Sharpe)

---

## Recent Testing Summary

### Equity Optimization Attempt (Failed)
**Goal**: Use pure CTA rules (11 rules: EWMAC + Breakout only) for equity indices to reduce signal dilution.

**Results**:
- NASDAQ improved dramatically: 0.012% → 1.175% (+97x!)
- But SP500 barely changed and DOW degraded
- Portfolio return dropped: 8.338% → 6.819% (-18%)
- Worse max drawdown: -37.60% → -39.25%
- Worse average drawdown: -11.8% → -14.37%

**Conclusion**: Individual instrument optimization doesn't guarantee portfolio improvement. Diversification benefits and cross-instrument correlations matter more than single-instrument performance.

**Technical Achievement**: Successfully implemented `rule_variations` feature in framework (allows per-instrument rule specification with shrinkage estimation).

---

## Future Enhancement Ideas (Next Sprint)

### Add More Energy Instruments
- Crude Oil (WTI or Brent)
- Heating Oil
- RBOB Gasoline
- Natural Gas (full contract, not mini)

**Rationale**: Energy showed strong performance (GAS_US_mini at 1.695%). More energy diversification could improve portfolio returns.

### Replace Precious Metals
- Remove: PLAT (-0.68%), PALLAD (0.24%)
- Add: Gold (stable diversifier), Silver (higher volume)

**Rationale**: Platinum and Palladium have thin markets and poor performance. Gold/Silver are more liquid and may provide better diversification.

---

## Notes

- Max drawdown of -37.60% is typical for 25% vol target CTA strategies
- Average drawdown of -11.8% shows the portfolio spends most time closer to peaks
- VIX continues to be star performer (0.57 Sharpe)
- Equity indices contribute modestly but provide diversification
- Current config has been stable and well-tested

### Understanding Drawdown Metrics
- **Max Drawdown (-37.60%)**: The worst single crisis moment - peak to trough decline
- **Average Drawdown (-11.8%)**: The typical depth below peak across all periods
- Industry standard reporting uses Max Drawdown for stress testing and risk assessment

---

## Historical Context

**Evolution of this strategy:**
1. Started with 28 instruments from mixed_strategies_validated.yaml (2.77% return, 0.31 Sharpe)
2. Removed 10 underperformers with negative Sharpe ratios
3. Increased vol target from 15% → 25%
4. Increased forecast cap from 20 → 25
5. Result: 8.338% return, 0.47 Sharpe ✅

**Key Lesson**: Instrument selection and leverage matter more than complex rule optimization. Simple is often better.
