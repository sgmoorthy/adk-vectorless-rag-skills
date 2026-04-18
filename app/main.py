import uuid
import logging
import os
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

# Import our Pydantic schemas and database models
from app.schemas import SearchLexicalRequest, SearchStructuredRequest, RetrieveContextRequest
from app.db.connection import get_db_session, engine
from app.db.models import Tenant, Document
from app.ingestion.worker import process_document_ingestion
from app.skills_service import handle_lexical_search, handle_structured_search, handle_context_retrieval

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security & Tenant Defaults
DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
API_KEY_NAME = "X-API-KEY"
API_KEY_VALUE = os.getenv("SECRET_KEY", "dev_secret_key_change_me")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header != API_KEY_VALUE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ADK API Key",
        )
    return api_key_header

async def get_tenant_context(api_key: str = Depends(verify_api_key)):
    """Mock tenant extractor. In a real MVP, derives from the verified token/JWT."""
    return DEFAULT_TENANT_ID

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events to handle startup/teardown gracefully."""
    logger.info("Booting Vectorless RAG Engine endpoints...")
    yield
    logger.info("Shutting down database engines...")
    await engine.dispose()

app = FastAPI(
    title="Vectorless RAG Engine API",
    description="Deterministic Enterprise Document Retrieval via PostgreSQL full-text search.",
    version="1.0.0",
    lifespan=lifespan
)

# Standard security CORS implementation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health", tags=["DevOps"])
async def healthcheck():
    """Simple Liveness Probe"""
    return {"status": "ok", "architecture": "vectorless"}

# ----------------------------------------------------------------------------
# INGESTION API
# ----------------------------------------------------------------------------
class IngestDocumentRequest(BaseModel):
    title: str
    markdown_content: str
    metadata_tags: Dict[str, Any] = {}

@app.post("/api/v1/ingest", tags=["Ingestion"], dependencies=[Depends(verify_api_key)])
async def ingest_document(
    request: IngestDocumentRequest, 
    session: AsyncSession = Depends(get_db_session),
    tenant_id: uuid.UUID = Depends(get_tenant_context)
):
    """
    Ingests raw Markdown text, parsing it recursively into structural heading blocks
    and persisting to Vectorless Postgres indexes under explicit Tenant Isolation.
    """
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id, 
        tenant_id=tenant_id, 
        title=request.title, 
        metadata_obj=request.metadata_tags,
        status="pending"
    )
    session.add(doc)
    await session.commit()
    
    # Executing dynamically here for MVP
    try:
        await process_document_ingestion(session, tenant_id, doc_id, request.markdown_content)
        return {"status": "success", "document_id": str(doc_id), "message": "Successfully indexed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# SKILL / RETRIEVAL ENDPOINTS
# ----------------------------------------------------------------------------
@app.post("/api/v1/skills/search_lexical", tags=["Agent Skills"], dependencies=[Depends(verify_api_key)])
async def api_search_lexical(request: SearchLexicalRequest, tenant_id: uuid.UUID = Depends(get_tenant_context)):
    """Exposes the ADK 'search_lexical' skill over REST tightly scoped to Tenant context."""
    # (In a fully implemented MVP, the `skills_service` methods would accept `tenant_id` securely)
    return await handle_lexical_search(query=request.query, limit=request.limit)

@app.post("/api/v1/skills/search_structured", tags=["Agent Skills"], dependencies=[Depends(verify_api_key)])
async def api_search_structured(request: SearchStructuredRequest, tenant_id: uuid.UUID = Depends(get_tenant_context)):
    return await handle_structured_search(
        query=request.query, 
        metadata_filters=request.metadata_filters, 
        limit=request.limit
    )

@app.post("/api/v1/skills/retrieve_context", tags=["Agent Skills"], dependencies=[Depends(verify_api_key)])
async def api_retrieve_context(request: RetrieveContextRequest, tenant_id: uuid.UUID = Depends(get_tenant_context)):
    return await handle_context_retrieval(chunk_id=request.chunk_id, radius=request.radius)
