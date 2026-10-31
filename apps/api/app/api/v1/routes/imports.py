"""Import endpoints for statement and notification file ingestion."""
import json
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.ingestion.import_service import ImportService
from app.repositories.import_repository import ImportRepository
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("/preview", status_code=status.HTTP_200_OK)
async def preview_import(
    file: UploadFile = File(...),
    import_type: str = Form("statement"),
    synthetic_confirmed: bool = Form(False),
    column_overrides: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate unpersisted import preview with validation report and duplicate check."""
    if not synthetic_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Synthetic confirmation is required. Only synthetic demo data can be uploaded.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # Parse column overrides if provided
    overrides_dict = None
    if column_overrides:
        try:
            overrides_dict = json.loads(column_overrides)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="column_overrides must be valid JSON object.",
            )

    user = UserRepository.get_or_create_demo_user(db)

    result = ImportService.preview(
        db=db,
        user_id=user.id,
        filename=file.filename or "uploaded_file",
        content=content,
        import_type=import_type,
        synthetic_confirmed=synthetic_confirmed,
        column_overrides=overrides_dict,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to generate preview."),
        )

    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_import(
    file: UploadFile = File(...),
    import_type: str = Form("statement"),
    synthetic_confirmed: bool = Form(False),
    column_overrides: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Execute import and persist valid non-duplicate records to PostgreSQL."""
    if not synthetic_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Synthetic confirmation is required. Only synthetic demo data can be uploaded.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    overrides_dict = None
    if column_overrides:
        try:
            overrides_dict = json.loads(column_overrides)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="column_overrides must be valid JSON object.",
            )

    user = UserRepository.get_or_create_demo_user(db)

    try:
        result = ImportService.execute_import(
            db=db,
            user_id=user.id,
            filename=file.filename or "uploaded_file",
            content=content,
            import_type=import_type,
            synthetic_confirmed=synthetic_confirmed,
            column_overrides=overrides_dict,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", status_code=status.HTTP_200_OK)
def list_imports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve paginated list of previous imports."""
    user = UserRepository.get_or_create_demo_user(db)
    imports = ImportRepository.list_by_user(db, user_id=user.id, limit=limit, offset=offset)
    total_count = ImportRepository.count_by_user(db, user_id=user.id)

    items = []
    for imp in imports:
        items.append({
            "id": str(imp.id),
            "filename": imp.filename_display,
            "file_type": imp.file_type,
            "source_label": imp.source_label,
            "status": imp.status,
            "row_count": imp.row_count,
            "accepted_count": imp.accepted_count,
            "duplicate_count": imp.duplicate_count,
            "rejected_count": imp.rejected_count,
            "created_at": imp.created_at.isoformat() if imp.created_at else None,
            "finished_at": imp.finished_at.isoformat() if imp.finished_at else None,
            "error_summary": imp.error_summary,
        })

    return {
        "items": items,
        "total": total_count,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{import_id}", status_code=status.HTTP_200_OK)
def get_import(
    import_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve detailed metadata for a specific import record."""
    imp = ImportRepository.get_by_id(db, import_id)
    if not imp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found.")

    return {
        "id": str(imp.id),
        "filename": imp.filename_display,
        "file_type": imp.file_type,
        "source_label": imp.source_label,
        "status": imp.status,
        "row_count": imp.row_count,
        "accepted_count": imp.accepted_count,
        "duplicate_count": imp.duplicate_count,
        "rejected_count": imp.rejected_count,
        "created_at": imp.created_at.isoformat() if imp.created_at else None,
        "finished_at": imp.finished_at.isoformat() if imp.finished_at else None,
        "error_summary": imp.error_summary,
    }


@router.get("/{import_id}/status", status_code=status.HTTP_200_OK)
def get_import_status(
    import_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Quick status check for import execution."""
    imp = ImportRepository.get_by_id(db, import_id)
    if not imp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found.")

    return {
        "id": str(imp.id),
        "status": imp.status,
        "accepted_count": imp.accepted_count,
        "duplicate_count": imp.duplicate_count,
        "rejected_count": imp.rejected_count,
        "finished_at": imp.finished_at.isoformat() if imp.finished_at else None,
    }
