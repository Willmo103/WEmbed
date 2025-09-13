import subprocess  # <-- Correct import
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Set
from uuid import uuid4

from sqlite_utils import Database
import typer

from config import app_config
from schemas import ScanResult


def _iter_files(base: Path) -> Iterable[Path]:
    for item in base.rglob("*"):
        if item.is_file():
            yield item


def _should_skip(
    item: Path, parts: Set[str] = app_config.ignore_parts
) -> bool:
    # Skip if any path segment matches a blocked part
    return any(seg in parts for seg in item.parts)


def _scan_core(
    path: str, tracked_only: bool = True, md_only: bool = False
) -> ScanResult:
    """
    Generic scanner for repos and vaults.
    Returns a list of ScanResult objects.
    """
    scan_result: ScanResult
    base = Path(path).resolve()

    # --- Restored original logic block per your feedback ---
    if md_only:
        scan_type = "vault"
        marker_pattern = app_config.vault_folder
    elif tracked_only:
        scan_type = "repo"
        marker_pattern = ".git"
    else:
        scan_type = "repo"
        marker_pattern = ".git"

    # --- Corrected way to create the ignore set from a list ---
    ignore_list = set(app_config.ignore_parts) | {".git"}

    for marker in base.rglob(marker_pattern):
        if not marker.is_dir() or _should_skip(marker.parent, ignore_list):
            continue

        root = marker.parent.resolve()
        name = root.name
        files: Set[str] = set()
        scan_start = datetime.now(tz=timezone.utc)

        if scan_type == "repo":
            if tracked_only:
                try:
                    out = subprocess.run(
                        ["git", "-C", str(root), "ls-files"],
                        capture_output=True,
                        text=True,
                        check=True,
                        encoding="utf-8",
                    )
                    for line in out.stdout.splitlines():
                        p = (root / line).resolve()
                        if (
                            _should_skip(p, ignore_list)
                            or p.suffix in app_config.ignore_extensions
                            or p.name in app_config.ignore_extensions
                        ):
                            continue
                        files.add(Path(line).as_posix())
                except Exception:
                    for f in _iter_files(root):
                        if (
                            _should_skip(f, ignore_list)
                            or f.suffix in app_config.ignore_extensions
                            or f.name in app_config.ignore_extensions
                        ):
                            continue
                        rel = f.relative_to(root).as_posix()
                        files.add(rel)
            else:
                for f in _iter_files(root):
                    if (
                        _should_skip(f, ignore_list)
                        or f.suffix in app_config.ignore_extensions
                        or f.name in app_config.ignore_extensions
                    ):
                        continue
                    rel = f.relative_to(root).as_posix()
                    files.add(rel)

        elif scan_type == "vault":
            for f in root.rglob("*.md"):
                if app_config.vault_folder in f.parts:
                    continue
                rel = f.relative_to(root).as_posix()
                files.add(rel)

        scan_end = datetime.now(tz=timezone.utc)
        duration = (scan_end - scan_start).total_seconds()

        scan_result = ScanResult(
            id=uuid4().hex,
            root=root.as_posix(),
            name=name,
            scan_type=scan_type,
            files=list(files),
            scan_start=scan_start,
            scan_end=scan_end,
            duration=duration,
            options={
                "path_arg": path,
                "scan_type": scan_type,
                "tracked_only": tracked_only,
                "md_only": md_only,
            },
        )
    return scan_result


def scan_repos(path: str) -> List[ScanResult]:
    """Return a list of ScanResult objects for any folder containing a .git."""
    return _scan_core(path, tracked_only=True)


def scan_vaults(path: str) -> List[ScanResult]:
    """Return a list of ScanResult objects for any Obsidian vault under path."""
    return _scan_core(path, md_only=True)


def list_files(
    path: str,
    json: bool = False,
    nl: bool = False,
    store: bool = True,
    dirs: bool = False,
) -> str | List[Path]:
    """List all files in a directory, excluding ignored paths."""
    files: List[Path] = []
    root = Path(path).resolve()
    scan_start = datetime.now(tz=timezone.utc)
    options = {
        "path_arg": str(path),
        "json": json,
        "nl": nl,
        "store": store,
    }
    parts_with_git = [*app_config.ignore_parts, ".git"]

    for item in root.rglob("*"):
        try:
            if (
                (item.is_file() and not dirs) and not _should_skip(item, parts_with_git)
            ) or (item.is_dir() and dirs and not _should_skip(item, parts_with_git)):
                files.append(item)
        except Exception:
            pass
    scan_end = datetime.now(tz=timezone.utc)
    duration = (scan_end - scan_start).total_seconds()
    result = ScanResult(
        id=uuid4().hex,
        root=root.as_posix(),
        name=root.name,
        scan_type="list",  # <-- Populate the new field for this function
        files=list(f.as_posix() for f in files),
        scan_start=scan_start,
        scan_end=scan_end,
        duration=duration,
        options=options,
    )
    if store:
        db = Database(app_config.db_path)
        table_name = "scan_results"
        db[table_name].insert(result.model_dump(), pk="id", alter=True)
    if json:
        return result.model_dump_json(indent=2)
    if nl:
        return "\n".join(f.as_posix() for f in files)
    return "\n".join(f.as_posix() for f in files)


file_filter_cli = typer.Typer(name="files")


@file_filter_cli.command(name="repos", help="Scan for git repos", no_args_is_help=True)
def scan_repos_command(
    path: str = typer.Argument(
        ..., help="Path to scan", dir_okay=True, file_okay=False
    ),
):
    result = scan_repos(path)
    typer.echo(result.model_dump_json(indent=2))


@file_filter_cli.command(
    name="vaults", help="Scan for Obsidian vaults", no_args_is_help=True
)
def scan_vaults_command(
    path: str = typer.Argument(
        ..., help="Path to scan", dir_okay=True, file_okay=False
    ),
):
    result = scan_vaults(path)
    typer.echo(result.model_dump_json(indent=2))


@file_filter_cli.command(
    name="list", help="List files in a directory", no_args_is_help=True
)
def list_files_command(
    path: str = typer.Argument(
        ..., help="Path to list files", dir_okay=True, file_okay=False
    ),
    json: bool = typer.Option(False, help="Output as JSON"),
    nl: bool = typer.Option(False, help="Output as newlines"),
    store: bool = typer.Option(True, help="Store results in database"),
):
    result = list_files(path, json=json, nl=nl, store=store)
    typer.echo(result)


if __name__ == "__main__":
    file_filter_cli()
