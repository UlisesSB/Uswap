# Contributing to USwap

Thanks for helping! Bug reports, ideas, translations and pull requests are all welcome.

## Before you start

* Search existing issues first.
* For large changes (new engine, new mode) open an issue to discuss the approach.
* Project principles: **minimal, fast, keyboard-first, offline**. No GUI toolkits, no emoji, no network calls.

## Setup

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). In short: `pip install -e ".[dev]"`, then `pytest` and `ruff check .`.

## Pull requests

1. Branch from `main`.
2. Keep changes focused; add or update tests.
3. `ruff check .` and `pytest` must pass.
4. New user-facing text goes in **both** `uswap/locales/en.json` and `es.json`.
5. Add a line to `CHANGELOG.md` under *Unreleased*.
6. Describe what you changed and how you tested it, including the OS.

## Reporting bugs

Include: OS and terminal, Python version, `uswap --version`, the output of `uswap --doctor`, the exact command, and the error message.

## Code style

Python 3.10+, type hints where they help, `ruff` formatting (line length 100). Engines must never raise into the UI; return a `ConversionResult` instead.

## Conduct

Be respectful and constructive. Harassment of any kind is not tolerated.
