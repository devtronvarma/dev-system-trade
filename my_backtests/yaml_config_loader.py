"""
YAML Configuration Loader for Backtests

This module provides functionality to load backtest configurations from YAML files
and convert them into BacktestConfig objects that can be used by the BacktestRunner.

The YAML format provides a clean, declarative way to define backtests without
hardcoding everything in Python.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from backtest_framework import (
    BacktestConfig,
    create_ewmac_rule,
    create_mr_wings_rule,
    create_breakout_rule,
    create_carry_rule,
    create_accel_rule,
    create_normmom_rule,
    create_mrinasset_rule,
)


class YAMLConfigLoader:
    """
    Loads and parses YAML backtest configuration files.

    The loader handles:
    - Trading rule definitions with proper parameter mapping
    - Backtest parameters (dates, capital, risk)
    - Output settings
    - Validation of required fields
    """

    # Map of rule types to their creation functions
    RULE_CREATORS = {
        'ewmac': create_ewmac_rule,
        'mr_wings': create_mr_wings_rule,
        'breakout': create_breakout_rule,
        'carry': create_carry_rule,
        'accel': create_accel_rule,
        'normmom': create_normmom_rule,
        'mrinasset': create_mrinasset_rule,
    }

    def __init__(self, config_path: str):
        """
        Initialize the loader with a YAML config file path.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.raw_config = None
        self._load_yaml()

    def _load_yaml(self):
        """Load and parse the YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.raw_config = yaml.safe_load(f)

        if not self.raw_config:
            raise ValueError(f"Empty or invalid YAML file: {self.config_path}")

    def _create_trading_rule(self, rule_name: str, rule_config: Dict[str, Any]):
        """
        Create a TradingRule object from YAML configuration.

        Args:
            rule_name: Name of the rule (e.g., 'ewmac_64_256')
            rule_config: Dictionary containing rule type and parameters

        Returns:
            TradingRule object
        """
        rule_type = rule_config.get('type')
        if not rule_type:
            raise ValueError(f"Rule '{rule_name}' missing 'type' field")

        if rule_type not in self.RULE_CREATORS:
            raise ValueError(
                f"Unknown rule type '{rule_type}'. "
                f"Available types: {list(self.RULE_CREATORS.keys())}"
            )

        creator_func = self.RULE_CREATORS[rule_type]

        # Extract parameters based on rule type
        if rule_type == 'ewmac':
            Lfast = rule_config.get('Lfast')
            Lslow = rule_config.get('Lslow')
            if Lfast is None or Lslow is None:
                raise ValueError(f"EWMAC rule '{rule_name}' requires Lfast and Lslow")
            return creator_func(Lfast, Lslow)

        elif rule_type == 'mr_wings':
            Lfast = rule_config.get('Lfast', 4)
            return creator_func(Lfast)

        elif rule_type == 'breakout':
            lookback = rule_config.get('lookback')
            if lookback is None:
                raise ValueError(f"Breakout rule '{rule_name}' requires lookback")
            smooth = rule_config.get('smooth')
            return creator_func(lookback, smooth)

        elif rule_type == 'carry':
            smooth_days = rule_config.get('smooth_days', 90)
            return creator_func(smooth_days)

        elif rule_type == 'accel':
            Lfast = rule_config.get('Lfast', 4)
            return creator_func(Lfast)

        elif rule_type == 'normmom':
            Lfast = rule_config.get('Lfast')
            if Lfast is None:
                raise ValueError(f"Normmom rule '{rule_name}' requires Lfast")
            vol_days = rule_config.get('vol_days', 35)
            return creator_func(Lfast, vol_days)

        elif rule_type == 'mrinasset':
            horizon = rule_config.get('horizon')
            if horizon is None:
                raise ValueError(f"MRinasset rule '{rule_name}' requires horizon")
            return creator_func(horizon)

        else:
            # This shouldn't happen given the earlier check, but just in case
            raise ValueError(f"Unhandled rule type: {rule_type}")

    def _parse_trading_rules(self) -> Dict:
        """
        Parse trading rules section from YAML and create TradingRule objects.

        Returns:
            Dictionary of {rule_name: TradingRule}
        """
        rules_config = self.raw_config.get('trading_rules', {})
        if not rules_config:
            raise ValueError("No trading_rules defined in config")

        trading_rules = {}
        for rule_name, rule_params in rules_config.items():
            trading_rules[rule_name] = self._create_trading_rule(rule_name, rule_params)

        return trading_rules

    def _parse_backtest_params(self) -> Dict[str, Any]:
        """
        Parse backtest parameters section from YAML.

        Returns:
            Dictionary of backtest parameters
        """
        backtest_config = self.raw_config.get('backtest', {})

        # Extract parameters with defaults
        params = {
            'start_date': backtest_config.get('start_date', "2000-01-01"),
            'end_date': backtest_config.get('end_date'),
            'percentage_vol_target': backtest_config.get('percentage_vol_target', 15),
            'notional_trading_capital': backtest_config.get('notional_trading_capital', 1_000_000),
            'base_currency': backtest_config.get('base_currency', "USD"),
            'forecast_scalar_pooling': backtest_config.get('forecast_scalar_pooling', False),
            'forecast_weight_method': backtest_config.get('forecast_weight_method', 'shrinkage'),
            'instrument_weight_method': backtest_config.get('instrument_weight_method', 'shrinkage'),
            'use_estimations': backtest_config.get('use_estimations', True),
            'forecast_cap': backtest_config.get('forecast_cap', 20.0),
            'forecast_div_multiplier': backtest_config.get('forecast_div_multiplier'),
            'instrument_div_multiplier': backtest_config.get('instrument_div_multiplier'),
        }

        return params

    def load_config(self) -> BacktestConfig:
        """
        Load and parse the complete YAML config into a BacktestConfig object.

        Returns:
            BacktestConfig object ready to use with BacktestRunner
        """
        # Get instruments
        instruments = self.raw_config.get('instruments', [])
        if not instruments:
            raise ValueError("No instruments defined in config")

        # Parse trading rules
        trading_rules = self._parse_trading_rules()

        # Parse backtest parameters
        params = self._parse_backtest_params()

        # Get forecast_weights and instrument_weights if provided
        # These are optional and will be None if not specified
        forecast_weights = self.raw_config.get('forecast_weights')
        instrument_weights = self.raw_config.get('instrument_weights')

        # Create BacktestConfig
        config = BacktestConfig(
            instruments=instruments,
            trading_rules=trading_rules,
            forecast_weights=forecast_weights,
            instrument_weights=instrument_weights,
            **params
        )

        return config

    def get_metadata(self) -> Dict[str, str]:
        """
        Get metadata about this backtest configuration.

        Returns:
            Dictionary with name, description, etc.
        """
        return {
            'name': self.raw_config.get('name', 'Unnamed Backtest'),
            'description': self.raw_config.get('description', ''),
            'config_file': str(self.config_path),
        }

    def get_output_settings(self) -> Dict[str, Any]:
        """
        Get output settings from YAML config.

        Returns:
            Dictionary with output configuration
        """
        output_config = self.raw_config.get('output', {})

        return {
            'save_results': output_config.get('save_results', True),
            'output_dir': output_config.get('output_dir', 'outputs'),
            'plot_filename': output_config.get('plot_filename'),
            'export_stats': output_config.get('export_stats', False),
            'stats_filename': output_config.get('stats_filename'),
        }


def load_backtest_from_yaml(yaml_path: str) -> tuple[BacktestConfig, Dict[str, Any], Dict[str, Any]]:
    """
    Convenience function to load a backtest configuration from YAML.

    Args:
        yaml_path: Path to YAML configuration file

    Returns:
        Tuple of (BacktestConfig, metadata, output_settings)

    Example:
        >>> config, meta, output = load_backtest_from_yaml('configs/my_backtest.yaml')
        >>> runner = BacktestRunner(config)
        >>> results = runner.run()
    """
    loader = YAMLConfigLoader(yaml_path)
    config = loader.load_config()
    metadata = loader.get_metadata()
    output_settings = loader.get_output_settings()

    return config, metadata, output_settings


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Test loading a YAML config
    config_path = "configs/trend_mr_portfolio.yaml"

    print(f"Loading config from: {config_path}")
    print("=" * 70)

    try:
        config, metadata, output_settings = load_backtest_from_yaml(config_path)

        print(f"\nMetadata:")
        print(f"  Name: {metadata['name']}")
        print(f"  Description: {metadata['description']}")

        print(f"\nConfiguration:")
        print(f"  Instruments: {config.instruments}")
        print(f"  Trading Rules: {list(config.trading_rules.keys())}")
        print(f"  Start Date: {config.start_date}")
        print(f"  Vol Target: {config.percentage_vol_target}%")
        print(f"  Capital: ${config.notional_trading_capital:,.0f}")

        print(f"\nOutput Settings:")
        print(f"  Save Results: {output_settings['save_results']}")
        print(f"  Output Dir: {output_settings['output_dir']}")
        print(f"  Plot File: {output_settings['plot_filename']}")

        print("\n✓ Config loaded successfully!")

    except Exception as e:
        print(f"\n✗ Error loading config: {e}")
        import traceback
        traceback.print_exc()
