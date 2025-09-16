import datetime
import hashlib
import json
import mimetypes
import os
import shutil
import traceback
from typing import Optional
from uuid import uuid4
from sqlite_utils import Database
from schemas import FileRecordSchema, ScanResult, ScanResultList
from pathlib import Path
from db import get_session_local, get_session_remote
from db import models
from sqlalchemy.orm import Session
from config import app_config

def _get_latest_version(record: models.FileRecord, session: Session):
    return (
        session.query(models.FileRecord)
        .filter(models.FileRecord.path == record.path, models.FileRecord.sha256 == record.sha256, models.FileRecord.host == record.host)
        .order_by(models.FileRecord.version.desc())
        .first()
    )


def save_markdown_to_vault(
    record: FileRecordSchema, source_type: str, path: Path = app_config.md_vault,
) -> None:

    # Use the pre-calculated relative path from the record for efficiency
    relative_path = Path(record.relative_path)

    # Delete the entire folder if it exists
    shutil.rmtree(dest_path.parent, ignore_errors=True)

    dest_path = (
        path / source_type / record.source_name / relative_path
    ).with_suffix(record.suffix + ".md")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    dest_path.write_text(record.markdown, encoding="utf-8")
    # Quieter output to let the progress bar be the main indicator.
    # typer.echo(f"  -> Saved MD to: {dest_path}")
    app_config.local_db["md_xref"].insert(
        {
            "file_sha256": record["sha256"],
            "file_uri": record["uri"],
            "file_path": record["path"],
            "source_root": record["source_root"],
            "source_name": record["source_name"],
            "source_type": record["source"].split(":")[0],
            "vault_path": dest_path.as_posix(),
            "last_rendered": datetime.now(datetime.timezone.utc).isoformat(),
        },
        alter=True,
        replace=True,
        pk="file_sha256",
    )




def process_result_files(
    sr: ScanResult,
    db: Session
) -> Optional[dict]:
    """
    Processes a single file: creates a metadata record, generates markdown,
    saves both to the DB and the central vault. Skips file if unchanged.
    """
    results = ScanResultList( results=[] )
    for full_path in sr.files:
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
        ):
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
            source=sr.name,
            source_root=sr.root_path.as_posix(),
            source_name=sr.name,
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
                stat.st_ctime, tz=datetime.timezone.utc
            ).isoformat(),
            mtime_iso=datetime.fromtimestamp(
                stat.st_mtime, tz=datetime.timezone.utc
            ).isoformat(),
            created_at=datetime.now(datetime.timezone.utc).isoformat(),
            line_count=content_text.count("\n") + 1 if content_text else 0,
            uri=f"file://{full_path.as_posix()}",
            mimetype=mimetypes.guess_type(full_path.name)[0],
            version=new_version,
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
| **Last Rendered At** | `{file_record.last_rendered_at}`      |

---

## File Content

```{app_config.md_xref.get(file_record.suffix, "")}
{content_text.replace("\n\n", "\n").replace("\n\r", "\n") if content_text else "<Binary or non-text content>"}
```
"""
        file_record.markdown = md_content

        # A new UUID is always generated, so replace=True is not needed.
        # alter=True is good practice as it adds new columns if they exist in the record.
        models.FileLineRecord(
        save_markdown_to_vault(file_record, md_content, MD_VAULT)

        return file_record
    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as log:
            log.write(
                f"{datetime.now().isoformat()} - Error processing {full_path}: {e}\nDetails: {traceback.format_exc()}"
            )
        typer.secho(f"Error processing {full_path}: {e}", fg=typer.colors.RED)
        return None
