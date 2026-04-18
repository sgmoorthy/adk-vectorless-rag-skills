import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Computed, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, TSVECTOR
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Tenant(Base):
    __tablename__ = 'tenants'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    
    documents = relationship("Document", back_populates="tenant")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    source_uri = Column(Text, nullable=True)
    local_path = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    metadata_obj = Column('metadata', JSONB, default=dict)
    acl_groups = Column(ARRAY(Text), default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_docs_meta', 'metadata', postgresql_using='gin'),
    )

class Chunk(Base):
    __tablename__ = 'chunks'
    
    # We use composite partitioning on larger scales, but here we enforce tenant_id for shallow indexing.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete="CASCADE"), nullable=False)
    parent_chunk_id = Column(UUID(as_uuid=True), ForeignKey('chunks.id', ondelete="SET NULL"), nullable=True)
    
    path_hierarchy = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # The pure heart of Vectorless FTS
    search_vector = Column(TSVECTOR, Computed(
        "setweight(to_tsvector('english', coalesce(path_hierarchy, '')), 'A') || "
        "setweight(to_tsvector('english', content), 'B')", 
        persisted=True
    ))
    
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index('idx_chunks_fts', search_vector, postgresql_using='gin'),
    )

class SynonymMap(Base):
    __tablename__ = 'synonym_maps'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete="CASCADE"), nullable=False)
    root_term = Column(String(100), nullable=False)
    synonyms = Column(ARRAY(Text), nullable=False)
