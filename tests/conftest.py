"""
Pytest configuration for knowledge compiler tests.
"""
import sys
from pathlib import Path

# Add project root (parent of src and tests) to Python path
project_root = Path(__file__).parent.parent
project_root_resolved = project_root.resolve()
sys.path.insert(0, str(project_root_resolved))

print(f"Conftest: Added {project_root_resolved} to sys.path")
