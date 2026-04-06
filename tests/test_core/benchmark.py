import time
import tempfile
import shutil
from src.wiki.core import WikiCore, WikiPage, PageType

def benchmark_creation(count=100):
    """Benchmark creating Wiki pages."""
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)

    start = time.time()
    for i in range(count):
        page = WikiPage(
            id=f"page-{i}",
            title=f"Page {i}",
            content=f"Content for page {i}" * 100,
            page_type=PageType.TOPIC
        )
        core.create_page(page)
    elapsed = time.time() - start

    shutil.rmtree(temp_dir, ignore_errors=True)
    return elapsed

def benchmark_search(core, queries=10):
    """Benchmark search operations."""
    import random

    start = time.time()
    for _ in range(queries):
        query = f"page {random.randint(0, 99)}"
        core.search(query)
    elapsed = time.time() - start

    return elapsed

if __name__ == "__main__":
    print("Benchmarking WikiCore performance...")

    # Benchmark creation
    creation_time = benchmark_creation(100)
    print(f"Created 100 pages in {creation_time:.2f}s ({creation_time/100*1000:.2f}ms per page)")

    # Benchmark search
    temp_dir = tempfile.mkdtemp()
    core = WikiCore(storage_path=temp_dir)
    for i in range(100):
        core.create_page(WikiPage(
            id=f"page-{i}",
            title=f"Page {i}",
            content=f"Content for page {i}" * 100,
            page_type=PageType.TOPIC
        ))

    search_time = benchmark_search(core, 10)
    print(f"Performed 10 searches in {search_time:.2f}s ({search_time/10*1000:.2f}ms per search)")

    shutil.rmtree(temp_dir, ignore_errors=True)
