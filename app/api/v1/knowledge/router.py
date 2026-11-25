import io
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.models import KnowledgeDocument
from app.services import rag_service

router = APIRouter(tags=["knowledge"])


class DocumentCreate(BaseModel):
    title: str
    content: str


class SearchRequest(BaseModel):
    query: str


def _doc_to_dict(doc: KnowledgeDocument) -> Dict[str, Any]:
    return {
        "id": doc.id,
        "title": doc.title,
        "content": doc.content,
        "status": doc.status,
        "mime_type": doc.mime_type,
        "chunked": doc.chunked,
        "char_count": doc.char_count,
        "chunk_count": doc.chunk_count,
        "error": doc.error,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _extract_text(raw: bytes, mime_type: str, filename: str) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf") or "pdf" in (mime_type or ""):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to extract text from PDF")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text or PDF")


@router.post("/documents", status_code=201)
async def create_document(
    payload: DocumentCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Content is required")
    doc = rag_service.ingest_document(
        db,
        owner_id=user_id,
        title=payload.title,
        content=payload.content,
        mime_type="text/plain",
    )
    return _doc_to_dict(doc)


@router.post("/documents/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    content = _extract_text(raw, file.content_type or "", file.filename or "")
    doc = rag_service.ingest_document(
        db,
        owner_id=user_id,
        title=title or file.filename or "Untitled document",
        content=content,
        mime_type=file.content_type or "application/octet-stream",
        file_url=file.filename,
    )
    return _doc_to_dict(doc)


@router.get("/documents", response_model=List[Dict[str, Any]])
async def list_documents(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return [_doc_to_dict(doc) for doc in rag_service.list_documents(db, user_id)]


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    doc = (
        db.query(KnowledgeDocument)
        .filter(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.owner_id == user_id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_to_dict(doc)


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if not rag_service.delete_document(db, document_id, user_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return None


@router.post("/search", response_model=List[Dict[str, Any]])
async def search_knowledge(
    payload: SearchRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return rag_service.search(payload.query, user_id, db)
