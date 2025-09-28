from os import environ as env

import pytest

from wembed.config import AppConfig


class TestAppConfiguration:
    @pytest.fixture
    def testing_env(self):
        testing_flag = {"TESTING": "1"}
        env.update(testing_flag)
        yield
        env.pop("TESTING", None)
        env.pop("APP_DB_URI", None)
        env.pop("EMBED_MODEL_HF_ID", None)
        env.pop("EMBED_MODEL_NAME", None)
        env.pop("EMBEDDING_LENGTH", None)
        env.pop("USERNAME", None)
