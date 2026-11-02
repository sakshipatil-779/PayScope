"""Demo data and sample file download endpoints."""
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.generators.config import GeneratorConfig
from app.generators.dataset_generator import DatasetGenerator
from app.generators.export_generator import export_dataset

router = APIRouter(prefix="/demo", tags=["Demo Data"])

# Allowed downloadable files
ALLOWED_SAMPLE_FILES = {
    "synthetic_bank_statement.csv": {
        "description": "Standard synthetic multi-month bank statement with 12 recurring scenarios and daily living expenses.",
        "media_type": "text/csv",
        "format": "csv",
    },
    "synthetic_bank_statement.xlsx": {
        "description": "Excel spreadsheet version of the synthetic bank statement with identical records.",
        "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "format": "xlsx",
    },
    "synthetic_payment_notifications.json": {
        "description": "Synthetic multi-channel payment and mandate notifications covering mandate creation, cancellation, price hikes, and alerts.",
        "media_type": "application/json",
        "format": "json",
    },
    "dataset_manifest.json": {
        "description": "Deterministic dataset manifest detailing seed, scenario coverage, and aggregate transaction amounts.",
        "media_type": "application/json",
        "format": "json",
    },
}


def _get_sample_data_dir() -> Path:
    """Resolve sample_data directory relative to repository root."""
    candidate = Path(__file__).resolve()
    for p in candidate.parents:
        if (p / "MandateLens_Project_Docs").exists():
            return p / "sample_data"
    return Path.cwd() / "sample_data"


class GenerateRequest(BaseModel):
    seed: int = 42


@router.get("/sample-files", status_code=status.HTTP_200_OK)
def list_sample_files() -> List[Dict[str, Any]]:
    """List available synthetic sample files with metadata."""
    sample_dir = _get_sample_data_dir()
    results = []

    for filename, meta in ALLOWED_SAMPLE_FILES.items():
        file_path = sample_dir / filename
        size_bytes = file_path.stat().st_size if file_path.exists() else 0
        exists = file_path.exists()
        results.append({
            "filename": filename,
            "format": meta["format"],
            "description": meta["description"],
            "size_bytes": size_bytes,
            "available": exists,
            "download_url": f"/api/v1/demo/sample-files/{filename}",
        })

    return results


@router.get("/sample-files/{filename}")
def download_sample_file(filename: str):
    """Safely stream a synthetic sample file preventing path traversal."""
    # Strict whitelist check
    if filename not in ALLOWED_SAMPLE_FILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' is not an authorized sample file.",
        )

    # Path traversal protection
    if Path(filename).name != filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename specified.",
        )

    sample_dir = _get_sample_data_dir()
    file_path = sample_dir / filename

    if not file_path.exists():
        # Auto-generate if missing
        config = GeneratorConfig(seed=42)
        generator = DatasetGenerator(config)
        dataset = generator.generate()
        export_dataset(dataset, sample_dir)

    meta = ALLOWED_SAMPLE_FILES[filename]
    return FileResponse(
        path=str(file_path),
        media_type=meta["media_type"],
        filename=filename,
    )


@router.post("/generate", status_code=status.HTTP_200_OK)
def generate_sample_data(req: GenerateRequest) -> Dict[str, Any]:
    """Trigger deterministic generation of synthetic sample data files with specified seed."""
    sample_dir = _get_sample_data_dir()
    config = GeneratorConfig(seed=req.seed)
    generator = DatasetGenerator(config)
    dataset = generator.generate()
    exported = export_dataset(dataset, sample_dir)

    return {
        "success": True,
        "seed": req.seed,
        "manifest": dataset["manifest"],
        "files_generated": [p.name for p in exported.values()],
    }


@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_demo_workspace(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Idempotently seed canonical merchants, synthetic bank transactions, recurring commitments, and insights."""
    from datetime import datetime, timezone
    from app.matching.seed_merchants import seed_canonical_merchants
    from app.ingestion.import_service import ImportService
    from app.analytics.commitment_detector import CommitmentDetector
    from app.analytics.insights import run_insight_detection
    from app.matching.reprocessor import TransactionReprocessor
    from app.repositories.user_repository import UserRepository
    from app.models.transaction import Transaction
    from app.models.commitment import Commitment

    # 1. Seed canonical merchants
    merchant_stats = seed_canonical_merchants(db)

    # 2. Get or create demo user
    user = UserRepository.get_or_create_demo_user(db)

    # 3. Check if transactions exist; if not, import sample CSV
    tx_count = db.query(Transaction).filter(Transaction.user_id == user.id).count()
    imported_rows = 0
    if tx_count == 0:
        sample_dir = _get_sample_data_dir()
        csv_file = sample_dir / "synthetic_bank_statement.csv"
        if not csv_file.exists():
            config = GeneratorConfig(seed=42)
            dataset = DatasetGenerator(config).generate()
            export_dataset(dataset, sample_dir)
        with open(csv_file, "rb") as f:
            content = f.read()
        res = ImportService.execute_import(
            db=db,
            user_id=user.id,
            filename="synthetic_bank_statement.csv",
            content=content,
            import_type="statement",
            synthetic_confirmed=True,
        )
        imported_rows = res.get("accepted_count", 0)

    # 4. Reprocess any transactions with unassigned merchants
    reprocess_report = TransactionReprocessor.reprocess(db, user_id=user.id)

    # 5. Discover commitments
    detector = CommitmentDetector(db)
    discovery = detector.discover_user_commitments(user.id)

    # 6. Confirm representative commitments for demo
    commitments = db.query(Commitment).filter(Commitment.user_id == user.id).all()
    confirmed_count = 0
    now = datetime.now(timezone.utc)
    for c in commitments:
        if c.cadence in ("monthly", "annual", "quarterly", "weekly"):
            c.status = "user_confirmed"
            c.user_decision = "confirmed"
            c.confidence_band = "high"
            c.user_decision_at = now
            c.updated_at = now
            confirmed_count += 1

    db.commit()

    # 7. Run insight detection
    insights_summary = run_insight_detection(db, user.id)

    return {
        "success": True,
        "merchants": merchant_stats,
        "transactions_imported": imported_rows,
        "reprocessed": reprocess_report,
        "total_discovered": discovery.total_discovered,
        "commitments_confirmed": confirmed_count,
        "insights_detected": insights_summary.total_detected if hasattr(insights_summary, "total_detected") else 0,
    }


