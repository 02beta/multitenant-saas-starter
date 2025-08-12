"""Flexible CRUD base class for all domains."""

from datetime import datetime
from typing import Generic, List, Optional, Protocol, TypeVar
from uuid import UUID

from sqlmodel import Session, select


# Protocol for models with audit fields
class AuditableModel(Protocol):
    created_at: datetime
    updated_at: Optional[datetime]

    def set_audit_fields(
        self, updated_by_id: Optional[UUID] = None
    ) -> None: ...


# Protocol for models with soft delete fields
class SoftDeletableModel(AuditableModel, Protocol):
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]

    def soft_delete(self, deleted_by_id: Optional[UUID] = None) -> None: ...
    def restore(self) -> None: ...


ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Type-safe CRUD base class.
    Supports models with or without audit/softdelete fields.
    """

    def __init__(self, model: type[ModelType]):
        self.model = model

    def create(
        self, session: Session, *, obj_in: CreateSchemaType
    ) -> ModelType:
        """Create new record."""
        if hasattr(obj_in, "model_dump"):
            create_data = obj_in.model_dump(exclude_unset=True)
        else:
            create_data = obj_in.dict(exclude_unset=True)

        # Set created_at if present in model
        if (
            hasattr(self.model, "created_at")
            and "created_at" not in create_data
        ):
            create_data["created_at"] = datetime.utcnow()

        db_obj = self.model(**create_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def get(self, session: Session, id: UUID) -> Optional[ModelType]:
        """Get record by ID. If model supports soft delete, only return active records."""
        stmt = select(self.model).where(self.model.id == id)
        # If model supports soft delete, filter out deleted records
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        return session.exec(stmt).first()

    def get_multi(
        self, session: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records. If model supports soft delete, only return active records."""
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        stmt = stmt.offset(skip).limit(limit)
        return list(session.exec(stmt).all())

    def update(
        self,
        session: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType,
        updated_by_id: Optional[UUID] = None,
    ) -> ModelType:
        """Update record. If model supports audit fields, update them."""
        if hasattr(obj_in, "model_dump"):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        # If model supports audit fields, update them
        if hasattr(db_obj, "set_audit_fields") and callable(
            getattr(db_obj, "set_audit_fields")
        ):
            db_obj.set_audit_fields(updated_by_id)

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def remove(
        self,
        session: Session,
        *,
        id: UUID,
        deleted_by_id: Optional[UUID] = None,
    ) -> bool:
        """
        Remove record.
        If model supports soft delete, perform soft delete.
        Otherwise, delete from database.
        """
        obj = self.get(session, id)
        if not obj:
            return False

        if hasattr(obj, "soft_delete") and callable(
            getattr(obj, "soft_delete")
        ):
            obj.soft_delete(deleted_by_id)
            session.add(obj)
        else:
            session.delete(obj)
        session.commit()
        return True
