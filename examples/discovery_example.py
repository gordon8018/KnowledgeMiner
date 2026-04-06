"""
Knowledge Discovery Engine Usage Example

This example demonstrates how to use the Knowledge Discovery Engine
to discover hidden relationships, patterns, gaps, and insights in your
knowledge base.
"""

import os
from datetime import datetime
from src.discovery import (
    KnowledgeDiscoveryEngine,
    InteractiveDiscovery,
    DiscoveryConfig
)
from src.core.concept_model import EnhancedConcept, ConceptType
from src.core.document_model import EnhancedDocument
from src.core.relation_model import Relation, RelationType
from src.integrations.llm_providers import create_llm_provider
from src.ml.embeddings import EmbeddingGenerator


def create_sample_data():
    """Create sample documents and concepts for demonstration."""

    # Sample documents
    doc1 = EnhancedDocument(
        id="doc1",
        path="./docs/momentum.md",
        title="Momentum Trading Strategy",
        content="""
# Momentum Trading Strategy

Momentum is a technical indicator that shows the rate of change of a security's price.
It is often used to identify trend strength and potential reversal points.

## Key Features
- Measures velocity of price changes
- Helps identify overbought/oversold conditions
- Often used with RSI and MACD indicators

## Applications
- Trend following strategies
- Reversal detection
- Entry/exit signal generation
        """,
        metadata={"category": "technical_analysis", "difficulty": "intermediate"},
        sections=[],
        hash="abc123",
        created_at=datetime.now()
    )

    doc2 = EnhancedDocument(
        id="doc2",
        path="./docs/rsi.md",
        title="Relative Strength Index (RSI)",
        content="""
# Relative Strength Index

RSI is a momentum oscillator that measures the speed and change of price movements.
It ranges from 0 to 100 and is typically used to identify overbought/oversold conditions.

## Key Features
- Range-bound oscillator (0-100)
- Overbought: RSI > 70
- Oversold: RSI < 30

## Relationships
- Often combined with Momentum indicator
- Complements MACD analysis
        """,
        metadata={"category": "technical_analysis", "difficulty": "beginner"},
        sections=[],
        hash="def456",
        created_at=datetime.now()
    )

    # Sample concepts
    momentum = EnhancedConcept(
        id="concept1",
        name="Momentum",
        type=ConceptType.INDICATOR,
        definition="A technical indicator showing the rate of price change",
        properties={
            "calculation": "Price difference over time period",
            "typical_period": "14 days"
        }
    )

    rsi = EnhancedConcept(
        id="concept2",
        name="RSI",
        type=ConceptType.INDICATOR,
        definition="Relative Strength Index - momentum oscillator measuring price velocity",
        properties={
            "range": "0-100",
            "overbought_threshold": 70,
            "oversold_threshold": 30
        }
    )

    trend_following = EnhancedConcept(
        id="concept3",
        name="Trend Following",
        type=ConceptType.STRATEGY,
        definition="Trading strategy that follows existing market trends",
        properties={
            "key_indicators": ["Momentum", "RSI", "MACD"]
        }
    )

    # Existing relations
    existing_relations = [
        Relation(
            id="rel1",
            source_concept="Momentum",
            target_concept="RSI",
            relation_type=RelationType.RELATES_TO,
            strength=0.8,
            properties={"context": "technical_analysis"}
        ),
        Relation(
            id="rel2",
            source_concept="Momentum",
            target_concept="Trend Following",
            relation_type=RelationType.USES,
            strength=0.9,
            properties={"context": "strategy_implementation"}
        )
    ]

    return [doc1, doc2], [momentum, rsi, trend_following], existing_relations


def example_basic_discovery():
    """Example 1: Basic knowledge discovery."""
    print("\n" + "="*80)
    print("Example 1: Basic Knowledge Discovery")
    print("="*80)

    # Create configuration
    config = DiscoveryConfig(
        enable_explicit_mining=True,
        enable_implicit_mining=True,
        enable_statistical_mining=True,
        enable_semantic_mining=True,
        enable_temporal_detection=True,
        enable_causal_detection=True,
        enable_evolutionary_detection=True,
        enable_conflict_detection=True,
        enable_concept_gap_analysis=True,
        enable_relation_gap_analysis=True,
        enable_evidence_analysis=True
    )

    # Initialize LLM provider (configure with your API key)
    # For this example, we'll use a mock provider
    try:
        llm_provider = create_llm_provider(
            provider="openai",
            model="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here")
        )
    except Exception as e:
        print(f"Warning: Could not initialize LLM provider: {e}")
        print("Continuing without LLM capabilities...")
        llm_provider = None

    # Initialize embedding generator
    try:
        embedder = EmbeddingGenerator()
    except Exception as e:
        print(f"Warning: Could not initialize embedding generator: {e}")
        print("Continuing without embedding capabilities...")
        embedder = None

    # Create discovery engine
    engine = KnowledgeDiscoveryEngine(
        config=config,
        llm_provider=llm_provider,
        embedding_generator=embedder
    )

    # Create sample data
    documents, concepts, existing_relations = create_sample_data()

    # Run discovery
    print("\n🔍 Running knowledge discovery...")
    result = engine.discover(
        documents=documents,
        concepts=concepts,
        relations=existing_relations
    )

    # Display results
    print("\n📊 Discovery Results:")
    print(f"   Total Relations: {len(result.relations)}")
    print(f"   Total Patterns: {len(result.patterns)}")
    print(f"   Total Gaps: {len(result.gaps)}")
    print(f"   Total Insights: {len(result.insights)}")
    print(f"   Generated At: {result.generated_at}")

    # Show discovered relations
    print("\n🔗 Discovered Relations:")
    for i, rel in enumerate(result.relations[:5], 1):
        print(f"   {i}. {rel.source_concept} --[{rel.relation_type}]--> {rel.target_concept}")
        print(f"      Strength: {rel.strength:.2f}")

    # Show detected patterns
    print("\n🎯 Detected Patterns:")
    for i, pattern in enumerate(result.patterns[:3], 1):
        print(f"   {i}. {pattern.title}")
        print(f"      Type: {pattern.pattern_type}")
        print(f"      Confidence: {pattern.confidence:.2f}")

    # Show identified gaps
    print("\n📋 Identified Gaps:")
    for i, gap in enumerate(result.gaps[:3], 1):
        print(f"   {i}. {gap.gap_type}: {gap.description}")
        print(f"      Priority: {gap.priority}/10")

    # Show top insights
    print("\n💡 Top Insights:")
    for i, insight in enumerate(result.insights[:3], 1):
        print(f"   {i}. {insight.title}")
        print(f"      Significance: {insight.significance:.2f}")
        print(f"      {insight.description[:100]}...")

    return result


def example_interactive_exploration():
    """Example 2: Interactive knowledge exploration."""
    print("\n" + "="*80)
    print("Example 2: Interactive Knowledge Exploration")
    print("="*80)

    # Create configuration
    config = DiscoveryConfig()

    # Initialize engine (without LLM for this example)
    engine = KnowledgeDiscoveryEngine(config=config)

    # Create sample data
    documents, concepts, existing_relations = create_sample_data()

    # Create interactive discovery instance
    interactive = InteractiveDiscovery(engine)

    # Run discovery and store results
    print("\n🔍 Running discovery...")
    result = interactive.discover_and_store(
        documents=documents,
        concepts=concepts,
        relations=existing_relations
    )

    # Explore relations for a specific concept
    print("\n🔗 Exploring relations for 'Momentum':")
    momentum_relations = interactive.explore_relations("Momentum")
    for rel in momentum_relations:
        direction = "→" if rel.source_concept == "Momentum" else "←"
        target = rel.target_concept if rel.source_concept == "Momentum" else rel.source_concept
        print(f"   Momentum {direction} {target} ({rel.relation_type})")

    # Find patterns related to 'momentum'
    print("\n🎯 Finding patterns related to 'momentum':")
    momentum_patterns = interactive.find_patterns("momentum")
    for pattern in momentum_patterns:
        print(f"   - {pattern.title}")

    # Analyze gaps in 'technical_analysis'
    print("\n📋 Analyzing gaps in 'technical_analysis':")
    ta_gaps = interactive.analyze_gaps_in_domain("technical")
    for gap in ta_gaps:
        print(f"   - {gap.description}")

    # Get top insights
    print("\n💡 Top 5 Insights:")
    top_insights = interactive.get_top_insights(5)
    for i, insight in enumerate(top_insights, 1):
        print(f"   {i}. {insight.title}")
        print(f"      Significance: {insight.significance:.2f}")

    # Ask a natural language question (requires LLM)
    print("\n❓ Asking a natural language question:")
    try:
        answer = interactive.ask_question(
            "How are Momentum and RSI indicators related in trading strategies?"
        )
        print(f"   Answer: {answer}")
    except Exception as e:
        print(f"   Could not generate answer (LLM not configured): {e}")


def example_custom_configuration():
    """Example 3: Custom configuration for specific needs."""
    print("\n" + "="*80)
    print("Example 3: Custom Configuration")
    print("="*80)

    # Create configuration focused on pattern detection
    config = DiscoveryConfig(
        # Enable only pattern detection
        enable_explicit_mining=False,
        enable_implicit_mining=False,
        enable_statistical_mining=False,
        enable_semantic_mining=False,

        # Enable all pattern types
        enable_temporal_detection=True,
        enable_causal_detection=True,
        enable_evolutionary_detection=True,
        enable_conflict_detection=True,

        # Higher confidence threshold for patterns
        min_pattern_confidence=0.7,

        # Disable gap analysis
        enable_concept_gap_analysis=False,
        enable_relation_gap_analysis=False,
        enable_evidence_analysis=False,

        # Adjust insight generation
        max_insights=20,
        insight_significance_threshold=0.8
    )

    print("\n⚙️  Custom Configuration:")
    print(f"   Relation Mining: Disabled")
    print(f"   Pattern Detection: Enabled (all types)")
    print(f"   Gap Analysis: Disabled")
    print(f"   Min Pattern Confidence: {config.min_pattern_confidence}")
    print(f"   Max Insights: {config.max_insights}")

    # Initialize engine
    engine = KnowledgeDiscoveryEngine(config=config)

    # Create sample data
    documents, concepts, existing_relations = create_sample_data()

    # Run discovery
    print("\n🔍 Running focused pattern detection...")
    result = engine.discover(
        documents=documents,
        concepts=concepts,
        relations=existing_relations
    )

    # Display pattern-focused results
    print("\n📊 Pattern Detection Results:")
    print(f"   Total Patterns: {len(result.patterns)}")
    print(f"   High Confidence Patterns: {len([p for p in result.patterns if p.confidence >= 0.7])}")

    print("\n🎯 Detected Patterns:")
    for i, pattern in enumerate(result.patterns, 1):
        print(f"   {i}. {pattern.title}")
        print(f"      Type: {pattern.pattern_type}")
        print(f"      Confidence: {pattern.confidence:.2f}")
        print(f"      Related Concepts: {', '.join(pattern.related_concepts[:3])}")


def example_incremental_discovery():
    """Example 4: Incremental discovery with existing relations."""
    print("\n" + "="*80)
    print("Example 4: Incremental Discovery")
    print("="*80)

    config = DiscoveryConfig()
    engine = KnowledgeDiscoveryEngine(config=config)

    documents, concepts, existing_relations = create_sample_data()

    print(f"\n📊 Starting with {len(existing_relations)} existing relations:")
    for rel in existing_relations:
        print(f"   - {rel.source_concept} -> {rel.target_concept} ({rel.relation_type})")

    # Run discovery with existing relations
    print("\n🔍 Running incremental discovery...")
    result = engine.discover(
        documents=documents,
        concepts=concepts,
        relations=existing_relations  # Provide existing relations
    )

    print(f"\n📊 Discovery Results:")
    print(f"   Total Relations (including existing): {len(result.relations)}")
    print(f"   New Relations Discovered: {len(result.relations) - len(existing_relations)}")

    print("\n🔗 All Relations:")
    for i, rel in enumerate(result.relations, 1):
        source = rel.source_concept
        target = rel.target_concept
        rel_type = rel.relation_type
        is_new = " (NEW)" if rel not in existing_relations else ""
        print(f"   {i}. {source} --[{rel_type}]--> {target}{is_new}")


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("Knowledge Discovery Engine - Usage Examples")
    print("="*80)

    print("""
This example demonstrates the Knowledge Discovery Engine capabilities:

1. Basic Discovery - Run complete discovery pipeline
2. Interactive Exploration - Explore results interactively
3. Custom Configuration - Focus on specific discovery aspects
4. Incremental Discovery - Build on existing knowledge

Note: Some examples require LLM API keys for full functionality.
    """)

    # Run examples
    try:
        example_basic_discovery()
        example_interactive_exploration()
        example_custom_configuration()
        example_incremental_discovery()

        print("\n" + "="*80)
        print("All examples completed successfully!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
