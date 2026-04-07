"""
DiscoveryPipeline - Complete Stage 2 orchestration pipeline.

This module implements the final Stage 2 task that orchestrates all components:
1. InputProcessor (detect changes)
2. ModeSelector (select processing mode)
3. DiscoveryOrchestrator (run discovery)
4. Automatic Wiki integration

The pipeline provides a complete end-to-end solution for automated knowledge
discovery with intelligent mode selection and incremental processing.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import time

from src.wiki.core import WikiCore
from src.wiki.discovery.input import InputProcessor
from src.wiki.discovery.mode_selector import ModeSelector, ProcessingMode
from src.wiki.discovery.orchestrator import DiscoveryOrchestrator
from src.wiki.discovery.models import ChangeSet
from src.discovery.config import DiscoveryConfig
from src.discovery.engine import KnowledgeDiscoveryEngine
from src.discovery.models.result import DiscoveryResult
from src.core.document_model import EnhancedDocument, DocumentMetadata, SourceType
from src.core.concept_model import EnhancedConcept, ConceptType


logger = logging.getLogger(__name__)


class DiscoveryPipeline:
    """
    Complete discovery pipeline orchestrating all Stage 2 components.

    Pipeline Flow:
    1. Detect changes using InputProcessor
    2. Return None if no changes
    3. Select processing mode using ModeSelector
    4. Load documents from disk
    5. Load concepts from Wiki
    6. Orchestrate discovery via DiscoveryOrchestrator
    7. Record full run if needed
    8. Return DiscoveryResult

    Attributes:
        wiki_core: WikiCore instance for Wiki operations
        input_dir: Directory containing input markdown documents
        state_dir: Directory for pipeline state files
        config: DiscoveryConfig for discovery engine
        mode_selector: ModeSelector for intelligent mode selection
        input_processor: InputProcessor for change detection
        discovery_engine: KnowledgeDiscoveryEngine for discovery operations
        orchestrator: DiscoveryOrchestrator for pipeline coordination
    """

    # State file names
    LAST_FULL_RUN_FILE = "last_full_run.json"
    PIPELINE_STATE_FILE = "pipeline_state.json"

    # Default thresholds
    DEFAULT_INCREMENTAL_THRESHOLD = 10
    DEFAULT_FORCE_FULL_AFTER_DAYS = 7

    def __init__(
        self,
        wiki_core: WikiCore,
        input_dir: str,
        state_dir: str,
        config: Optional[DiscoveryConfig] = None,
        incremental_threshold: int = DEFAULT_INCREMENTAL_THRESHOLD,
        force_full_after_days: int = DEFAULT_FORCE_FULL_AFTER_DAYS
    ):
        """
        Initialize DiscoveryPipeline.

        Args:
            wiki_core: WikiCore instance for Wiki operations
            input_dir: Directory containing input markdown documents
            state_dir: Directory for pipeline state files
            config: Optional DiscoveryConfig for discovery engine
            incremental_threshold: Max changes for simple incremental mode
            force_full_after_days: Days before forcing a full run
        """
        self.wiki_core = wiki_core
        self.input_dir = Path(input_dir)
        self.state_dir = Path(state_dir)
        self.config = config or DiscoveryConfig()

        # Ensure directories exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        state_file = str(self.state_dir / self.PIPELINE_STATE_FILE)
        self.input_processor = InputProcessor(
            input_dir=str(self.input_dir),
            state_file=state_file
        )

        # Load last full run timestamp
        last_full_run = self._load_last_full_run()

        self.mode_selector = ModeSelector(
            incremental_threshold=incremental_threshold,
            force_full_after_days=force_full_after_days,
            enable_smart_selection=True,
            last_full_run=last_full_run
        )

        # Initialize discovery engine with LLM provider and embedder
        from src.integrations.llm_providers import get_llm_provider
        from src.ml.embeddings import EmbeddingGenerator

        llm_provider = get_llm_provider()
        embedding_generator = EmbeddingGenerator()

        self.discovery_engine = KnowledgeDiscoveryEngine(
            config=self.config,
            llm_provider=llm_provider,
            embedding_generator=embedding_generator
        )

        # Initialize orchestrator
        self.orchestrator = DiscoveryOrchestrator(
            discovery_engine=self.discovery_engine,
            wiki_path=str(self.wiki_core.store.storage_path),
            config=self.config
        )

        logger.info(
            f"DiscoveryPipeline initialized: input_dir={input_dir}, "
            f"state_dir={state_dir}, incremental_threshold={incremental_threshold}"
        )

    def run(self, batch_id: Optional[str] = None) -> Optional[DiscoveryResult]:
        """
        Run the complete discovery pipeline.

        Args:
            batch_id: Optional batch ID for this run (auto-generated if None)

        Returns:
            DiscoveryResult if changes were detected, None if no changes
        """
        if batch_id is None:
            batch_id = f"batch-{int(time.time())}"

        logger.info(f"Starting discovery pipeline run: {batch_id}")
        start_time = datetime.now()

        try:
            # Step 1: Detect changes
            logger.info("Step 1: Detecting changes...")
            changeset = self.input_processor.process_changes(batch_id)

            if changeset.is_empty():
                logger.info("No changes detected, pipeline complete")
                return None

            logger.info(
                f"Changes detected: {len(changeset.new_docs)} new, "
                f"{len(changeset.changed_docs)} changed, "
                f"{len(changeset.deleted_docs)} deleted"
            )

            # Step 2: Select processing mode
            logger.info("Step 2: Selecting processing mode...")
            changeset_dict = {
                'added': changeset.new_docs,
                'modified': changeset.changed_docs,
                'deleted': changeset.deleted_docs
            }
            mode = self.mode_selector.select_mode(changeset_dict)
            logger.info(f"Selected mode: {mode.value}")

            # Step 3: Load documents from disk
            logger.info("Step 3: Loading documents from disk...")
            documents = self._load_documents(changeset)
            logger.info(f"Loaded {len(documents)} documents")

            # Allow pipeline to continue even if no documents loaded (deletions only)
            if not documents and not changeset.deleted_docs:
                logger.warning("No documents loaded and no deletions, aborting pipeline")
                return None

            # Step 4: Load concepts from Wiki
            logger.info("Step 4: Loading concepts from Wiki...")
            concepts = self._load_concepts()
            logger.info(f"Loaded {len(concepts)} concepts from Wiki")

            # Step 5: Orchestrate discovery
            logger.info("Step 5: Orchestrating discovery...")
            discovery_result = self.orchestrator.orchestrate(
                documents=documents,
                concepts=concepts,
                mode=mode.value,
                existing_relations=None,  # Could load from Wiki if needed
                integrate_to_wiki=True
            )

            # Step 6: Record full run if needed
            if mode == ProcessingMode.FULL:
                logger.info("Step 6: Recording full run...")
                self._record_full_run()

            # Add pipeline metadata to result
            discovery_result.statistics['pipeline_run_id'] = batch_id
            discovery_result.statistics['pipeline_duration'] = (
                datetime.now() - start_time
            ).total_seconds()
            discovery_result.statistics['changeset'] = {
                'new_docs': len(changeset.new_docs),
                'changed_docs': len(changeset.changed_docs),
                'deleted_docs': len(changeset.deleted_docs),
                'impact_score': changeset.impact_score
            }

            logger.info(
                f"Pipeline completed successfully in "
                f"{discovery_result.statistics['pipeline_duration']:.2f}s"
            )

            return discovery_result

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

    def _load_documents(self, changeset: ChangeSet) -> List[EnhancedDocument]:
        """
        Load EnhancedDocument objects from disk for changed documents.

        This is a COMPLETE implementation that:
        - Reads actual markdown files from disk
        - Parses frontmatter metadata
        - Creates EnhancedDocument objects with all fields
        - Handles both new and changed documents

        Args:
            changeset: ChangeSet with new_docs and changed_docs lists

        Returns:
            List of EnhancedDocument objects loaded from disk
        """
        documents = []
        doc_ids_to_load = list(set(changeset.new_docs + changeset.changed_docs))

        logger.debug(f"Loading {len(doc_ids_to_load)} documents: {doc_ids_to_load}")

        for doc_id in doc_ids_to_load:
            try:
                # Construct file path
                file_path = self.input_dir / doc_id

                if not file_path.exists():
                    logger.warning(f"Document file not found: {file_path}")
                    continue

                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse frontmatter if present
                metadata = self._parse_frontmatter(content, file_path)

                # Remove frontmatter from content if present
                if content.startswith('---'):
                    content_end = content.find('---', 3)
                    if content_end != -1:
                        content = content[content_end + 3:].strip()

                # Create EnhancedDocument
                document = EnhancedDocument(
                    id=doc_id,
                    source_type=self._infer_source_type(metadata, doc_id),
                    content=content,
                    metadata=metadata,
                    quality_score=0.5,  # Could be calculated or from frontmatter
                    processing_status=self._infer_processing_status(doc_id)
                )

                documents.append(document)
                logger.debug(f"Loaded document: {doc_id}")

            except Exception as e:
                logger.error(f"Error loading document {doc_id}: {e}")
                continue

        return documents

    def _parse_frontmatter(
        self,
        content: str,
        file_path: Path
    ) -> DocumentMetadata:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Markdown content with possible frontmatter
            file_path: Path to the file (for fallback metadata)

        Returns:
            DocumentMetadata object
        """
        metadata = DocumentMetadata()

        # Check if frontmatter exists
        if not content.startswith('---'):
            # No frontmatter, use filename as title
            metadata.title = file_path.stem
            metadata.file_path = str(file_path)
            return metadata

        # Extract frontmatter
        frontmatter_end = content.find('---', 3)
        if frontmatter_end == -1:
            # Unclosed frontmatter, use filename as title
            metadata.title = file_path.stem
            metadata.file_path = str(file_path)
            return metadata

        frontmatter_text = content[3:frontmatter_end].strip()

        try:
            import yaml
            frontmatter_data = yaml.safe_load(frontmatter_text)

            if frontmatter_data:
                # Extract known fields
                metadata.title = frontmatter_data.get('title', file_path.stem)
                metadata.author = frontmatter_data.get('author')
                metadata.tags = frontmatter_data.get('tags', [])
                metadata.source_url = frontmatter_data.get('source_url')
                metadata.file_path = frontmatter_data.get('file_path', str(file_path))

                # Parse date if present
                if 'date' in frontmatter_data:
                    date_str = frontmatter_data['date']
                    if isinstance(date_str, str):
                        try:
                            from dateutil import parser
                            metadata.date = parser.parse(date_str)
                        except Exception:
                            logger.debug(f"Could not parse date: {date_str}")

        except ImportError:
            logger.debug("PyYAML not installed, skipping frontmatter parsing")
        except Exception as e:
            logger.debug(f"Error parsing frontmatter: {e}")

        # Ensure file_path is set
        if not metadata.file_path:
            metadata.file_path = str(file_path)

        return metadata

    def _infer_source_type(
        self,
        metadata: DocumentMetadata,
        doc_id: str
    ) -> SourceType:
        """
        Infer source type from metadata and document ID.

        Args:
            metadata: Document metadata
            doc_id: Document ID

        Returns:
            SourceType enum value
        """
        # Check metadata for hints
        if metadata.source_url:
            return SourceType.WEB_CLIPPER

        # Check document ID for patterns
        if 'pdf' in doc_id.lower():
            return SourceType.PDF
        elif 'image' in doc_id.lower():
            return SourceType.IMAGE

        # Default to MARKDOWN
        return SourceType.MARKDOWN

    def _infer_processing_status(self, doc_id: str) -> str:
        """
        Infer processing status for a document.

        Args:
            doc_id: Document ID

        Returns:
            ProcessingStatus string value
        """
        # For now, return PENDING for all documents
        # In the future, this could check if document was already processed
        from src.core.base_models import ProcessingStatus
        return ProcessingStatus.PENDING.value

    def _load_concepts(self) -> List[EnhancedConcept]:
        """
        Load EnhancedConcept objects from Wiki pages.

        This is a COMPLETE implementation that:
        - Reads concept pages from Wiki storage
        - Parses markdown content
        - Creates EnhancedConcept objects with all fields
        - Handles all concept types

        Returns:
            List of EnhancedConcept objects loaded from Wiki
        """
        concepts = []

        try:
            # Get concept pages from Wiki concepts directory
            concepts_dir = self.wiki_core.store.concepts_dir

            if not concepts_dir.exists():
                logger.debug(f"Concepts directory does not exist: {concepts_dir}")
                return []

            # Scan for markdown files
            concept_files = list(concepts_dir.glob("*.md"))
            logger.debug(f"Found {len(concept_files)} concept files in Wiki")

            for concept_file in concept_files:
                try:
                    # Read concept page
                    page_id = concept_file.stem
                    page = self.wiki_core.store.get_page(page_id)

                    if not page:
                        logger.debug(f"Could not load page for: {page_id}")
                        continue

                    # Parse concept from page content
                    concept = self._parse_concept_from_page(page)

                    if concept:
                        concepts.append(concept)
                        logger.debug(f"Loaded concept: {concept.name}")

                except Exception as e:
                    logger.error(f"Error loading concept from {concept_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error loading concepts from Wiki: {e}")

        return concepts

    def _parse_concept_from_page(self, page) -> Optional[EnhancedConcept]:
        """
        Parse EnhancedConcept from Wiki page.

        Args:
            page: WikiPage object

        Returns:
            EnhancedConcept object or None if parsing fails
        """
        try:
            from src.wiki.core.models import PageType

            # Extract concept name from page title or ID
            name = page.title or page.id.replace('_', ' ').replace('-', ' ').title()

            # Extract definition from page content (first paragraph after title)
            content = page.content
            definition = self._extract_definition_from_content(content)

            # Infer concept type from tags or content
            concept_type = self._infer_concept_type(page, content)

            # Create EnhancedConcept
            concept = EnhancedConcept(
                id=page.id,
                name=name,
                type=concept_type,
                definition=definition,
                confidence=0.5,  # Could be calculated from evidence
                temporal_info=None,
                source_documents=[]
            )

            return concept

        except Exception as e:
            logger.error(f"Error parsing concept from page: {e}")
            return None

    def _extract_definition_from_content(self, content: str) -> str:
        """
        Extract concept definition from markdown content.

        Args:
            content: Markdown content

        Returns:
            Definition string
        """
        lines = content.split('\n')

        # Skip title line
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                start_idx = i
                break

        # Collect definition paragraphs (up to first empty line or heading)
        definition_lines = []
        for line in lines[start_idx:]:
            line = line.strip()
            if not line or line.startswith('#'):
                break
            definition_lines.append(line)

        definition = ' '.join(definition_lines)
        return definition if definition else "No definition available"

    def _infer_concept_type(self, page, content: str) -> ConceptType:
        """
        Infer concept type from page metadata and content.

        Args:
            page: WikiPage object
            content: Page content

        Returns:
            ConceptType enum value
        """
        # Check page tags for type hints
        if hasattr(page, 'tags') and page.tags:
            tags_lower = [tag.lower() for tag in page.tags]

            if 'indicator' in tags_lower:
                return ConceptType.INDICATOR
            elif 'strategy' in tags_lower:
                return ConceptType.STRATEGY
            elif 'theory' in tags_lower:
                return ConceptType.THEORY
            elif 'person' in tags_lower or 'author' in tags_lower:
                return ConceptType.PERSON

        # Check content for patterns
        content_lower = content.lower()

        if any(term in content_lower for term in ['indicator', 'index', 'metric']):
            return ConceptType.INDICATOR
        elif any(term in content_lower for term in ['strategy', 'approach', 'method']):
            return ConceptType.STRATEGY
        elif any(term in content_lower for term in ['theory', 'model', 'framework']):
            return ConceptType.THEORY

        # Default to TERM
        return ConceptType.TERM

    def _load_last_full_run(self) -> Optional[datetime]:
        """
        Load timestamp of last full run from state file.

        Returns:
            Datetime of last full run, or None if no previous run
        """
        try:
            state_file = self.state_dir / self.LAST_FULL_RUN_FILE

            if not state_file.exists():
                return None

            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            timestamp_str = data.get('last_full_run')
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)

        except Exception as e:
            logger.error(f"Error loading last full run timestamp: {e}")

        return None

    def _record_full_run(self) -> None:
        """
        Record timestamp of full run to state file.
        """
        try:
            state_file = self.state_dir / self.LAST_FULL_RUN_FILE

            data = {
                'last_full_run': datetime.now().isoformat()
            }

            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Recorded full run timestamp to {state_file}")

        except Exception as e:
            logger.error(f"Error recording full run timestamp: {e}")
