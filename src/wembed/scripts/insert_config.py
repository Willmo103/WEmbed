import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlite_utils import Database

from wembed.config import app_config
from wembed.db.base import Base
from wembed.db.tables.ignore_ext_table import IgnoreExtTable
from wembed.db.tables.ignore_parts_table import IgnorePartsTable
from wembed.db.tables.md_xref_table import MdXrefTable

_uri = app_config.app_db_uri
_engine = create_engine(_uri)
_session = Session(bind=_engine)


def insert_default_configs():

    ignore_ext = app_config.ignore_extensions
    ignore_parts = app_config.ignore_parts
    md_xref = app_config.md_xref

    for key in md_xref:
        md_ref = MdXrefTable(k=key, v=md_xref[key])
        _session.add(md_ref)
    _session.commit()
    print(f"Inserted {len(md_xref.keys())} md_xref")

    for ext in ignore_ext:
        ext_rec = IgnoreExtTable(ext=ext)
        _session.merge(ext_rec)
    _session.commit()
    print(f"Inserted {len(ignore_ext)} ignore_ext")

    for part in ignore_parts:
        ignore_part = IgnorePartsTable(part=part)
        _session.merge(ignore_part)
    _session.commit()
    print(f"Inserted {len(ignore_parts)} ignore_parts")

    _session.close()

    print("Default configurations inserted successfully.")


if __name__ == "__main__":
    insert_default_configs()
