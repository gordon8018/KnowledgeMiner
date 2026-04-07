# Changelog

All notable changes to KnowledgeMiner will be documented in this file.

## [4.0.0] - 2026-04-07

### Added
- Three-layer architecture (Raw Sources → Enhanced Models → Wiki Models)
- SourceLoader and SourceParser for raw source handling
- ConceptExtractor with confidence scoring
- PatternDetector, GapAnalyzer, InsightGenerator for knowledge discovery
- Wiki operations: PageWriter, IndexWriter, PageReader, IndexSearcher
- Lint functionality with orphan and broken link detection
- Migration scripts for transitioning from old system
- High-level orchestrator for workflow coordination
- Comprehensive test suite (114 tests, 100% pass rate)
- Production-ready documentation

### Changed
- Complete rewrite from KnowledgeMiner 3.x
- New data models using Pydantic
- Obsidian-compatible wiki format
- Enhanced error handling and validation
- Improved performance and scalability

### Fixed
- Model compatibility issues from previous versions
- Data flow breaks in legacy code
- Fragmented functionality across multiple systems

### Migration Notes
- Use `scripts/migrate_sources.py` to migrate from old output/
- Use `scripts/rebuild_wiki.py` to rebuild wiki
- See USAGE.md for detailed migration guide

## [3.0.0] - Previous Release
- Legacy KnowledgeMiner functionality
- See old documentation for details
