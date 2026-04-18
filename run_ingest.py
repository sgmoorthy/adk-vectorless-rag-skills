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
        from app.db.models import Chunk
        import logging
        logging.basicConfig(level=logging.INFO)
        await process_document_ingestion(session, tenant_id, doc_id, sample_markdown)
        print(f"Document Indexed into Vectorless PostgreSQL structure! Doc ID: {doc_id}")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
