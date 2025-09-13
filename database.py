from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker


def _get_engine(uri: str) -> Engine:
    return create_engine(uri)


def create_models(uri: str):
    from . import models

    models.Base.metadata.create_all(_get_engine(uri))


def get_session(uri: str) -> Session:
    engine = _get_engine(uri)
    return sessionmaker(bind=engine)()
