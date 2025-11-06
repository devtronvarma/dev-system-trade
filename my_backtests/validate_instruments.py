#!/usr/bin/env python
"""
Instrument Data Validator for pysystemtrade Backtests

Validates instrument data quality before running backtests to catch issues like:
- Negative prices (data corruption)
- Insufficient historical data
- Large data gaps
- Extreme outliers
- Stale data

Usage:
    # Standalone
    python validate_instruments.py --config configs/mixed_strategies.yaml

    # Programmatic
    from validate_instruments import validate_instrument_list
    results = validate_instrument_list(instruments, start_date='2000-01-01')
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
import yaml


# ==============================================================================
# CONFIGURATION
# ==============================================================================

class ValidationConfig:
    """Configuration for data validation checks"""

    def __init__(
        self,
        min_start_date: str = "2000-01-01",
        max_gap_days: int = 30,
        min_data_density: float = 0.80,
        max_days_since_last: int = 365,  # Allow up to 1 year old data
        outlier_std_threshold: float = 10.0,  # Relax outlier detection (10 sigma)
        data_dir: Optional[Path] = None
    ):
        self.min_start_date = pd.Timestamp(min_start_date)
        self.max_gap_days = max_gap_days
        self.min_data_density = min_data_density
        self.max_days_since_last = max_days_since_last
        self.outlier_std_threshold = outlier_std_threshold

        # Set data directory
        if data_dir is None:
            # Assume we're in my_backtests/ and data is in ../data/
            script_dir = Path(__file__).parent
            self.data_dir = script_dir.parent / "data" / "futures" / "adjusted_prices_csv"
        else:
            self.data_dir = Path(data_dir)


# ==============================================================================
# VALIDATION CHECKS
# ==============================================================================

class InstrumentValidator:
    """Validates individual instrument data quality"""

    def __init__(self, config: ValidationConfig):
        self.config = config

    def load_instrument_data(self, instrument: str) -> Optional[pd.DataFrame]:
        """Load adjusted price data for an instrument"""
        csv_path = self.config.data_dir / f"{instrument}.csv"

        if not csv_path.exists():
            return None

        try:
            df = pd.read_csv(csv_path, parse_dates=['DATETIME'], index_col='DATETIME')
            return df
        except Exception as e:
            print(f"Error loading {instrument}: {e}")
            return None

    def check_data_exists(self, instrument: str) -> Tuple[bool, str]:
        """Check if data file exists"""
        df = self.load_instrument_data(instrument)
        if df is None:
            return False, f"Data file not found: {self.config.data_dir / instrument}.csv"
        if len(df) == 0:
            return False, "Data file is empty"
        return True, f"Found {len(df):,} price records"

    def check_price_range(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Check for negative prices and extreme outliers"""
        if df is None or len(df) == 0:
            return False, "No data to check"

        prices = df['price']

        # Check for negative prices
        negative_count = (prices < 0).sum()
        if negative_count > 0:
            first_negative = df[prices < 0].index[0]
            return False, f"Found {negative_count} negative prices (first at {first_negative})"

        # Check for extreme outliers (>5 std devs from mean)
        price_changes = prices.pct_change().dropna()
        if len(price_changes) > 0:
            mean_change = price_changes.mean()
            std_change = price_changes.std()
            outliers = price_changes[
                np.abs(price_changes - mean_change) > self.config.outlier_std_threshold * std_change
            ]
            if len(outliers) > 10:  # More than 10 extreme outliers
                return False, f"Found {len(outliers)} extreme price changes (>{self.config.outlier_std_threshold}σ)"

        min_price = prices.min()
        max_price = prices.max()
        return True, f"Price range: [{min_price:.2f}, {max_price:.2f}]"

    def check_data_coverage(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Check if data starts early enough"""
        if df is None or len(df) == 0:
            return False, "No data to check"

        first_date = df.index[0]

        if first_date > self.config.min_start_date:
            missing_days = (first_date - self.config.min_start_date).days
            return False, f"Data starts {first_date.date()} (missing {missing_days} days from {self.config.min_start_date.date()})"

        return True, f"Data starts {first_date.date()} ✓"

    def check_data_continuity(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Check for large gaps in data"""
        if df is None or len(df) == 0:
            return False, "No data to check"

        # Calculate gaps between consecutive dates
        date_diffs = df.index.to_series().diff()
        max_gap = date_diffs.max()

        if max_gap > timedelta(days=self.config.max_gap_days):
            gap_location = date_diffs.idxmax()
            return False, f"Large gap: {max_gap.days} days at {gap_location.date()}"

        # Check overall data density
        date_range = (df.index[-1] - df.index[0]).days
        expected_days = date_range * (5/7)  # Assume 5 trading days per week
        actual_days = len(df)
        density = actual_days / expected_days if expected_days > 0 else 0

        if density < self.config.min_data_density:
            return False, f"Low data density: {density:.1%} (expected >{self.config.min_data_density:.0%})"

        return True, f"Max gap: {max_gap.days} days, density: {density:.1%}"

    def check_recent_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Check if data is recent enough"""
        if df is None or len(df) == 0:
            return False, "No data to check"

        last_date = df.index[-1]
        days_since_last = (pd.Timestamp.now() - last_date).days

        if days_since_last > self.config.max_days_since_last:
            return False, f"Last data: {last_date.date()} ({days_since_last} days old)"

        return True, f"Last data: {last_date.date()} ({days_since_last} days ago)"

    def validate_instrument(self, instrument: str) -> Dict:
        """Run all validation checks on an instrument"""

        result = {
            'instrument': instrument,
            'overall_pass': False,
            'checks': {}
        }

        # Load data once
        df = self.load_instrument_data(instrument)

        # Run all checks
        checks = [
            ('data_exists', lambda: self.check_data_exists(instrument)),
            ('price_range', lambda: self.check_price_range(df)),
            ('data_coverage', lambda: self.check_data_coverage(df)),
            ('data_continuity', lambda: self.check_data_continuity(df)),
            ('recent_data', lambda: self.check_recent_data(df))
        ]

        all_passed = True
        for check_name, check_func in checks:
            passed, message = check_func()
            result['checks'][check_name] = {
                'passed': passed,
                'message': message
            }
            if not passed:
                all_passed = False

        result['overall_pass'] = all_passed

        # Add summary stats
        if df is not None and len(df) > 0:
            result['stats'] = {
                'num_records': len(df),
                'start_date': df.index[0].strftime('%Y-%m-%d'),
                'end_date': df.index[-1].strftime('%Y-%m-%d'),
                'price_min': float(df['price'].min()),
                'price_max': float(df['price'].max())
            }
        else:
            result['stats'] = None

        return result


# ==============================================================================
# REPORT GENERATION
# ==============================================================================

def generate_console_report(results: List[Dict]) -> None:
    """Print validation results to console"""

    print("\n" + "="*80)
    print("INSTRUMENT DATA VALIDATION REPORT")
    print("="*80)

    passed = [r for r in results if r['overall_pass']]
    failed = [r for r in results if not r['overall_pass']]

    print(f"\nSummary: {len(passed)}/{len(results)} instruments passed validation")
    print(f"  ✓ Passed: {len(passed)}")
    print(f"  ✗ Failed: {len(failed)}")

    if failed:
        print("\n" + "-"*80)
        print("FAILED INSTRUMENTS:")
        print("-"*80)

        for r in failed:
            print(f"\n✗ {r['instrument']}")
            for check_name, check_result in r['checks'].items():
                if not check_result['passed']:
                    print(f"    {check_name}: {check_result['message']}")

    if passed:
        print("\n" + "-"*80)
        print(f"PASSED INSTRUMENTS ({len(passed)}):")
        print("-"*80)
        print(", ".join([r['instrument'] for r in passed]))

    print("\n" + "="*80 + "\n")


def generate_csv_report(results: List[Dict], output_path: Path) -> None:
    """Generate CSV report of validation results"""

    rows = []
    for r in results:
        row = {
            'instrument': r['instrument'],
            'overall_pass': r['overall_pass']
        }

        # Add check results
        for check_name, check_result in r['checks'].items():
            row[f'{check_name}_pass'] = check_result['passed']
            row[f'{check_name}_msg'] = check_result['message']

        # Add stats
        if r['stats']:
            row.update(r['stats'])

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"CSV report saved to: {output_path}")


def generate_html_report(results: List[Dict], output_path: Path) -> None:
    """Generate HTML report with visual dashboard"""

    passed = [r for r in results if r['overall_pass']]
    failed = [r for r in results if not r['overall_pass']]

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Instrument Validation Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}
        .stat-card.total {{
            background: #e3f2fd;
            border: 2px solid #2196f3;
        }}
        .stat-card.passed {{
            background: #e8f5e9;
            border: 2px solid #4caf50;
        }}
        .stat-card.failed {{
            background: #ffebee;
            border: 2px solid #f44336;
        }}
        .stat-number {{
            font-size: 48px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #333;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .pass {{
            color: #4caf50;
            font-weight: bold;
        }}
        .fail {{
            color: #f44336;
            font-weight: bold;
        }}
        .check-details {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section-title {{
            font-size: 24px;
            color: #333;
            margin: 20px 0 10px 0;
            border-left: 4px solid #007bff;
            padding-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Instrument Data Validation Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <div class="stat-card total">
                <div class="stat-label">Total Instruments</div>
                <div class="stat-number">{len(results)}</div>
            </div>
            <div class="stat-card passed">
                <div class="stat-label">✓ Passed</div>
                <div class="stat-number">{len(passed)}</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-label">✗ Failed</div>
                <div class="stat-number">{len(failed)}</div>
            </div>
        </div>
"""

    # Failed instruments table
    if failed:
        html += """
        <div class="section">
            <div class="section-title">❌ Failed Instruments</div>
            <table>
                <thead>
                    <tr>
                        <th>Instrument</th>
                        <th>Data Exists</th>
                        <th>Price Range</th>
                        <th>Coverage</th>
                        <th>Continuity</th>
                        <th>Recent Data</th>
                    </tr>
                </thead>
                <tbody>
"""
        for r in failed:
            checks = r['checks']
            html += f"""
                    <tr>
                        <td><strong>{r['instrument']}</strong></td>
"""
            for check_name in ['data_exists', 'price_range', 'data_coverage', 'data_continuity', 'recent_data']:
                check = checks.get(check_name, {})
                status_class = 'pass' if check.get('passed') else 'fail'
                status_symbol = '✓' if check.get('passed') else '✗'
                message = check.get('message', 'N/A')
                html += f"""
                        <td class="{status_class}">
                            {status_symbol}
                            <div class="check-details">{message}</div>
                        </td>
"""
            html += """
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""

    # Passed instruments table
    if passed:
        html += """
        <div class="section">
            <div class="section-title">✅ Passed Instruments</div>
            <table>
                <thead>
                    <tr>
                        <th>Instrument</th>
                        <th>Records</th>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Price Range</th>
                    </tr>
                </thead>
                <tbody>
"""
        for r in passed:
            stats = r.get('stats', {})
            html += f"""
                    <tr>
                        <td><strong>{r['instrument']}</strong></td>
                        <td>{stats.get('num_records', 'N/A'):,}</td>
                        <td>{stats.get('start_date', 'N/A')}</td>
                        <td>{stats.get('end_date', 'N/A')}</td>
                        <td>{stats.get('price_min', 0):.2f} - {stats.get('price_max', 0):.2f}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""

    html += """
    </div>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"HTML report saved to: {output_path}")


# ==============================================================================
# MAIN VALIDATION FUNCTION
# ==============================================================================

def validate_instrument_list(
    instruments: List[str],
    config: Optional[ValidationConfig] = None,
    verbose: bool = True
) -> List[Dict]:
    """
    Validate a list of instruments

    Args:
        instruments: List of instrument codes to validate
        config: ValidationConfig (uses defaults if None)
        verbose: Print progress messages

    Returns:
        List of validation result dictionaries
    """
    if config is None:
        config = ValidationConfig()

    validator = InstrumentValidator(config)
    results = []

    if verbose:
        print(f"\nValidating {len(instruments)} instruments...")
        print(f"Data directory: {config.data_dir}")
        print(f"Minimum start date: {config.min_start_date.date()}\n")

    for i, instrument in enumerate(instruments, 1):
        if verbose:
            print(f"[{i}/{len(instruments)}] Validating {instrument}...", end=' ')

        result = validator.validate_instrument(instrument)
        results.append(result)

        if verbose:
            status = "✓ PASS" if result['overall_pass'] else "✗ FAIL"
            print(status)

    return results


def create_validated_yaml(
    original_yaml_path: Path,
    results: List[Dict],
    output_yaml_path: Path
) -> None:
    """Create a new YAML config with only validated instruments"""

    # Load original YAML
    with open(original_yaml_path) as f:
        config = yaml.safe_load(f)

    # Get passed instruments
    passed_instruments = [r['instrument'] for r in results if r['overall_pass']]

    # Update instrument list
    config['instruments'] = passed_instruments

    # Update forecast_weights to only include passed instruments
    if 'forecast_weights' in config:
        validated_weights = {
            inst: weights
            for inst, weights in config['forecast_weights'].items()
            if inst in passed_instruments
        }
        config['forecast_weights'] = validated_weights

    # Add validation metadata
    config['_validation'] = {
        'validated_at': datetime.now().isoformat(),
        'original_instruments': len(results),
        'validated_instruments': len(passed_instruments),
        'removed_instruments': [r['instrument'] for r in results if not r['overall_pass']]
    }

    # Save new YAML
    with open(output_yaml_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\nValidated config saved to: {output_yaml_path}")
    print(f"  Original: {len(results)} instruments")
    print(f"  Validated: {len(passed_instruments)} instruments")
    print(f"  Removed: {len(results) - len(passed_instruments)} instruments")


# ==============================================================================
# CLI
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validate instrument data quality for backtesting"
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to YAML config file'
    )
    parser.add_argument(
        '--instruments',
        type=str,
        nargs='+',
        help='List of instrument codes to validate'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='2000-01-01',
        help='Minimum required start date (default: 2000-01-01)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        help='Path to data directory (default: ../data/futures/adjusted_prices_csv/)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs',
        help='Output directory for reports (default: outputs/)'
    )
    parser.add_argument(
        '--create-validated-yaml',
        action='store_true',
        help='Create a new YAML config with only validated instruments'
    )

    args = parser.parse_args()

    # Get instruments from config or command line
    instruments = []
    config_path = None

    if args.config:
        config_path = Path(args.config)
        with open(config_path) as f:
            yaml_config = yaml.safe_load(f)
            instruments = yaml_config.get('instruments', [])
    elif args.instruments:
        instruments = args.instruments
    else:
        parser.error("Must provide either --config or --instruments")

    # Create validation config
    validation_config = ValidationConfig(
        min_start_date=args.start_date,
        data_dir=args.data_dir
    )

    # Run validation
    results = validate_instrument_list(
        instruments,
        config=validation_config,
        verbose=True
    )

    # Generate reports
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    generate_console_report(results)
    generate_csv_report(results, output_dir / 'validation_results.csv')
    generate_html_report(results, output_dir / 'validation_report.html')

    # Create validated YAML if requested
    if args.create_validated_yaml and config_path:
        validated_path = config_path.parent / f"{config_path.stem}_validated.yaml"
        create_validated_yaml(config_path, results, validated_path)

    # Exit with error code if any instruments failed
    failed_count = sum(1 for r in results if not r['overall_pass'])
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == '__main__':
    main()
