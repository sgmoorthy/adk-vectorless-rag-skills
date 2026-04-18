import pytest
from app.ingestion.chunker import MarkdownDeterministicChunker

def test_markdown_deterministic_chunker():
    chunker = MarkdownDeterministicChunker()
    markdown = """
# Root Level
This is root context.
## Sub level 1
Sub 1 text
### Sub level 2
Sub 2 text
## Second sub level
Second text
    """
    chunks = chunker.parse_text(markdown)
    
    assert len(chunks) == 4
    
    c1, c2, c3, c4 = chunks
    assert c1["path_hierarchy"] == "Root Level"
    assert "root context" in c1["content"]
    
    assert c2["path_hierarchy"] == "Root Level > Sub level 1"
    assert "Sub 1 text" in c2["content"]
    
    assert c3["path_hierarchy"] == "Root Level > Sub level 1 > Sub level 2"
    assert "Sub 2 text" in c3["content"]
    
    assert c4["path_hierarchy"] == "Root Level > Second sub level"
    assert "Second text" in c4["content"]
