#!/usr/bin/env python3
"""
Batch Backtest Comparison Tool

This script runs multiple backtests and generates comparison reports.
Useful for comparing different strategies, parameter sets, or instrument combinations.

Usage:
    # Compare all configs in a directory
    python batch_compare.py configs/

    # Compare specific configs
    python batch_compare.py configs/trend_mr_portfolio.yaml configs/equal_weights_test.yaml

    # Generate comparison report
    python batch_compare.py configs/ --output comparison_report.html
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))

from backtest_framework import BacktestRunner, QUANTSTATS_AVAILABLE
from yaml_config_loader import load_backtest_from_yaml

if QUANTSTATS_AVAILABLE:
    import quantstats as qs


class BacktestComparator:
    """
    Runs multiple backtests and compares their performance.
    """

    def __init__(self):
        self.results = []
        self.comparison_df: Optional[pd.DataFrame] = None

    def run_backtests(self, config_paths: List[str], verbose: bool = True):
        """
        Run multiple backtests and collect results.

        Args:
            config_paths: List of YAML config file paths
            verbose: Print progress information
        """
        print(f"\n{'=' * 70}")
        print(f"BATCH COMPARISON: Running {len(config_paths)} backtests")
        print('=' * 70)

        for i, config_path in enumerate(config_paths, 1):
            try:
                if verbose:
                    print(f"\n[{i}/{len(config_paths)}] Running: {config_path}")

                # Load config
                config, metadata, _ = load_backtest_from_yaml(config_path)

                # Run backtest
                runner = BacktestRunner(config)
                runner.build_system()
                portfolio = runner.run()

                # Extract key statistics
                stats = portfolio.net.percent.stats()

                self.results.append({
                    'name': metadata['name'],
                    'config_path': config_path,
                    'runner': runner,
                    'portfolio': portfolio,
                    'stats': stats,
                    'instruments': config.instruments,
                    'rules': list(config.trading_rules.keys()),
                })

                if verbose:
                    print(f"  ✓ Sharpe: {stats['sharpe']:.2f} | Ann. Return: {stats['ann_mean']:.2%}")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue

        if verbose:
            print(f"\n✓ Completed {len(self.results)}/{len(config_paths)} backtests")

    def create_comparison_table(self) -> pd.DataFrame:
        """
        Create a comparison table of key metrics across all backtests.

        Returns:
            DataFrame with comparison metrics
        """
        if not self.results:
            raise ValueError("No results to compare. Run backtests first.")

        # Define metrics to compare
        metrics = [
            'sharpe',
            'ann_mean',
            'ann_std',
            'max_drawdown',
            'calmar',
            'sortino',
            'avg_drawdown',
            'skew',
        ]

        # Build comparison dictionary
        comparison_data = {}

        for result in self.results:
            name = result['name']
            stats = result['stats']

            comparison_data[name] = {
                metric: stats.get(metric, None)
                for metric in metrics
            }

            # Add custom fields
            comparison_data[name]['instruments'] = ', '.join(result['instruments'][:3]) + \
                                                   ('...' if len(result['instruments']) > 3 else '')
            comparison_data[name]['num_rules'] = len(result['rules'])

        # Convert to DataFrame
        self.comparison_df = pd.DataFrame(comparison_data).T

        # Reorder columns
        first_cols = ['instruments', 'num_rules']
        other_cols = [col for col in self.comparison_df.columns if col not in first_cols]
        self.comparison_df = self.comparison_df[first_cols + other_cols]

        return self.comparison_df

    def print_comparison_table(self):
        """Print formatted comparison table to console."""
        if self.comparison_df is None:
            self.create_comparison_table()

        print(f"\n{'=' * 70}")
        print("PERFORMANCE COMPARISON")
        print('=' * 70)
        print(self.comparison_df.to_string())
        print('=' * 70)

    def plot_comparison(self, save_path: str = None, show_plot: bool = True):
        """
        Create comparison plots for all backtests.

        Args:
            save_path: Optional path to save the figure
            show_plot: Whether to display the plot
        """
        if not self.results:
            raise ValueError("No results to plot")

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Plot 1: Cumulative returns
        ax1 = axes[0, 0]
        for result in self.results:
            curve = result['portfolio'].net.percent.curve()
            curve.plot(ax=ax1, label=result['name'], linewidth=2)
        ax1.set_title('Cumulative Returns Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cumulative Return (%)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Sharpe Ratio comparison
        ax2 = axes[0, 1]
        names = [r['name'] for r in self.results]
        sharpes = [r['stats']['sharpe'] for r in self.results]
        colors = ['green' if s > 0 else 'red' for s in sharpes]
        ax2.barh(names, sharpes, color=colors, alpha=0.7)
        ax2.set_title('Sharpe Ratio Comparison', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Sharpe Ratio')
        ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax2.grid(True, alpha=0.3, axis='x')

        # Plot 3: Drawdown comparison
        ax3 = axes[1, 0]
        for result in self.results:
            dd = result['portfolio'].net.percent.drawdown()
            dd.plot(ax=ax3, label=result['name'], linewidth=2, alpha=0.7)
        ax3.set_title('Drawdown Comparison', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Drawdown (%)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Plot 4: Risk-Return scatter
        ax4 = axes[1, 1]
        returns = [r['stats']['ann_mean'] * 100 for r in self.results]
        volatilities = [r['stats']['ann_std'] * 100 for r in self.results]
        ax4.scatter(volatilities, returns, s=200, alpha=0.6)
        for i, result in enumerate(self.results):
            ax4.annotate(
                result['name'],
                (volatilities[i], returns[i]),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=9
            )
        ax4.set_title('Risk-Return Profile', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Annual Volatility (%)')
        ax4.set_ylabel('Annual Return (%)')
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\nComparison plot saved to: {save_path}")

        if show_plot:
            plt.show()
        else:
            plt.close(fig)

    def export_comparison_csv(self, csv_path: str):
        """
        Export comparison table to CSV.

        Args:
            csv_path: Path to save CSV file
        """
        if self.comparison_df is None:
            self.create_comparison_table()

        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        self.comparison_df.to_csv(csv_path)
        print(f"\nComparison table exported to: {csv_path}")

    def generate_html_reports(self, output_dir: str = "outputs/reports"):
        """
        Generate individual QuantStats HTML reports for each backtest.

        Args:
            output_dir: Directory to save HTML reports

        Returns:
            List of generated report paths
        """
        if not QUANTSTATS_AVAILABLE:
            print("⚠️  QuantStats not available. Install with: pip install quantstats")
            return []

        if not self.results:
            raise ValueError("No results to generate reports for")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        report_paths = []

        print(f"\n{'=' * 70}")
        print("GENERATING QUANTSTATS HTML REPORTS")
        print('=' * 70)

        for i, result in enumerate(self.results, 1):
            name = result['name']
            safe_name = name.replace(' ', '_').replace('/', '_')
            report_file = output_path / f"{safe_name}.html"

            print(f"\n[{i}/{len(self.results)}] Generating report for: {name}")

            try:
                result['runner'].generate_quantstats_report(
                    result['portfolio'],
                    output_path=str(report_file),
                    title=name
                )
                report_paths.append(str(report_file))
            except Exception as e:
                print(f"  ✗ Error generating report: {e}")
                continue

        print(f"\n{'=' * 70}")
        print(f"✓ Generated {len(report_paths)} HTML reports in: {output_dir}")
        print('=' * 70)

        return report_paths


def main():
    """Main entry point for the batch comparison tool."""
    parser = argparse.ArgumentParser(
        description='Compare multiple backtest configurations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'configs',
        nargs='+',
        help='YAML config file(s) or directory containing configs'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Output file for comparison plot (e.g., comparison.png)'
    )

    parser.add_argument(
        '--csv',
        help='Export comparison table to CSV'
    )

    parser.add_argument(
        '--no-plot',
        action='store_true',
        help='Do not display plots'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate individual QuantStats HTML reports for each backtest'
    )

    parser.add_argument(
        '--html-dir',
        default='outputs/reports',
        help='Directory for HTML reports (default: outputs/reports)'
    )

    args = parser.parse_args()

    # Resolve config paths
    config_paths = []
    for path_str in args.configs:
        path = Path(path_str)

        if path.is_file() and path.suffix in ['.yaml', '.yml']:
            config_paths.append(str(path))
        elif path.is_dir():
            # Add all YAML files in directory
            config_paths.extend([
                str(p) for p in path.glob('*.yaml')
            ])
            config_paths.extend([
                str(p) for p in path.glob('*.yml')
            ])

    if not config_paths:
        print("Error: No valid configuration files found")
        sys.exit(1)

    # Create comparator and run backtests
    comparator = BacktestComparator()
    comparator.run_backtests(config_paths, verbose=not args.quiet)

    if not comparator.results:
        print("Error: No successful backtests to compare")
        sys.exit(1)

    # Print comparison table
    comparator.print_comparison_table()

    # Export to CSV if requested
    if args.csv:
        comparator.export_comparison_csv(args.csv)

    # Plot comparison
    show_plot = not args.no_plot
    plot_path = args.output if args.output else 'outputs/backtest_comparison.png'

    comparator.plot_comparison(save_path=plot_path, show_plot=show_plot)

    # Generate HTML reports if requested
    if args.html:
        comparator.generate_html_reports(output_dir=args.html_dir)

    print(f"\n{'=' * 70}")
    print("Comparison complete!")
    print('=' * 70)


if __name__ == "__main__":
    main()
