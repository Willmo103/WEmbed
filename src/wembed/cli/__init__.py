from wembed.config.model import AppConfig

from ..services.db_service import DbService

cli_config = AppConfig()
cli_db_service = DbService(cli_config)
