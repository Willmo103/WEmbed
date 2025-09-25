from unittest import mock

import pytest

# To make the integration test runnable, we need a simple SQLAlchemy model.
# If you have existing models in your project, you can import and use one of them instead.
from sqlalchemy import Column, Integer, String

# Assuming your project structure allows this import.
# This is simpler and more direct than using importlib.
from src.wembed import db as wdb
from src.wembed.db import Base


class SampleModel(Base):
    """A simple model for testing database operations."""

    __tablename__ = "sample_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)


# --- Unit Tests for Session Selection Logic ---
# These tests use mocking to verify the correctness of the session fallback logic
# without needing a real database connection. They are fast and test one specific thing.


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

        # Replace the actual session functions with mocks that return sentinel values
        monkeypatch.setattr(wdb, "get_session_remote", lambda: sentinel_remote)
        monkeypatch.setattr(wdb, "get_session_local", lambda: sentinel_local)

        result = wdb.get_session()
        assert (
            result is sentinel_remote
        ), "Should have returned the remote session object"

    def test_get_session_returns_none_when_remote_is_none(self, monkeypatch):
        """
        Tests the current behavior where get_session returns None if the remote
        session is None and no exception was raised.
        NOTE: This test confirms the actual implementation. A potential bug exists in
        db/__init__.py's get_session(), as it should arguably fall back to the local
        session in this scenario, not return None.
        """
        sentinel_local = object()

        # Mock get_session_remote to return None, simulating an unavailable remote
        monkeypatch.setattr(wdb, "get_session_remote", lambda: None)

        # Mock get_session_local to ensure it's NOT called
        local_mock = mock.Mock(return_value=sentinel_local)
        monkeypatch.setattr(wdb, "get_session_local", local_mock)

        result = wdb.get_session()

        # Assert the actual behavior: it returns None
        assert (
            result is None
        ), "get_session should return None when remote is None and no exception occurs"

        # Assert that the fallback to local was NOT triggered
        local_mock.assert_not_called()

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


# --- Integration Tests for Database Functionality ---
# These tests connect to a REAL (but temporary) database to ensure
# that the session handling, model creation, and transactions work correctly.


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

        # Create an in-memory SQLite database engine just for this test
        engine = create_engine("sqlite:///:memory:")

        # Create all tables defined by models that inherit from your Base
        Base.metadata.create_all(engine)

        # FIX: Instead of patching a non-existent internal variable, we patch the
        # function responsible for creating the engine. Now, any call to get_session_local()
        # will use our temporary in-memory engine.
        monkeypatch.setattr(wdb, "_get_engine", lambda uri: engine)

        # get_session_local will now use the patched _get_engine
        session = wdb.get_session_local()

        try:
            yield session
        finally:
            # This is the crucial cleanup step!
            # It closes the session and releases the connection, preventing ResourceWarning.
            session.close()

    def test_local_session_can_read_and_write(self, temp_db_session):
        """
        This is an end-to-end test for the local DB session. It verifies:
        1. A session can be obtained from our temporary DB.
        2. The database schema (tables) can be created.
        3. Data can be written and committed.
        4. The same data can be read back.
        """
        # `temp_db_session` is our active, temporary session from the fixture
        session = temp_db_session

        # 1. Create a new object and add it to the session
        new_item = SampleModel(name="test_item")
        session.add(new_item)
        session.commit()

        # 2. Query the database to see if the item was saved correctly
        retrieved_item = (
            session.query(SampleModel).filter_by(name="test_item").one_or_none()
        )

        assert retrieved_item is not None
        assert retrieved_item.name == "test_item"
        assert retrieved_item.id is not None  # Should have an auto-generated ID

    def test_module_structure_and_exports(self):
        """
        Tests that the db module has the expected public API.
        """
        assert hasattr(wdb, "get_session")
        assert hasattr(wdb, "get_session_local")
        assert hasattr(wdb, "get_session_remote")
        assert hasattr(wdb, "Base")
        assert hasattr(wdb.Base, "metadata")
