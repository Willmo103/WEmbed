from sqlalchemy import create_engine, Engine
import typer
from config import app_config


def create_local_engine() -> Engine:
    import models
    models.Base.metadata.create_all(bind=create_engine(app_config.local_db_uri))
    typer.echo("Local database created.")


def create_remote_tables() -> None:
    if not app_config.remote_db_uri:
        typer.echo("No remote database URI configured.")
        return
    import models
    engine = create_engine(app_config.remote_db_uri)
    models.Base.metadata.create_all(bind=engine)
    typer.echo("Remote database tables created.")
