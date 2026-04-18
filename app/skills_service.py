import json
from typing import Dict, Any
from sqlalchemy import text
from google_adk.skills import skill
from google_adk.telemetry import trace

# For local tests and vectorless architecture execution
from app.db.connection import SessionLocal

def format_as_skill_output(records: list) -> str:
    """Format DB dicts to a clean JSON string for the Agent's context window."""
    if not records:
        return json.dumps({"message": "No evidence found matching the exact query."})
    return json.dumps([dict(r) for r in records], default=str)

@skill(name="search_lexical")
@trace()
async def handle_lexical_search(query: str, limit: int = 5) -> str:
    """Perform a strict lexical FTS search securely using Vectorless principles."""
    async with SessionLocal() as session:
        # Utilizing plainto_tsquery for pure structural FTS
        sql = text("""
            SELECT id, document_id, path_hierarchy, content, 
                   ts_rank(search_vector, plainto_tsquery('english', :query)) as rank 
            FROM chunks 
            WHERE search_vector @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """)
        
        result = await session.execute(sql, {"query": query, "limit": limit})
        records = result.mappings().fetchall()
        
    return format_as_skill_output(records)

@skill(name="search_structured")
@trace()
async def handle_structured_search(query: str, metadata_filters: str, limit: int = 5) -> str:
    """Perform FTS combined with deep metadata attribute filters."""
    # Decode JSON internally
    try:
        filters_dict = json.loads(metadata_filters)
    except json.JSONDecodeError:
        filters_dict = {}

    async with SessionLocal() as session:
        # Safe binding via postgres jsonb
        sql = text("""
            SELECT c.id, c.document_id, c.path_hierarchy, c.content 
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.search_vector @@ plainto_tsquery('english', :query)
              AND d.metadata @> :filters::jsonb
            LIMIT :limit
        """)
        
        result = await session.execute(sql, {
            "query": query, 
            "filters": json.dumps(filters_dict),
            "limit": limit
        })
        records = result.mappings().fetchall()
        
    return format_as_skill_output(records)

@skill(name="retrieve_context")
@trace()
async def handle_context_retrieval(chunk_id: str, radius: int = 1) -> str:
    """Pulls exactly sibling paragraphs above and below for context continuity."""
    # A true vectorless superpower: deterministic adjacent block iteration.
    async with SessionLocal() as session:
        sql = text("""
            WITH target_chunk AS (
                SELECT document_id, chunk_index FROM chunks WHERE id = :chunk_id::uuid
            )
            SELECT id, chunk_index, content
            FROM chunks
            WHERE document_id = (SELECT document_id FROM target_chunk)
              AND chunk_index BETWEEN ((SELECT chunk_index FROM target_chunk) - :radius) 
                                  AND ((SELECT chunk_index FROM target_chunk) + :radius)
            ORDER BY chunk_index ASC
        """)
        result = await session.execute(sql, {"chunk_id": chunk_id, "radius": radius})
        records = result.mappings().fetchall()
        
    return format_as_skill_output(records)
