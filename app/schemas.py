from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SearchLexicalRequest(BaseModel):
    query: str = Field(..., description="The query term to perform full text search on.")
    limit: int = Field(5, description="Maximum number of chunks to return.")

class SearchStructuredRequest(BaseModel):
    query: str = Field(..., description="The exact FTS query.")
    metadata_filters: str = Field(
        ..., description="JSON string filters to apply, e.g. '{\"status\": \"approved\"}'"
    )
    limit: int = Field(5, description="Maximum number of chunks to return.")

class RetrieveContextRequest(BaseModel):
    chunk_id: str = Field(..., description="The specific chunk UUID to expand context for.")
    radius: int = Field(1, description="Number of sibling chunks to pull before and after.")
