"""Local RAG: chunk documents, embed with sentence-transformers (offline fallback),
persist vectors and answer queries with cosine similarity.
"""

import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)

_model = None
_model_loaded = False
FALLBACK_DIM = 384

BUILTIN_KNOWLEDGE = [
    {
        "id": "kb-followup",
        "title": "Follow-up Best Practices",
        "content": "Follow up within 24 hours. Reference specific requirements discussed on the call.",
        "keywords": ["follow", "followup", "callback", "next", "follow up", "follow-up"],
    },
    {
        "id": "kb-qualification",
        "title": "Lead Qualification Criteria",
        "content": "Qualify on need, urgency, budget, authority, and fit.",
        "keywords": ["qualify", "qualification", "budget", "interest", "need", "urgency"],
    },
    {
        "id": "kb-objection",
        "title": "Handling Objections",
        "content": "Acknowledge the concern, clarify value, and offer a human callback when requested.",
        "keywords": ["objection", "expensive", "human", "callback", "handoff", "cost"],
    },
]


def _get_model():
    global _model, _model_loaded
    if _model_loaded:
        return _model
    _model_loaded = True
    try:
        cache = settings.embeddings_cache_dir
        if cache:
            os.makedirs(cache, exist_ok=True)
            os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", cache)
            os.environ.setdefault("HF_HOME", cache)
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Loaded embedding model %s", settings.embedding_model)
    except Exception as exc:
        logger.warning("Embedding model unavailable (%s); using offline hash embeddings", type(exc).__name__)
        _model = None
    return _model


def _hash_embedding(text: str, dim: int = FALLBACK_DIM) -> List[float]:
    vec = np.zeros(dim, dtype=float)
    normalized = (text or "").lower()
    words = re.findall(r"\w+", normalized)
    grams = [
        normalized[i : i + 3]
        for i in range(max(0, len(normalized) - 2))
        if normalized[i : i + 3].strip()
    ]
    for token in words + grams:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        vec[index] += 1.0
    norm = np.linalg.norm(vec) or 1.0
    return (vec / norm).tolist()


def embed(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    model = _get_model()
    if model is not None:
        try:
            vectors = model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=32,
            )
            return [np.asarray(v, dtype=float).tolist() for v in vectors]
        except Exception as exc:
            logger.warning("Embedding failed (%s); using offline hash embeddings", type(exc).__name__)
    return [_hash_embedding(text) for text in texts]


def chunk_text(
    text: str,
    size: Optional[int] = None,
    overlap: Optional[int] = None,
) -> List[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    size = size or settings.rag_chunk_size
    overlap = overlap or settings.rag_chunk_overlap
    size = max(120, size)
    overlap = max(0, min(overlap, size // 2))

    chunks: List[str] = []
    start = 0
    while start < len(raw):
        end = min(start + size, len(raw))
        if end < len(raw):
            window = raw[start:end]
            split = max(window.rfind("."), window.rfind("\n"), window.rfind(" "))
            if split > size // 2:
                end = start + split + 1
        piece = raw[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(raw):
            break
        start = max(start + 1, end - overlap)
    return chunks


def ingest_document(
    db: Session,
    owner_id: str,
    title: str,
    content: str,
    mime_type: str = "text/plain",
    file_url: str = None,
) -> KnowledgeDocument:
    doc = KnowledgeDocument(
        id=str(__import__("uuid").uuid4()),
        title=(title or "Untitled document").strip(),
        content=content,
        mime_type=mime_type,
        file_url=file_url,
        char_count=len(content or ""),
        chunked=False,
        status="processing",
        owner_id=owner_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        chunks = chunk_text(content)
        if not chunks:
            raise ValueError("Document has no extractable text")
        vectors = embed(chunks)
        for index, (piece, vector) in enumerate(zip(chunks, vectors)):
            db.add(
                KnowledgeChunk(
                    id=str(__import__("uuid").uuid4()),
                    document_id=doc.id,
                    owner_id=owner_id,
                    chunk_index=index,
                    content=piece,
                    embedding=json.dumps(vector),
                )
            )
        doc.chunk_count = len(chunks)
        doc.chunked = True
        doc.status = "ready"
        doc.error = None
    except Exception as exc:
        doc.status = "error"
        doc.error = str(exc)[:500]
        logger.warning("Failed to ingest document %s: %s", doc.id, type(exc).__name__)
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, document_id: str, owner_id: str) -> bool:
    doc = (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.id == document_id, KnowledgeDocument.owner_id == owner_id)
        .first()
    )
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True


def list_documents(db: Session, owner_id: str) -> List[KnowledgeDocument]:
    return (
        db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.owner_id == owner_id)
        .order_by(KnowledgeDocument.created_at.desc())
        .all()
    )


def search(
    query: str,
    owner_id: str,
    db: Session,
    top_k: Optional[int] = None,
    min_score: float = 0.05,
) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    top_k = top_k or settings.rag_top_k

    rows = (
        db.query(KnowledgeChunk, KnowledgeDocument.title)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .filter(
            KnowledgeChunk.owner_id == owner_id,
            KnowledgeDocument.status == "ready",
        )
        .all()
    )
    if not rows:
        return []

    query_vector = np.asarray(embed([q])[0], dtype=float)
    scored = []
    for chunk, title in rows:
        try:
            vector = np.asarray(json.loads(chunk.embedding), dtype=float)
        except (TypeError, ValueError):
            continue
        if vector.shape != query_vector.shape:
            continue
        score = float(np.dot(query_vector, vector))
        if score >= min_score:
            scored.append(
                {
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "title": title,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "relevance_score": round(score, 4),
                }
            )
    scored.sort(key=lambda item: item["relevance_score"], reverse=True)
    return scored[:top_k]


def builtin_search(query: str) -> List[Dict[str, Any]]:
    q = (query or "").strip().lower()[:300]
    results = []
    for item in BUILTIN_KNOWLEDGE:
        if any(word in q for word in item["keywords"]) or q in item["content"].lower():
            results.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "content": item["content"],
                    "relevance_score": 0.5,
                }
            )
    return results[: settings.rag_top_k]
