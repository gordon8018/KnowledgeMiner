import re
from typing import List, Tuple

def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """Parse YAML frontmatter from markdown content."""
    import frontmatter

    post = frontmatter.loads(content)
    metadata = dict(post.metadata)
    content = post.content
    return metadata, content

def parse_sections(content: str) -> List[dict]:
    """Parse markdown sections from content."""
    sections = []
    lines = content.split('\n')

    current_section = None
    start_line = 0

    for i, line in enumerate(lines):
        # Check for heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            # Save previous section
            if current_section:
                current_section['end_line'] = i
                sections.append(current_section)

            # Start new section
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            current_section = {
                'title': title,
                'level': level,
                'content': '',
                'start_line': i
            }
        elif current_section:
            current_section['content'] += line + '\n'

    # Save last section
    if current_section:
        current_section['end_line'] = len(lines)
        sections.append(current_section)

    return sections

def extract_latex_formulas(content: str) -> List[str]:
    """Extract LaTeX formulas from content."""
    # Inline math: $...$
    inline = re.findall(r'\$([^$]+)\$', content)
    # Block math: $$...$$
    block = re.findall(r'\$\$([^$]+)\$\$', content, re.DOTALL)
    return inline + block