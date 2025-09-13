from ast import Tuple
from asyncio import subprocess
from pathlib import Path
from typing import Iterable, List, Set
from config import app_config


def _iter_files(base: Path) -> Iterable[Path]:
    for item in base.rglob("*"):
        if item.is_file():
            yield item


def _should_skip(item: Path, parts: Set[str] = app_config.ignore_parts) -> bool:
    # Skip if any path segment matches a blocked part
    return any(seg in parts for seg in item.parts)


def _scan_core(
    path: str, pattern: str, tracked_only: bool = True
) -> List[Tuple[str, str, Set[str]]]:
    """
    Generic scanner used by repo/vault functions.
    Returns (root, name, files) tuples.
    """
    results: List[Tuple[str, str, Set[str]]] = []
    base = Path(path).resolve()

    for marker in base.rglob(pattern):
        # Do not mutate IGNORE_PARTS; extend for this check only
        parts_with_git = app_config.ignore_parts | {".git"}

        # Only consider directory markers, and skip if the parent is in ignore list
        if not marker.is_dir() or _should_skip(marker.parent, parts_with_git):
            continue

        repo_root = marker.parent.resolve()
        name = repo_root.name
        files: Set[str] = set()

        if tracked_only:
            try:
                out = subprocess.run(
                    ["git", "-C", str(repo_root), "ls-files"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                for line in out.stdout.splitlines():
                    p = (repo_root / line).resolve()
                    if _should_skip(p):
                        continue
                    if (
                        p.suffix in app_config.ignore_extensions
                        or p.name in app_config.ignore_extensions
                    ):
                        continue
                    files.add(Path(line).as_posix())
            except Exception:
                # Fallback: full walk if git unavailable
                for f in _iter_files(repo_root):
                    if _should_skip(f):
                        continue
                    if (
                        f.suffix in app_config.ignore_extensions
                        or f.name in app_config.ignore_extensions
                    ):
                        continue
                    rel = f.relative_to(repo_root).as_posix()
                    files.add(rel)
        else:
            for f in _iter_files(repo_root):
                if _should_skip(f):
                    continue
                if (
                    f.suffix in app_config.ignore_extensions
                    or f.name in app_config.ignore_extensions
                ):
                    continue
                rel = f.relative_to(repo_root).as_posix()
                files.add(rel)

        results.append((repo_root.as_posix(), name, files))

    return results


def scan_repos(
    path: str, tracked_only: bool = True
) -> List[Tuple[str, str, Set[str]]]:
    """Return list of tuples (repo_root, name, files) for any folder containing a .git."""
    return _scan_core(path, ".git", tracked_only)


def scan_vaults(path: str) -> List[Tuple[str, str, Set[str]]]:
    """Return list of tuples (vault_root, name, files) for any Obsidian vault under path."""
    results: List[Tuple[str, str, Set[str]]] = []
    base = Path(path).resolve()
    for marker in base.rglob(app_config.vault_folder):
        vault_root = marker.parent.resolve()
        if _should_skip(vault_root):
            continue
        name = vault_root.name
        files: Set[str] = set()
        # rglob is recursive; "*.md" is sufficient
        for f in vault_root.rglob("*.md"):
            if app_config.vault_folder in f.parts:
                # exclude files inside .obsidian
                continue
            rel = f.relative_to(vault_root).as_posix()
            files.add(rel)
        results.append((vault_root.as_posix(), name, files))
    return results
