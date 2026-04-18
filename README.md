# Vectorless RAG Engine & ADK Skills

This repository provides an enterprise-grade, deterministic, and vectorless Retrieval-Augmented Generation (RAG) platform, built as a suite of async Agent Skills natively integrated with [Google ADK (Python)](https://github.com/google/adk-python).

It actively replaces semantic embedding search with highly configurable **PostgreSQL Full-Text Search (tsvector)** and hierarchical chunk linking, delivering precise, auditable document referencing.

---

## Prerequisites
- **Python 3.10+**
- **Docker Compose** (for local PostgreSQL testing)
- `google-adk`, `sqlalchemy`, `asyncpg`, `alembic`, `pydantic`

## 1. Installation & Environment Setup

First, initialize a python virtual environment and set up your configurations:

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows

# 2. Install required application dependencies
pip install sqlalchemy asyncpg alembic pydantic fastapi uvicorn

# 3. Apply Environment Configs
cp .env.example .env
```

## 2. Infrastructure Spin-up

The vectorless engine operates strictly on PostgreSQL (`uuid-ossp` and `pg_trgm` extensions). Boot the local database sandbox using the provided Docker configuration:

```bash
docker-compose up -d postgres
```

*(Note: Prior to running Alembic, ensure your models export properly in `migrations/env.py`.)* 
Once PostgreSQL is healthy, synchronize the ORM schema via alembic to construct the FTS `chunks` and `documents` tables:

```bash
alembic revision --autogenerate -m "Initial Schema"
alembic upgrade head
```

## 3. Example 1: Ingesting a Document (Vectorless Chunking)

To insert knowledge into the system, you must run text through the deterministic header-aware chunker. The chunker splits documents strictly on structural points (like Markdown headers) instead of pure token overlap, making citations explicit.

Create a quick ingestion script test file (`run_ingest.py`):
```python
import asyncio
import uuid
from app.db.connection import SessionLocal
from app.db.models import Tenant, Document
from app.ingestion.worker import process_document_ingestion

async def run_ingestion():
    async with SessionLocal() as session:
        # 1. Setup Mock Enterprise Tenant & Document definition
        tenant_id = uuid.uuid4()
        session.add(Tenant(id=tenant_id, name="Acme Corp HQ"))
        
        doc_id = uuid.uuid4()
        doc = Document(
            id=doc_id, 
            tenant_id=tenant_id, 
            title="SOP-Database-Failover", 
            status="approved",
            metadata_obj={"status": "approved", "region": "US"}
        )
        session.add(doc)
        await session.commit()

        # 2. Raw Markdown Target
        sample_markdown = """
# Database Failover Procedure
This is the root scope.
## Trigger Conditions
A failover should trigger if ERROR_X99 occurs.
## Approval Steps
1. VP of Engineering must sign off.
2. The network switch must be manually overridden. 
        """

        # 3. Ingest into Vectorless storage
        await process_document_ingestion(session, tenant_id, doc_id, sample_markdown)
        print("Document Indexed into Vectorless PostgreSQL structure!")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
```

Execute this script to fill your text search indexes:
```bash
python run_ingest.py
```

## 4. Example 2: Querying via Autonomous ADK Agents

Now that our Vectorless Postgres Engine holds structural fragments, we can execute intelligent querying using Google ADK. We use the `@skill` service mapped out in `skills_service.py` to route explicit requests directly to PostgreSQL.

Run the provided orchestrator agent example:

```bash
# This script uses the exact vectorless skills to execute natural language agent routing!
python -m app.adk.agents
```

### What Happens Under the Hood?

1. **Coordinator Routing**: The `CoordinatorAgent` reads your prompt: *"Find the latest approved incident response SOP for database failover and summarize."*
2. **Skill Selection**: The `RetrievalSpecialist` Agent identifies that it needs specific policies and invokes the `search_structured` Python skill you provided to it.
3. **Deterministic FTS**: The `search_structured` capability executes pure PostgreSQL `tsvector` lookups. It checks for exact literal strings (like `database failover`) simultaneously filtered aggressively on JSONB tags (e.g., `status: 'approved'`).
4. **Context Assembly**: The agent synthesizes the raw returned text chunks, giving precise references via deterministic `chunk_ids`, ensuring complete explainability without vector drift!
