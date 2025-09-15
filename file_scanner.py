import subprocess  # <-- Correct import
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Literal, Set
from uuid import uuid4

from pydantic import BaseModel
from sqlite_utils import Database
import typer

from config import app_config
from enums import ScanTypes
from schemas import FileRecord, ScanResult


class ListFileOpts(BaseModel):
    path_arg: Path | None = None
    resolved_path: Path | None = None
    json: bool = False
    nl: bool = False
    dirs: bool = False
    scan_type: str | None = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            Path: lambda v: v.as_posix() if (v and isinstance(v, Path)) else ""
        }


def _iter_files(base: Path) -> Iterable[Path]:
    for item in base.rglob("*"):
        if item.is_file():
            yield item


def _should_skip(item: Path, parts: Set[str] = app_config.ignore_parts) -> bool:
    # Skip if any path segment matches a blocked part
    return any(seg in parts for seg in item.parts)


def _scan_core(
    path: str,
    scan_type: str,
    tracked_only: bool = False,
    pattern: str | None = None
) -> ScanResult:
    """
    Generic scanner for repos and vaults.
    Returns a list of ScanResult objects.
    """
    scan_result: ScanResult
    base = Path(path).resolve()

    # --- Restored original logic block per your feedback ---
    if scan_type == ScanTypes.VAULT:
        marker_pattern = ".obsidian"
    elif scan_type == ScanTypes.REPO:
        marker_pattern = ".git"
        tracked_only = True
    elif scan_type == ScanTypes.LIST:
        marker_pattern = pattern if pattern else "*"
    else:
        raise ValueError(f"Unknown scan_type: {scan_type}")

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
            options=ListFileOpts(
                path_arg=path,
                resolved_path=root.as_posix(),
                json=False,
                nl=False,
                dirs=True,
                scan_type=scan_type
            )
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
    dirs: bool = False,
) -> str | List[Path]:
    """List all files in a directory, excluding ignored paths."""
    files: List[Path] = []
    root = Path(path).resolve()
    scan_start = datetime.now(tz=timezone.utc)
    options = ListFileOpts(
        path_arg=str(path),
        json=json,
        nl=nl,
        dirs=dirs,
    )
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


def save_markdown_to_vault(
    record: FileRecord, markdown_content: str, vault_base_path: Path
) -> None:
    """
    Saves the generated markdown file to the central MD_VAULT,
    preserving the original directory structure.

    An idiot's guide to what's happening:
    1. We get the base path, like 'C:/storage/md_vault'.
    2. We get the source type, like 'Repo' or 'Vault'.
    3. We get the source name, like 'my-cool-project'.
    4. We get the file's original relative path, like 'src/api/main.py'.
    5. We combine them and add '.md' to create the new path:
       'C:/storage/md_vault/Repo/my-cool-project/src/api/main.py.md'
    6. We make sure the folders exist and write the file.
    """
    source_type = "Repo" if record.source.startswith("REPO") else "Vault"

    # Use the pre-calculated relative path from the record for efficiency
    relative_path = Path(record.relative_path)

    dest_path = (
        vault_base_path / source_type / record.source_name / relative_path
    ).with_suffix(record.suffix + ".md")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    # remove the current item, this is meant to be a record of the current state
    dest_path.unlink(missing_ok=True)
    dest_path.write_text(markdown_content, encoding="utf-8")
    # Quieter output to let the progress bar be the main indicator.
    # typer.echo(f"  -> Saved MD to: {dest_path}")
    MD_DB["md_xref"].insert(
        {
            "file_sha256": record["sha256"],
            "file_uri": record["uri"],
            "file_path": record["path"],
            "source_root": record["source_root"],
            "source_name": record["source_name"],
            "source_type": record["source"].split(":")[0],
            "vault_path": dest_path.as_posix(),
            "last_rendered": datetime.now(timezone.utc).isoformat(),
        },
        alter=True,
        replace=True,
        pk="file_sha256",
    )


def process_file(
    full_path: Path,
    source_root: Path,
    scan_type: Literal[ScanTypes.REPO, ScanTypes.VAULT, ScanTypes.LIST],
    source_name: str,
    db: Database,
    sync_md: bool = True,
) -> Optional[dict]:
    """
    Processes a single file: creates a metadata record, generates markdown,
    saves both to the DB and the central vault. Skips file if unchanged.
    """
    if not full_path.is_file():
        return None

    try:
        content = full_path.read_bytes()
        new_sha256 = hashlib.sha256(content).hexdigest()

        # 1. Check for the latest existing version of this file in the database.
        latest_version_record = _get_latest_version(full_path, db)

        # 2. If a version exists and its hash matches the current file's hash,
        #    it means the file is unchanged. We can skip it for efficiency.
        if (
            latest_version_record
            and latest_version_record.sha256 == new_sha256
            and not sync_md
        ):
            return None  # File is already indexed and has not changed.

        if sync_md and latest_version_record:
            save_markdown_to_vault(
                latest_version_record, latest_version_record.markdown, MD_VAULT
            )
            return None  # Only sync markdown, no new record needed.
        # 3. If the file is new or has been modified, determine its new version number.
        if latest_version_record:
            # It's a modified file; increment the latest known version.
            new_version = latest_version_record.bump_version()
        else:
            # It's a brand new file.
            new_version = 1

        try:
            content_text = content.decode("utf-8")
        except UnicodeDecodeError:
            content_text = content.decode("latin-1", errors="replace")

        stat = full_path.stat()
        relative_path = full_path.relative_to(source_root).as_posix()

        file_record = FileRecord(
            id=str(uuid4().hex),
            version=new_version,
            source=f'"{scan_type.upper().strip()}:({source_name.strip()})"',
            source_root=source_root.as_posix(),
            source_name=source_name,
            host=os.environ.get("COMPUTERNAME", "unknown"),
            user=os.environ.get("USERNAME", "unknown"),
            name=full_path.name,
            stem=full_path.stem,
            path=full_path.as_posix(),
            relative_path=relative_path,
            suffix=full_path.suffix,
            sha256=new_sha256,
            md5=hashlib.md5(content).hexdigest(),
            mode=oct(stat.st_mode),
            size=stat.st_size,
            content=content,
            content_text=content_text,
            markdown=None,
            ctime_iso=datetime.fromtimestamp(
                stat.st_ctime, tz=timezone.utc
            ).isoformat(),
            mtime_iso=datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(),
            created_at=datetime.now(timezone.utc).isoformat(),
            line_count=content_text.count("\n") + 1 if content_text else 0,
            uri=f"file://{full_path.as_posix()}",
            mimetype=mimetypes.guess_type(full_path.name)[0],
        )

        # The full markdown format is preserved here.
        md_content = f"""---
id: {file_record.id}
host: {file_record.host}
user: {file_record.user}
sha256: {file_record.sha256}
uri: {file_record.uri}
source: {file_record.source}
generated_at: {file_record.created_at}
version: {file_record.version}
---

# {file_record.name} *(Version {file_record.version})*

## File Information

**URI:** `{file_record.uri}`

| Property                | Value                   |
|-------------------------|-------------------------|
| **Host** | `{file_record.host}`            |
| **User** | `{file_record.user}`            |
| **Source** | `{file_record.source}`          |
| **File Hash (sha256)** | `{file_record.sha256}`         |
| **File Hash (md5)** | `{file_record.md5}`            |
| **ID** | `{file_record.id}`              |
| **Full Path** | `{file_record.path}`        |
| **Relative Path** | `{file_record.relative_path}`            |
| **File Name** | `{file_record.name}`            |
| **File Stem** | `{file_record.stem}`            |
| **File Mode** | `{file_record.mode}`            |
| **File Suffix** | `{file_record.suffix}`          |
| **Size (bytes)** | `{file_record.size}`            |
| **Line Count** | `{file_record.line_count}`      |
| **MIME Type** | `{file_record.mimetype}`        |
| **Created At** | `{file_record.ctime_iso}`        |
| **Modified At** | `{file_record.mtime_iso}`        |
| **Indexed At** | `{file_record.created_at}`      |

---

## File Content

```{MD_XREF.get(file_record.suffix, "")}
{content_text.replace("\n\n", "\n").replace("\n\r", "\n") if content_text else "<Binary or non-text content>"}
```
"""
        file_record.markdown = md_content

        # A new UUID is always generated, so replace=True is not needed.
        # alter=True is good practice as it adds new columns if they exist in the record.
        file_record.save_to_sqlite(MD_DB)
        save_markdown_to_vault(file_record, md_content, MD_VAULT)

        return file_record
    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as log:
            log.write(
                f"{datetime.now().isoformat()} - Error processing {full_path}: {e}\nDetails: {traceback.format_exc()}"
            )
        typer.secho(f"Error processing {full_path}: {e}", fg=typer.colors.RED)
        return None


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
