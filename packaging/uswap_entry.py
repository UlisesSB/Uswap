"""PyInstaller entry point (kept outside the package on purpose)."""

import sys

from uswap.cli import main

if __name__ == "__main__":
    sys.exit(main())
