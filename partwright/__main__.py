"""Entry point for `python -m partwright`.

Mirrors the `partwright` console script declared in `pyproject.toml`, so the CLI
can be exercised without installing the package (useful for verification).
"""

from partwright.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
