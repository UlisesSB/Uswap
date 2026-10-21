"""Allow `python -m uswap`."""

import sys

from uswap.cli import main

if __name__ == "__main__":
    sys.exit(main())
