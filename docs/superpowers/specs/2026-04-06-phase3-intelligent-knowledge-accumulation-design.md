# Phase 3: Intelligent Knowledge Accumulation System - Design Specification

**Date**: 2026-04-06
**Version**: 1.1 (Revised)
**Status**: Design Approved with Modifications
**Target**: KnowledgeMiner 3.0

---

## Executive Summary

Phase 3 transforms KnowledgeMiner from a one-time analysis tool into a persistent knowledge accumulation system based on the LLM Wiki pattern. This comprehensive redesign implements a complete Wiki ecosystem with automatic maintenance, intelligent insight backfilling, and continuous quality assurance.

**Key Objectives**:
- Transform from static analysis to dynamic knowledge accumulation
- Implement persistent Wiki with version history
- Enable incremental updates as new documents arrive
- Automatically backfill insights to historical content
- Maintain Wiki quality through automated health checks

**Architecture Approach**: Complete redesign (Option 2) with **simplified complexity** to manage risk and ensure successful implementation.

**Key Modifications (v1.1)**:
- Simplified WikiCore (focus on storage, defer advanced features)
- Clarified incremental mode (hybrid approach)
- Reduced insight propagation complexity (direct only initially)
- Staged auto-repair system (manual → semi-auto → auto)
- Expanded testing scope (added resilience testing)
- Adjusted timeline (19-22 weeks with additional testing)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core Components (Simplified)](#2-core-components-simplified)
3. [Data Flow](#3-data-flow)
4. [Integration with Phase 2](#4-integration-with-phase-2)
5. [Technical Stack](#5-technical-stack)
6. [Implementation Roadmap (Revised)](#6-implementation-roadmap-revised)
7. [Success Criteria](#7-success-criteria)
8. [Risk Management](#8-risk-management)

---

## 1. System Overview

### 1.1 Current State (Phase 2)

KnowledgeMiner 2.0 is a one-time analysis tool that:
- Processes documents in batches
- Extracts concepts and relations
- Discovers patterns and insights
- Generates static reports
- Requires manual re-runs for updates

### 1.2 Target State (Phase 3)

KnowledgeMiner 3.0 becomes a persistent knowledge accumulation system that:
- Maintains a living Wiki with version history
- Automatically processes new documents in batches
- Intelligently backfills insights to historical content
- Continuously monitors and improves Wiki quality
- Provides semantic search and knowledge exploration

### 1.3 Key Design Decisions

**Document Arrival Mode**: Batch processing (A)
- New documents arrive daily or weekly
- Scheduled batch processing tasks
- No requirement for real-time processing

**Wiki Structure**: Hybrid approach (C)
- Topic-based organization for clarity
- Complete version history for traceability
- Each page has revision history

**Wiki Maintenance**: LLM-driven (A)
- LLM automatically generates and updates Wiki content
- Human review primarily for critical changes
- High-frequency automated updates

**Insight Backfilling**: Smart prioritization (C)
- Important insights backfilled immediately
- Less critical insights batched
- Balances freshness and efficiency

**Document Lifecycle**: Incremental growth (A)
- Wiki grows monotonically
- All historical versions preserved
- Complete audit trail

### 1.4 Complexity Management Strategy

**Principle**: Start simple, iterate rapidly, add complexity only when proven necessary.

**Simplification Decisions**:
1. **WikiCore**: Focus on storage and versioning, use existing NetworkX for graphs
2. **Incremental Mode**: Hybrid approach (smart selection based on change size)
3. **Insight Propagation**: Direct propagation only in Stage 3, defer advanced features
4. **Auto-Repair**: Three-stage rollout (manual → semi-auto → auto)
5. **Time Travel**: Defer to Phase 4 (focus on current state in Phase 3)

---

## 2. Core Components (Simplified)

### 2.1 WikiCore - Knowledge Storage Foundation

**Purpose**: Central storage and retrieval engine for all Wiki content.

**Responsibilities**:
1. Unified storage of Wiki documents (topics, concepts, relations)
2. Version control with complete history
3. Efficient retrieval by topic, time, relationships
4. Transactional guarantees for consistency

**SIMPLIFIED Internal Structure**:

```
WikiCore
├── WikiStore (Storage Engine)
│   ├── DocumentStore
│   │   ├── TopicPages (topic-specific Wiki pages)
│   │   ├── ConceptEntries (concept definitions)
│   │   └── RelationRecords (relationship records)
│   ├── VersionLog
│   │   ├── Snapshots (complete snapshots)
│   │   └── Deltas (incremental changes)
│   └── MetadataIndex
│       ├── BasicIndex (topic, concept, type)
│       └── TemporalIndex (time-based queries)
│
├── KnowledgeGraph (Uses Phase 2 NetworkX)
│   ├── ConceptGraph (reuse from Phase 2)
│   └── SimpleTemporalGraph (time-based relationships)
│
└── QueryEngine
    ├── BasicSearch (full-text search via Whoosh)
    ├── RelationQuery (via NetworkX)
    └── TimelineQuery (version history)
```

**Key Simplifications**:
- **Removed**: Advanced multi-dimensional indexing (defer to Phase 3.5)
- **Removed**: Time-travel queries (defer to Phase 4)
- **Removed**: InfluenceGraph (too complex, use simple propagation)
- **Reused**: NetworkX from Phase 2 for graph operations
- **Focused**: Core storage and versioning functionality

**Key Features**:
- **Immutable Storage**: All writes are append-only
- **Version History**: Complete audit trail via Git
- **Graph Queries**: Via proven NetworkX integration
- **Basic Search**: Full-text search via Whoosh

**File Structure**:
```
wiki_storage/
├── .git/                    # Git version control
├── topics/                   # Topic pages
│   ├── machine_learning.md
│   └── reinforcement_learning.md
├── concepts/                 # Concept entries
│   ├── q_learning.md
│   └── policy_gradient.md
├── relations/                # Relation records
│   └── relations.json
├── meta/                     # Metadata (SQLite)
│   └── wiki.db
└── schema/                   # Schema files
    └── WIKI_SCHEMA.md
```

---

### 2.2 DiscoveryPipeline 2.0 - Unified Discovery Engine

**Purpose**: Redesigned discovery pipeline supporting full, incremental, and hybrid modes.

**Key Differences from Phase 2**:
- **Phase 2**: One-time full analysis, static reports
- **Phase 3**: Continuous analysis, direct Wiki updates, smart mode selection

**Internal Structure**:

```
DiscoveryPipeline 2.0
├── InputProcessor
│   ├── BatchProcessor
│   │   ├── DetectNewDocs
│   │   ├── DetectChangedDocs
│   │   └── DetectDeletedDocs
│   └── ChangeSetBuilder
│       └── GenerateChangeSet
│
├── ModeSelector (CLARIFIED)
│   ├── FullMode
│   │   └── ProcessAllDocs (complete re-analysis)
│   ├── IncrementalMode
│   │   └── ProcessChangedDocsOnly (update changed only)
│   └── HybridMode (NEW)
│       ├── AnalyzeChangeSet (assess impact)
│       ├── SmartModeSelection (auto-select based on heuristics)
│       └── Heuristics:
│           ├── Change size (< 10 docs → incremental)
│           ├── Change scope (isolated → incremental, global → full)
│           ├── Time since last run (> 1 week → full)
│           └── User preference (configurable)
│
├── DiscoveryOrchestrator
│   ├── Phase2Components (reused as-is)
│   │   ├── RelationMiningEngine
│   │   ├── PatternDetector
│   │   ├── GapAnalyzer
│   │   └── InsightGenerator
│   └── WikiIntegrator
│       ├── UpdateTopicPages
│       ├── UpdateConceptEntries
│       ├── UpdateRelationRecords
│       └── CreateVersionSnapshot
│
└── OutputPublisher
    ├── WikiPublisher
    ├── ChangeNotifier
    └── MetricsCollector
```

**CLARIFIED Workflows**:

**Full Mode** (initial run or periodic rebuild):
```
All Documents → Phase 2 Full Analysis → Complete Wiki → Initial Version
```

**Incremental Mode** (small, isolated changes):
```
Changed Documents → Filter Affected → Phase 2 on Changed Set → Partial Wiki Update → Delta Version
```

**Hybrid Mode** (smart auto-selection - DEFAULT):
```
Analyze ChangeSet → Apply Heuristics → Select Mode → Execute → Update Wiki
```

**Change Detection Heuristics**:
- **New documents**: Never seen before
- **Changed documents**: Content, timestamp, or metadata changed
- **Deleted documents**: Removed from input
- **Impact analysis**:
  - **Isolated changes**: Only affect specific topics → incremental
  - **Global changes**: Affect core concepts → full
  - **Change size**: < 10 docs → incremental, > 50 docs → full

**Configuration**:
```python
@dataclass
class IncrementalConfig:
    mode: str = "hybrid"  # full, incremental, hybrid
    incremental_threshold: int = 10  # max docs for incremental mode
    force_full_after_days: int = 7   # force full run after N days
    enable_smart_selection: bool = True
```

---

### 2.3 InsightManager - Insight Lifecycle Management

**Purpose**: Unified management of insight lifecycle from discovery to backfilling.

**Responsibilities**:
1. Receive insights from DiscoveryPipeline
2. Multi-dimensional priority scoring
3. Intelligent backfilling based on priority
4. Knowledge propagation (SIMPLIFIED to direct only)

**SIMPLIFIED Internal Structure**:

```
InsightManager
├── InsightReceiver
│   ├── CollectInsights
│   ├── DeduplicateInsights
│   └── IndexInsights
│
├── PriorityScorer
│   ├── NoveltyScorer (NEW: specific rubrics)
│   ├── ImpactScorer (NEW: specific rubrics)
│   ├── ActionabilityScorer (NEW: specific rubrics)
│   └── CompositeScorer
│       └── CalculatePriority
│
├── BackfillScheduler
│   ├── PriorityQueue (P0, P1, P2, P3)
│   ├── ImmediateQueue (P0 only)
│   ├── BatchQueue (P1, P2, P3)
│   └── Scheduler
│
├── BackfillExecutor
│   ├── TargetFinder (find affected pages)
│   ├── ContentUpdater (update Wiki pages)
│   └── VersionCreator (create new version)
│
└── InsightPropagator (SIMPLIFIED)
    ├── DirectPropagation (ONLY)
    │   ├── FindDirectlyAffectedPages
    │   ├── UpdateDirectReferences
    │   └── VerifyDirectConsistency
    └── CycleDetector (prevent infinite loops)
        └── MaxDepth: 2 hops
```

**Key Simplifications**:
- **Removed**: Transitive propagation (defer to Stage 3.5)
- **Removed**: Conditional propagation (too complex)
- **Added**: Specific scoring rubrics for each dimension
- **Added**: Strict depth limits (max 2 hops)
- **Added**: Comprehensive cycle detection

**Enhanced Priority Scoring**:

**Scoring Rubrics**:

**Novelty Score (0-1)**:
- **0.9-1.0**: Breakthrough discovery, contradicts established knowledge
- **0.7-0.9**: Significant new pattern, not previously documented
- **0.5-0.7**: Moderate new information, extends existing knowledge
- **0.3-0.5**: Minor refinement or clarification
- **0.0-0.3**: Confirming existing knowledge

**Impact Score (0-1)**:
- **0.9-1.0**: Affects core concepts, > 100 Wiki pages
- **0.7-0.9**: Affects major topics, 10-100 Wiki pages
- **0.5-0.7**: Affects specific concepts, 5-10 Wiki pages
- **0.3-0.5**: Affects few pages, 2-5 Wiki pages
- **0.0-0.3**: Minimal impact, 1-2 Wiki pages

**Actionability Score (0-1)**:
- **0.9-1.0**: Immediately actionable, changes decisions
- **0.7-0.9**: Actionable with available resources
- **0.5-0.7**: Actionable but requires significant effort
- **0.3-0.5**: Somewhat actionable, needs more research
- **0.0-0.3**: Interesting but not actionable

**Priority Calculation**:
```python
priority_score = (novelty * 0.25) + (impact * 0.40) + (actionability * 0.35)

P0 (Immediate): score >= 0.8
P1 (Priority): 0.6 <= score < 0.8
P2 (Standard): 0.4 <= score < 0.6
P3 (Deferred): score < 0.4
```

**Simplified Propagation**:
```
Original insight: "A causes B"
↓ Direct propagation (max 2 hops)
Page B: "A causes B" (add citation)
↓ Direct propagation
Page C (directly references B): "Related: A causes B"
↓ STOP (max depth reached)
```

---

### 2.4 QualitySystem - Wiki Health Guardian

**Purpose**: Continuous monitoring of Wiki health with staged issue detection and repair.

**Responsibilities**:
1. Periodic health scans
2. Staged repair (manual → semi-auto → auto)
3. Flag issues requiring human review
4. Generate quality metrics and improvement suggestions

**STAGED Internal Structure**:

```
QualitySystem
├── HealthMonitor
│   ├── ConsistencyChecker
│   │   ├── CheckInternalConsistency
│   │   ├── CheckCrossReferenceConsistency
│   │   └── CheckTemporalConsistency
│   ├── QualityAnalyzer
│   │   ├── AnalyzeConfidence
│   │   ├── AnalyzeEvidence
│   │   └── AnalyzeCompleteness
│   └── StaleDetector
│       ├── DetectStaleContent
│       ├── DetectOrphanedPages
│       └── DetectOutdatedInsights
│
├── IssueClassifier
│   ├── CriticalIssues (Contradictions, BrokenRefs, Corruption)
│   ├── ImportantIssues (LowConfidence, WeakEvidence, Incomplete)
│   └── MinorIssues (Formatting, Typos, Style)
│
├── STAGED Repair System
│   ├── Stage 1: Manual Review Queue (ALL repairs)
│   │   ├── CriticalQueue
│   │   ├── ImportantQueue
│   │   └── MinorQueue
│   │   └── Workflow: Detect → Queue → Human Review → Apply
│   │
│   ├── Stage 2: Semi-Auto (high-confidence, low-risk only)
│   │   ├── AutoProposeRepairs
│   │   ├── HumanApproval (one-click approve)
│   │   └── Workflow: Detect → Propose → Approve → Apply
│   │
│   └── Stage 3: Full Auto (low-risk, high-confidence)
│       ├── AutoApplyRepairs
│       ├── AuditLog (all actions)
│       └── Workflow: Detect → Apply → Log → Monitor
│
├── ManualReviewQueue
│   ├── CriticalQueue
│   ├── ImportantQueue
│   └── MinorQueue
│
└── QualityReporter
    ├── MetricsCollector
    ├── TrendAnalyzer
    └── ReportGenerator
```

**Key Safeguards**:
- **All repairs are logged**: Complete audit trail
- **All repairs are reversible**: One-click undo
- **Staged rollout**: Start manual, gradually enable auto
- **Monitoring**: Track repair success rate and quality impact

**Auto-Repair Staging Criteria**:

**Stage 1 (Manual)**: All repairs
- Human review required for all fixes
- Builds trust in the system
- Validates repair logic

**Stage 2 (Semi-Auto)**: High-confidence, low-risk repairs
- Examples: Formatting fixes, typos, style consistency
- Requirements: > 95% confidence, < 1% risk
- Workflow: System proposes, human approves

**Stage 3 (Full Auto)**: Very high-confidence, very low-risk repairs
- Examples: Broken references, obvious contradictions
- Requirements: > 99% confidence, < 0.1% risk
- Workflow: System applies, logs, monitors

**Quality Metrics**:
- Health score (0-100)
- Issue distribution (critical/important/minor)
- Repair success rate
- Quality trends (improving/declining)
- Activity metrics (update frequency, new pages)

---

## 3. Data Flow

### 3.1 Complete Workflow

```
Batch Documents Arrive (daily/weekly scheduled task)
        │
        ▼
InputProcessor - Detect Changes
  • Scan input directory
  • Identify new/changed/deleted docs
  • Generate ChangeSet
        │
        ▼
ModeSelector - Choose Processing Mode (Hybrid/Smart)
  • Analyze change set size and scope
  • Apply heuristics
  • Select: full / incremental / hybrid
        │
    ┌───┴──────────────┐
    │                  │
Full Mode          Incremental/Hybrid Mode
    │                  │
    ▼                  ▼
Process All Docs    Analyze Changes
    │                  │
    └────────┬─────────┘
             │
             ▼
       DiscoveryOrchestrator
       • Call Phase 2 components
       • Generate insights
             │
             ▼
       ┌─────┴─────────┐
       │               │
       ▼               ▼
  WikiIntegrator  InsightManager
  (Direct Update)  (Smart Backfill)
       │               │
       └───────┬───────┘
               │
               ▼
         WikiCore - Storage
         • DocumentStore
         • VersionLog
         • KnowledgeGraph
               │
               ▼
         OutputPublisher
         • Notifications
         • Metrics
               │
               ▼
       QualitySystem (Background)
       • Health checks
       • Staged repairs
       • Quality reports
```

### 3.2 Key Data Structures

**ChangeSet**:
```python
@dataclass
class ChangeSet:
    new_docs: List[str]        # New document IDs
    changed_docs: List[str]    # Changed document IDs
    deleted_docs: List[str]    # Deleted document IDs
    timestamp: datetime
    batch_id: str
    impact_score: float        # NEW: 0-1, estimated impact
```

**InsightPacket**:
```python
@dataclass
class InsightPacket:
    insight: Insight
    priority: int              # 0-3 (P0-P3)
    priority_score: float      # NEW: 0-1 (raw score)
    affected_pages: List[str]
    propagation_depth: int     # Max 2 in Phase 3
    discovered_at: datetime
```

**WikiUpdate**:
```python
@dataclass
class WikiUpdate:
    page_id: str
    update_type: str           # create/update/delete/merge
    content: str
    metadata: Dict[str, Any]
    version: int
    parent_version: int
    change_summary: str
    repair_id: Optional[str]   # NEW: if from auto-repair
```

---

## 4. Integration with Phase 2

### 4.1 Component Reuse Strategy

**Completely Reused Phase 2 Components**:
```python
# No modifications needed, direct usage
from src.discovery.relation_miner import RelationMiningEngine
from src.discovery.pattern_detector import PatternDetector
from src.discovery.gap_analyzer import GapAnalyzer
from src.discovery.insight_generator import InsightGenerator
```

**Extended Phase 2 Components**:
```python
# Add mode parameter (full/incremental)
class RelationMiningEngine:
    def mine_relations(self, documents, concepts, mode='full'):
        if mode == 'full':
            return self._mine_full(documents, concepts)
        elif mode == 'incremental':
            # Only process new/changed documents
            # May miss cross-document patterns
            return self._mine_incremental(documents, concepts)
        else:  # hybrid
            # Smart selection based on heuristics
            return self._mine_hybrid(documents, concepts)
```

**Data Model Compatibility**:
```python
# Phase 2 models fully compatible
from src.core.document_model import EnhancedDocument
from src.core.concept_model import EnhancedConcept
from src.core.relation_model import Relation
from src.discovery.models.pattern import Pattern
from src.discovery.models.gap import KnowledgeGap
from src.discovery.models.insight import Insight

# Phase 3 new models
from src.wiki.models import WikiPage, WikiVersion, WikiUpdate, ChangeSet
```

### 4.2 Configuration System

**Extended Configuration with Profiles**:
```python
@dataclass
class WikiConfig:
    discovery: DiscoveryConfig      # Reuse Phase 2 config

    # Wiki storage
    wiki_storage_path: str
    version_retention_days: int
    enable_auto_maintenance: bool

    # Incremental update
    batch_schedule: str              # Cron: "0 2 * * *" (daily 2am)
    incremental_threshold: int       # Max docs for incremental mode
    force_full_after_days: int       # Force full run after N days
    enable_smart_selection: bool     # Enable hybrid mode

    # Backfill
    enable_backfill: bool
    backfill_schedule: str           # Cron: "0 3 * * 0" (weekly 3am Sun)
    immediate_backfill_threshold: float  # P0 threshold
    max_propagation_depth: int       # Max 2 in Phase 3

    # Quality system
    enable_quality_system: bool
    quality_check_schedule: str      # Cron: "0 4 * * *" (daily 4am)
    auto_repair_stage: int           # 1=manual, 2=semi-auto, 3=auto

    # NEW: Configuration Profiles
    @classmethod
    def profile_development(cls) -> 'WikiConfig':
        """Development profile: fast feedback, minimal automation"""
        return cls(
            batch_schedule="* * * * *",  # Every minute for testing
            incremental_threshold=5,
            enable_smart_selection=False,
            enable_backfill=False,
            auto_repair_stage=1  # Manual only
        )

    @classmethod
    def profile_production(cls) -> 'WikiConfig':
        """Production profile: robust, monitored, staged automation"""
        return cls(
            batch_schedule="0 2 * * *",  # Daily 2am
            incremental_threshold=10,
            force_full_after_days=7,
            enable_smart_selection=True,
            enable_backfill=True,
            backfill_schedule="0 3 * * 0",
            immediate_backfill_threshold=0.8,
            max_propagation_depth=2,
            auto_repair_stage=2  # Semi-auto
        )

    @classmethod
    def profile_minimal(cls) -> 'WikiConfig':
        """Minimal profile: basic functionality only"""
        return cls(
            batch_schedule="0 2 * * *",
            incremental_threshold=50,
            enable_smart_selection=False,
            enable_backfill=False,
            auto_repair_stage=1  # Manual only
        )
```

### 4.3 Testing Strategy

- All 117 Phase 2 tests must continue passing
- Add Phase 3 integration tests for complete workflows
- Ensure backward compatibility: Phase 2 standalone usage unaffected
- NEW: Add migration tests (Phase 2 → Phase 3)
- NEW: Add resilience tests (crashes, corruption, concurrent access)

---

## 5. Technical Stack

### 5.1 Phase 3 Additions

**Wiki Storage Layer**:
- **SQLite**: Structured data (metadata, versions, relations)
- **JSON/Markdown**: Wiki content (human-readable, VCS-friendly)
- **Git**: Version control integration (complete history)

**Task Scheduling**:
- **APScheduler**: Scheduled task management
  - Batch processing (daily/weekly)
  - Backfill tasks (priority queue)
  - Health checks (periodic)

**Search Engine**:
- **Whoosh**: Full-text search
  - Semantic search (with vectors)
  - Result highlighting
  - Pure Python, no external services

**Graph Operations**:
- **NetworkX**: Reused from Phase 2
  - Concept graphs
  - Relationship queries
  - No new graph database needed

### 5.2 Complete Dependency List

```
# Phase 2 dependencies (unchanged)
pydantic>=2.0
networkx>=3.0
numpy>=1.24
anthropic>=0.5.0
openai>=1.0
pytest>=7.0
pytest-cov>=4.0

# Phase 3 additions
apscheduler>=3.10.0      # Task scheduling
whoosh>=2.7.4            # Full-text search
gitpython>=3.1.40        # Git integration
```

### 5.3 Deployment Architecture

```
Single Machine Deployment
├── KnowledgeMiner 3.0
│   ├── WikiCore (resident process)
│   ├── Scheduler (cron triggers)
│   └── CLI (manual operations)
├── wiki_storage/
│   ├── .git/
│   ├── topics/
│   ├── concepts/
│   ├── relations/
│   └── meta/
└── config/
    ├── wiki_config.yaml
    └── profiles/
        ├── development.yaml
        ├── production.yaml
        └── minimal.yaml
```

**Rationale for Lightweight Stack**:
- Simplified deployment: No external services needed
- Sufficient performance: Knowledge base workloads are manageable
- Easy backup: Single file database + Git repository
- Proven technology: All components mature and stable

---

## 6. Implementation Roadmap (Revised)

### 6.1 Stage Overview (REVISED)

```
Phase 3: Intelligent Knowledge Accumulation (19-22 weeks)
│
├── Stage 1: Foundation (3-4 weeks)
│   ├── WikiCore storage engine (SIMPLIFIED)
│   ├── WIKI_SCHEMA system
│   └── Basic APIs
│   Milestone: Can store and query Wiki documents
│
├── Stage 2: Discovery Integration (3-4 weeks)
│   ├── DiscoveryPipeline 2.0 with CLARIFIED modes
│   ├── Incremental update engine (HYBRID approach)
│   └── Wiki integrator
│   Milestone: New docs can auto-update Wiki
│
├── Stage 3: Insight Management (4-5 weeks)
│   ├── InsightManager with SIMPLIFIED propagation
│   ├── Smart backfill system (direct only)
│   └── Enhanced priority scoring
│   Milestone: Insights auto-backfill (direct propagation)
│
├── Stage 4: Quality Assurance (3 weeks)
│   ├── QualitySystem with STAGED repairs
│   ├── Health checks (manual review queue)
│   └── Quality reporting
│   Milestone: Wiki quality monitoring (manual repairs)
│
├── Stage 5: Production Readiness (3-4 weeks) - EXPANDED
│   ├── Performance optimization
│   ├── Monitoring & alerting
│   ├── Documentation (PARALLEL development)
│   └── Test coverage (EXPANDED)
│   Milestone: System ready for beta testing
│
└── Stage 6: Resilience & Hardening (2-3 weeks) - NEW
    ├── Chaos engineering tests
    ├── Large-scale performance tests
    ├── Migration & rollback tests
    └── Long-running stability tests
    Milestone: Production ready
```

### 6.2 Detailed Timeline (REVISED)

**Stage 1: Foundation (Weeks 1-4)**

*Week 1-2: WikiCore Storage Engine (SIMPLIFIED)*
- Task 1.1: Implement simplified WikiStore
  - DocumentStore (topics, concepts, relations)
  - VersionLog (snapshots, deltas)
  - BasicIndex (topic, concept, temporal)
  - 20+ tests

- Task 1.2: Integrate NetworkX for graphs
  - Reuse Phase 2 NetworkX components
  - SimpleTemporalGraph for time-based queries
  - 10+ tests

- Task 1.3: Implement QueryEngine
  - Basic search (Whoosh integration)
  - Relation queries (NetworkX)
  - Timeline queries
  - 15+ tests

*Week 3: WIKI_SCHEMA System*
- Task 1.4: Design Schema structure
  - Metadata definition
  - Validation rules
  - Version management

- Task 1.5: Implement Schema manager
  - Schema parser
  - Schema validator
  - Schema updater
  - 10+ tests

*Week 4: Basic APIs and Integration*
- Task 1.6: Implement basic APIs
  - CRUD interfaces
  - Version management interfaces
  - Query interfaces
  - 15+ tests

- Task 1.7: End-to-end integration tests
  - Complete workflow tests
  - Performance benchmarks (establish baseline)
  - 10+ tests

**Stage 1 Total**: 80+ tests
**Milestone**: Simplified WikiCore functional, baseline performance established

---

**Stage 2: Discovery Integration (Weeks 5-8)**

*Week 5-6: DiscoveryPipeline 2.0 with CLARIFIED Modes*
- Task 2.1: Implement InputProcessor
  - Batch processing
  - Change detection
  - ChangeSet generation with impact_score
  - 15+ tests

- Task 2.2: Implement ModeSelector with HYBRID mode
  - Full mode
  - Incremental mode
  - **Hybrid mode** (smart selection with heuristics)
  - 15+ tests

- Task 2.3: Implement DiscoveryOrchestrator
  - Integrate Phase 2 components
  - Wiki integrator
  - Version snapshots
  - 20+ tests

*Week 7: Incremental Update Engine*
- Task 2.4: Implement incremental discovery
  - Extend Phase 2 components for incremental mode
  - Document impact analysis
  - Change propagation
  - 15+ tests

*Week 8: Task Scheduling and Configuration*
- Task 2.5: Implement task scheduling
  - APScheduler integration
  - Batch processing logic
  - Error handling and retry
  - 10+ tests

- Task 2.6: Configuration profiles
  - Development profile
  - Production profile
  - Minimal profile
  - Configuration validation
  - 5+ tests

**Stage 2 Total**: 80+ tests
**Milestone**: New documents can automatically update Wiki with smart mode selection

---

**Stage 3: Insight Management (Weeks 9-13)**

*Week 9-10: InsightManager Core with Enhanced Scoring*
- Task 3.1: Implement InsightReceiver
  - Insight collection and deduplication
  - Indexing and caching
  - 10+ tests

- Task 3.2: Implement Enhanced PriorityScorer
  - **Specific rubrics** for novelty, impact, actionability
  - Priority calculation with configurable weights
  - Priority level classification (P0-P3)
  - 15+ tests

- Task 3.3: Implement BackfillScheduler
  - Priority queues (P0-P3)
  - Scheduling strategy
  - 15+ tests

*Week 11-12: SIMPLIFIED Backfill Execution*
- Task 3.4: Implement BackfillExecutor
  - Target finding (affected pages)
  - Content updates
  - Version creation
  - 20+ tests

- Task 3.5: Implement SIMPLIFIED InsightPropagator
  - **Direct propagation only**
  - Strict depth limits (max 2 hops)
  - Comprehensive cycle detection
  - 15+ tests

*Week 13: Integration and Testing*
- Task 3.6: End-to-end tests
  - Insight discovery → backfill → propagation (direct only)
  - Performance tests
  - Edge case tests
  - 15+ tests

**Stage 3 Total**: 90+ tests
**Milestone**: Insights automatically backfill with direct propagation (max 2 hops)

---

**Stage 4: Quality Assurance (Weeks 14-16)**

*Week 14-15: QualitySystem with STAGED Repairs*
- Task 4.1: Implement HealthMonitor
  - Consistency checks
  - Quality analysis
  - Staleness detection
  - 20+ tests

- Task 4.2: Implement **STAGED** repair system
  - **Stage 1**: Manual review queue (all repairs)
  - Audit logging
  - One-click undo
  - 15+ tests

- Task 4.3: Implement QualityReporter
  - Metrics collection
  - Trend analysis
  - Report generation
  - 10+ tests

*Week 16: Integration and Validation*
- Task 4.4: End-to-end tests
  - Quality detection → manual review → repair workflow
  - Long-running tests (1 week continuous operation)
  - 10+ tests

**Stage 4 Total**: 55+ tests
**Milestone**: Wiki quality monitoring with manual repair queue (Stage 1)

---

**Stage 5: Production Readiness (Weeks 17-19)** - EXPANDED

*Week 17: Performance Optimization*
- Task 5.1: Performance optimization
  - Query optimization (based on Stage 1 baseline)
  - Caching strategies
  - Concurrent processing
  - 10+ tests

- Task 5.2: Monitoring and alerting
  - Structured logging
  - Metrics collection
  - Alert rules
  - Dashboard
  - 5+ tests

*Week 18: Documentation (PARALLEL)*
- Task 5.3: Comprehensive documentation
  - API documentation (with examples)
  - User manual
  - Deployment guide
  - Migration guide (Phase 2 → Phase 3)
  - Troubleshooting guide
  - 3+ complete examples

*Week 19: Feature Flags and Staging*
- Task 5.4: Implement feature flags
  - Enable gradual rollout
  - Support A/B testing
  - Quick rollback capability
  - 5+ tests

- Task 5.5: Configuration validation
  - Comprehensive config validation
  - Helpful error messages
  - Profile testing
  - 5+ tests

**Stage 5 Total**: 30+ tests
**Milestone**: System ready for beta testing with observability

---

**Stage 6: Resilience & Hardening (Weeks 20-22)** - NEW

*Week 20: Chaos Engineering*
- Task 6.1: Failure injection tests
  - Crash recovery
  - Data corruption scenarios
  - Network failures
  - Disk full scenarios
  - 15+ tests

- Task 6.2: Concurrent access tests
  - Multiple processes updating Wiki
  - Race conditions
  - Lock contention
  - 10+ tests

*Week 21: Large-Scale Testing*
- Task 6.3: Performance at scale
  - 10,000+ Wiki pages
  - 100,000+ concept entries
  - 1,000+ document batch
  - Stress tests
  - 15+ tests

*Week 22: Migration and Stability*
- Task 6.4: Migration tests
  - Phase 2 → Phase 3 migration
  - Data integrity verification
  - Rollback scenarios
  - 10+ tests

- Task 6.5: Long-running stability tests
  - 4 weeks of continuous operation simulation
  - Memory leak detection
  - Performance degradation detection
  - 10+ tests

**Stage 6 Total**: 60+ tests
**Milestone**: Production ready with proven resilience

---

### 6.3 Summary (REVISED)

**Total Timeline**: 19-22 weeks (5-6 months)

**Total Test Count**: 395+ tests (increased from 335+)

**Code Estimate**: 15,000-20,000 lines of new code

**Key Milestones**: 6 stage acceptance points (increased from 5)

**Major Changes from v1.0**:
- Simplified WikiCore (remove advanced features)
- Clarified incremental mode (hybrid approach)
- Simplified insight propagation (direct only)
- Staged auto-repair (manual → semi-auto → auto)
- Expanded testing (added Stage 6: Resilience)
- Increased timeline (15-19 weeks → 19-22 weeks)
- More comprehensive documentation (parallel development)

---

## 7. Success Criteria

### 7.1 Functional Requirements

**Must Have**:
- ✅ Wiki stores all knowledge with complete version history
- ✅ Batch processing of new documents (daily/weekly)
- ✅ **Hybrid incremental updates** (smart mode selection)
- ✅ Insights automatically backfill to relevant historical pages
- ✅ **Direct insight propagation** (max 2 hops)
- ✅ Quality system with **manual repair queue** (Stage 1)
- ✅ All Phase 2 tests continue passing (117+ tests)
- ✅ Full-text search across all Wiki content
- ✅ Configuration profiles (dev, production, minimal)

**Should Have**:
- ✅ Semantic search with vector embeddings
- ✅ Knowledge graph navigation (via NetworkX)
- ✅ **Version history queries** (not full time travel)
- ✅ Change notifications and alerts
- ✅ Performance monitoring and metrics
- ✅ Comprehensive documentation
- ✅ **Migration tools** (Phase 2 → Phase 3)

**Nice to Have** (Deferred to Phase 4):
- 🔄 Time travel queries (query any historical state)
- 🔄 Transitive insight propagation
- 🔄 Conditional insight propagation
- 🔄 Auto-repair Stage 2 (semi-auto)
- 🔄 Auto-repair Stage 3 (full auto)
- 🔄 User interface for Wiki browsing
- 🔄 Advanced visualization tools

### 7.2 Non-Functional Requirements

**Performance** (ADJUSTED based on Stage 1 baseline):
- Full analysis of 100 documents: < 5 minutes
- Incremental update of 10 documents: < 30 seconds
- Wiki query response: < 1 second
- Backfill processing: < 1 hour for P0 insights

**Scalability**:
- Support 10,000+ Wiki pages
- Support 100,000+ concept entries
- Support 1,000,000+ relation records
- Handle batch of 1,000+ documents

**Reliability**:
- 99% uptime for automated tasks
- Zero data loss (Git + SQLite durability)
- Automatic recovery from failures
- Complete audit trail (all repairs logged)
- **Proven resilience** (chaos engineering tests)

**Maintainability**:
- Test coverage > 85%
- Clear separation of concerns
- Comprehensive documentation
- Easy to extend and modify
- **Configuration profiles** for different environments

### 7.3 Quality Metrics

**Code Quality**:
- All tests passing (395+ tests)
- Code coverage > 85%
- No critical linting issues
- Code review approved

**System Quality**:
- Health score > 90 (auto-graded)
- < 5% critical issues
- < 10% important issues
- Quality trend: improving or stable
- **Repair success rate > 95%** (before enabling Stage 2 auto-repair)

**User Acceptance**:
- Complete example workflows
- User documentation available
- Deployment guide tested
- Performance benchmarks met
- **Migration guide validated**

---

## 8. Risk Management

### 8.1 Key Risks and Mitigations

**Risk 1: WikiCore Complexity**
- **Impact**: High
- **Probability**: Medium (reduced by simplification)
- **Mitigation**:
  - Simplified scope (storage + versioning only)
  - Reuse NetworkX for graphs
  - Defer advanced features to Phase 4
  - Proof-of-concept in Week 0

**Risk 2: Incremental Mode Effectiveness**
- **Impact**: High
- **Probability**: Medium
- **Mitigation**:
  - Hybrid mode with smart selection
  - Clear documentation of trade-offs
  - Configuration options for mode selection
  - Performance testing to validate benefit

**Risk 3: Insight Propagation Errors**
- **Impact**: Medium
- **Probability**: Low (reduced by simplification)
- **Mitigation**:
  - Direct propagation only (max 2 hops)
  - Strict cycle detection
  - Comprehensive testing
  - Easy rollback via Git

**Risk 4: Auto-Repair Mistakes**
- **Impact**: High
- **Probability**: Low (reduced by staging)
- **Mitigation**:
  - Staged rollout (manual → semi-auto → auto)
  - All repairs logged and reversible
  - One-click undo
  - Success rate > 95% before Stage 2

**Risk 5: Performance Degradation**
- **Impact**: Medium
- **Probability**: Medium
- **Mitigation**:
  - Baseline established in Stage 1
  - Performance testing in each stage
  - Optimization in Stage 5
  - Large-scale tests in Stage 6

**Risk 6: Data Migration Issues**
- **Impact**: High
- **Probability**: Low
- **Mitigation**:
  - Comprehensive migration tests (Stage 6)
  - Rollback procedures tested
  - Data integrity verification
  - Migration guide validated

### 8.2 Complexity Management

**Principles**:
1. Start simple, add complexity when proven necessary
2. Use proven technology (NetworkX, Git, SQLite)
3. Comprehensive testing at each stage
4. Staged rollout of risky features
5. Continuous monitoring and adjustment

**Simplifications**:
- WikiCore: Focus on storage, defer advanced features
- Incremental mode: Hybrid with smart selection
- Insight propagation: Direct only, defer transitive
- Auto-repair: Manual first, gradual automation
- Testing: Add resilience stage (Stage 6)

**Success Criteria for Adding Complexity**:
- Current implementation is stable and tested
- Clear use case for additional complexity
- Performance impact is acceptable
- Can be tested and validated
- Can be rolled back if needed

### 8.3 Monitoring and Adjustment

**Metrics to Track**:
- Development velocity (features per week)
- Test pass rate (target: > 95%)
- Performance against baseline
- Bug discovery rate
- Code review turnaround time

**Decision Points**:
- End of Stage 1: Validate WikiCore performance, adjust targets if needed
- End of Stage 3: Evaluate direct propagation effectiveness
- End of Stage 4: Assess repair success rate, decide on Stage 2/3 enablement
- End of Stage 5: Beta readiness, go/no-go for Stage 6

**Escalation Criteria**:
- Stage falls > 2 weeks behind schedule
- Test pass rate < 90% for > 1 week
- Performance < 50% of target
- Critical bugs remain unresolved > 1 week

---

## Appendix A: Glossary

**Wiki**: Living knowledge base maintained by LLMs with version history

**Backfilling**: Process of applying new insights to historical content

**Incremental Update**: Processing only changed documents rather than full re-analysis

**Hybrid Mode**: Smart selection between full and incremental based on heuristics

**ChangeSet**: Set of document changes (new, changed, deleted) with impact score

**Direct Propagation**: Updating only directly related pages (max 2 hops)

**Health Score**: Composite metric (0-100) of Wiki quality

**Priority Scoring**: Multi-dimensional assessment (novelty × impact × actionability)

**Staged Repair**: Gradual automation (manual → semi-auto → auto)

**Configuration Profile**: Pre-configured settings for specific environments (dev, prod, minimal)

---

## Appendix B: References

**Phase 2 Implementation**:
- KnowledgeMiner 2.0 complete implementation
- 117 tests passing
- 89% code coverage
- Location: `.worktrees/phase2-discovery`

**LLM Wiki Pattern**:
- Original concept document
- Wiki auto-generation principles
- Knowledge backfilling strategies

**Related Systems**:
- Obsidian: Knowledge base with graph view
- Roam Research: Bidirectional linking
- Confluence: Enterprise Wiki with versioning
- Notion: Block-based Wiki with databases

**Design Review**:
- Version 1.0 review completed 2026-04-06
- Key issues identified and addressed in v1.1
- Approved with modifications

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-06 | Claude | Initial design specification |
| 1.1 | 2026-04-06 | Claude | **REVISED**: Simplified WikiCore, clarified incremental mode, reduced propagation complexity, staged auto-repair, expanded testing, adjusted timeline (19-22 weeks) |

---

**END OF DESIGN SPECIFICATION v1.1**
