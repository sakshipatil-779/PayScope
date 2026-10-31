"""Demo data and sample file download endpoints."""
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
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

