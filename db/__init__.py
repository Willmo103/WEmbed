from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker
from ._base import Base
from config import app_config, Config

DB_INIT = False
_local_uri = app_config.local_db_uri
_remote_uri = app_config.remote_db_uri


def _get_engine(uri: str) -> Engine:
    return create_engine(uri)


def _init_db(uri: str) -> None:
    global DB_INIT
    if not DB_INIT:
        create_models(uri)
        DB_INIT = True


def create_models(uri: str) -> tuple[bool, str]:
    global DB_INIT
    try:
        from . import models

        models.Base.metadata.create_all(_get_engine(uri))
        DB_INIT = True
        return True, "Database models created successfully."
    except Exception as e:
        return False, str(e) or "No error message available."


def get_session_local(uri: str = _local_uri) -> Session:
    sesh: Session = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine(uri))()
    return sesh


def get_session_remote(uri: str = _remote_uri) -> Session | None:
    try:
        return sessionmaker(autocommit=False, autoflush=False, bind=_get_engine(uri))()
    except Exception:
        return None
