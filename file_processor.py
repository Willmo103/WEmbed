from dataclasses import dataclass
import datetime
import hashlib
import json
import mimetypes
import os
import shutil
import traceback
from typing import Generator, List, Optional
from uuid import uuid4
from sqlite_utils import Database
import typer
from schemas import FileRecordSchema, ScanResult, ScanResultList
from pathlib import Path
from db import get_session
from db import models
from sqlalchemy.orm import Session
from config import Config, app_config


@dataclass
class RepoFileProcessingPaths:
    read_path: Path
    render_path: Path
    vault_version_exists: bool


@dataclass
class VaultFileProcessingPaths:
    read_path: Path
    render_path: Path
    vault_version_exists: bool


def _get_repo_results() -> list[models.RepoRecord]:
    session = get_session()
    return session.query(models.RepoRecord).all()


def _get_vault_results() -> list[models.VaultRecord]:
    session = get_session()
    return session.query(models.VaultRecord).all()


def _get_repo_files() -> Generator[RepoFileProcessingPaths, None, None]:
    repos = _get_repo_results()

    for repo in repos:
        root = repo.root_path
        name = repo.name

        for repo_file in repo.files:
            yield RepoFileProcessingPaths(
                read_path=Path(root) / repo_file,
                render_path=app_config.md_vault / "Repo" / name / repo_file + ".md",
                vault_version_exists=(
                    True
                    if (
                        app_config.md_vault / "Repo" / name / repo_file + ".md"
                    ).exists()
                    else False
                ),
            )


def _get_vault_files() -> Generator[VaultFileProcessingPaths, None, None]:
    vaults = _get_vault_results()

    for vault in vaults:
        root = vault.root_path
        name = vault.name

        for vault_file in vault.files:
            yield VaultFileProcessingPaths(
                read_path=Path(root) / vault_file,
                render_path=app_config.md_vault / "Vault" / name / vault_file + ".md",
                vault_version_exists=(
                    True
                    if (
                        app_config.md_vault / "Vault" / name / vault_file + ".md"
                    ).exists()
                    else False
                ),
            )


def _get_latest_version(record: models.FileRecord, session: Session):
    return (
        session.query(models.FileRecord)
        .filter(
            models.FileRecord.path == record.path,
            models.FileRecord.sha256 == record.sha256,
            models.FileRecord.host == record.host,
        )
        .order_by(models.FileRecord.version.desc())
        .first()
    )


def _file_record_exists(path: Path) -> bool:
    session = get_session()
    if path.is_file():
        _user = os.environ.get("USERNAME", "unknown")
        _host = os.environ.get("COMPUTERNAME", "unknown")
        _sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                _sha256.update(chunk)
        sha256 = _sha256.hexdigest()
    return (
        session.query(models.FileRecord)
        .filter(
            models.FileRecord.path == path,
            models.FileRecord.sha256 == sha256,
            models.FileRecord.host == _host,
            models.FileRecord.user == _user,
        )
        .count()
        > 0
    )


def _file_record_to_markdown(file_record: FileRecordSchema) -> str:
    return f"""---
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
| **Last Rendered At** | `{file_record.last_rendered_at}`      |

---

## File Content

```{app_config.md_xref.get(file_record.suffix, "")}
{file_record.content_text.replace("\n\n", "\n").replace("\n\r", "\n") if file_record.content_text else "<Binary or non-text content>"}
```
"""


def _write_markdown_to_vault(record: FileRecordSchema, config: Config) -> None:
    markdown_content = _file_record_to_markdown(record)
    dest_path = (
        config.md_vault / record.source_type / record.source_name / record.relative_path
    ).with_suffix(record.suffix + ".md")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(markdown_content, encoding="utf-8")


def process_result_files(scan_result: ScanResult, db: Session) -> Optional[dict]:
    """
    Processes a single file: creates a metadata record, generates markdown,
    saves both to the DB and the central vault. Skips file if unchanged.
    """
    source_root = scan_result.root_path
    for f in scan_result.files:
        full_path = Path(source_root) / f
        if not full_path.is_file() and not full_path.exists():
            continue
    try:
        content = full_path.read_bytes()
        new_sha256 = hashlib.sha256(content).hexdigest()

        # 1. Check for the latest existing version of this file in the database.
        latest_version_record = _get_latest_version(full_path, db)

        # 2. If a version exists and its hash matches the current file's hash,
        #    it means the file is unchanged. We can skip it for efficiency.
        if latest_version_record and latest_version_record.sha256 == new_sha256:
            return None

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

        file_record = FileRecordSchema(
            id=str(uuid4().hex),
            version=new_version,
            source_type=scan_result.scan_type,
            source_root=scan_result.root_path.as_posix(),
            source_name=scan_result.name,
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
                stat.st_birthtime, tz=datetime.timezone.utc
            ).isoformat(),
            mtime_iso=datetime.fromtimestamp(
                stat.st_mtime, tz=datetime.timezone.utc
            ).isoformat(),
            created_at=datetime.now(datetime.timezone.utc).isoformat(),
            uri=f"file://{full_path.as_posix()}",
            mimetype=mimetypes.guess_type(full_path.name)[0],
        )

        file_record.markdown = _file_record_to_markdown(file_record)

        models.FileRecord(
            id=file_record.id,
            version=file_record.version,
            source_type=file_record.source_type,
            source_root=file_record.source_root,
            source_name=file_record.source_name,
            host=file_record.host,
            user=file_record.user,
            name=file_record.name,
            stem=file_record.stem,
            path=file_record.path,
            relative_path=file_record.relative_path,
            suffix=file_record.suffix,
            sha256=file_record.sha256,
            md5=file_record.md5,
            mode=file_record.mode,
            size=file_record.size,
            content=file_record.content,
            content_text=file_record.content_text,
            markdown=file_record.markdown,
            ctime_iso=file_record.ctime_iso,
            mtime_iso=file_record.mtime_iso,
            created_at=file_record.created_at,
            uri=file_record.uri,
            mimetype=file_record.mimetype,
            line_count=file_record.line_count,
        )
        db.add(file_record)
        db.commit()

        return file_record
    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as log:
            log.write(
                f"{datetime.now().isoformat()} - Error processing {full_path}: {e}\nDetails: {traceback.format_exc()}"
            )
        typer.secho(f"Error processing {full_path}: {e}", fg=typer.colors.RED)
        return None


vault_cli = typer.Typer(
    name="vault", help="Vault-related commands", no_args_is_help=True
)
