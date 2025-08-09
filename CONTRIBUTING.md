## Contributing to Confradar

1. Create a venv and install in editable mode:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -U pip
   pip install -e .[rss]
   ```
2. Run the CLI:
   ```bash
   confradar
   ```
3. Submit PRs with descriptive titles. New commands should have tests where practical.

### Releasing

1. Bump version in `pyproject.toml`.
2. Tag and push: `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. GitHub Actions will build and publish to PyPI using OIDC.


