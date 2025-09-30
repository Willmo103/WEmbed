from typing import Tuple

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from wembed import AppConfig, Base


class DbService:
    """
    Encapsulates all database connection and initialization logic.
    It is instantiated with a configuration object.
    """

    def __init__(self, config: AppConfig) -> None:
        """Initializes the service with a database URI from the config."""
        self._db_uri = config.sqlalchemy_db_uri
        self._engine = create_engine(self._db_uri, echo=False, future=True)

    def test_connection(self) -> bool:
        """Tests if a connection to the database can be established."""
        try:
            with self._engine.connect():
                return True
        except Exception:
            return False

    def get_engine(self) -> Engine:
        """Returns the underlying SQLAlchemy Engine instance."""
        return self._engine

    def get_session(self) -> sessionmaker:
        """Returns a configured SQLAlchemy sessionmaker."""
        return sessionmaker(bind=self.get_engine(), autoflush=False)

    def initialize_tables(self, force: bool = False) -> Tuple[bool, str]:
        """
        Creates all necessary tables based on the imported models.

        Args:
            force: If True, all existing tables will be dropped before creation.

        Returns:
            A tuple containing a success boolean and a status message.
        """
        try:
            if force:
                # Drop all tables defined in the Base metadata
                Base.metadata.drop_all(self._engine)

            # Create all tables
            Base.metadata.create_all(self._engine)
            return True, "Database tables initialized successfully."
        except Exception as e:
            return False, f"An error occurred during table initialization: {e}"
