import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Set
from uuid import uuid4

import typer

from wembed.constants.ignore_ext import IGNORE_EXTENSIONS
from wembed.constants.ignore_parts import IGNORE_PARTS

from . import DbService
from .db import (
    RepoRecordRepo,
    RepoRecordSchema,
    ScanResult_Controller,
    ScanResultSchema,
    VaultRecordRepo,
    VaultRecordSchema,
)
from .enums import ScanTypes


def iter_files_from_pl_path(base: Path) -> Iterable[Path]:
    """
    Yields all files in a directory and its subdirectories.
    Args:
        base (pathlib.Path): A pathlib.Path object representing the base directory to iterate.
    Yields:
        Iterable[pathlib.Path]: An iterable of pathlib.Path objects for each file found.
    """
    for item in base.rglob("*"):
        if item.is_file():
            yield item


def iter_git_tracked_files(base: Path) -> Iterable[Path]:
    """
    Yields all git-tracked files in a directory and its subdirectories.
    Args:
        base (pathlib.Path): A pathlib.Path object representing the base directory to iterate.
    Yields:
        Iterable[pathlib.Path]: An iterable of pathlib.Path objects for each git-tracked file found.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(base), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        file_paths = out.stdout.splitlines()
        for rel_path in file_paths:
            p = base / rel_path
            if p.is_file():
                yield p
    except Exception:
        # Fallback for non-git dirs or errors
        yield from iter_files_from_pl_path(base)


def path_has_ignored_part(item: Path, parts: Set[str] = IGNORE_PARTS) -> bool:
    """
    Checks each pathlib.Path().part of `item` against each str in `parts`
    and returns True if any match. The default for 'parts' comes from
    [src/wembed/config/ignore_parts.py] if the
    IGNORE_PARTS environment variable is not set.

    Args:
        item (pathlib.Path): The file or directory path to check.
        parts (Set[str]): A set of path segments to ignore.

    Returns:
        bool: True if any part of the path matches an ignored segment, False otherwise.
    """
    return any(seg in parts for seg in item.parts)


def _scan_directory(
    path: str, scan_type: ScanTypes, tracked_only: bool = False
) -> list[ScanResultSchema]:
    """
    Core scanning logic for REPO, VAULT, and LIST scan types.
    Returns a list of ScanResultSchema objects.
    """
    results = []
    base = Path(path).resolve()

    ignore_list = set(IGNORE_PARTS) | {".git"}

    # --- Logic for REPO and VAULT scans (marker-based) ---
    if scan_type in [ScanTypes.REPO, ScanTypes.VAULT]:
        marker_pattern = ".git" if scan_type == ScanTypes.REPO else ".obsidian"

        for marker in base.rglob(marker_pattern):
            if not marker.is_dir() or path_has_ignored_part(marker.parent, ignore_list):
                continue

            root = marker.parent.resolve()
            name = root.name
            files = set()
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
                        for f in iter_files_from_pl_path(root)
                    ]
            # All markdown files for VAULT scan
            elif scan_type == ScanTypes.VAULT:
                file_paths = [
                    f.relative_to(root).as_posix()
                    for f in root.rglob("*.md")
                    if not path_has_ignored_part(f, ignore_list)
                ]
            # All files for non-tracked REPO scan
            else:
                file_paths = [
                    f.relative_to(root).as_posix()
                    for f in iter_files_from_pl_path(root)
                ]

            # Common filtering logic
            for rel_path in file_paths:
                p = root / rel_path
                if not (
                    path_has_ignored_part(p, ignore_list)
                    or p.suffix in IGNORE_EXTENSIONS
                    or p.name in IGNORE_EXTENSIONS
                ):
                    files.add(rel_path)

            scan_end = datetime.now(tz=timezone.utc)
            results.append(
                ScanResultSchema(
                    id=uuid4().hex,
                    root_path=root.as_posix(),
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
                    user=os.environ.get("USERNAME", "unknown"),
                    host=os.environ.get("COMPUTERNAME", "unknown"),
                )
            )

    # --- Logic for LIST scan (non-marker-based) ---
    elif scan_type == ScanTypes.LIST:
        root = base
        files = set()
        scan_start = datetime.now(tz=timezone.utc)
        for item in iter_files_from_pl_path(root):
            if not path_has_ignored_part(item, ignore_list):
                files.add(item.relative_to(root).as_posix())

        scan_end = datetime.now(tz=timezone.utc)
        results.append(
            ScanResultSchema(
                id=uuid4().hex,
                root_path=root.as_posix(),
                name=root.name,
                scan_type=ScanTypes.LIST.value,
                files=sorted(list(files)),
                scan_start=scan_start,
                scan_end=scan_end,
                duration=(scan_end - scan_start).total_seconds(),
                options={"path_arg": path, "scan_type": scan_type.value},
                host=os.environ.get("COMPUTERNAME", "unknown"),
                user=os.environ.get("USERNAME", "unknown"),
            )
        )

    return results


def store_scan_results(scan_results: list[ScanResultSchema], db_svc: DbService) -> None:
    """Store scan results in the database using CRUD operations."""
    session = db_svc.get_session()
    try:
        for result in scan_results:
            ScanResult_Controller.create(session, result)
        typer.echo(f"Stored {len(scan_results)} scan results.")
    except Exception as e:
        typer.secho(f"Error storing scan results: {e}", fg=typer.colors.RED)
        session.rollback()
    finally:
        session.close()


def convert_scan_results_to_records(
    scan_results: list[ScanResultSchema],
    db_svc: DbService,
) -> None:
    """Convert scan results to Vault/Repo records based on scan type."""
    session = db_svc.get_session()
    try:
        for result in scan_results:
            if result.scan_type == ScanTypes.VAULT.value:
                vault_record = VaultRecordSchema(
                    name=result.name,
                    host=result.host,
                    root_path=result.root_path,
                    files=result.files,
                    file_count=len(result.files) if result.files else 0,
                    indexed_at=datetime.now(timezone.utc),
                )
                VaultRecordRepo.create(session, vault_record)

            elif result.scan_type == ScanTypes.REPO.value:
                repo_record = RepoRecordSchema(
                    name=result.name,
                    host=result.host,
                    root_path=result.root_path,
                    files=result.files,
                    file_count=len(result.files) if result.files else 0,
                    indexed_at=datetime.now(timezone.utc),
                )
                RepoRecordRepo.create(session, repo_record)

        typer.echo(f"Converted {len(scan_results)} scan results to records.")
    except Exception as e:
        typer.secho(f"Error converting scan results: {e}", fg=typer.colors.RED)
        session.rollback()
    finally:
        session.close()


# --- CLI Wrapper Functions ---


def scan_repos(path: str) -> list[ScanResultSchema]:
    """Return a list of ScanResult objects for any folder containing a .git."""
    return _scan_directory(path, scan_type=ScanTypes.REPO, tracked_only=True)


def scan_vaults(path: str) -> list[ScanResultSchema]:
    """Return a list of ScanResult objects for any Obsidian vault under path."""
    return _scan_directory(path, scan_type=ScanTypes.VAULT)


def scan_list(path: str) -> list[ScanResultSchema]:
    """Return a single ScanResult for a simple directory listing."""
    return _scan_directory(path, scan_type=ScanTypes.LIST)
