"""
Photo/video upload router.
Uses Cloudinary for free media storage.
"""
import uuid
import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select
import httpx

from ..config import settings
from ..db import get_db
from ..models import Media, Report

router = APIRouter(prefix="/api/v1", tags=["media"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def upload_to_cloudinary(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Upload file to Cloudinary and return the URL."""
    cloud_name = settings.CLOUDINARY_CLOUD_NAME
    upload_preset = settings.CLOUDINARY_UPLOAD_PRESET

    # Convert to base64
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    data_uri = f"data:{content_type};base64,{b64}"

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/auto/upload"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(upload_url, data={
            "file": data_uri,
            "upload_preset": upload_preset,
            "folder": "crisislens",
            "public_id": f"report_{uuid.uuid4().hex[:8]}",
        })

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Upload failed: {response.text}")

    result = response.json()
    return result["secure_url"]


@router.post("/reports/{report_id}/media")
async def upload_media(
    report_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a photo or video for a report."""

    # Check report exists
    report = db.scalar(select(Report).where(Report.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Validate file type
    content_type = file.content_type or ""
    is_image = content_type in ALLOWED_IMAGE_TYPES
    is_video = content_type in ALLOWED_VIDEO_TYPES

    if not is_image and not is_video:
        raise HTTPException(
            status_code=400,
            detail=f"File type {content_type} not allowed. Use JPEG, PNG, WebP, MP4, or MOV."
        )

    # Read and check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB.")

    # Upload to Cloudinary
    try:
        url = await upload_to_cloudinary(file_bytes, file.filename or "upload", content_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

    # Save media record
    media = Media(
        id=uuid.uuid4(),
        report_id=report_id,
        url=url,
        type="image" if is_image else "video",
    )
    db.add(media)

    # Update photo count
    report.photo_count = (report.photo_count or 0) + 1
    db.add(report)
    db.commit()
    db.refresh(media)

    return {
        "id": str(media.id),
        "report_id": str(report_id),
        "url": url,
        "type": media.type,
    }


@router.get("/reports/{report_id}/media")
def get_media(report_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get all media for a report."""
    report = db.scalar(select(Report).where(Report.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    items = db.scalars(select(Media).where(Media.report_id == report_id)).all()
    return [{"id": str(m.id), "url": m.url, "type": m.type} for m in items]
