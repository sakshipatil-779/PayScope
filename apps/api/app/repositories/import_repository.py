"""Import Record repository operations."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, select
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
        accepted_count: int = 0,
        rejected_count: int = 0,
        duplicate_count: int = 0,
        synthetic_confirmed: bool = True,
        error_summary: Optional[str] = None,
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
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            duplicate_count=duplicate_count,
            synthetic_confirmed=synthetic_confirmed,
            error_summary=error_summary,
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

    @staticmethod
    def list_by_user(
        db: Session, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> List[ImportRecord]:
        """Retrieve all imports for a user ordered by creation time descending."""
        stmt = (
            select(ImportRecord)
            .where(ImportRecord.user_id == user_id)
            .order_by(desc(ImportRecord.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def count_by_user(db: Session, user_id: uuid.UUID) -> int:
        """Count all imports for a user."""
        stmt = select(ImportRecord).where(ImportRecord.user_id == user_id)
        return len(list(db.scalars(stmt).all()))

    @staticmethod
    def update_status(
        db: Session,
        import_record: ImportRecord,
        status: str,
        accepted_count: Optional[int] = None,
        rejected_count: Optional[int] = None,
        duplicate_count: Optional[int] = None,
        error_summary: Optional[str] = None,
    ) -> ImportRecord:
        """Update processing status and counters for an import."""
        import_record.status = status
        if accepted_count is not None:
            import_record.accepted_count = accepted_count
        if rejected_count is not None:
            import_record.rejected_count = rejected_count
        if duplicate_count is not None:
            import_record.duplicate_count = duplicate_count
        if error_summary is not None:
            import_record.error_summary = error_summary
        if status in ("completed", "failed", "partially_completed"):
            import_record.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(import_record)
        return import_record
