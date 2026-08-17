#!/usr/bin/env python3
"""Backward-compatible entry point for the Cyclistic analysis pipeline."""

from __future__ import annotations

from cyclistic.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
