# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

Python package for systematic futures trading and backtesting (package name: `pysystemtrade`). Code is organized into layered modules for data access, domain objects, trading system logic, execution/broker adapters, and production orchestration. Tests are driven with pytest (including doctests) and formatting is enforced with Black.

## Setup

- Python: >= 3.10
- Install (dev mode with test/format tools):
  - macOS/Linux: `python -m pip install --upgrade pip setuptools && python -m pip install --editable '.[dev]'`
  - Standard install (no dev tools): `python -m pip install .`

## Common commands

- Format (Black 23.11.0): `python -m pip install black==23.11.0 && black .`
- Pre-commit (optional): `pre-commit run -a`
  - Note: The repo has a `.pre-commit-config.yaml` using Black; prefer Black 23.11.0 to match CI/pyproject.
- Run all tests (quick suite): `pytest`
  - Pytest is configured via `pyproject.toml` to also run doctests across modules.
- Run slow tests: `pytest --runslow`
- Run a single test file: `pytest systems/tests/test_portfolio.py`
- Run a single test function: `pytest systems/tests/test_portfolio.py::test_position_sizing`
- Generate JUnit XML (as CI does): `pytest --junit-xml=tests.xml`

CI reference (GitHub Actions):
- Lint: Black 23.11.0 (`.github/workflows/lint.yml`)
- Quick tests: `pip install '.[dev]' && pytest` (`.github/workflows/quick-test.yml`)
- Slow tests (scheduled): `pip install '.[dev]' && pytest --runslow` (`.github/workflows/slow-test.yml`)
- OS matrix sanity: `pip install .` (`.github/workflows/os-test.yml`)

## High-level architecture

Big picture data-flow and module responsibilities (avoid enumerating files; focus on boundaries and how components interact):

- sysdata (data access layer)
  - Unified interfaces to read/write market data, prices, rolls, positions, config, etc.
  - Multiple backends: CSV, Parquet, MongoDB, and Arctic (see subpackages `csv/`, `parquet/`, `mongodb/`, `arctic/`).
  - Configuration lives under `sysdata/config/` (e.g., `defaults.yaml`, `production_config.py`, `private_config.py`).

- sysobjects (domain objects)
  - Core domain models for instruments, contracts, trading hours, prices, rolls, spreads, positions, and production state objects.
  - Provides typed structures used across systems and execution.

- systems (trading system logic)
  - End-to-end system components: forecasting, combining forecasts, buffering, position sizing, portfolio/risk, staging and cache.
  - `systems/provided/` contains ready-made example systems and YAML configs (e.g., classic/dynamic systems, example configs, rule libraries).
  - `systems/accounts/` provides account curves and order-simulator logic used in backtesting.

- sysexecution (order generation and execution)
  - Algorithms and order stacks to translate target positions into broker orders, with sampling/cancellation checks and fills handling.

- sysbrokers (broker adapters)
  - Broker-agnostic interfaces and an Interactive Brokers implementation under `sysbrokers/IB/` (clients, contracts, positions, prices, trading hours, commissions).

- sysproduction (orchestration and reporting)
  - Command-line entry scripts and utilities to run production workflows: daily updates, strategy order generation, reporting, backups.
  - Reporting modules under `sysproduction/reporting/` produce metrics and operational reports.

- sysinit (initialization and ETL)
  - Scripts and functions to seed and transform data stores (e.g., build roll calendars, import prices, clone data, conversions between stores).

- syscontrol (process control & monitoring)
  - Monitoring, timers, control configuration (`syscontrol/control_config.yaml`), and utilities to run/report long-lived processes.

- syscore (shared/core utilities)
  - Cross-cutting utilities: date/time, math, caching, text, pandas helpers, interactive utilities, exceptions, file I/O.

- syslogging / syslogdiag (logging)
  - Logging configuration and helpers (YAML configs for prod/sim), email alerting, and log routing.

- Ancillary folders
  - docs/: User and operator docs (installation, data, IB, backtesting, production).
  - examples/: Minimal runnable examples and scripts for data and systems.
  - dashboard/: Simple Flask app entry (`dashboard/app.py`).
  - my_backtests/: Local backtesting harness, configs, and scripts to run or compare backtests.
  - tests/: Top-level tests plus per-package `tests/` directories (pytest discovers based on `pyproject.toml::[tool.pytest.ini_options]`).

## Pytest configuration highlights (`pyproject.toml`)

- Doctests are enabled for modules (`--doctest-modules`).
- Default `testpaths` target core packages: `syscore/pandas`, `syscore/tests`, `sysdata/config`, `sysdata/tests`, `sysinit/futures/tests`, `systems/tests`, `sysobjects/production`, `sysobjects/tests`, `sysquant/optimisation`, and top-level `tests/`.
- Logging is enabled during tests with a consistent format and timestamp.

## Formatting and style

- Black is required at version 23.11.0 (see `[tool.black]` in `pyproject.toml` and CI). Line length 88, target Python 3.10.

## Notes

- `setup.py` and `tox.ini` are kept for legacy compatibility; prefer `pip install .` / `pip install '.[dev]'` and `pytest` per `pyproject.toml` and CI workflows.
- Some functionality (e.g., MongoDB/Arctic backends) requires the corresponding services; these are not exercised by the default test suite unless you target those modules explicitly.
