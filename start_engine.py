#!/usr/bin/env python3
"""Pulse AI Discovery Engine — Universal Cross-Platform 1-Click Entrypoint.

Usage:
    python start_engine.py
"""

import sys
import run_engine_24x7

if __name__ == "__main__":
    try:
        run_engine_24x7.main()
    except KeyboardInterrupt:
        print("\nShutdown complete.")
        sys.exit(0)
