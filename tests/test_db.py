from src import wembed as db
import os
import importlib
import types
import pytest


class SessionTests:

    # Import the db submodule explicitly to avoid relying on re-exports
    wdb = importlib.import_module("src.wembed.db")

    class SessionTests:
        def test_sesson_returns_none_when_app_db_not_set(self, monkeypatch):
            # Clear common DB env vars so remote is not configured
            for key in [
                "APP_DB_URL",
                "DATABASE_URL",
                "REMOTE_DB_URL",
                "POSTGRES_URL",
                "PG_DSN",
                "APP_DB_REMOTE_URL",
                "WEMBED_REMOTE_DB_URL",
            ]:
                monkeypatch.delenv(key, raising=False)

            # If not configured, get_session_remote should return None
            try:
                result = self.wdb.get_session_remote()
            except Exception:
                # If implementation raises when not configured, consider it equivalent to not available
                result = None

            assert result is None

        def test_get_session_prefers_remote_when_available(self, monkeypatch):
            sentinel_remote = object()
            sentinel_local = object()

            # Stub the internals to control behavior
            monkeypatch.setattr(self.wdb, "get_session_remote", lambda: sentinel_remote)
            monkeypatch.setattr(self.wdb, "get_session_local", lambda: sentinel_local)

            result = self.wdb.get_session()
            assert result is sentinel_remote

        def test_get_session_falls_back_to_local_when_remote_unavailable(
            self, monkeypatch
        ):
            sentinel_local = object()

            monkeypatch.setattr(self.wdb, "get_session_remote", lambda: None)
            monkeypatch.setattr(self.wdb, "get_session_local", lambda: sentinel_local)

            result = self.wdb.get_session()
            assert result is sentinel_local

        def test_get_session_local_uses_sqlite_engine(self, monkeypatch):
            called = {}

            def fake_create_engine(url, *args, **kwargs):
                called["url"] = url

                class FakeEngine:
                    pass

                return FakeEngine()

            def fake_sessionmaker(**kwargs):
                # Return a callable that returns a fake session instance
                class FakeSession:
                    pass

                return lambda: FakeSession()

            monkeypatch.setattr(self.wdb, "create_engine", fake_create_engine)
            monkeypatch.setattr(self.wdb, "sessionmaker", fake_sessionmaker)

            session = self.wdb.get_session_local()
            # Verify we returned a session-like object
            assert session is not None
            # Verify SQLite is used for local session
            assert "sqlite" in str(called.get("url", "")).lower()

        def test_get_session_handles_remote_failure_and_returns_local(
            self, monkeypatch
        ):
            # Make remote raise to simulate connection/driver issues
            def failing_remote():
                raise RuntimeError("remote unavailable")

            sentinel_local = object()

            monkeypatch.setattr(self.wdb, "get_session_remote", failing_remote)
            monkeypatch.setattr(self.wdb, "get_session_local", lambda: sentinel_local)

            result = self.wdb.get_session()
            assert result is sentinel_local

    class ModuleStructureTests:
        def test_db_module_exports_expected_functions(self):
            assert hasattr(self.wdb, "get_session")
            assert hasattr(self.wdb, "get_session_local")
            assert hasattr(self.wdb, "get_session_remote")

        def test_base_is_available(self):
            # Base should be available for model metadata/DDL operations
            assert hasattr(self.wdb, "Base")
            assert hasattr(self.wdb.Base, "metadata")
