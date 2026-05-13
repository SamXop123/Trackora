"""Allow ``python3 -m trackora`` from the Trackora project root."""

from trackora.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
