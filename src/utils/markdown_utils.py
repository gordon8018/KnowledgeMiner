import re
from typing import List, Tuple, Dict, Any

def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content."""
    try:
        import frontmatter
        post = frontmatter.loads(content)
        metadata = dict(post.metadata) if post.metadata else {}
        content = post.content
        return metadata, content
    except ImportError:
        # Fallback: simple frontmatter parsing without frontmatter library
        return _parse_frontmatter_simple(content)

def _parse_frontmatter_simple(content: str) -> Tuple[Dict[str, Any], str]:
    """Simple frontmatter parsing fallback without frontmatter library."""
    lines = content.split('\n')

    if not content.startswith('---'):
        return {}, content

    # Find end of frontmatter
    end_index = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_index = i
            break

    if end_index == -1:
        return {}, content

    # Parse YAML frontmatter
    frontmatter_lines = lines[1:end_index]
    metadata = {}

    for line in frontmatter_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    content_without_frontmatter = '\n'.join(lines[end_index + 1:])
    return metadata, content_without_frontmatter

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