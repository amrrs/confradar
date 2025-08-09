 # Confradar

 A colorful CLI to explore upcoming tech conferences. Built with Typer and Rich.

## Screenshot

![Confradar TUI](https://raw.githubusercontent.com/amrrs/confradar/main/docs/assets/tui.png)

## Install

- Recommended (no venv hassle):
  ```bash
  pipx install confradar
  # upgrade later
  pipx upgrade confradar
  ```
- Alternative (user site):
  ```bash
  python3 -m pip install --user confradar
  # ensure ~/.local/bin (Linux) or ~/Library/Python/*/bin (macOS) is on PATH
  ```

### Install from GitHub (no venv needed)

- pipx from a Git tag (recommended):
  ```bash
  pipx install "confradar @ git+https://github.com/amrrs/confradar.git@v0.1.0"
  # upgrade later (rebuilds from Git):
  pipx upgrade confradar
  ```
- pipx from main (latest):
  ```bash
  pipx install "confradar @ git+https://github.com/amrrs/confradar.git@main"
  ```
- pip (user site) from Git:
  ```bash
  python3 -m pip install --user "confradar @ git+https://github.com/amrrs/confradar.git@v0.1.0"
  # ensure ~/.local/bin (Linux) or ~/Library/Python/*/bin (macOS) is on PATH
  ```
- Local clone with pipx:
  ```bash
  git clone https://github.com/amrrs/confradar.git
  cd confradar
  pipx install .
  ```

### If `confradar` is not found after pip --user install

Add your user scripts directory to PATH (macOS example for Python 3.9):

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Portable (any OS/Python version):

```bash
USER_BASE="$(python3 -m site --user-base)"
echo 'export PATH="'"$USER_BASE"'/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Using pipx avoids PATH issues:

```bash
pipx ensurepath
```

 ## Quickstart

 ```bash
 # From the project root
 python -m venv .venv && source .venv/bin/activate
 pip install -U pip
 pip install -e .
 confradar --help
 confradar interactive
 ```

## Usage

 - `confradar list` — list conferences
   - Options: `--topic`, `--country`, `--after YYYY-MM-DD`, `--before YYYY-MM-DD`
 - `confradar show "name"` — show details for matching conferences
- `confradar interactive` — full-screen TUI with keyboard navigation
- `confradar add NAME --start-date YYYY-MM-DD --end-date YYYY-MM-DD --city CITY --country COUNTRY --url URL --topics "a,b,c"` — add a local conference (persisted)
- `confradar star NAME` / `confradar unstar NAME` — manage favorites
- `confradar sources list|add <URL-or-path>|remove <index>` — manage refreshable data sources (JSON URL or local JSON file)
- `confradar refresh` — fetch from configured sources and update cache

First run convenience:
- `confradar refresh` seeds sources with the built-in dataset if none configured, so you always get a result.

## Data & Persistence

Ships with a small sample dataset in `confradar/data/conferences.json`. User-added conferences and starred items are saved under your OS data dir (via platformdirs), e.g. `~/Library/Application Support/confradar/` on macOS.

## TUI keys

- Up/Down (or k/j): move one row
- PageUp / PageDown / Space: page
- Home / End: jump to start/end
- Enter / o: open link in browser
- *: star/unstar
- t: set topic filter
- c: set country filter
- r: refresh sources
- x: clear filters
- q: quit

 ## License

 MIT


