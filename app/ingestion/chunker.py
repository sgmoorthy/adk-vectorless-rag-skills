import re
from typing import List, Dict, Optional

class HeadingNode:
    def __init__(self, level: int, title: str, content: str = ""):
        self.level = level
        self.title = title
        self.content = content
        self.children: List['HeadingNode'] = []
        self.parent: Optional['HeadingNode'] = None

    def add_child(self, node: 'HeadingNode'):
        node.parent = self
        self.children.append(node)

    def get_path_hierarchy(self) -> str:
        path = [self.title]
        curr = self.parent
        while curr and curr.title != "Root":
            path.insert(0, curr.title)
            curr = curr.parent
        return " > ".join(path)

class MarkdownDeterministicChunker:
    """Parses markdown deterministically by heading levels maintaining structural tree patterns."""
    
    def __init__(self, max_tokens: int = 1000):
        self.max_tokens = max_tokens
        
    def parse_text(self, markdown_text: str) -> List[Dict]:
        root = HeadingNode(level=0, title="Root")
        current_node = root
        
        lines = markdown_text.split("\n")
        
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.*)', line)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                new_node = HeadingNode(level=level, title=title)
                
                # Find appropriate parent based on level hierarchy
                while current_node.level >= level and current_node.parent:
                    current_node = current_node.parent
                    
                current_node.add_child(new_node)
                current_node = new_node
            else:
                if line.strip():
                    current_node.content += line + "\n"
                    
        return self._flatten_tree(root)

    def _flatten_tree(self, node: HeadingNode, chunks: List[Dict] = None, index: int = 0) -> List[Dict]:
        if chunks is None:
            chunks = []
            
        if node.content.strip() and node.title != "Root":
            chunks.append({
                "chunk_index": index,
                "path_hierarchy": node.get_path_hierarchy(),
                "content": node.content.strip(),
                "parent_title": node.parent.title if node.parent else None
            })
            index += 1
            
        for child in node.children:
            chunks = self._flatten_tree(child, chunks, index)
            index = len(chunks)
            
        return chunks
