# Knowledge Compiler Architecture

This document describes the architecture of the Knowledge Compiler 2.0 system, including both Phase 1 (Foundation) and Phase 2 (Knowledge Discovery Engine) components.

## Table of Contents

1. [System Overview](#system-overview)
2. [Phase 1 Architecture](#phase-1-architecture)
3. [Phase 2 Architecture](#phase-2-architecture)
4. [Data Flow](#data-flow)
5. [Component Interaction](#component-interaction)
6. [Technology Stack](#technology-stack)
7. [Design Principles](#design-principles)

## System Overview

The Knowledge Compiler 2.0 is a modular, multi-phase system for transforming raw markdown documents into a structured, explorable knowledge base.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Knowledge Compiler 2.0                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Phase 1: Foundation          Phase 2: Knowledge Discovery      │
│  ┌─────────────────────┐     ┌─────────────────────────────┐   │
│  │ Document Processing │     │ Relation Mining Engine      │   │
│  │ Concept Extraction  │───▶ │ Pattern Detector            │   │
│  │ Content Generation  │     │ Gap Analyzer                │   │
│  │ Indexing            │     │ Insight Generator           │   │
│  └─────────────────────┘     └─────────────────────────────┘   │
│            │                            │                       │
│            ▼                            ▼                       │
│  ┌─────────────────────┐     ┌─────────────────────────────┐   │
│  │ Structured Knowledge │◀───▶│ Discovered Knowledge        │   │
│  │ - Documents         │     │ - Relations                 │   │
│  │ - Concepts          │     │ - Patterns                  │   │
│  │ - Relations         │     │ - Gaps                      │   │
│  │ - Embeddings        │     │ - Insights                  │   │
│  └─────────────────────┘     └─────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1 Architecture

### Core Layer

The core layer provides the foundational data models and abstractions.

#### Document Model

```
EnhancedDocument
├── id: str
├── path: str
├── title: str
├── content: str
├── metadata: Dict[str, Any]
├── sections: List[Section]
├── hash: str
├── embeddings: Optional[np.ndarray]
└── created_at: datetime
```

**Key Features:**
- Unique hash-based identification
- Semantic embedding support
- Structured section representation
- Rich metadata support

#### Concept Model

```
EnhancedConcept
├── id: str
├── name: str
├── type: ConceptType
├── definition: str
├── embeddings: Optional[np.ndarray]
├── properties: Dict[str, Any]
├── relations: List[str]
└── evidence: List[Evidence]
```

**Key Features:**
- Type-safe concept categorization
- Semantic embedding support
- Flexible property system
- Evidence tracking

#### Relation Model

```
Relation
├── id: str
├── source_concept: str
├── target_concept: str
├── relation_type: RelationType
├── strength: float
├── evidence_count: int
└── properties: Dict[str, Any]
```

**Key Features:**
- Typed relationships (DEFINES, RELATES_TO, CAUSES, etc.)
- Strength scoring
- Evidence counting
- Extensible properties

### Integration Layer

#### LLM Provider Architecture

```
LLMProvider (Abstract)
├── OpenAIProvider
├── AnthropicProvider
└── OllamaProvider
```

**Key Features:**
- Unified interface for multiple LLM providers
- Automatic retry with exponential backoff
- Error handling and fallback support
- Token counting and rate limiting

#### Embedding Generator

```
EmbeddingGenerator
├── generate_embeddings(texts: List[str]) → np.ndarray
├── batch_embeddings(texts: List[str], batch_size: int) → np.ndarray
└── cosine_similarity(vec1, vec2) → float
```

**Key Features:**
- Batch processing for efficiency
- Multiple model support
- Similarity computation utilities

### Processing Layer

#### Document Analysis Pipeline

```
DocumentAnalyzer
├── 1. Read file
├── 2. Parse frontmatter
├── 3. Extract sections
├── 4. Compute hash
└── 5. Create EnhancedDocument
```

#### Concept Extraction Pipeline

```
ConceptExtractor
├── 1. Pattern-based extraction
│   └── Regex patterns for common formats
├── 2. LLM-based extraction
│   └── Context-aware concept identification
├── 3. Confidence scoring
└── 4. Deduplication
```

#### Content Generation Pipeline

```
ArticleGenerator
├── 1. Concept article generation
├── 2. Template rendering
└── 3. Output formatting

SummaryGenerator
├── 1. Document analysis
├── 2. Key point extraction
└── 3. Summary generation

BacklinkGenerator
├── 1. Relation discovery
├── 2. Link generation
└── 3. Cross-referencing
```

#### Indexing Pipeline

```
FileIndexer
├── Path-based lookup
└── Hash-based deduplication

CategoryIndexer
├── Category organization
└── Tag-based filtering

RelationMapper
├── Explicit relation extraction
└── Implicit relation inference
```

## Phase 2 Architecture

### Knowledge Discovery Engine

The Knowledge Discovery Engine is the core of Phase 2, orchestrating multiple specialized components.

```
KnowledgeDiscoveryEngine
├── RelationMiningEngine
├── PatternDetector
├── GapAnalyzer
└── InsightGenerator
```

### Relation Mining Engine

Discovers relationships between concepts using multiple strategies.

```
RelationMiningEngine
├── ExplicitRelationMiner
│   ├── Text pattern matching
│   └── Syntactic analysis
├── ImplicitRelationMiner
│   ├── Context inference
│   └── LLM-based extraction
├── StatisticalRelationMiner
│   ├── Co-occurrence analysis
│   ├── Correlation computation
│   └── Graph algorithms
└── SemanticRelationMiner
    ├── Embedding similarity
    └── Semantic clustering
```

**Mining Process:**
1. **Explicit Mining**: Find directly stated relationships in text
2. **Implicit Mining**: Infer relationships from context
3. **Statistical Mining**: Discover relationships through co-occurrence
4. **Semantic Mining**: Use embeddings to find semantic relationships

**Output:** List of `Relation` objects with confidence scores

### Pattern Detector

Identifies patterns in knowledge structure and evolution.

```
PatternDetector
├── TemporalPatternDetector
│   ├── Time series analysis
│   └── Trend detection
├── CausalPatternDetector
│   ├── Cause-effect chain analysis
│   └── Causal graph construction
├── EvolutionaryPatternDetector
│   ├── Concept evolution tracking
│   └── Development stage identification
└── ConflictPatternDetector
    ├── Contradiction detection
    └── Tension identification
```

**Pattern Types:**
- **Temporal**: Time-based patterns and trends
- **Causal**: Cause-effect relationships and chains
- **Evolutionary**: Concept development and change over time
- **Conflict**: Contradictions and tensions between concepts

**Output:** List of `Pattern` objects with confidence scores

### Gap Analyzer

Identifies missing knowledge in the knowledge base.

```
GapAnalyzer
├── ConceptGapAnalyzer
│   ├── Concept space analysis
│   └── Missing concept identification
├── RelationGapAnalyzer
│   ├── Connectivity analysis
│   └── Disconnected component detection
└── EvidenceAnalyzer
│   ├── Evidence quality assessment
│   └── Unsupported claim detection
```

**Gap Types:**
- **Missing Concept**: Concepts that should exist but don't
- **Missing Relation**: Concepts that should be related but aren't
- **Missing Evidence**: Claims without sufficient support

**Output:** List of `KnowledgeGap` objects with priority scores

### Insight Generator

Synthesizes discoveries into actionable insights.

```
InsightGenerator
├── PatternSynthesizer
│   ├── Pattern combination
│   └── Pattern significance scoring
├── GapPrioritizer
│   ├── Impact analysis
│   └── Priority scoring
└── InsightComposer
    ├── Insight generation
    └── Action item formulation
```

**Insight Types:**
- **Pattern Insight**: Important patterns discovered
- **Gap Insight**: Critical gaps to address
- **Strategic Insight**: High-level recommendations

**Output:** List of `Insight` objects with significance scores

### Interactive Discovery API

Provides interactive exploration capabilities.

```
InteractiveDiscovery
├── discover_and_store()
├── explore_relations(concept_name)
├── find_patterns(keyword)
├── analyze_gaps_in_domain(domain)
├── get_top_insights(n)
└── ask_question(question)
```

## Data Flow

### Phase 1 Data Flow

```
Raw Markdown Documents
        │
        ▼
┌───────────────────┐
│ Document Analyzer │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Concept Extractor │
└─────────┬─────────┘
          │
          ├─────────────┬─────────────┬─────────────┐
          ▼             ▼             ▼             ▼
    ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Index  │  │Generate  │  │Generate  │  │Generate  │
    │         │  │Articles  │  │Summaries │  │Backlinks │
    └─────────┘  └──────────┘  └──────────┘  └──────────┘
          │             │             │             │
          └─────────────┴─────────────┴─────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │ Structured Knowledge│
              │ - Documents         │
              │ - Concepts          │
              │ - Relations         │
              │ - Embeddings        │
              └─────────────────────┘
```

### Phase 2 Data Flow

```
Structured Knowledge (from Phase 1)
        │
        ▼
┌──────────────────────────────┐
│  Knowledge Discovery Engine  │
└──────────────┬───────────────┘
               │
               ├───────────────────────────────────────┐
               │                                       │
               ▼                                       ▼
    ┌────────────────────┐              ┌────────────────────┐
    │ Relation Mining    │              │ Pattern Detection  │
    │ - Explicit         │              │ - Temporal         │
    │ - Implicit         │              │ - Causal           │
    │ - Statistical      │              │ - Evolutionary     │
    │ - Semantic         │              │ - Conflict         │
    └─────────┬──────────┘              └─────────┬──────────┘
              │                                   │
              └───────────────────┬───────────────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │ Gap Analysis  │
                          │ - Concepts    │
                          │ - Relations   │
                          │ - Evidence    │
                          └───────┬───────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │  Insight Gen  │
                          │ - Synthesize  │
                          │ - Prioritize  │
                          │ - Compose     │
                          └───────┬───────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │    Discovered Knowledge      │
                    │ - New Relations              │
                    │ - Patterns                   │
                    │ - Gaps                       │
                    │ - Insights                   │
                    └─────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │  Interactive Exploration     │
                    │ - Query by concept           │
                    │ - Search patterns            │
                    │ - Analyze gaps               │
                    │ - Ask questions              │
                    └─────────────────────────────┘
```

### Combined Phase 1 + Phase 2 Flow

```
Raw Documents
      │
      ▼
┌─────────────────┐
│  Phase 1:       │
│  Compilation    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Structured     │
│  Knowledge      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Phase 2:       │
│  Discovery      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Enhanced       │
│  Knowledge      │
│  + Discoveries  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Interactive    │
│  Exploration    │
└─────────────────┘
```

## Component Interaction

### Phase 1 Component Interactions

```
KnowledgeCompiler (Orchestrator)
    │
    ├──▶ DocumentAnalyzer
    │       └──▶ EnhancedDocument[]
    │
    ├──▶ ConceptExtractor
    │       ├──▶ LLMProvider (for extraction)
    │       └──▶ EnhancedConcept[]
    │
    ├──▶ EmbeddingGenerator
    │       └──▶ Embeddings for concepts/documents
    │
    ├──▶ ArticleGenerator
    │       ├──▶ EnhancedConcept[]
    │       └──▶ Articles (Markdown)
    │
    ├──▶ SummaryGenerator
    │       ├──▶ EnhancedDocument[]
    │       └──▶ Summaries (Markdown)
    │
    ├──▶ BacklinkGenerator
    │       ├──▶ EnhancedConcept[]
    │       └──▶ Backlinks (Markdown)
    │
    └──▶ Indexers
            ├──▶ FileIndexer
            ├──▶ CategoryIndexer
            └──▶ RelationMapper
```

### Phase 2 Component Interactions

```
KnowledgeDiscoveryEngine (Orchestrator)
    │
    ├──▶ RelationMiningEngine
    │       ├──▶ ExplicitRelationMiner
    │       ├──▶ ImplicitRelationMiner
    │       │       └──▶ LLMProvider
    │       ├──▶ StatisticalRelationMiner
    │       │       ├──▶ NetworkX (graph algorithms)
    │       │       └──▶ Scikit-learn (correlation)
    │       └──▶ SemanticRelationMiner
    │               └──▶ EmbeddingGenerator
    │
    ├──▶ PatternDetector
    │       ├──▶ TemporalPatternDetector
    │       ├──▶ CausalPatternDetector
    │       ├──▶ EvolutionaryPatternDetector
    │       └──▶ ConflictPatternDetector
    │               └──▶ LLMProvider
    │
    ├──▶ GapAnalyzer
    │       ├──▶ ConceptGapAnalyzer
    │       │       └──▶ NetworkX (graph analysis)
    │       ├──▶ RelationGapAnalyzer
    │       │       └──▶ NetworkX (connectivity)
    │       └──▶ EvidenceAnalyzer
    │               └──▶ LLMProvider
    │
    └──▶ InsightGenerator
            ├──▶ PatternSynthesizer
            ├──▶ GapPrioritizer
            └──▶ InsightComposer
                    └──▶ LLMProvider
```

### Cross-Phase Interactions

```
Phase 1 Components           Phase 2 Components
        │                            │
        ▼                            ▼
KnowledgeCompiler  ───────▶  KnowledgeDiscoveryEngine
        │                            │
        ├── EnhancedDocument         ├── Relation[]
        ├── EnhancedConcept          ├── Pattern[]
        ├── Relation                ├── KnowledgeGap[]
        ├── Embeddings               └── Insight[]
        │                            │
        └──▶ InteractiveDiscovery ◀──┘
                    │
                    └──▶ User Queries
```

## Technology Stack

### Core Technologies

- **Python 3.8+**: Primary language
- **Pydantic**: Data validation and settings management
- **Dataclasses**: Data modeling
- **Type Hints**: Type safety

### LLM Integration

- **OpenAI API**: GPT models for extraction and analysis
- **Anthropic API**: Claude models for advanced reasoning
- **Ollama**: Local model support

### Machine Learning

- **NumPy**: Numerical computing and embeddings
- **Scikit-learn**: Statistical analysis and clustering
- **NetworkX**: Graph algorithms and analysis

### Document Processing

- **Frontmatter**: YAML metadata parsing
- **Markdown**: Document format parsing
- **Regex**: Pattern matching

### Testing

- **Pytest**: Test framework
- **Coverage.py**: Code coverage measurement

## Design Principles

### 1. Modularity

Each component has a single, well-defined responsibility and can be used independently or combined with other components.

### 2. Extensibility

The system is designed to be easily extended with new:
- Relation mining strategies
- Pattern types
- Gap analysis methods
- Insight generation approaches

### 3. Testability

All components are thoroughly tested with unit tests, integration tests, and end-to-end tests.

### 4. Performance

- Batch processing for efficiency
- Caching of intermediate results
- Parallel processing where applicable
- Streaming for large datasets

### 5. Data Quality

- Confidence scoring for all discoveries
- Evidence tracking and validation
- Deduplication and conflict resolution
- Quality thresholds and filtering

### 6. User Experience

- Clear, intuitive APIs
- Comprehensive error messages
- Interactive exploration capabilities
- Extensive documentation and examples

## Future Architecture Enhancements

### Planned Improvements

1. **Distributed Processing**: Support for large-scale knowledge bases
2. **Real-time Updates**: Incremental discovery as knowledge changes
3. **Visualization**: Interactive graph visualization of knowledge
4. **API Server**: REST API for remote access
5. **Web Interface**: Browser-based exploration and management

### Scalability Considerations

- Horizontal scaling for relation mining
- Distributed pattern detection
- Caching strategies for improved performance
- Database integration for persistent storage
