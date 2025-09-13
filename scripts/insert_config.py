import json
from pathlib import Path
from pydantic import BaseModel
from sqlite_utils import Database


class IgnoreExts(BaseModel):
    ext: str


class MarkdownXref(BaseModel):
    k: str
    v: str


class IgnoreParts(BaseModel):
    part: str


def insert_configs(data_path: str | None = None):
    if data_path is None:
        data_path = Path(__file__).resolve().parent.parent.parent / "data"
    if not data_path.exists():
        print(f"Data path {data_path} does not exist. Please create it.")
        exit(1)

    ignore_ext = data_path / "ignore_ext.json"
    ignore_parts = data_path / "ignore_parts.json"
    md_xref = data_path / "md_xref.json"

    db = Database(data_path / "local.db")

    exts = json.loads(ignore_ext.read_text()) if ignore_ext.exists() else []
    parts = json.loads(ignore_parts.read_text()) if ignore_parts.exists() else []
    xrefs = json.loads(md_xref.read_text()) if md_xref.exists() else []

    for key in xrefs.keys():
        xref = MarkdownXref(k=key, v=xrefs[key])
        db["md_xref"].upsert(xref.model_dump(), pk="k")

    for ext in exts:
        ignore_ext = IgnoreExts(ext=ext)
        db["ignore_ext"].upsert(ignore_ext.model_dump(), pk="ext")

    for part in parts:
        ignore_part = IgnoreParts(part=part)
        db["ignore_parts"].upsert(ignore_part.model_dump(), pk="part")

    print(f"Inserted {len(exts)} ignore_ext, {len(parts)} ignore_parts, {len(xrefs)} md_xref")


if __name__ == "__main__":
    insert_configs()
