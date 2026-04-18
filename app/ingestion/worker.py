import uuid
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, Chunk
from app.ingestion.chunker import MarkdownDeterministicChunker

logger = logging.getLogger(__name__)

async def process_document_ingestion(
    session: AsyncSession, 
    tenant_id: uuid.UUID, 
    document_id: uuid.UUID, 
    markdown_content: str
):
    """
    Simulated Background worker process that parses robust markdown and writes chunks to Postgres.
    """
    try:
        # Load the document
        doc = await session.get(Document, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        # Chunk the text deterministically using architectural constraints
        chunker = MarkdownDeterministicChunker()
        extracted_chunks = chunker.parse_text(markdown_content)
        
        # Linear processing
        db_chunks = []
        for c in extracted_chunks:
            chunk = Chunk(
                tenant_id=tenant_id,
                document_id=document_id,
                path_hierarchy=c["path_hierarchy"],
                content=c["content"],
                chunk_index=c["chunk_index"]
            )
            db_chunks.append(chunk)

        session.add_all(db_chunks)
        doc.status = "indexed"
        
        await session.commit()
        logger.info(f"Successfully processed {len(db_chunks)} chunks for document {document_id}")
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to process ingestion for {document_id}: {str(e)}")
        raise
