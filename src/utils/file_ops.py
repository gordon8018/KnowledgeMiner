import os
import glob
from typing import List, Optional
from pathlib import Path


def ensure_dir(directory: str) -> bool:
    """Ensure a directory exists, creating it if necessary.

    Args:
        directory: Path to the directory

    Returns:
        True if directory exists or was created, False otherwise

    Raises:
        OSError: If the path exists but is not a directory
    """
    if os.path.exists(directory):
        if not os.path.isdir(directory):
            raise OSError(f"Path exists but is not a directory: {directory}")
        return True

    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except OSError:
        return False


def copy_file(source: str, destination: str) -> bool:
    """Copy a file from source to destination.

    Args:
        source: Path to source file
        destination: Path to destination file

    Returns:
        True if copy successful, False otherwise

    Raises:
        ValueError: If source and destination are the same
        FileNotFoundError: If source file doesn't exist
    """
    if source == destination:
        raise ValueError("Source and destination cannot be the same")

    if not os.path.exists(source):
        return False

    if not os.path.isfile(source):
        return False

    try:
        import shutil
        shutil.copy2(source, destination)
        return True
    except OSError:
        return False


def write_file(file_path: str, content: str) -> bool:
    """Write content to a file.

    Args:
        file_path: Path to the file
        content: Content to write

    Returns:
        True if write successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(file_path)
        if parent_dir:
            ensure_dir(parent_dir)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except OSError:
        return False


def read_file(file_path: str) -> Optional[str]:
    """Read content from a file.

    Args:
        file_path: Path to the file

    Returns:
        File content as string if successful, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def find_markdown_files(directory: str = None, pattern: str = "*.md", recursive: bool = True) -> List[str]:
    """Find markdown files in a directory.

    Args:
        directory: Directory to search (defaults to current directory)
        pattern: File pattern to match (defaults to "*.md")
        recursive: Whether to search subdirectories (defaults to True)

    Returns:
        List of relative file paths matching the pattern
    """
    if directory is None:
        directory = os.getcwd()

    if not os.path.exists(directory):
        return []

    if not os.path.isdir(directory):
        return []

    # Use glob to find files
    if recursive:
        # Recursive search
        search_pattern = os.path.join(directory, "**", pattern)
        files = glob.glob(search_pattern, recursive=True)
    else:
        # Current directory only
        search_pattern = os.path.join(directory, pattern)
        files = glob.glob(search_pattern)

    # Convert to relative paths
    relative_files = []
    base_path = os.path.abspath(directory)

    for file_path in files:
        if os.path.isfile(file_path):
            relative_path = os.path.relpath(file_path, base_path)
            relative_files.append(relative_path)

    return sorted(relative_files)


def find_files_by_extension(directory: str = None, extensions: List[str] = None, recursive: bool = True) -> List[str]:
    """Find files by extension(s).

    Args:
        directory: Directory to search (defaults to current directory)
        extensions: List of file extensions (e.g., ['.md', '.txt'])
        recursive: Whether to search subdirectories (defaults to True)

    Returns:
        List of relative file paths matching the extensions
    """
    if extensions is None:
        extensions = []

    if directory is None:
        directory = os.getcwd()

    if not os.path.exists(directory):
        return []

    # Ensure extensions start with dot
    normalized_extensions = []
    for ext in extensions:
        if not ext.startswith('.'):
            ext = '.' + ext
        normalized_extensions.append(ext.lower())

    # Use glob to find files
    files = []
    base_path = os.path.abspath(directory)

    if recursive:
        # Search all files
        search_pattern = os.path.join(directory, "**", "*")
        all_files = glob.glob(search_pattern, recursive=True)
    else:
        # Current directory only
        search_pattern = os.path.join(directory, "*")
        all_files = glob.glob(search_pattern)

    # Filter by extension
    for file_path in all_files:
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in normalized_extensions:
                relative_path = os.path.relpath(file_path, base_path)
                files.append(relative_path)

    return sorted(files)


def get_file_size(file_path: str) -> Optional[int]:
    """Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes if successful, None otherwise
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None


def file_exists(file_path: str) -> bool:
    """Check if a file exists.

    Args:
        file_path: Path to the file

    Returns:
        True if file exists, False otherwise
    """
    return os.path.isfile(file_path)


def is_markdown_file(file_path: str) -> bool:
    """Check if a file is a markdown file.

    Args:
        file_path: Path to the file

    Returns:
        True if file has .md extension, False otherwise
    """
    if not file_exists(file_path):
        return False

    return file_path.lower().endswith('.md')