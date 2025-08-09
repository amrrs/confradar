from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich import box
from readchar import readkey, key as rkey

from .core import Conference, filter_conferences, load_conferences
from .storage import load_stars, save_stars
from .sources import refresh_sources


@dataclass
class TuiState:
    conferences: List[Conference]
    cursor: int = 0
    offset: int = 0  # top index of the viewport
    topic_filter: Optional[str] = None
    country_filter: Optional[str] = None
    starred: set[str] = None

    def apply_filters(self) -> List[Conference]:
        return filter_conferences(
            self.conferences,
            topic=self.topic_filter,
            country=self.country_filter,
        )


HELP = """
↑/↓: Move  PgUp/PgDn/Space: Page  Home/End: Jump  Enter: Open  f: Star  t: Topic  c: Country  x: Clear  r: Refresh  q: Quit
"""


def render(state: TuiState, console: Console | None = None) -> Panel:
    console = console or Console()
    filtered = state.apply_filters()

    # Determine page size based on terminal height (rough estimate)
    height = console.size.height if console.size else 24
    # Reserve rows for borders, title, header, subtitle
    page_size = max(5, height - 10)
    total = len(filtered)

    # Clamp offset so cursor is visible
    if state.cursor < state.offset:
        state.offset = state.cursor
    if state.cursor >= state.offset + page_size:
        state.offset = max(0, state.cursor - page_size + 1)
    state.offset = max(0, min(state.offset, max(total - page_size, 0)))

    start = state.offset
    end = min(start + page_size, total)

    table = Table(box=box.SIMPLE_HEAVY, expand=True)
    table.add_column(" ", no_wrap=True)
    table.add_column("Dates", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Location", style="magenta")
    table.add_column("Topics", style="green")

    for global_idx in range(start, end):
        c = filtered[global_idx]
        dates = f"{c.start_dt():%Y-%m-%d} → {c.end_dt():%Y-%m-%d}"
        loc = f"{c.city}, {c.country}"
        topics = ", ".join(c.topics)
        is_cursor = global_idx == state.cursor
        is_star = c.name in state.starred
        cursor_cell = ("➤" if is_cursor else " ") + ("★" if is_star else " ")
        style = "reverse" if is_cursor else ""
        table.add_row(cursor_cell, dates, c.name, loc, topics, style=style)

    range_str = f"{start + 1 if total else 0}–{end} of {total}"
    subtitle = f"{range_str}    Filters: topic=[{state.topic_filter or '-'}] country=[{state.country_filter or '-'}]  |  {HELP.strip()}"
    return Panel(table, title="Confradar TUI", subtitle=subtitle, border_style="bright_blue")


def _open_url(url: str) -> None:
    import webbrowser

    try:
        webbrowser.open_new_tab(url)
    except Exception:
        pass


def run_tui(console: Console | None = None) -> None:
    console = console or Console()
    state = TuiState(conferences=load_conferences(), starred=load_stars())

    with Live(render(state, console), console=console, refresh_per_second=30, screen=True) as live:
        while True:
            ch = readkey()
            items = state.apply_filters()
            if ch in {"q", "Q"}:
                save_stars(state.starred or set())
                return
            if ch in {rkey.UP, "k", "K"}:
                state.cursor = max(0, state.cursor - 1)
            elif ch in {rkey.DOWN, "j", "J"}:
                state.cursor = min(max(len(items) - 1, 0), state.cursor + 1)
            elif ch in {rkey.PAGE_UP, "b", "B"}:
                height = console.size.height if console.size else 24
                page = max(5, height - 10)
                state.cursor = max(0, state.cursor - page)
            elif ch in {rkey.PAGE_DOWN, " ", "f", "F"}:
                height = console.size.height if console.size else 24
                page = max(5, height - 10)
                state.cursor = min(max(len(items) - 1, 0), state.cursor + page)
            elif ch in {rkey.HOME, "g"}:
                state.cursor = 0
            elif ch in {rkey.END, "G"}:
                state.cursor = max(len(items) - 1, 0)
            elif ch in {rkey.ENTER, "\r", "\n", "o", "O"} and items:
                _open_url(items[state.cursor].url)
            elif ch in {"t", "T"}:
                console.print("Enter topic (blank to cancel): ", end="")
                t = console.input("")
                state.topic_filter = t or None
                state.cursor = 0
            elif ch in {"c", "C"}:
                console.print("Enter country (blank to cancel): ", end="")
                c = console.input("")
                state.country_filter = c or None
                state.cursor = 0
            elif ch in {"x", "X"}:
                state.topic_filter = None
                state.country_filter = None
                state.cursor = 0
            elif ch in {"*"} and items:
                name = items[state.cursor].name
                if name in (state.starred or set()):
                    state.starred.remove(name)
                else:
                    if state.starred is None:
                        state.starred = set()
                    state.starred.add(name)
            elif ch in {"r", "R"}:
                # Refresh sources and reload list
                try:
                    refresh_sources()
                except Exception:
                    pass
                state.conferences = load_conferences()
                state.cursor = 0
            live.update(render(state, console))


