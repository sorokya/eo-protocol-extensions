"""
eolib-ext CLI — apply protocol extensions to a forked eolib implementation.

Commands:
  apply     Fetch extensions, merge XML, clone eolib, output a ready-to-build fork.
  list      List extensions available in the official (or custom) registry.
  validate  Check extensions.xml for merge conflicts without cloning the eolib.
"""

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import git
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from .languages import get_target, KNOWN_LANGUAGES
from .merger import MergeError, merge_protocol_file, load_base_elements
from .models import Extension
from .sources import OFFICIAL_REPO, resolve, resolve_extension_files

app = typer.Typer(
    name="eolib-ext",
    help="Apply protocol extensions to a forked eolib implementation.",
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Config parsing
# ---------------------------------------------------------------------------

def parse_extensions_xml(config_path: Path) -> list[Extension]:
    """Parse extensions.xml and return a list of Extension objects."""
    try:
        tree = ET.parse(config_path)
    except (ET.ParseError, FileNotFoundError) as e:
        err_console.print(f"[red]Error:[/red] Cannot read {config_path}: {e}")
        raise typer.Exit(1)

    root = tree.getroot()
    if root.tag != "extensions":
        err_console.print(
            f"[red]Error:[/red] {config_path}: root element must be <extensions>"
        )
        raise typer.Exit(1)

    extensions: list[Extension] = []
    for el in root:
        if el.tag != "extension":
            continue
        ext_type = el.get("type")
        name = el.get("name")
        if not ext_type or not name:
            err_console.print(
                f"[red]Error:[/red] Each <extension> requires 'type' and 'name' attributes."
            )
            raise typer.Exit(1)
        extensions.append(Extension(
            type=ext_type,
            name=name,
            repo=el.get("repo"),
            ref=el.get("ref"),
            path=el.get("path"),
        ))
    return extensions


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

@app.command()
def apply(
    language: str = typer.Option(..., "--language", "-l", help="Target eolib language (rs, ts, java, python, php)"),
    config: Path = typer.Option(Path("extensions.xml"), "--config", "-c", help="Path to extensions.xml"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory (default: ./eolib-<language>-extended)"),
):
    """Fetch extensions, merge XML, and produce a ready-to-build forked eolib."""

    console.rule("[bold]eolib-ext[/bold]")

    # Resolve language
    try:
        target = get_target(language)
    except ValueError as e:
        err_console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)

    output_dir = output or Path(f"./eolib-{language}-extended")
    config_dir = config.parent.resolve()

    console.print(f"  [dim]Language[/dim]   {language}")
    console.print(f"  [dim]Config[/dim]     {config}")
    console.print(f"  [dim]Output[/dim]     {output_dir}")
    console.print()

    # Parse config
    if not config.exists():
        err_console.print(f"[red]Error:[/red] Config file not found: {config}")
        err_console.print("  Create an extensions.xml file or pass --config <path>.")
        raise typer.Exit(1)

    extensions = parse_extensions_xml(config)
    if not extensions:
        err_console.print("[yellow]Warning:[/yellow] No extensions defined in config. Nothing to do.")
        raise typer.Exit(0)

    ext_names = ", ".join(e.name for e in extensions)
    console.print(f"  [dim]Extensions[/dim] {ext_names}\n")

    # Resolve extension sources
    resolved_extensions = []
    with console.status("Fetching extension sources..."):
        for ext in extensions:
            try:
                resolved = resolve(ext, config_dir)
                resolved_extensions.append(resolved)
                repo_label = ext.repo or OFFICIAL_REPO
                ref_label = f" @ {ext.ref}" if ext.ref else ""
                console.print(f"  [green]✓[/green] {ext.name:<20} {repo_label if ext.type == 'git' else ext.path}{ref_label}")
            except ValueError as e:
                console.print(f"  [red]✗[/red] {ext.name}")
                err_console.print(f"\n[red]Error:[/red] {e}")
                raise typer.Exit(1)

    console.print()

    # Clone eolib
    with console.status(f"Cloning {target.repo_url}..."):
        if output_dir.exists():
            shutil.rmtree(output_dir)
        try:
            eolib_repo = git.Repo.clone_from(target.repo_url, output_dir)
            eolib_repo.git.submodule("update", "--init", "--recursive")
        except git.GitCommandError as e:
            err_console.print(f"\n[red]Error:[/red] Failed to clone eolib: {e}")
            raise typer.Exit(1)

    console.print(f"  [green]✓[/green] Cloned {target.repo_url}")
    console.print()

    # Locate base protocol files
    protocol_xml_root = output_dir / "eo-protocol" / "xml"
    if not protocol_xml_root.exists():
        err_console.print(
            f"[red]Error:[/red] Could not find eo-protocol/xml inside cloned eolib at {output_dir}.\n"
            f"  This eolib may not use the standard eo-protocol submodule layout."
        )
        raise typer.Exit(1)

    # Apply extensions
    console.print("  Applying extensions...")
    base_files = sorted(protocol_xml_root.rglob("protocol.xml"))
    base_elements = load_base_elements(base_files)

    all_results = []
    for resolved in resolved_extensions:
        ext_files = resolve_extension_files(resolved)
        try:
            for ext_file in ext_files:
                result = merge_protocol_file(base_elements, ext_file, resolved.name)
                all_results.append(result)
                console.print(f"  [green]✓[/green] {resolved.name:<20} {result.summary()}")
        except MergeError as e:
            console.print(f"  [red]✗[/red] {resolved.name:<20} merge error")
            err_console.print(f"\n[red]Error: Merge failed in extension '{resolved.name}'[/red]\n\n  {e}")
            raise typer.Exit(1)

    console.print()
    console.print(f"  [bold green]Output:[/bold green] {output_dir}/")
    console.print()
    _print_usage_hint(language, output_dir)


def _print_usage_hint(language: str, output_dir: Path) -> None:
    hints = {
        "rs": (
            "To use in your project, add to Cargo.toml:\n\n"
            f"  [dependencies]\n"
            f"  eolib = {{ path = \"{output_dir}\" }}"
        ),
        "ts": (
            "To use in your project, add to package.json:\n\n"
            f'  "dependencies": {{\n'
            f'    "eolib": "file:{output_dir}"\n'
            f'  }}'
        ),
        "python": f"To install locally:\n\n  pip install -e {output_dir}",
        "php": f"To use locally, add to composer.json repositories.",
        "java": f"Build the output directory and add as a local Maven/Gradle dependency.",
    }
    hint = hints.get(language.lower())
    if hint:
        console.print(f"  {hint}")
        console.print()


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

@app.command(name="list")
def list_extensions(
    repo: str = typer.Option(OFFICIAL_REPO, "--repo", "-r", help="Extension registry URL to inspect"),
):
    """List extensions available in the official or a custom registry."""
    from .sources import _cache_path, CACHE_DIR
    import os

    cache = _cache_path(repo)
    with console.status(f"Fetching registry {repo}..."):
        try:
            if cache.exists():
                git_repo = git.Repo(cache)
                git_repo.remotes.origin.fetch()
                git_repo.remotes.origin.pull()
            else:
                cache.parent.mkdir(parents=True, exist_ok=True)
                git_repo = git.Repo.clone_from(repo, cache)
        except git.GitCommandError as e:
            err_console.print(f"[red]Error:[/red] Failed to fetch registry: {e}")
            raise typer.Exit(1)

    extensions_dir = cache / "extensions"
    if not extensions_dir.exists():
        console.print("[yellow]No extensions/ directory found in this registry.[/yellow]")
        raise typer.Exit(0)

    entries = sorted(p for p in extensions_dir.iterdir() if p.is_dir() and not p.name.startswith("."))

    if not entries:
        console.print("[yellow]No extensions found in registry.[/yellow]")
        raise typer.Exit(0)

    table = Table(title=f"Extensions in {repo}", show_header=True)
    table.add_column("Name", style="bold")
    table.add_column("Files")

    for entry in entries:
        file_count = len(list(entry.rglob("protocol.xml")))
        table.add_row(entry.name, f"{file_count} protocol file(s)")

    console.print(table)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

@app.command()
def validate(
    config: Path = typer.Option(Path("extensions.xml"), "--config", "-c", help="Path to extensions.xml"),
    protocol_dir: Optional[Path] = typer.Option(None, "--protocol-dir", "-p", help="Path to base protocol xml/ directory"),
):
    """Check extensions.xml for merge conflicts without cloning the full eolib."""

    console.print("[bold]Validating extensions...[/bold]\n")

    if not config.exists():
        err_console.print(f"[red]Error:[/red] Config file not found: {config}")
        raise typer.Exit(1)

    config_dir = config.parent.resolve()
    extensions = parse_extensions_xml(config)

    # Resolve sources
    resolved_extensions = []
    for ext in extensions:
        try:
            resolved = resolve(ext, config_dir)
            resolved_extensions.append(resolved)
            console.print(f"  [green]✓[/green] {ext.name} — source resolved")
        except ValueError as e:
            console.print(f"  [red]✗[/red] {ext.name} — source error")
            err_console.print(f"\n[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print()

    # Load base elements if protocol_dir provided
    base_elements = []
    if protocol_dir:
        base_files = sorted(protocol_dir.rglob("protocol.xml"))
        base_elements = load_base_elements(base_files)
        console.print(f"  Loaded base protocol from {protocol_dir}")
    else:
        console.print("  [dim]No --protocol-dir given; validating extension conflicts only.[/dim]")

    console.print()

    # Dry-run merge
    for resolved in resolved_extensions:
        ext_files = resolve_extension_files(resolved)
        try:
            for ext_file in ext_files:
                result = merge_protocol_file(base_elements, ext_file, resolved.name)
                console.print(f"  [green]✓[/green] {resolved.name:<20} {result.summary()}")
        except MergeError as e:
            console.print(f"  [red]✗[/red] {resolved.name:<20} conflict")
            err_console.print(f"\n[red]Conflict:[/red] {e}")
            raise typer.Exit(1)

    console.print()
    console.print("[bold green]All extensions are valid — no conflicts detected.[/bold green]")


if __name__ == "__main__":
    app()
