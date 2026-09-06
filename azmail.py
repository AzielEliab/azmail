"""Shim so `python azmail.py` matches sibling Aziel Eliab products."""

from azmail.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
