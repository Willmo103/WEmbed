import json
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy import Column, String, create_engine
from sqlite_utils import Database
from db._base import Base
from config import app_config


class IgnoreExtTable(Base):
    __tablename__ = "_dl_ignore_ext"
    ext = Column(String, primary_key=True, index=True)


class IgnoreExts(BaseModel):
    ext: str


class MdXrefTable(Base):
    __tablename__ = "_dl_md_xref"
    k = Column(String, primary_key=True, index=True)
    v = Column(String, index=True)


class MarkdownXref(BaseModel):
    k: str
    v: str


class IgnorePartsTable(Base):
    __tablename__ = "_dl_ignore_parts"
    part = Column(String, primary_key=True, index=True)


engine = create_engine(
    "sqlite:///" + str(Path(app_config.app_storage).joinpath("test_db.db"))
)
Base.metadata.create_all(bind=engine)


class IgnoreParts(BaseModel):
    part: str


def insert_configs():

    ignore_ext = app_config.app_storage / "ignore_ext.json"
    ignore_parts = app_config.app_storage / "ignore_parts.json"
    md_xref = app_config.app_storage / "md_xref.json"

    db = Database(app_config.db_path)

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

    print(
        f"Inserted {len(exts)} ignore_ext, {len(parts)} ignore_parts, {len(xrefs)} md_xref"
    )


if __name__ == "__main__":
    insert_configs()
