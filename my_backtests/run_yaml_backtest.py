#!/usr/bin/env python3
"""
CLI Tool for Running YAML-Based Backtests

This script allows you to run backtests from YAML configuration files.
It provides a clean command-line interface for single or batch backtest execution.

Usage:
    # Run a single backtest
    python run_yaml_backtest.py configs/trend_mr_portfolio.yaml

    # Run multiple backtests
    python run_yaml_backtest.py configs/trend_mr_portfolio.yaml configs/mixed_strategies.yaml

    # Run all backtests in a directory
    python run_yaml_backtest.py configs/*.yaml

    # Run with custom options
    python run_yaml_backtest.py configs/trend_mr_portfolio.yaml --no-plot --export-stats
"""

import argparse
import sys
from pathlib import Path
from typing import List
import time

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from backtest_framework import BacktestRunner
from yaml_config_loader import load_backtest_from_yaml


def run_single_backtest(
    config_path: str,
    show_plot: bool = True,
    export_stats: bool = None,
    generate_html: bool = False,
    verbose: bool = True
) -> tuple:
    """
    Run a single backtest from a YAML configuration file.

    Args:
        config_path: Path to YAML config file
        show_plot: Whether to display plots interactively
        export_stats: Override YAML setting for stats export (None = use YAML setting)
        generate_html: Generate QuantStats HTML report
        verbose: Print detailed output

    Returns:
        Tuple of (runner, results, success)
    """
    try:
        if verbose:
            print(f"\n{'=' * 70}")
            print(f"Loading configuration: {config_path}")
            print('=' * 70)

        # Load configuration from YAML
        config, metadata, output_settings = load_backtest_from_yaml(config_path)

        if verbose:
            print(f"\n{metadata['name']}")
            if metadata['description']:
                print(f"{metadata['description']}")
            print(f"\nInstruments: {', '.join(config.instruments)}")
            print(f"Rules: {', '.join(config.trading_rules.keys())}")
            print(f"Period: {config.start_date} to {config.end_date or 'latest'}")
            print(f"Vol Target: {config.percentage_vol_target}%")
            print(f"Capital: ${config.notional_trading_capital:,.0f}")

        # Create runner and build system
        start_time = time.time()
        runner = BacktestRunner(config)

        if verbose:
            print("\nBuilding system...")
        runner.build_system()

        # Run backtest
        if verbose:
            print("Running backtest...")
        results = runner.run()

        elapsed_time = time.time() - start_time
        if verbose:
            print(f"✓ Backtest completed in {elapsed_time:.1f} seconds")

        # Print results
        if verbose:
            runner.print_results(results)

        # Handle output settings
        output_dir = Path(output_settings.get('output_dir', 'outputs'))
        output_dir.mkdir(parents=True, exist_ok=True)

        # Plot results
        plot_filename = output_settings.get('plot_filename')
        if plot_filename:
            plot_path = output_dir / plot_filename
            runner.plot_results(results, save_path=str(plot_path), show_plot=show_plot)
        elif show_plot:
            runner.plot_results(results)

        # Export stats
        should_export = export_stats if export_stats is not None else output_settings.get('export_stats', False)
        if should_export:
            stats_filename = output_settings.get('stats_filename', 'backtest_stats.csv')
            stats_path = output_dir / stats_filename
            runner.export_stats_to_csv(results, str(stats_path))

        # Generate HTML report
        if generate_html:
            config_name = Path(config_path).stem
            html_path = output_dir / f"{config_name}_quantstats.html"
            runner.generate_quantstats_report(
                results,
                output_path=str(html_path),
                title=metadata['name']
            )

        return runner, results, True

    except Exception as e:
        print(f"\n✗ Error running backtest: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return None, None, False


def run_batch_backtests(
    config_paths: List[str],
    show_plot: bool = True,
    export_stats: bool = None,
    generate_html: bool = False,
    verbose: bool = True
) -> dict:
    """
    Run multiple backtests from a list of YAML configuration files.

    Args:
        config_paths: List of paths to YAML config files
        show_plot: Whether to display plots interactively
        export_stats: Override YAML setting for stats export
        generate_html: Generate QuantStats HTML reports
        verbose: Print detailed output

    Returns:
        Dictionary with results summary
    """
    print(f"\n{'=' * 70}")
    print(f"BATCH BACKTEST EXECUTION")
    print(f"Running {len(config_paths)} backtest(s)")
    print('=' * 70)

    results_summary = {
        'total': len(config_paths),
        'successful': 0,
        'failed': 0,
        'results': []
    }

    start_time = time.time()

    for i, config_path in enumerate(config_paths, 1):
        print(f"\n[{i}/{len(config_paths)}] Processing: {config_path}")

        runner, results, success = run_single_backtest(
            config_path,
            show_plot=show_plot,
            export_stats=export_stats,
            generate_html=generate_html,
            verbose=verbose
        )

        if success:
            results_summary['successful'] += 1
            results_summary['results'].append({
                'config': config_path,
                'status': 'success',
                'runner': runner,
                'results': results
            })
        else:
            results_summary['failed'] += 1
            results_summary['results'].append({
                'config': config_path,
                'status': 'failed'
            })

    total_time = time.time() - start_time

    # Print summary
    print(f"\n{'=' * 70}")
    print("BATCH EXECUTION SUMMARY")
    print('=' * 70)
    print(f"Total: {results_summary['total']}")
    print(f"Successful: {results_summary['successful']}")
    print(f"Failed: {results_summary['failed']}")
    print(f"Total Time: {total_time:.1f} seconds")
    print('=' * 70)

    return results_summary


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description='Run backtests from YAML configuration files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a single backtest
  %(prog)s configs/trend_mr_portfolio.yaml

  # Run multiple backtests
  %(prog)s configs/trend_mr_portfolio.yaml configs/mixed_strategies.yaml

  # Run without showing plots
  %(prog)s configs/trend_mr_portfolio.yaml --no-plot

  # Export statistics to CSV
  %(prog)s configs/trend_mr_portfolio.yaml --export-stats

  # Quiet mode (less verbose output)
  %(prog)s configs/trend_mr_portfolio.yaml --quiet
        """
    )

    parser.add_argument(
        'config_files',
        nargs='+',
        help='Path(s) to YAML configuration file(s)'
    )

    parser.add_argument(
        '--no-plot',
        action='store_true',
        help='Do not display plots interactively (still saves if configured in YAML)'
    )

    parser.add_argument(
        '--export-stats',
        action='store_true',
        help='Export statistics to CSV (overrides YAML setting)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate QuantStats HTML report(s)'
    )

    args = parser.parse_args()

    # Resolve file paths and handle wildcards
    config_paths = []
    for pattern in args.config_files:
        pattern_path = Path(pattern)
        if pattern_path.exists() and pattern_path.is_file():
            config_paths.append(str(pattern_path))
        else:
            # Try glob pattern
            matches = list(Path.cwd().glob(pattern))
            config_paths.extend([str(p) for p in matches if p.is_file()])

    if not config_paths:
        print("Error: No valid configuration files found")
        sys.exit(1)

    # Run backtest(s)
    show_plot = not args.no_plot
    export_stats = args.export_stats if args.export_stats else None
    generate_html = args.html
    verbose = not args.quiet

    if len(config_paths) == 1:
        # Single backtest
        runner, results, success = run_single_backtest(
            config_paths[0],
            show_plot=show_plot,
            export_stats=export_stats,
            generate_html=generate_html,
            verbose=verbose
        )
        sys.exit(0 if success else 1)
    else:
        # Batch backtests
        summary = run_batch_backtests(
            config_paths,
            show_plot=show_plot,
            export_stats=export_stats,
            generate_html=generate_html,
            verbose=verbose
        )
        sys.exit(0 if summary['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
