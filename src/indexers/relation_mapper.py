from typing import Dict, List, Set, Optional
from src.models.document import Document
from src.models.concept import Concept, CandidateConcept


class RelationMapper:
    """Manages concept relationships and mappings between documents and concepts."""

    def __init__(self):
        """Initialize the RelationMapper with empty data structures."""
        self.documents: Dict[str, Document] = {}
        self.concepts: Dict[str, Concept] = {}
        self.candidate_concepts: Dict[str, List[CandidateConcept]] = {}
        self.relations: Dict[str, Dict[str, str]] = {}

    def add_document(self, document: Document) -> None:
        """Add a document to the mapper.

        Args:
            document: Document to add
        """
        self.documents[document.path] = document

    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the mapper.

        Args:
            concept: Concept to add
        """
        if concept.name not in self.concepts:
            self.concepts[concept.name] = concept

    def add_candidate_concept(self, candidate: CandidateConcept) -> None:
        """Add a candidate concept to the mapper.

        Args:
            candidate: Candidate concept to add
        """
        if candidate.name not in self.candidate_concepts:
            self.candidate_concepts[candidate.name] = []

        if candidate not in self.candidate_concepts[candidate.name]:
            self.candidate_concepts[candidate.name].append(candidate)

    def add_concept_relation(self, source: str, target: str, relation_type: str) -> None:
        """Add a relation between two concepts.

        Args:
            source: Source concept name
            target: Target concept name
            relation_type: Type of relation (e.g., 'parent', 'child', 'related')
        """
        if source not in self.relations:
            self.relations[source] = {}

        self.relations[source][target] = relation_type

    def get_concept(self, name: str) -> Optional[Concept]:
        """Get a concept by name.

        Args:
            name: Concept name

        Returns:
            Concept if found, None otherwise
        """
        return self.concepts.get(name)

    def get_concept_relations(self, name: str) -> Dict[str, str]:
        """Get all relations for a concept.

        Args:
            name: Concept name

        Returns:
            Dictionary of target concept names to relation types
        """
        return self.relations.get(name, {})

    def get_concepts_by_relation_type(self, relation_type: str) -> List[str]:
        """Get all concepts that have a specific relation type.

        Args:
            relation_type: Relation type to search for

        Returns:
            List of concept names that have the specified relation type
        """
        result = []
        for source, relations in self.relations.items():
            for target, rel_type in relations.items():
                if rel_type == relation_type:
                    result.append(source)
        return result

    def find_concepts_in_document(self, document_path: str) -> List[CandidateConcept]:
        """Find all concepts mentioned in a specific document.

        Args:
            document_path: Path to the document

        Returns:
            List of candidate concepts found in the document
        """
        result = []
        for concept_name, candidates in self.candidate_concepts.items():
            for candidate in candidates:
                if candidate.source_file == document_path:
                    result.append(candidate)
        return result

    def get_concept_occurrence_count(self, concept_name: str) -> int:
        """Get the number of times a concept appears across all documents.

        Args:
            concept_name: Concept name

        Returns:
            Number of occurrences
        """
        return len(self.candidate_concepts.get(concept_name, []))

    def get_related_concepts(self, concept_name: str, relation_type: str) -> List[str]:
        """Get concepts related to a specific concept by relation type.

        Args:
            concept_name: Source concept name
            relation_type: Relation type to filter by

        Returns:
            List of related concept names
        """
        relations = self.relations.get(concept_name, {})
        return [target for target, rel_type in relations.items()
                if rel_type == relation_type]

    def remove_concept(self, name: str) -> bool:
        """Remove a concept from the mapper.

        Args:
            name: Concept name to remove

        Returns:
            True if concept was removed, False if not found
        """
        if name in self.concepts:
            del self.concepts[name]
            return True
        return False

    def clear_concept_relations(self, concept_name: str) -> None:
        """Clear all relations for a specific concept.

        Args:
            concept_name: Concept name to clear relations for
        """
        if concept_name in self.relations:
            del self.relations[concept_name]

        # Remove concept from other concepts' relations
        for source, relations in self.relations.items():
            if concept_name in relations:
                del relations[concept_name]

    def get_concept_sources(self, concept_name: str) -> List[str]:
        """Get all source documents that mention a concept.

        Args:
            concept_name: Concept name

        Returns:
            List of source document paths
        """
        sources = []
        candidates = self.candidate_concepts.get(concept_name, [])
        for candidate in candidates:
            sources.append(candidate.source_file)
        return sources

    def get_all_concept_names(self) -> List[str]:
        """Get all concept names.

        Returns:
            List of all concept names
        """
        return list(self.concepts.keys())

    def get_relation_statistics(self) -> Dict[str, int]:
        """Get statistics about relation types.

        Returns:
            Dictionary mapping relation types to their counts
        """
        stats = {}
        for relations in self.relations.values():
            for relation_type in relations.values():
                stats[relation_type] = stats.get(relation_type, 0) + 1
        return stats

    def find_concept_by_similarity(self, query: str, threshold: float = 0.6) -> Optional[str]:
        """Find a concept by name similarity.

        Args:
            query: Search query
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            Most similar concept name if found, None otherwise
        """
        best_match = None
        best_score = 0

        # Search in both actual concepts and candidate concepts
        for concept_name in set(self.concepts.keys()) | set(self.candidate_concepts.keys()):
            # Simple similarity calculation - can be enhanced
            score = self._simple_similarity(query, concept_name)
            if score > threshold and score > best_score:
                best_score = score
                best_match = concept_name

        return best_match

    def _simple_similarity(self, query: str, target: str) -> float:
        """Simple similarity calculation between query and target."""
        query_lower = query.lower()
        target_lower = target.lower()

        if query_lower == target_lower:
            return 1.0

        # Check if query is a substring of target
        if query_lower in target_lower:
            return len(query_lower) / len(target_lower)

        # Check if target is a substring of query
        if target_lower in query_lower:
            return len(target_lower) / len(query_lower)

        # Check character overlap
        query_chars = set(query_lower)
        target_chars = set(target_lower)
        overlap = len(query_chars.intersection(target_chars))
        union = len(query_chars.union(target_chars))

        if union == 0:
            return 0.0

        return overlap / union

    def map_relations(self, documents: List[Document], concepts: List[Concept]) -> None:
        """Map relationships between concepts based on document analysis.

        Args:
            documents: List of documents to analyze
            concepts: List of concepts to map relations for
        """
        # Clear existing relations
        self.relations.clear()

        # Create concept name to concept mapping for easy lookup
        concept_map = {concept.name: concept for concept in concepts}

        for document in documents:
            # Get all concepts mentioned in this document
            doc_concepts = self.find_concepts_in_document(document.path)
            doc_concept_names = {concept.name for concept in doc_concepts}

            # Find related concepts within the same document
            for concept_name in doc_concept_names:
                if concept_name in concept_map:
                    concept = concept_map[concept_name]

                    # Add relations based on predefined relationships
                    for related_name in concept.related_concepts:
                        if related_name in concept_map and related_name != concept_name:
                            # Check if related concept is also in this document
                            if related_name in doc_concept_names:
                                self.add_concept_relation(concept_name, related_name, "related")

                    # Infer hierarchical relationships based on concept names or content
                    for other_name in doc_concept_names:
                        if other_name != concept_name:
                            # Simple heuristic: if one concept name contains another, it might be a parent/child relationship
                            if concept_name in other_name:
                                self.add_concept_relation(other_name, concept_name, "parent")
                            elif other_name in concept_name:
                                self.add_concept_relation(concept_name, other_name, "parent")

    def generate_markdown(self, output_path: str = None, include_mermaid: bool = True) -> str:
        """Generate markdown documentation of concept relationships.

        Args:
            output_path: Optional path to save the markdown file
            include_mermaid: Whether to include mermaid graph visualization

        Returns:
            Markdown string of concept relationships
        """
        markdown_lines = []

        # Add title
        markdown_lines.append("# Concept Relationship Map")
        markdown_lines.append("")

        # Add summary statistics
        markdown_lines.append("## Summary")
        markdown_lines.append("")

        num_concepts = len(self.concepts)
        num_relations = sum(len(relations) for relations in self.relations.values())
        relation_stats = self.get_relation_statistics()

        markdown_lines.append(f"- **Total Concepts**: {num_concepts}")
        markdown_lines.append(f"- **Total Relations**: {num_relations}")
        markdown_lines.append(f"- **Relation Types**: {len(relation_stats)}")
        markdown_lines.append("")

        if relation_stats:
            markdown_lines.append("### Relation Type Distribution")
            markdown_lines.append("")
            for rel_type, count in sorted(relation_stats.items(), key=lambda x: x[1], reverse=True):
                markdown_lines.append(f"- **{rel_type}**: {count}")
            markdown_lines.append("")

        # Add mermaid graph if requested
        if include_mermaid and self.relations:
            markdown_lines.append("## Concept Relationship Graph")
            markdown_lines.append("")
            markdown_lines.append("```mermaid")
            markdown_lines.append("graph TD")

            # Add nodes
            for concept_name in self.concepts.keys():
                # Sanitize concept names for mermaid
                safe_name = concept_name.replace(" ", "_").replace("-", "_")
                markdown_lines.append(f'    {safe_name}["{concept_name}"]')

            # Add edges
            for source, relations in self.relations.items():
                safe_source = source.replace(" ", "_").replace("-", "_")
                for target, rel_type in relations.items():
                    safe_target = target.replace(" ", "_").replace("-", "_")
                    style = ""
                    if rel_type == "parent":
                        style = ":::parent"
                    elif rel_type == "child":
                        style = ":::child"

                    markdown_lines.append(f'    {safe_source} -->{style} {safe_target}')

            markdown_lines.append("```")
            markdown_lines.append("")

        # Add detailed concept information
        markdown_lines.append("## Concept Details")
        markdown_lines.append("")

        for concept_name, concept in sorted(self.concepts.items()):
            markdown_lines.append(f"### {concept_name}")
            markdown_lines.append("")

            # Add concept description if available
            if hasattr(concept, 'description') and concept.description:
                markdown_lines.append(f"**Description**: {concept.description}")
                markdown_lines.append("")

            # Add sources
            sources = self.get_concept_sources(concept_name)
            if sources:
                markdown_lines.append("**Source Documents**:")
                for source in sorted(sources):
                    markdown_lines.append(f"- {source}")
                markdown_lines.append("")

            # Add relations
            relations = self.get_concept_relations(concept_name)
            if relations:
                markdown_lines.append("**Relations**:")
                for target, rel_type in sorted(relations.items()):
                    markdown_lines.append(f"- **{rel_type}**: {target}")
                markdown_lines.append("")

        # Add occurrence counts
        markdown_lines.append("## Concept Occurrence Analysis")
        markdown_lines.append("")

        concept_occurrences = []
        for concept_name in self.concepts.keys():
            count = self.get_concept_occurrence_count(concept_name)
            concept_occurrences.append((concept_name, count))

        # Sort by occurrence count
        concept_occurrences.sort(key=lambda x: x[1], reverse=True)

        for concept_name, count in concept_occurrences:
            if count > 0:
                markdown_lines.append(f"- **{concept_name}**: {count} occurrences")
        markdown_lines.append("")

        # Combine all lines
        markdown_content = "\n".join(markdown_lines)

        # Save to file if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

        return markdown_content