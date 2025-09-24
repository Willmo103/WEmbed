import pytest
from unittest import mock


from src.wembed import db as wdb
from src.wembed.db import Base


from sqlalchemy import Column, Integer, String


class SampleModel(Base):
    """A simple model for testing database operations."""

    __tablename__ = "sample_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class TestSessionSelectionLogic:
    """
    Tests the logic of get_session() using mocks to isolate it from the database.
    """

    def test_get_session_prefers_remote_when_available(self, monkeypatch):
        """
        Ensures that if a remote session is available, it is returned.
        """
        sentinel_remote = object()
        sentinel_local = object()

        monkeypatch.setattr(wdb, "get_session_remote", lambda: sentinel_remote)
        monkeypatch.setattr(wdb, "get_session_local", lambda: sentinel_local)

        result = wdb.get_session()
        assert (
            result is sentinel_remote
        ), "Should have returned the remote session object"

    def test_get_session_falls_back_to_local_when_remote_is_none(self, monkeypatch):
        """
        Ensures that if get_session_remote() returns None, get_session_local() is used.
        """
        sentinel_local = object()

        monkeypatch.setattr(wdb, "get_session_remote", lambda: None)
        monkeypatch.setattr(wdb, "get_session_local", lambda: sentinel_local)

        result = wdb.get_session()
        assert (
            result is sentinel_local
        ), "Should have fallen back to the local session object"

    def test_get_session_falls_back_to_local_when_remote_raises_exception(
        self, monkeypatch
    ):
        """
        Ensures that if get_session_remote() raises an error, it is caught
        and the system falls back to the local session.
        """

        def failing_remote():
            raise RuntimeError("Database connection failed")

        sentinel_local = object()

        monkeypatch.setattr(wdb, "get_session_remote", failing_remote)
        monkeypatch.setattr(wdb, "get_session_local", lambda: sentinel_local)

        result = wdb.get_session()
        assert (
            result is sentinel_local
        ), "Should have fallen back to local after remote raised an exception"


class TestDatabaseIntegration:
    """
    Tests the actual database interaction with a temporary in-memory DB.
    """

    @pytest.fixture(scope="function")
    def temp_db_session(self, monkeypatch):
        """
        A fixture that provides a fully functional, temporary in-memory SQLite session.
        It handles setup (engine, tables) and teardown (closing the session).

        This fixture is key to preventing 'ResourceWarning' by ensuring proper cleanup.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine("sqlite:///:memory:")

        Base.metadata.create_all(engine)

        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        monkeypatch.setattr(wdb, "_local_engine", engine)
        monkeypatch.setattr(wdb, "_LocalSession", TestSessionLocal)

        session = wdb.get_session_local()

        try:
            yield session
        finally:

            session.close()

    def test_local_session_can_read_and_write(self, temp_db_session):
        """
        This is an end-to-end test for the local DB session. It verifies:
        1. A session can be obtained from our temporary DB.
        2. The database schema (tables) can be created.
        3. Data can be written and committed.
        4. The same data can be read back.
        """

        session = temp_db_session

        new_item = SampleModel(name="test_item")
        session.add(new_item)
        session.commit()

        retrieved_item = (
            session.query(SampleModel).filter_by(name="test_item").one_or_none()
        )

        assert retrieved_item is not None
        assert retrieved_item.name == "test_item"
        assert retrieved_item.id is not None

    def test_module_structure_and_exports(self):
        """
        Tests that the db module has the expected public API.
        """
        assert hasattr(wdb, "get_session")
        assert hasattr(wdb, "get_session_local")
        assert hasattr(wdb, "get_session_remote")
        assert hasattr(wdb, "Base")
        assert hasattr(wdb.Base, "metadata")
