from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class LlmModelTable(Base):
    __tablename__ = "_dl_llm_models"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    host: Mapped[str] = mapped_column(String(200), nullable=False)
    system_msg: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    info: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
