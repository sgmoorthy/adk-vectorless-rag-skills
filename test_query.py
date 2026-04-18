import asyncio
import json
from sqlalchemy import text
from app.db.connection import SessionLocal

async def test_search():
    print("Executing Vectorless PostgreSQL FTS Query...\n")
    async with SessionLocal() as session:
        # We simulate what the skills_service does natively.
        query = "database failover"
        sql = text("""
            SELECT c.id, c.path_hierarchy, c.content, d.title
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.search_vector @@ plainto_tsquery('english', :query)
        """)
        
        result = await session.execute(sql, {"query": query})
        records = result.mappings().fetchall()
        
        if records:
            print(f"Found {len(records)} Exact Match Chunks!\n")
            for r in records:
                print(f"--- MATCH IN DOCUMENT: {r['title']} ---")
                print(f"HIERARCHY: {r['path_hierarchy']}")
                print(f"CONTENT:\n{r['content']}")
                print("-" * 50)
        else:
            print("No matches found.")

if __name__ == "__main__":
    asyncio.run(test_search())
