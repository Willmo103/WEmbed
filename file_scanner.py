# file_scanner.py

import hashlib
import mimetypes
import os
import subprocess
import traceback
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Set
from uuid import uuid4

import typer
from sqlite_utils import Database

from config import app_config
from schemas import FileRecord, ScanResult
from enums import ScanTypes

# An Idiot's Guide to this change:
# We've created an Enum to represent the different kinds of scans we can do.
# Using an Enum instead of raw strings like "repo" or "vault" prevents typos
# and makes the code's intent much clearer.

# MOVED to enums.py
# class ScanTypes(str, Enum):
#     REPO = "repo"
#     VAULT = "vault"
#     LIST = "list"


def _iter_files(base: Path) -> Iterable[Path]:
    """Yields all files in a directory and its subdirectories."""
    for item in base.rglob("*"):
        if item.is_file():
            yield item


def _should_skip(
    item: Path, parts: Set[str] = app_config.ignore_parts
) -> bool:
    """Checks if a file's path contains any ignored segments."""
    return any(seg in parts for seg in item.parts)


def _scan_core(
    path: str, scan_type: ScanTypes, tracked_only: bool = False
) -> List[ScanResult]:
    """
    Core scanner for repos, vaults, and simple file lists.
    Returns a list of ScanResult objects.

    An Idiot's Guide to this function:
    1. It takes a path and a 'scan_type' (REPO, VAULT, or LIST).
    2. For REPO or VAULT, it looks for "marker" folders (.git, .obsidian) to find roots.
       It can find MULTIPLE roots (e.g., a folder containing several git repos).
    3. For LIST, it treats the given path AS the root and finds all files inside.
    4. For each root it finds, it creates a 'ScanResult' object containing a list of files.
    5. It returns a list of all the 'ScanResult' objects it created.
    """
    scan_results: List[ScanResult] = []
    base = Path(path).resolve()
    ignore_list = set(app_config.ignore_parts) | {".git"}

    # --- Logic for REPO and VAULT scans (marker-based) ---
    if scan_type in [ScanTypes.REPO, ScanTypes.VAULT]:
        marker_pattern = ".git" if scan_type == ScanTypes.REPO else ".obsidian"

        for marker in base.rglob(marker_pattern):
            if not marker.is_dir() or _should_skip(marker.parent, ignore_list):
                continue

            root = marker.parent.resolve()
            name = root.name
            files: Set[str] = set()
            scan_start = datetime.now(tz=timezone.utc)

            # Git-tracked files for REPO scan
            if scan_type == ScanTypes.REPO and tracked_only:
                try:
                    out = subprocess.run(
                        ["git", "-C", str(root), "ls-files"],
                        capture_output=True,
                        text=True,
                        check=True,
                        encoding="utf-8",
                    )
                    file_paths = out.stdout.splitlines()
                except Exception:
                    # Fallback for non-git dirs or errors
                    file_paths = [
                        f.relative_to(root).as_posix()
                        for f in _iter_files(root)
                    ]
            # All markdown files for VAULT scan
            elif scan_type == ScanTypes.VAULT:
                file_paths = [
                    f.relative_to(root).as_posix()
                    for f in root.rglob("*.md")
                    if not _should_skip(f, ignore_list)
                ]
            # All files for non-tracked REPO scan
            else:
                file_paths = [
                    f.relative_to(root).as_posix() for f in _iter_files(root)
                ]

            # Common filtering logic
            for rel_path in file_paths:
                p = root / rel_path
                if not (
                    _should_skip(p, ignore_list)
                    or p.suffix in app_config.ignore_extensions
                    or p.name in app_config.ignore_extensions
                ):
                    files.add(rel_path)

            scan_end = datetime.now(tz=timezone.utc)
            scan_results.append(
                ScanResult(
                    id=uuid4().hex,
                    root=root.as_posix(),
                    name=name,
                    scan_type=scan_type.value,
                    files=sorted(list(files)),
                    scan_start=scan_start,
                    scan_end=scan_end,
                    duration=(scan_end - scan_start).total_seconds(),
                    options={
                        "path_arg": path,
                        "scan_type": scan_type.value,
                        "tracked_only": tracked_only,
                    },
                )
            )
    # --- Logic for LIST scan (non-marker-based) ---
    elif scan_type == ScanTypes.LIST:
        root = base
        files = set()
        scan_start = datetime.now(tz=timezone.utc)
        for item in _iter_files(root):
            if not _should_skip(item, ignore_list):
                files.add(item.as_posix())

        scan_end = datetime.now(tz=timezone.utc)
        scan_results.append(
            ScanResult(
                id=uuid4().hex,
                root=root.as_posix(),
                name=root.name,
                scan_type=scan_type.value,
                files=sorted(list(files)),
                scan_start=scan_start,
                scan_end=scan_end,
                duration=(scan_end - scan_start).total_seconds(),
                options={"path_arg": path, "scan_type": scan_type.value},
            )
        )

    return scan_results


# --- CLI Wrapper Functions ---


def scan_repos(path: str) -> List[ScanResult]:
    """Return a list of ScanResult objects for any folder containing a .git."""
    return _scan_core(path, scan_type=ScanTypes.REPO, tracked_only=True)


def scan_vaults(path: str) -> List[ScanResult]:
    """Return a list of ScanResult objects for any Obsidian vault under path."""
    return _scan_core(path, scan_type=ScanTypes.VAULT)


def scan_list(path: str) -> Optional[ScanResult]:
    """Return a single ScanResult for a simple directory listing."""
    results = _scan_core(path, scan_type=ScanTypes.LIST)
    return results[0] if results else None


# --- Typer CLI Application ---

file_filter_cli = typer.Typer(name="files")


@file_filter_cli.command(
    name="repos", help="Scan for git repos", no_args_is_help=True
)
def scan_repos_command(
    path: str = typer.Argument(
        ..., help="Path to scan", dir_okay=True, file_okay=False
    )
):
    results = scan_repos(path)
    # Since multiple repos can be found, we dump the list of results
    typer.echo([r.model_dump_json(indent=2) for r in results])


@file_filter_cli.command(
    name="vaults", help="Scan for Obsidian vaults", no_args_is_help=True
)
def scan_vaults_command(
    path: str = typer.Argument(
        ..., help="Path to scan", dir_okay=True, file_okay=False
    )
):
    results = scan_vaults(path)
    typer.echo([r.model_dump_json(indent=2) for r in results])


@file_filter_cli.command(
    name="list", help="List all files in a directory", no_args_is_help=True
)
def list_files_command(
    path: str = typer.Argument(
        ..., help="Path to list files", dir_okay=True, file_okay=False
    ),
    json: bool = typer.Option(False, "--json", "-j", help="Output as JSON."),
    nl: bool = typer.Option(
        False, "--nl", "-n", help="Output as newline-delimited list."
    ),
):
    result = scan_list(path)
    if not result:
        typer.secho("No files found.", fg=typer.colors.YELLOW)
        return

    # The formatting logic now lives here, in the presentation layer.
    db = Database(app_config.db_path)
    db["scan_results"].insert(result.model_dump(), pk="id", alter=True)
    typer.secho(
        f"Stored scan result {result.id} to the database.",
        fg=typer.colors.GREEN,
    )

    if json:
        typer.echo(result.model_dump_json(indent=2))
    elif nl:
        typer.echo("\n".join(result.files))
    else:
        # Default output is also newline-delimited
        typer.echo("\n".join(result.files))


if __name__ == "__main__":
    file_filter_cli()
