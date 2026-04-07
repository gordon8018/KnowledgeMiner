"""
Migrate sources from old KnowledgeMiner output to new raw/ structure
"""

import os
import shutil
import glob
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def classify_source(filepath: str) -> str:
    """
    Classify a source file into a category

    Args:
        filepath: Path to source file

    Returns:
        Category name (papers/articles/reports/notes)
    """
    # Simple classification based on filename and content
    filename = os.path.basename(filepath).lower()

    if "paper" in filename or "arxiv" in filename or filename.endswith(".pdf"):
        return "papers"
    elif "report" in filename:
        return "reports"
    elif "note" in filename:
        return "notes"
    else:
        return "articles"


def add_frontmatter(filepath: str, category: str) -> None:
    """
    Add YAML frontmatter to a source file

    Args:
        filepath: Path to source file
        category: Category of the source
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if already has frontmatter
    if content.startswith("---"):
        return

    # Add basic frontmatter
    title = os.path.basename(filepath).replace(".md", "").replace("_", " ").title()

    frontmatter = f"""---
title: "{title}"
source_type: "{category}"
tags: []
---

"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)


def migrate_sources():
    """Migrate sources from old output/ to new raw/ structure"""
    # Scan old output directory
    old_sources = glob.glob("output/**/*.md", recursive=True)

    if not old_sources:
        print("No sources found in output/ directory")
        return

    print(f"Found {len(old_sources)} sources to migrate")

    migrated = 0
    errors = 0

    for source in old_sources:
        try:
            # Classify
            category = classify_source(source)

            # Add frontmatter
            add_frontmatter(source, category)

            # Move to new location
            filename = os.path.basename(source)
            new_path = f"raw/{category}/{filename}"

            os.makedirs(f"raw/{category}", exist_ok=True)
            shutil.move(source, new_path)

            print(f"✓ Migrated: {source} -> {new_path}")
            migrated += 1

        except Exception as e:
            print(f"✗ Error migrating {source}: {e}")
            errors += 1

    print(f"\nMigration complete:")
    print(f"  Migrated: {migrated}/{len(old_sources)} sources")
    print(f"  Errors: {errors}")


if __name__ == "__main__":
    migrate_sources()
