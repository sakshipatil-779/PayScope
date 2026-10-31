"""Import Record repository operations."""
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.import_record import ImportRecord


class ImportRepository:
    """Repository for ImportRecord persistence operations."""

    @staticmethod
    def create(
        db: Session,
        user_id: uuid.UUID,
        filename_display: str,
        storage_key: str,
        account_id: Optional[uuid.UUID] = None,
        file_type: str = "csv",
        source_label: str = "synthetic_upload",
        status: str = "uploaded",
        row_count: int = 0,
    ) -> ImportRecord:
        """Create and persist a new import tracking record."""
        import_record = ImportRecord(
            user_id=user_id,
            account_id=account_id,
            filename_display=filename_display,
            storage_key=storage_key,
            file_type=file_type,
            source_label=source_label,
            status=status,
            row_count=row_count,
        )
        db.add(import_record)
        db.commit()
        db.refresh(import_record)
        return import_record

    @staticmethod
    def get_by_id(db: Session, import_id: uuid.UUID) -> Optional[ImportRecord]:
        """Retrieve an import record by UUID."""
        stmt = select(ImportRecord).where(ImportRecord.id == import_id)
        return db.scalar(stmt)
