import asyncio
from google_adk.agent import Agent
from google_adk.skills import SkillProvider

# The skills_service.py exposes our decorated RAG skills natively
rag_provider = SkillProvider(
    service_script="app/skills_service.py",
    env={"DATABASE_URL": "postgresql+asyncpg://admin:pass@localhost:5432/rag"}
)

retrieval_specialist = Agent(
    name="RetrievalSpecialist",
    instructions="""
    You are an expert at retrieving precise enterprise policies and IT runbooks.
    You operate on a Vectorless RAG architecture.
    
    RULES:
    1. Always use 'search_lexical' with specific terms or policy numbers.
    2. If a policy has a strict status requirement (e.g. 'approved'), use 'search_structured'.
    3. If you find a relevant chunk, but need the paragraph before/after to understand the full context, use the 'retrieve_context' skill on its ID.
    4. CITE the source document_id and chunk_id in your response.
    """,
    skills=rag_provider.get_skills()
)

coordinator_agent = Agent(
    name="CoordinatorAgent",
    instructions="""
    You are the primary interface. Determine if the user's request requires internal policy knowledge.
    If it does, delegate the query directly to RetrievalSpecialist. Synthesize the response back to the user clearly.
    """,
    sub_agents=[retrieval_specialist]
)

if __name__ == "__main__":
    async def run_example():
        query = "Find the latest approved incident response SOP for database failover and summarize."
        print(f"Executing Query: {query}\n")
        
        # Dispatch to coordinator
        response = await coordinator_agent.run(query)
        print("Final Synthesis:")
        print(response)

    asyncio.run(run_example())
