from __future__ import annotations

import json
from typing import List, Optional
import sys
from importlib import resources

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from .storage import (
    load_user_conferences,
    save_user_conferences,
    load_stars,
    save_stars,
)
from .tui import run_tui
from .core import Conference, load_conferences, filter_conferences
from .sources import refresh_sources
from .storage import load_sources, save_sources

app = typer.Typer(add_completion=False, help="Confradar - your radar for upcoming conferences")
console = Console()



# --------------------------- Data model and IO ---------------------------


def filter_conferences(
    items: Iterable[Conference],
    *,
    topic: Optional[str] = None,
    country: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
) -> List[Conference]:
    result = list(items)
    if topic:
        t = topic.lower()
        result = [c for c in result if any(t in s.lower() for s in c.topics) or t in c.name.lower()]
    if country:
        ctry = country.lower()
        result = [c for c in result if ctry in c.country.lower()]
    if after:
        after_dt = datetime.fromisoformat(after)
        result = [c for c in result if c.end_dt() >= after_dt]
    if before:
        before_dt = datetime.fromisoformat(before)
        result = [c for c in result if c.start_dt() <= before_dt]
    return sorted(result, key=lambda c: c.start_dt())


# ------------------------------- Rendering -------------------------------
def render_list(confs: List[Conference]) -> None:
    table = Table(title="Upcoming Conferences", box=box.SIMPLE_HEAVY)
    table.add_column("Dates", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Location", style="magenta")
    table.add_column("Topics", style="green")
    table.add_column("URL", style="blue", overflow="fold")

    for c in confs:
        date_str = f"{c.start_dt():%Y-%m-%d} → {c.end_dt():%Y-%m-%d}"
        loc = f"{c.city}, {c.country}"
        topics_str = ", ".join(c.topics)
        table.add_row(date_str, c.name, loc, topics_str, c.url)

    console.print(table)


def render_hero() -> None:
    console.print(
        Panel.fit(
            "[bold white]Confradar[/] — your radar for upcoming [cyan]tech conferences[/]",
            subtitle="Type a command or choose an option",
            border_style="bright_blue",
        )
    )


# --------------------------------- CLI ----------------------------------
@app.command("list")
def cmd_list(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Filter by topic keyword"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Filter by country"),
    after: Optional[str] = typer.Option(None, help="Include conferences ending on/after this ISO date (YYYY-MM-DD)"),
    before: Optional[str] = typer.Option(None, help="Include conferences starting on/before this ISO date (YYYY-MM-DD)"),
) -> None:
    """List upcoming conferences with optional filters."""
    confs = filter_conferences(load_conferences(), topic=topic, country=country, after=after, before=before)
    if not confs:
        console.print("[yellow]No conferences matched your filters.[/]")
        raise typer.Exit(code=0)
    render_list(confs)


@app.command("show")
def cmd_show(name: str = typer.Argument(..., help="Exact or partial conference name")) -> None:
    confs = load_conferences()
    matches = [c for c in confs if name.lower() in c.name.lower()]
    if not matches:
        console.print(f"[red]No conference found matching[/] '{name}'.")
        raise typer.Exit(code=1)
    for c in matches:
        console.rule(f"[bold]{c.name}")
        console.print(f"[cyan]Dates:[/] {c.start_dt():%Y-%m-%d} → {c.end_dt():%Y-%m-%d}")
        console.print(f"[magenta]Location:[/] {c.city}, {c.country}")
        console.print(f"[green]Topics:[/] {', '.join(c.topics)}")
        console.print(f"[blue]URL:[/] {c.url}\n")


@app.command("interactive")
def cmd_interactive() -> None:
    """Launch an interactive TUI with keyboard navigation and stars."""
    run_tui(console)


@app.command("add")
def cmd_add(
    name: str = typer.Argument(..., help="Conference name"),
    start_date: str = typer.Option(..., help="Start date YYYY-MM-DD"),
    end_date: str = typer.Option(..., help="End date YYYY-MM-DD"),
    city: str = typer.Option(..., help="City"),
    country: str = typer.Option(..., help="Country"),
    url: str = typer.Option(..., help="URL"),
    topics: str = typer.Option("", help="Comma-separated topics"),
) -> None:
    """Add a custom conference to your local library (persisted)."""
    topics_list = [t.strip() for t in topics.split(",") if t.strip()] or []
    existing = load_user_conferences()
    existing.append(
        {
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "city": city,
            "country": country,
            "url": url,
            "topics": topics_list,
        }
    )
    save_user_conferences(existing)
    console.print("[green]Added.[/]")


@app.command("star")
def cmd_star(name: str = typer.Argument(..., help="Conference name to star")) -> None:
    stars = load_stars()
    stars.add(name)
    save_stars(stars)
    console.print(f"Starred [bold]{name}[/]")


@app.command("unstar")
def cmd_unstar(name: str = typer.Argument(..., help="Conference name to unstar")) -> None:
    stars = load_stars()
    if name in stars:
        stars.remove(name)
        save_stars(stars)
        console.print(f"Unstarred [bold]{name}[/]")
    else:
        console.print(f"[yellow]{name} was not starred[/]")


@app.command("refresh")
def cmd_refresh() -> None:
    """Refresh remote sources and update the local cache."""
    count = refresh_sources()
    console.print(f"[green]Fetched {count} conferences from sources.[/]")


@app.command("sources")
def cmd_sources(
    action: str = typer.Argument(..., help="Action: add|list|remove|reset"),
    value: str = typer.Argument(None, help="For add: URL or file path; for remove: index (0-based)")
) -> None:
    """Manage data sources. Supports JSON URLs and local JSON files."""
    action = action.lower()
    sources = load_sources()
    if action == "list":
        if not sources:
            console.print("[yellow]No sources configured.[/]")
            return
        for i, s in enumerate(sources):
            console.print(f"[{i}] {s}")
        return
    if action == "add":
        if not value:
            console.print("[red]Provide a URL or path.[/]")
            raise typer.Exit(2)
        if value.startswith("http://") or value.startswith("https://"):
            sources.append({"type": "json", "url": value})
        else:
            sources.append({"type": "file-json", "path": value})
        save_sources(sources)
        console.print("[green]Source added.[/]")
        return
    if action == "remove":
        if value is None or not value.isdigit():
            console.print("[red]Provide the index to remove.[/]")
            raise typer.Exit(2)
        idx = int(value)
        try:
            removed = sources.pop(idx)
        except IndexError:
            console.print("[red]Invalid index.[/]")
            raise typer.Exit(2)
        save_sources(sources)
        console.print(f"[green]Removed {removed}[/]")
        return
    if action == "reset":
        # Reset to curated defaults
        try:
            with resources.files("confradar.data").joinpath("default_sources.json").open("r", encoding="utf-8") as f:
                defaults = json.load(f)
            save_sources(defaults)
            console.print("[green]Sources reset to curated defaults.[/]")
        except Exception:
            console.print("[red]Failed to reset sources.[/]")
        return
    console.print("[red]Unknown action. Use add|list|remove|reset.[/]")


def main() -> None:  # entry point
    # Avoid forcing interactive mode when invoked with no args in non-interactive contexts
    if len(sys.argv) == 1 and sys.stdin.isatty():
        cmd_interactive()
    else:
        app()


if __name__ == "__main__":
    main()


