from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass
class Section:
    title: str
    level: int
    content: str
    start_line: int = 0
    end_line: int = 0

@dataclass
class Document:
    path: str
    hash: str
    metadata: Dict[str, Any]
    sections: List[Section]
    content: str

    @property
    def title(self) -> Optional[str]:
        return self.metadata.get("title")

    @property
    def tags(self) -> List[str]:
        return self.metadata.get("tags", [])