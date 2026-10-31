"""File validator enforcing size, type, and synthetic confirmation."""
import hashlib
from dataclasses import dataclass
from typing import List, Optional, Set

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS: Set[str] = {".csv", ".xlsx", ".json"}


@dataclass
class FileValidationResult:
    """Outcome of file pre-validation."""

    is_valid: bool
    filename: str
    extension: str
    file_size_bytes: int
    checksum_sha256: str
    error_message: Optional[str] = None


class FileValidator:
    """Validates uploaded files against security, size, and prototype constraints."""

    @staticmethod
    def validate_upload(
        filename: str,
        content: bytes,
        synthetic_confirmed: bool,
    ) -> FileValidationResult:
        """Validate an uploaded file before parsing."""
        # 1. Enforce synthetic data confirmation
        if not synthetic_confirmed:
            return FileValidationResult(
                is_valid=False,
                filename=filename,
                extension="",
                file_size_bytes=len(content),
                checksum_sha256="",
                error_message=(
                    "Import rejected: Explicit confirmation is required that this file contains "
                    "only synthetic demo data. Real financial statements must never be uploaded."
                ),
            )

        # 2. Check file size
        file_size = len(content)
        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            return FileValidationResult(
                is_valid=False,
                filename=filename,
                extension="",
                file_size_bytes=file_size,
                checksum_sha256="",
                error_message=f"File exceeds maximum allowed size of {max_mb} MB (received {actual_mb:.2f} MB).",
            )

        if file_size == 0:
            return FileValidationResult(
                is_valid=False,
                filename=filename,
                extension="",
                file_size_bytes=0,
                checksum_sha256="",
                error_message="Uploaded file is empty (0 bytes).",
            )

        # 3. Check file extension
        lower_name = filename.lower()
        matched_ext = next((ext for ext in ALLOWED_EXTENSIONS if lower_name.endswith(ext)), None)
        if not matched_ext:
            allowed_list = ", ".join(ALLOWED_EXTENSIONS)
            return FileValidationResult(
                is_valid=False,
                filename=filename,
                extension="",
                file_size_bytes=file_size,
                checksum_sha256="",
                error_message=f"Unsupported file format. Supported file types: {allowed_list}",
            )

        # 4. Compute SHA256 checksum
        checksum = hashlib.sha256(content).hexdigest()

        return FileValidationResult(
            is_valid=True,
            filename=filename,
            extension=matched_ext,
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            error_message=None,
        )
