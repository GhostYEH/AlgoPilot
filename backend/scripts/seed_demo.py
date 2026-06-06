"""Compatibility entrypoint for A3 demo data seeding.

Run:
    python -m scripts.seed_demo
"""

from scripts.seed_a3_demo_data import main


if __name__ == "__main__":
    raise SystemExit(main())
