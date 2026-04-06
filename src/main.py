import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.config import Config
from src.analyzers.document_analyzer import DocumentAnalyzer
from src.extractors.concept_extractor import ConceptExtractor
from src.generators.article_generator import ArticleGenerator
from src.generators.summary_generator import SummaryGenerator
from src.generators.backlink_generator import BacklinkGenerator
from src.indexers.file_indexer import FileIndexer
from src.indexers.category_indexer import CategoryIndexer
from src.indexers.relation_mapper import RelationMapper
from src.utils.file_ops import find_markdown_files, ensure_dir, write_file
from src.models.document import Document, Section
from src.models.concept import Concept, ConceptType


class KnowledgeCompiler:
    """Main class that orchestrates the knowledge compilation process."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the KnowledgeCompiler.

        Args:
            config: Configuration instance (uses defaults if None)
        """
        # Handle dict config by converting to Config object
        if isinstance(config, dict):
            self.config = Config.from_dict(config)
        else:
            self.config = config or Config()
        self.setup_logging()

        # Initialize components
        self.document_analyzer = DocumentAnalyzer()
        self.concept_extractor = ConceptExtractor()
        self.article_generator = ArticleGenerator()
        self.summary_generator = SummaryGenerator()
        self.backlink_generator = BacklinkGenerator()

        # Initialize indexers
        self.file_indexer = FileIndexer()
        self.category_indexer = CategoryIndexer()
        self.relation_mapper = RelationMapper()

        # Processing state
        self.processed_documents: List[Document] = []
        self.extracted_concepts: List[Concept] = []
        self.generated_articles: List[str] = []
        self.generated_summaries: List[str] = []
        self.generated_backlinks: List[str] = []

    def setup_logging(self) -> None:
        """Setup logging configuration."""
        if self.config:
            log_level = self.config.get_log_level()
            log_file = os.path.join(self.config.output_dir, 'compiler.log')
        else:
            log_level = 'INFO'
            log_file = 'compiler.log'

        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def compile(self) -> Dict[str, Any]:
        """Run the complete knowledge compilation process.

        Returns:
            Dictionary containing compilation results and statistics
        """
        self.logger.info("Starting knowledge compilation process")
        results = {
            'total_files': 0,
            'processed_files': 0,
            'extracted_concepts': 0,
            'generated_articles': 0,
            'generated_summaries': 0,
            'generated_backlinks': 0,
            'errors': [],
            'warnings': []
        }

        try:
            # Step 1: Find and process documents
            results['total_files'] = self._find_and_process_documents(results)

            # Step 2: Extract concepts
            results['extracted_concepts'] = self._extract_concepts()

            # Step 3: Confirm concepts (interactive mode)
            if self.config.interactive_mode and self.extracted_concepts:
                self.extracted_concepts = self.confirm_concepts(self.extracted_concepts)
                results['confirmed_concepts'] = len(self.extracted_concepts)

            # Step 4: Generate outputs
            if self.config.generate_summaries:
                results['generated_summaries'] = self._generate_summaries()

            if self.config.generate_articles:
                results['generated_articles'] = self._generate_articles()

            if self.config.generate_backlinks:
                results['generated_backlinks'] = self._generate_backlinks()

            # Step 5: Generate index and hash files
            self._generate_index()
            self._generate_hashes()

        except Exception as e:
            error_msg = f"Compilation failed: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)

        self.logger.info("Knowledge compilation process completed")
        return results

    def _find_and_process_documents(self, results: Dict[str, Any]) -> int:
        """Find and process all source documents.

        Args:
            results: Results dictionary to update

        Returns:
            Number of files found
        """
        self.logger.info("Finding and processing source documents")

        # Find markdown files
        markdown_files = find_markdown_files(
            self.config.source_dir,
            recursive=self.config.recursive_processing
        )

        if not markdown_files:
            self.logger.warning("No markdown files found")
            results['warnings'].append("No markdown files found in source directory")
            return 0

        # Process each file
        processed_count = 0
        for file_path in markdown_files:
            full_path = os.path.join(self.config.source_dir, file_path)

            try:
                if self.config.should_process_file(full_path):
                    document = self.document_analyzer.analyze(full_path)
                    self.file_indexer.add_document(document)
                    self.category_indexer.add_document_to_category(document, "all")

                    if document.tags:
                        self.category_indexer.auto_categorize_by_tags(document)

                    self.processed_documents.append(document)
                    processed_count += 1

                    if self.config.verbose_output:
                        self.logger.info(f"Processed: {file_path}")
                else:
                    self.logger.info(f"Skipped (size or pattern): {file_path}")

            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)

        results['processed_files'] = processed_count
        return len(markdown_files)

    def _extract_concepts(self) -> int:
        """Extract concepts from all processed documents.

        Returns:
            Number of concepts extracted
        """
        self.logger.info("Extracting concepts from documents")

        concept_count = 0
        for document in self.processed_documents:
            try:
                # Read document content
                doc_path = os.path.join(self.config.source_dir, document.path)
                if not os.path.exists(doc_path):
                    self.logger.warning(f"Document file not found: {doc_path}")
                    continue

                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract concepts from document content
                concepts = self.concept_extractor.extract_concepts(content)

                # Add to relation mapper
                for concept in concepts:
                    self.relation_mapper.add_concept(concept)

                # Add all concepts as candidate concepts for tracking
                for candidate in concepts:
                    # Convert Concept to CandidateConcept if needed
                    from src.models.concept import CandidateConcept
                    if isinstance(candidate, CandidateConcept):
                        self.relation_mapper.add_candidate_concept(candidate)
                    else:
                        # Create CandidateConcept from Concept
                        candidate_concept = CandidateConcept(
                            name=candidate.name,
                            type=candidate.type,
                            confidence=0.8,  # Default confidence
                            context=candidate.definition[:200] if candidate.definition else "",
                            source_section="extracted",
                            source_file=document.path if hasattr(document, 'path') else "unknown"
                        )
                        self.relation_mapper.add_candidate_concept(candidate_concept)

                self.extracted_concepts.extend(concepts)
                concept_count += len(concepts)

                if self.config.verbose_output:
                    self.logger.info(f"Extracted {len(concepts)} concepts from {document.path}")

            except Exception as e:
                self.logger.error(f"Error extracting concepts from {document.path}: {str(e)}")

        self.logger.info(f"Total concepts extracted: {concept_count}")
        return concept_count

    def _generate_summaries(self) -> int:
        """Generate summaries for all processed documents.

        Returns:
            Number of summaries generated
        """
        self.logger.info("Generating document summaries")

        # Create summaries subdirectory
        summaries_dir = os.path.join(self.config.output_dir, "summaries")
        ensure_dir(summaries_dir)

        summary_count = 0
        for document in self.processed_documents:
            try:
                # Create a simple summary from the document
                summary = f"# Summary: {document.title or os.path.basename(document.path)}\n\n"
                summary += f"**Source**: {document.path}\n\n"

                if document.sections:
                    summary += "## Sections\n\n"
                    for section in document.sections:
                        summary += f"- {section.title}\n"
                    summary += "\n"

                if document.tags:
                    summary += f"**Tags**: {', '.join(document.tags)}\n\n"

                # Save summary in summaries subdirectory
                summary_filename = os.path.basename(document.path)
                summary_path = os.path.join(summaries_dir, summary_filename)
                write_file(summary_path, summary)

                self.generated_summaries.append(summary_path)
                summary_count += 1

                if self.config.verbose_output:
                    self.logger.info(f"Generated summary for {document.path}")

            except Exception as e:
                self.logger.error(f"Error generating summary for {document.path}: {str(e)}")

        self.logger.info(f"Total summaries generated: {summary_count}")
        return summary_count

    def _generate_articles(self) -> int:
        """Generate articles for extracted concepts.

        Returns:
            Number of articles generated
        """
        self.logger.info("Generating concept articles")

        article_count = 0
        for concept in self.extracted_concepts:
            try:
                article = self.article_generator.generate_article(concept, self.extracted_concepts)

                if article:
                    # Save article
                    article_path = os.path.join(
                        self.config.output_dir,
                        f"article_{concept.name.lower().replace(' ', '_')}.md"
                    )
                    ensure_dir(os.path.dirname(article_path))
                    write_file(article_path, article)

                    self.generated_articles.append(article_path)
                    article_count += 1

                    if self.config.verbose_output:
                        self.logger.info(f"Generated article for concept: {concept.name}")

            except Exception as e:
                self.logger.error(f"Error generating article for {concept.name}: {str(e)}")

        self.logger.info(f"Total articles generated: {article_count}")
        return article_count

    def _generate_backlinks(self) -> int:
        """Generate backlinks between related concepts.

        Returns:
            Number of backlinks generated
        """
        self.logger.info("Generating concept backlinks")

        # Generate all backlinks at once
        try:
            all_backlinks = self.backlink_generator.generate_backlinks(self.extracted_concepts)

            backlink_count = 0
            for concept in self.extracted_concepts:
                try:
                    backlinks = all_backlinks.get(concept.name, [])

                    if backlinks:
                        # Save backlinks for this concept
                        backlink_path = os.path.join(
                            self.config.output_dir,
                            f"backlinks_{concept.name.lower().replace(' ', '_')}.md"
                        )
                        ensure_dir(os.path.dirname(backlink_path))

                        # Format backlinks as markdown
                        backlink_content = f"# Backlinks for {concept.name}\n\n"
                        for backlink in backlinks:
                            backlink_content += f"- {backlink}\n"

                        write_file(backlink_path, backlink_content)
                        self.generated_backlinks.append(backlink_path)
                        backlink_count += 1

                        if self.config.verbose_output:
                            self.logger.info(f"Generated backlinks for concept: {concept.name}")

                except Exception as e:
                    self.logger.error(f"Error saving backlinks for {concept.name}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error generating backlinks: {str(e)}")

        self.logger.info(f"Total backlinks generated: {backlink_count}")
        return backlink_count

    def _generate_index(self) -> None:
        """Generate INDEX.md file listing all processed documents."""
        self.logger.info("Generating INDEX.md")

        index_path = os.path.join(self.config.output_dir, "INDEX.md")

        index_content = "# Knowledge Index\n\n"
        index_content += f"Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        index_content += "## Documents\n\n"

        for doc in self.processed_documents:
            doc_name = os.path.basename(doc.path)
            index_content += f"- [{doc_name}](summaries/{doc_name})\n"

        if self.extracted_concepts:
            index_content += "\n## Concepts\n\n"
            for concept in self.extracted_concepts:
                index_content += f"- {concept.name}\n"

        write_file(index_path, index_content)
        self.logger.info(f"Generated INDEX.md at {index_path}")

    def _generate_hashes(self) -> None:
        """Generate .hashes.json file for tracking document changes."""
        self.logger.info("Generating .hashes.json")

        from src.analyzers.hash_calculator import calculate_file_hash

        hashes_path = os.path.join(self.config.output_dir, ".hashes.json")

        hashes = {}
        for doc in self.processed_documents:
            doc_path = os.path.join(self.config.source_dir, doc.path)
            if os.path.exists(doc_path):
                file_hash = calculate_file_hash(doc_path)
                hashes[doc.path] = file_hash

        import json
        with open(hashes_path, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Generated .hashes.json at {hashes_path}")

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get detailed processing statistics.

        Returns:
            Dictionary containing processing statistics
        """
        stats = {
            'documents': {
                'total': len(self.processed_documents),
                'by_category': self.category_indexer.get_categories()
            },
            'concepts': {
                'total': len(self.extracted_concepts),
                'by_type': {},  # Could be implemented to group by concept type
                'relations': self.relation_mapper.get_relation_statistics()
            },
            'outputs': {
                'articles': len(self.generated_articles),
                'summaries': len(self.generated_summaries),
                'backlinks': len(self.generated_backlinks)
            }
        }

        return stats

    def save_results_report(self, report_path: str) -> None:
        """Save a detailed report of the compilation results.

        Args:
            report_path: Path to save the report file
        """
        stats = self.get_processing_statistics()

        report_content = f"""# Knowledge Compilation Report

## Overview
Processed {stats['documents']['total']} documents and extracted {stats['concepts']['total']} concepts.

## Documents by Category
"""

        for category in stats['documents']['by_category']:
            count = self.category_indexer.get_category_document_count(category)
            report_content += f"- {category}: {count} documents\n"

        report_content += f"""

## Concepts by Type
"""

        for concept_type, count in stats['concepts']['by_type'].items():
            report_content += f"- {concept_type}: {count} concepts\n"

        report_content += f"""

## Relation Statistics
"""

        for relation_type, count in stats['concepts']['relations'].items():
            report_content += f"- {relation_type}: {count} relations\n"

        report_content += f"""

## Generated Outputs
- Articles: {stats['outputs']['articles']}
- Summaries: {stats['outputs']['summaries']}
- Backlinks: {stats['outputs']['backlinks']}

## Output Files
"""

        for article in self.generated_articles:
            report_content += f"- {article}\n"

        for summary in self.generated_summaries:
            report_content += f"- {summary}\n"

        for backlink in self.generated_backlinks:
            report_content += f"- {backlink}\n"

        write_file(report_path, report_content)

    def confirm_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Interactively confirm concepts with the user.

        Args:
            concepts: List of concepts to confirm

        Returns:
            List of confirmed concepts
        """
        if not concepts or not self.config.interactive_mode:
            return concepts

        confirmed = []
        print(f"\nConfirming {len(concepts)} concepts:")
        print("-" * 50)

        for i, concept in enumerate(concepts):
            self._display_concept(concept)
            while True:
                try:
                    choice = input(f"\nConfirm '{concept.name}'? (y/n/skip/all): ").lower().strip()
                    if choice in ['y', 'yes']:
                        confirmed.append(concept)
                        break
                    elif choice in ['n', 'no']:
                        break
                    elif choice in ['s', 'skip']:
                        break
                    elif choice in ['a', 'all']:
                        confirmed.extend(concepts[i:])
                        return confirmed
                    else:
                        print("Please enter 'y' for yes, 'n' for no, 's' to skip, or 'a' for all")
                except KeyboardInterrupt:
                    print("\nOperation cancelled by user")
                    return confirmed

        return confirmed

    def _manual_edit_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Manually edit concepts interactively.

        Args:
            concepts: List of concepts to edit

        Returns:
            List of edited concepts
        """
        if not self.config.interactive_mode:
            return concepts

        print("\nManual concept editing:")
        print("-" * 30)

        # Call confirm_concepts to let user select which concepts to keep
        confirmed = self.confirm_concepts(concepts)
        return confirmed

    def _review_concepts_individually(self, concepts: List[Concept]) -> List[Concept]:
        """Review concepts individually with the option to edit or skip.

        Args:
            concepts: List of concepts to review

        Returns:
            List of concepts the user wants to keep
        """
        if not concepts or not self.config.interactive_mode:
            return concepts

        confirmed = []

        for i, concept in enumerate(concepts):
            print(f"\n[{i+1}/{len(concepts)}] Reviewing concept:")
            self._display_concept(concept)

            while True:
                try:
                    choice = input("\nAction? (k=keep, s=skip, q=quit, u=update): ").lower().strip()

                    if choice in ['k', 'keep']:
                        confirmed.append(concept)
                        break
                    elif choice in ['s', 'skip']:
                        break
                    elif choice in ['q', 'quit']:
                        return confirmed
                    elif choice in ['u', 'update']:
                        # Update definition
                        new_def = input(f"Enter new definition for '{concept.name}' (current: {concept.definition}): ").strip()
                        if new_def:
                            concept.definition = new_def
                        confirmed.append(concept)
                        break
                    else:
                        print("Please enter 'k' for keep, 's' for skip, 'q' to quit, or 'u' to update")
                except KeyboardInterrupt:
                    print("\nOperation cancelled by user")
                    return confirmed

        return confirmed

    def review_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Review concepts interactively.

        Args:
            concepts: List of concepts to review

        Returns:
            List of reviewed concepts
        """
        if not self.config.interactive_mode:
            return concepts

        return self._review_concepts_individually(concepts)

    def _display_concept(self, concept: Concept) -> None:
        """Display a concept in a user-friendly format.

        Args:
            concept: Concept to display
        """
        type_display = {
            ConceptType.TERM: "Term",
            ConceptType.INDICATOR: "Indicator",
            ConceptType.STRATEGY: "Strategy",
            ConceptType.THEORY: "Theory",
            ConceptType.PERSON: "Person"
        }.get(concept.type, "Unknown")

        definition_preview = concept.definition[:100] + "..." if len(concept.definition) > 100 else concept.definition

        print(f"\n📚 {concept.name}")
        print(f"   Type: {type_display}")
        print(f"   Definition: {definition_preview}")

        if concept.related_concepts:
            print(f"   Related: {', '.join(concept.related_concepts)}")

    def run_interactive_session(self) -> Dict[str, Any]:
        """Run an interactive compilation session.

        Returns:
            Session results
        """
        if not self.config.interactive_mode:
            return {'error': 'Interactive mode is disabled'}

        print("\n🚀 Starting Interactive Knowledge Compilation Session")
        print("=" * 50)

        try:
            # Run the compilation process
            results = self.compile()

            # Interactive concept review
            if self.extracted_concepts:
                print(f"\n📖 Found {len(self.extracted_concepts)} concepts")
                confirmed_concepts = self.review_concepts(self.extracted_concepts)

                # Update the compiler with confirmed concepts
                self.extracted_concepts = confirmed_concepts

                # Regenerate outputs with confirmed concepts
                if self.config.generate_articles:
                    self.generated_articles = []
                    for concept in confirmed_concepts:
                        article = self.article_generator.generate_article(concept, confirmed_concepts)
                        if article:
                            article_path = os.path.join(
                                self.config.output_dir,
                                f"article_{concept.name.lower().replace(' ', '_')}.md"
                            )
                            ensure_dir(os.path.dirname(article_path))
                            write_file(article_path, article)
                            self.generated_articles.append(article_path)

                if self.config.generate_backlinks:
                    # Generate all backlinks at once
                    all_backlinks = self.backlink_generator.generate_backlinks(confirmed_concepts)

                    self.generated_backlinks = []
                    for concept in confirmed_concepts:
                        try:
                            backlinks = all_backlinks.get(concept.name, [])

                            if backlinks:
                                # Save backlinks for this concept
                                backlink_path = os.path.join(
                                    self.config.output_dir,
                                    f"backlinks_{concept.name.lower().replace(' ', '_')}.md"
                                )
                                ensure_dir(os.path.dirname(backlink_path))

                                # Format backlinks as markdown
                                backlink_content = f"# Backlinks for {concept.name}\n\n"
                                for backlink in backlinks:
                                    backlink_content += f"- {backlink}\n"

                                write_file(backlink_path, backlink_content)
                                self.generated_backlinks.append(backlink_path)

                        except Exception as e:
                            self.logger.error(f"Error saving backlinks for {concept.name}: {str(e)}")

                results['confirmed_concepts'] = len(confirmed_concepts)
                results['filtered_concepts'] = len(self.extracted_concepts) - len(confirmed_concepts)

            print(f"\n✅ Compilation completed successfully!")
            return results

        except Exception as e:
            error_msg = f"Interactive session failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            return {'error': error_msg}