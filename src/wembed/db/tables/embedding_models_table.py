"""
This internal table stores various embedding model configurations used by the application.
It includes details such as:
- Model Name: The name of the embedding model. e.g. 'nomic-embed-text', 'all-minilm', 'embeddinggemma', etc.
- Hugging Face Model ID: The identifier for the model on Hugging Face, if applicable. (For pulling the correct tokenizer for Docling)
- Embedding Length: The dimensionality of the embeddings produced by the model. e.g. 768, 1024, etc.
- Context Length: The maximum context length (in tokens) that the model can handle. e.g. 512, 1024, etc.
- Is Default: A boolean flag indicating if this model is the default choice for embedding operations.
- Created At: Timestamp of when the record was created.
- Updated At: Timestamp of the last update to the record.
"""

from datetime import datetime, timezone
from typing import Optional, Required

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .. import DbService
from ..base import Base


class EmbeddingModelTable(Base):
    """
    SQLAlchemy model for the 'embedding_models' table.
    Stores configurations for various embedding models used by the application.

    Attributes:
        id (int): Primary key, auto-incremented.
        model_name (str): The name of the embedding model.
        hf_model_id (str | None): The Hugging Face model ID, if applicable.
        embedding_length (int): The dimensionality of the embeddings produced by the model.
        context_length (int): The maximum context length (in tokens) that the model can handle.
        is_default (bool): Indicates if this model is the default choice for embedding operations.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
    """

    __tablename__ = "_dl_embedding_models"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    hf_model_id: Mapped[str | None] = mapped_column(String, nullable=True)
    embedding_length: Mapped[int] = mapped_column(Integer, nullable=False)
    context_length: Mapped[int] = mapped_column(Integer, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )


class EmbeddingModelSchema(BaseModel):
    """
    Pydantic schema for the EmbeddingModelTable.
    Used for data validation and serialization.

    Attributes:
        id (int): Primary key, auto-incremented.
        model_name (str): The name of the embedding model.
        hf_model_id (str): The Hugging Face model ID, if applicable.
        embedding_length (int): The dimensionality of the embeddings produced by the model.
        context_length (int): The maximum context length (in tokens) that the model can handle.
        is_default (bool): Indicates if this model is the default choice for embedding operations.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
    """

    model_name: Required[str] = Field(
        ..., description="The name of the embedding model."
    )
    hf_model_id: Required[str] = Field(
        ..., description="The Hugging Face model ID, if applicable."
    )
    embedding_length: Required[int] = Field(
        ..., description="The dimensionality of the embeddings produced by the model."
    )
    context_length: Required[int] = Field(
        ...,
        description="The maximum context length (in tokens) that the model can handle.",
    )
    is_default: bool = Field(
        False,
        description="Indicates if this model is the default choice for embedding operations.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of when the record was created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the last update to the record.",
    )

    class Config:
        """Pydantic configuration for the schema."""

        orm_mode = True

    def update_timestamp(self) -> None:
        """Updates the 'updated_at' timestamp to the current UTC time."""
        self.updated_at = datetime.now(timezone.utc)


class EmbeddingModelRepo:
    """
    Repository class for managing EmbeddingModelTable records in the database.
    Provides methods for CRUD operations and querying embedding models.

    Methods:
        get_default(session): Retrieves the default embedding model.
        set_default(session, model_name): Sets an embedding model as the default.
        create(session, model_data): Adds a new embedding model to the database.
        get_by_name(session, model_name): Retrieves an embedding model by its name.
        get_by_id(session, model_id): Retrieves an embedding model by its ID.
        get_all_embedding_models(session): Retrieves all embedding models.
        update(session, model_name, update_data): Updates an existing embedding model.
        delete(session, model_name): Deletes an embedding model by its name.
        to_schema(model): Converts a database model instance to a Pydantic schema instance.
    """

    def __init__(self, db_svc: DbService) -> None:
        self._db_svc = db_svc

    def get_default(self) -> EmbeddingModelSchema | None:
        """Retrieves the default embedding model from the database."""
        with self._db_svc.get_session() as session:
            model = (
                session.query(EmbeddingModelTable).filter_by(is_default=True).first()
            )
            if model:
                return self.to_schema(model)
            return None

    def set_default(
        self, model_name: Optional[str] = None, model_id: Optional[int] = None
    ) -> bool:
        """Sets an embedding model as the default."""
        with self._db_svc.get_session() as session:
            if model_name:
                model = (
                    session.query(EmbeddingModelTable)
                    .filter_by(model_name=model_name)
                    .first()
                )
            elif model_id:
                model = (
                    session.query(EmbeddingModelTable).filter_by(id=model_id).first()
                )
            else:
                return False

            if not model:
                return False

            # Clear existing defaults
            session.query(EmbeddingModelTable).filter_by(is_default=True).update(
                {"is_default": False}
            )
            model.is_default = True
            session.commit()
            return True

    def create(self, model_data: EmbeddingModelSchema) -> EmbeddingModelSchema:
        """Adds a new embedding model to the database."""
        with self._db_svc.get_session() as session:
            model = EmbeddingModelTable(
                model_name=model_data.model_name,
                hf_model_id=model_data.hf_model_id,
                embedding_length=model_data.embedding_length,
                context_length=model_data.context_length,
                is_default=model_data.is_default,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self.to_schema(model)

    def get_model_by_name(self, model_name: str) -> EmbeddingModelSchema | None:
        """Retrieves an embedding model by its name."""
        with self._db_svc.get_session() as session:
            model = (
                session.query(EmbeddingModelTable)
                .filter_by(model_name=model_name)
                .first()
            )
            if model:
                return self.to_schema(model)
            return None

    def get_all_models(self) -> list[EmbeddingModelSchema]:
        """Lists all embedding models in the database."""
        with self._db_svc.get_session() as session:
            models = session.query(EmbeddingModelTable).all()
            return [self.to_schema(model) for model in models]

    def update(self, model_name: str, update_data: dict) -> EmbeddingModelSchema | None:
        """Updates an existing embedding model."""
        with self._db_svc.get_session() as session:
            model = (
                session.query(EmbeddingModelTable)
                .filter_by(model_name=model_name)
                .first()
            )
            if not model:
                return None
            for key, value in update_data.items():
                setattr(model, key, value)
            model.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(model)
            return self.to_schema(model)

    def delete(self, model_name: str) -> bool:
        """Deletes an embedding model by its name."""
        with self._db_svc.get_session() as session:
            model = (
                session.query(EmbeddingModelTable)
                .filter_by(model_name=model_name)
                .first()
            )
            if not model:
                return False
            session.delete(model)
            session.commit()
            return True

    def to_schema(self, model: EmbeddingModelTable) -> EmbeddingModelSchema:
        """Converts a database model instance to a Pydantic schema instance."""
        return EmbeddingModelSchema(
            id=model.id,
            model_name=model.model_name,
            hf_model_id=model.hf_model_id,
            embedding_length=model.embedding_length,
            context_length=model.context_length,
            is_default=model.is_default,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def initialize_defaults(self, schema: EmbeddingModelSchema) -> None:
        """
        Initializes the database with default embedding models if none exist.
        This method checks if any embedding models are present, and if not, it adds
        a predefined set of default models.
        """
        with self._db_svc.get_session() as session:
            existing_models = session.query(EmbeddingModelTable).count()
            if existing_models == 0:
                model = EmbeddingModelTable(
                    model_name=schema.model_name,
                    hf_model_id=schema.hf_model_id,
                    embedding_length=schema.embedding_length,
                    context_length=schema.context_length,
                    is_default=schema.is_default,
                )
                session.add(model)
                session.commit()
