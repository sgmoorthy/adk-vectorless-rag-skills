# Vectorless RAG Platform Architecture

## System Visual Architecture
```mermaid
graph TD
    classDef adk fill:#4285F4,stroke:#fff,color:#fff,stroke-width:2px;
    classDef postgres fill:#336791,stroke:#fff,color:#fff,stroke-width:2px;
    classDef worker fill:#34A853,stroke:#fff,color:#fff,stroke-width:2px;
    classDef external fill:#FABB05,stroke:#fff,color:#333,stroke-width:2px;
    
    User[User / Client]:::external -->|Natural Language Query| CA[ADK Coordinator Agent]:::adk
    
    subgraph "Google ADK Ecosystem"
        CA -->|Delegates Context| RS[ADK Retrieval Specialist]:::adk
        RS -->|Invokes Native Skills| SK[Vectorless Skills Service]:::adk
    end
    
    subgraph "Ingestion Pipeline (Async)"
        DOC[Raw Docs: PDF/DOCX]:::external -->|Upload POST| WA[FastAPI Ingestion Worker]:::worker
        WA -->|Structural Parsing| C[Deterministic Markdown Chunker]:::worker
    end
    
    subgraph "Vectorless FTS Datastore"
        C -->|Persists UUID Chunks| DB[(PostgreSQL + pg_trgm)]:::postgres
        SK -->|Executes Exact tsquery| DB
        DB -->|Returns Strict Formatted Diffs| SK
    end
```

## 1. EXECUTIVE GOAL
The Vectorless RAG platform solves the opacity, unpredictability, and non-determinism of embedding-based Retrieval-Augmented Generation systems. Traditional vector databases struggle with exact phrase matching (e.g., specific error codes, UUIDs, or policy numbers), lack debuggable explanation capabilities, and often fail in strict compliance boundary scenarios.

By reverting to a highly tuned **vectorless architecture**—combining PostgreSQL full-text search (tsvector/tsquery), lexical frequency matching, hierarchical chunk traversal, and metadata filtering—we create a retrieval system that is **100% deterministic and explainable**. This is critical for enterprise regulated environments (Audit, Legal, HR) where proving *why* a particular chunk was retrieved is just as important as the retrieval itself.

This platform implements the semantic retrieval layer natively as **Agent Skills**, making these exact-match capabilities effortlessly available to autonomous AI agents built via **Google ADK (Python)**. It provides a foundational bedrock for auditable agentic behavior. Future hybrid paths allow BM25/sparse-vector plugins exclusively behind configuration flags.

## 2. TARGET ARCHITECTURE
The system operates across highly decoupled layers to ensure scalability and auditability.

*   **Content Ingestion Layer**: Monitors configurable local storage paths, handles format normalization.
*   **Document Normalization Layer**: Converts PDF, HTML, DOCX into clean Markdown.
*   **Parsing and Segmentation Layer**: Executes heading-aware and semantic boundaries chunking.
*   **Indexing Layer**: Builds inverse term maps, `tsvector` Postgres indexes, and trigram logic.
*   **Query Understanding Layer**: Intercepts natural queries, extracts structured parameters (e.g., date ranges), and expands acronyms.
*   **Retrieval and Ranking Layer**: Executes FTS, processes document link traversals, and scores via defined heuristics.
*   **Context Assembly Layer**: Merges overlapping chunks and neighboring siblings.
*   **Skill Execution Layer**: Standardized native or remote skill endpoints.
*   **ADK Integration Layer**: Ground-up prompt alignment for skill calling.
*   **Persistence Layer**: Local disk + PostgreSQL instances.
*   **Security and Governance Layer**: RBAC/ABAC checking on every SQL execution.
*   **Observability Layer**: Logs, traces, indexing health.

### Architecture Diagram
```text
+---------------------+      +---------------------+
| Google ADK Agents   | <--> | Skill Execution Layer|
| (Coordinator, Sub)  |      | (Skill Abstraction)  |
+---------------------+      +---------------------+
                                       |
+-------------------------------------------------------------+
|               Query Processing & Ranking Layer              |
| [Query Intent] -> [Retrieval Strategy] -> [Score & Rerank]  |
+-------------------------------------------------------------+
                               |
+------------------------------+------------------------------+
| Security & Governance Layer (RBAC / Row-Level Tenant ACLs)  |
+------------------------------+------------------------------+
               |                               |
+------------------------------+ +----------------------------+
|      PostgreSQL Tier         | |      Local File Tier       |
| (Indexes, Meta, Graph Links) | | (Raw, Clean Source Snap)   |
+------------------------------+ +----------------------------+
               ^
+-------------------------------------------------------------+
|  Ingestion Pipeline (Parse -> Extract -> Chunk -> Index)    |
+-------------------------------------------------------------+
```

## 3. VECTORLESS RAG PRINCIPLES
The architecture embraces retrieval determinism:
*   **PostgreSQL Full-Text Search (tsvector/tsquery)**: English stemming and lexing support. Robust token matching with `limit`/`offset` efficiency.
*   **Keyword Retrieval with Field Boosting**: Titles (`A`), Headings (`B`), and Content (`C/D`).
*   **Exact Match & Phrase Match**: Supported via strict SQL matching (`LIKE`, regex).
*   **Fuzzy Term Matching**: Supported via `pg_trgm` extensions for OCR mistakes.
*   **Metadata Filtering**: High-speed JSONB (`@>`) querying for dates, tags, authors.
*   **Citation/Provenance-aware**: Every text node links to a parent `document_id`.
*   **Hierarchical Retrieval**: Pulling an entire `section` if `chunk` matches highly.
*   **Symbolic Query Expansion**: Normalizing "k8s" to "kubernetes" via a lookup table.
*   **Temporal & ACL Filtering**: Non-negotiable `WHERE act_group IN (...)` wrapping.
*   **Rule-based Reranking**: Combining TF-IDF logic with "document authority" and "recency".
*   **Document-link Traversal**: Hard-link graph extraction (e.g., parsing `See SOP-415`).

*Strengths*: Auditable, easily debuggable, flawless exact matching, lightweight hardware footprint.
*Weaknesses*: Struggles with pure semantic intent (e.g., "what's the vibe of this doc"). Mitigated via synonym expansion.

## 4. USE CASES
| Use Case | Retrieval Behavior | Ranking Priority |
| :--- | :--- | :--- |
| **Compliance Policy Lookup** | Exact Title match on policy ID. | Title match > Content FTS. |
| **HR Policy Lookup** | Filter by `region=US`, FTS on query terms. | Metadata > Recent Updates. |
| **IT Runbook Retrieval** | Title and phrase matching. | Exact heading matches. |
| **Incident SOP Lookup** | Error code specific strict search. | Exact term frequency (TF). |
| **Audit Evidence Lookup** | Temporal querying over date ranges. | Date relevance. |
| **Contract Clause**| Section-title specific querying. | Section title match. |
| **Product Support** | FTS combined with `version=v2` tags. | Version strictness. |
| **KB Article Search** | Fuzzy trigram match for misspelled tech terms.| Trigram similarity > FTS. |
| **Multi-Doc Cross-Ref** | Extracting links and doing neighbor lookups. | Graph-link traversal. |
| **Agent Tool Grounding**| Narrow context window retrieval. | Exact context continuity. |

## 5. AGENT SKILL SUITE
The system exposes 29 granular skills. A sample subset:

*   **`search_lexical`**: FTS retrieval. Input: `query`, `collection`, `limit`. Output: List of text chunks with URLs.
*   **`search_phrase`**: Exact literal match. Input: `phrase`. Output: Matched sentences.
*   **`search_structured`**: FTS mixed with complex JSONB filters. Input: `query`, `metadata_filters`.
*   **`retrieve_context`**: Pulls surrounding items given a chunk ID. Input: `chunk_id`, `radius`.
*   **`explain_retrieval`**: Yields explainability object for a query. Output: Scoring weights list.
*   **`ingest_document`**: Admin restricted. Input: `filepath`, `acls`. Async processing.
*   **`get_source_status`**: Polls ingestion queue.
*   **`trace_provenance`**: Returns the lineage of a document snippet (version, timestamp, ingested by).

*Skill Modifiers*: Read operations are autonomous-safe. Mutating skills (`ingest_document`, `rebuild_index`) require `require_human_approval` flags.

## 6. ADK INTEGRATION
ADK integrates with the platform by consuming these capabilities as native agent skills.
```python
from google_adk.agent import Agent
from google_adk.skills import SkillProvider

# Register Vectorless RAG Skills
rag_provider = SkillProvider(
    service_script="app/skills_service.py", 
    env={"TENANT_ID": "acme-corp"}
)

# Routing / Specialist Agent
retrieval_agent = Agent(
    name="PolicyRetrievalSpecialist",
    instructions="""
    You are an expert at finding enterprise policies. Use exact matching for policy IDs.
    If multiple chunks are found, use 'retrieve_context' to read surrounding paragraphs.
    Always cite the source document ID.
    """,
    skills=rag_provider.get_skills()
)
```
Agent uses skills dynamically, applying logical AND/OR via the `search_structured` capability.

## 7. DATA MODEL (PostgreSQL Schema)
*Note: For high-scale multi-tenancy, declarative partitioning on `tenant_id` is functionally required across `documents` and `chunks` to keep FTS indexes shallow.*
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),
    title VARCHAR(255),
    source_uri TEXT,
    local_path TEXT,
    status VARCHAR(50),
    metadata JSONB,
    acl_groups TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_docs_meta ON documents USING GIN(metadata);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    parent_chunk_id UUID REFERENCES chunks(id),
    path_hierarchy TEXT,
    content TEXT,
    chunk_index INT,
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(path_hierarchy, '')), 'A') || 
        setweight(to_tsvector('english', content), 'B')
    ) STORED
);
CREATE INDEX idx_chunks_fts ON chunks USING GIN(search_vector);

CREATE TABLE synonym_maps (
    id SERIAL PRIMARY KEY,
    tenant_id UUID,
    root_term VARCHAR(100),
    synonyms TEXT[]
);
```

## 8. LOCAL STORAGE STRATEGY
Disk acts as an immutable ledger. 
*   **Directory Structure**: `/data/{tenant_id}/raw/{YYYY}/{MM}/{doc_id}.pdf`
*   **Normalized path**: `/data/{tenant_id}/normalized/{doc_id}.md`
*   **Checksums**: SHA-256 computed on upload. Updates create new folders.
*   **Air-gapped friendly**: No external blob-store dependencies required.

## 9. INGESTION PIPELINE
Pipeline follows an asynchronous queue pattern (e.g., Celery/Redis or simple Postgres SKIP LOCKED).
1.  **Intake**: Save to local disk.
2.  **Normalization**: Apache Tika / MarkItDown to convert to markdown.
3.  **Parsing**: Markdown heading parser (H1, H2, H3).
4.  **Chunking**: *Deterministic*. Splits by heading boundaries. If > 1000 tokens, splits by sentences (no overlap needed since hierarchical references hold context).
5.  **Extraction**: Regex for URLs, acronyms.
6.  **DB Commit**: Inserts `documents` > `chunks`.

## 10. QUERY PROCESSING PIPELINE
*Pseudocode implementation:*
```python
def process_query(user_query, user_acls, metadata_filters):
    norm_query = expand_acronyms(user_query) # e.g. AWS -> Amazon Web Services
    
    # Base FTS Query
    sql = "SELECT id, content, ts_rank(search_vector, plainto_tsquery($1)) as rank "
    sql += "FROM chunks WHERE search_vector @@ plainto_tsquery($1)"
    
    # Strict ACL Wrapper
    sql += f" AND document_id IN (SELECT id FROM documents WHERE acl_groups && array{user_acls})"
    
    if metadata_filters:
        sql += " AND ... jsonb filtering ... "
        
    results = db.fetch(sql, [norm_query])
    return rerank_and_dedupe(results)
```

## 11. RANKING AND EXPLAINABILITY
Reranking uses a deterministic weighted formula:
`Score = (FTS_Rank * 0.5) + (Title_Match_Boost * 0.3) + (Recency_Penalty * 0.2)`
Explainability object returned by the `explain_retrieval` skill:
```json
{
  "chunk_id": "abc-123",
  "score": 0.85,
  "factors": {
     "lexical_match": 0.60,
     "title_bonus": 0.20,
     "metadata_boost": 0.05
  },
  "provenance_chain": "Root -> IT Rules -> Sec 3"
}
```

## 12. SECURITY AND GOVERNANCE
*   **Tenant Isolation**: Tenant ID implicitly prefixed on all reads.
*   **RBAC/ABAC**: PostgreSQL array overlaps (`&&`) for user-groups against chunk-level ACL configurations.
*   **Prompt Injection**: All retrieved text is encapsulated in clear XML tags (`<source id="...">...</source>`) during ADK composition to prevent confused deputy attacks.
*   **Skill Safety**: Skill configuration flags `require_human_approval=True` for destructive actions.

## 13. OBSERVABILITY AND OPERATIONS
*   **Logging**: Structured JSON logs.
*   **Metrics**: `index_queue_depth`, `retrieval_latency_ms`, `average_chunks_returned`.
*   **Detecting Drift**: Monitoring if search term misses are unusually high (candidate for synonym map update).

## 14. DEPLOYMENT TOPOLOGY
*Recommended Minimum Enterprise Baseline*:
**Docker Compose / Single Node**
*   Container 1: Python Skill Service (FastAPI / ADK Skills backend).
*   Container 2: PostgreSQL 16 (with `pg_trgm`).
*   Volume 1: Local NVMe mapped to `/data` structure.
*   *Future*: Easily transitions to Kubernetes (Deployments + PVCs).

## 15. REFERENCE IMPLEMENTATION (Repository Structure)
```
app/
  skills/          # Agent Skill implementations and schemas
  adk/             # Google ADK agent configurations and workflow
  ingestion/       # Format parsers, Chunkers, Workers
  retrieval/       # FTS execution, ranking math
  db/              # SQLAlchemy models, sessions
  security/        # ACL parsers and interceptors
migrations/        # Alembic
docker-compose.yml
```

## 16. SKILL INTEGRATION DESIGN
Implementation using strict ADK paradigms.
```python
from google_adk.skills import skill
from google_adk.telemetry import trace

@skill(name="search_lexical")
@trace()
async def handle_lexical_search(query: str, limit: int = 5) -> str:
    """Perform a strict lexical FTS search securely."""
    # Auth context derived from agent session
    # Yields JSON array string
    results = await retrieval_engine.run_fts_async(query, limit)
    return format_as_skill_output(results)
```

## 17. ADK EXAMPLE
**Query**: "Find the latest approved incident response SOP for database failover and summarize."
1.  **Coordinator Agent**: Infers need for external knowledge. Calls `search_structured(query="database failover incident response", filters={"status":"approved"})`.
2.  **Skill Execution**: Executes tsvector match heavily weighing title vectors. Returns top 3 chunks with provenance IDs.
3.  **Citation Verifier**: Synthesizes output, appending source URIs implicitly provided by the skill response.

## 18. CONFIGURATION (YAML/ENV)
```yaml
# config.yaml
skill_service:
  host: 0.0.0.0
  port: 8080
database:
  connection: postgresql://admin:pass@postgres:5432/rag
  pool_size: 20
retrieval:
  weights:
    title: 1.5
    content: 1.0
  enable_bm25_extension: false # Experimental
ingestion:
  max_chunk_chars: 2048
  storage_root: /data/documents
```

## 19. TESTING STRATEGY
*   **Unit Tests**: Validate text segmentation boundaries (Mocking DB).
*   **Relevance Tests**: Assert `search_phrase("XYZ")` returns Doc A before Doc B.
*   **ACL Testing**: Feed query under unprivileged user, assert HTTP 403 or empty array.
*   **Regression**: "Golden set" of 50 common queries against static fixtures yielding consistent ranking arrays.

## 20. SAMPLE QUERIES (Selection)
*   *Query*: `<SYS-101> fail error` -> *Skill*: `search_phrase` -> *Result*: Exact line match from SysAdmin manual.
*   *Query*: `When do US holidays apply?` -> *Skill*: `search_structured`, filtering metadata `region: US` -> *Ranking*: FTS + recency.
*   *Query*: `Is John approved for travel?` -> *Failure Handling*: FTS returns 0, agent correctly states "no evidence found" rather than hallucinating derived embedding sentiment.

## 21. IMPLEMENTATION ROADMAP
*   **Phase 1**: Ingestion MVP (Parsers, DB, `tsvector` generation).
*   **Phase 2**: Retrieval MVP (Python abstraction over PG).
*   **Phase 3**: Agent Skill Exposure & Testing suite.
*   **Phase 4**: ADK Integration and Multi-Agent definition.
*   **Phase 5**: Rollout (RBAC hooks, Monitoring dashboards).

## 22. DESIGN DECISIONS AND TRADE-OFFS
*   **Vectorless vs Sector**: Abandoning embeddings loses zero-shot semantic inferences (e.g. knowing "car" ~ "automobile"). We trade semantic magic for 100% deterministic, auditable exactness, mitigating this loss via manual `synonym_maps` which are safer for corporate governance.
*   **FTS vs Extended BM25**: Native FTS requires 0 extensions on managed Postgres (RDS/CloudSQL). Custom BM25 extensions are harder to host. FTS works elegantly.
*   **Local Disk vs S3**: Directory structures are natively debuggable and fast for single-node Enterprise IT bounds.

---
## 23. PROMPTS FOR CODE GENERATION
Use these exact prompts with your AI coding assistant to generate the next layers of implementation:

1. "Generate the SQLAlchemy data models and corresponding Alembic migration script for the Vectorless RAG architecture, covering tenants, documents, chunks, and synonym_maps. Ensure pg_trgm and uuid-ossp are enabled."
2. "Generate the Python Skill Backend (skills_service.py) using the Google ADK, implementing the search_lexical, search_structured, and retrieve_context skill definitions with Pydantic schemas."
3. "Generate the python ingestion pipeline focusing on heading-aware deterministic chunking of Markdown documents, maintaining parent-child node relationships."
4. "Generate the Google ADK Python script creating a Coordinator Agent and a Retrieval Specialist Agent that utilizes the defined agent skills to respond to Enterprise SOP queries."
5. "Generate the Docker Compose file structure and environment variable definitions to stand up the Postgres DB, Python Skill service, and an initialized schema volume."

---
## 24. UPSTREAM STRATEGY (google/adk-python)
To successfully issue these capabilities via a PR to the official `google/adk-python` repository, we must strict-box the contribution. A centralized Vectorless Storage backend is incompatible with a pure agent framework core, so the contribution must be focused and lightweight:

1. **Decouple the Framework from the Engine**: The `adk-python` repository is an agentic framework. We cannot commit the background ingestion workers or the local file watchers there. The PR should *strictly* include the **Agent Skills** (the Python modules that run FTS queries) and the **Pydantic schemas** under a designated package such as `google_adk.skills.rag.vectorless`.
2. **Native Async Operations**: `adk-python` heavily utilizes `asyncio`. The FTS SQL query execution within the skills must use `asyncpg` or async SQLAlchemy (`ext.asyncio`). All skill functions (`@skill`) must be `async def` and strictly `await` database results.
3. **Optional Dependencies (Extras)**: Dependencies like `asyncpg` and `sqlalchemy` cannot be forced onto all standard ADK users. The PR must introduce an extra dependency group in the `pyproject.toml` (e.g., `pip install google-adk[vectorless-rag]`).
4. **Telemetry & Tracing**: ADK requires pervasive observability. Every skill execution must be wrapped in ADK's native `@trace()` spans so that skill invocations and exact FTS parameters are transparent within ADK's debugging and metric viewer.
5. **Database Session Handler**: The skills must rely on ADK's existing `DatabaseSessionService` (or similar persistent state configurations) to manage and retrieve the PostgreSQL connection pool rather than instantiating ad-hoc database engines.
6. **Testing Validation**: Write comprehensive Pytest modules using `pytest-asyncio`. The tests must heavily mock the async DB returns so that the upstream `adk-python` CI/CD pipeline completes instantly without depending on a physical PostgreSQL harness in the runner.

---
## 25. SCALING & PERFORMANCE EVALUATION (End-to-End)
To dynamically scale this architecture for a Tier-1 enterprise deployment (e.g., millions of documents, thousands of concurrent ADK agents), the following architectural transitions must be enforced:

1. **Database Partitioning & Sharding**:
   - *Current*: A monolithic `chunks` table.
   - *Scale Requirement*: PostgreSQL declarative partitioning by `tenant_id`. This guarantees that FTS (`tsvector`) indexes remain shallow and queries traverse rapidly by instantly pruning irrelevant tenant partitions.
2. **Storage Layer Migration**:
   - *Current*: Local disk (`/data/`) designated as an "immutable ledger".
   - *Scale Requirement*: Replacements via high-availability Object Storage (Amazon S3, Google GCS, or on-prem MinIO). This enables horizontal scaling of stateless Kubernetes pods for format conversion and chunking without POSIX filesystem lock contention.
3. **Ingestion Queue Fan-Out**:
   - *Current*: Simple Postgres `SKIP LOCKED` job patterns.
   - *Scale Requirement*: Migrating the ingestion intake to a distributed event broker (Kafka, PubSub, or SQS). Dedicated headless Kubernetes worker pools handle CPU-intensive OCR and structure-aware markdown chunking independently.
4. **Connection Pooling under High Concurrency**:
   - *Current*: Standard internal asyncio DB connection pools inside the ADK agent instances.
   - *Scale Requirement*: Centralized connection multiplexing (e.g., **PgBouncer**). Thousands of active, distributed ADK agents invoking async retrieval skills can quickly exhaust native PostgreSQL connection limits. External pooling shields the DB horizontally.
5. **The Vectorless Ceiling Limit**:
   - *Evaluation Factor*: While PostgreSQL FTS and `pg_trgm` are exceptionally capable, when a single tenant surpasses roughly 50-100+ million chunks, complex `ts_rank` calculations begin to incur compute lag. The architecture fully accommodates this ceiling by keeping the vectorless philosophy intact but shifting the *indexer* from Postgres to a dedicated distributed search cluster (Elasticsearch / OpenSearch).
