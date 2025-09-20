from src import wembed as db


class SessionTests:

    def test_sesson_returns_none_when_app_db_not_set(self):
        assert db.