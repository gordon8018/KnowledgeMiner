import os
from typing import List
from src.models.document import Document, Section
from src.models.concept import ConceptType
from src.analyzers.hash_calculator import calculate_file_hash
from src.utils.markdown_utils import parse_frontmatter, parse_sections

class DocumentAnalyzer:
    def __init__(self):
        pass

    def analyze(self, file_path: str) -> Document:
        """Analyze a markdown file and return structured Document."""
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        # Parse frontmatter
        metadata, content = parse_frontmatter(raw_content)

        # Parse sections
        sections_data = parse_sections(content)
        sections = [
            Section(
                title=s['title'],
                level=s['level'],
                content=s['content'].strip(),
                start_line=s['start_line'],
                end_line=s['end_line']
            )
            for s in sections_data
        ]

        # Calculate hash
        file_hash = calculate_file_hash(file_path)

        # Get relative path
        rel_path = os.path.basename(file_path)

        return Document(
            path=rel_path,
            hash=file_hash,
            metadata=metadata,
            sections=sections,
            content=content
        )