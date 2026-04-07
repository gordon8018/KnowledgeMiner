#!/usr/bin/env python3
"""
Knowledge Compiler CLI Entry Point

This module provides the command-line interface for the Knowledge Compiler system.
"""

import argparse
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.compiler_config import Config
from src.main import KnowledgeCompiler


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""

    parser = argparse.ArgumentParser(
        description="Knowledge Compiler - Convert markdown documents into structured knowledge bases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --source ./docs --output ./knowledge_base
  %(prog)s --config config.json --verbose
  %(prog)s --source ./docs --output ./knowledge_base --no-interactive
  %(prog)s --quiet --source ./docs --output ./knowledge_base
        """
    )

    # Positional arguments
    parser.add_argument(
        'source_dir',
        nargs='?',
        default='.',
        help='Source directory containing markdown files (default: current directory)'
    )

    # Output options
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory for generated files (default: output)'
    )

    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file (JSON format)'
    )

    # Processing options
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        default=True,
        help='Process files recursively (default: True)'
    )

    parser.add_argument(
        '--non-recursive',
        action='store_true',
        help='Process files in the source directory only (no recursion)'
    )

    # Output generation options
    parser.add_argument(
        '--no-summaries',
        action='store_true',
        help='Disable summary generation'
    )

    parser.add_argument(
        '--no-articles',
        action='store_true',
        help='Disable article generation'
    )

    parser.add_argument(
        '--no-backlinks',
        action='store_true',
        help='Disable backlink generation'
    )

    # Interactive options
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Disable interactive mode'
    )

    # Logging options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )

    # Model options
    parser.add_argument(
        '--model',
        default='gpt-3.5-turbo',
        help='AI model to use for processing (default: gpt-3.5-turbo)'
    )

    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature for AI model (0.0-1.0, default: 0.7)'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=2000,
        help='Maximum tokens for AI model (default: 2000)'
    )

    # File options
    parser.add_argument(
        '--max-file-size',
        type=int,
        default=10 * 1024 * 1024,
        help='Maximum file size to process in bytes (default: 10MB)'
    )

    parser.add_argument(
        '--file-patterns',
        nargs='*',
        default=['*.md', '*.markdown'],
        help='File patterns to match (default: *.md *.markdown)'
    )

    # Analysis options
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.6,
        help='Minimum confidence threshold for concept extraction (0.0-1.0, default: 0.6)'
    )

    parser.add_argument(
        '--max-concepts',
        type=int,
        default=20,
        help='Maximum concepts to extract per document (default: 20)'
    )

    parser.add_argument(
        '--no-relations',
        action='store_true',
        help='Disable relation extraction'
    )

    # Version
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    return parser


def load_config(args) -> Config:
    """Load configuration from command line arguments and/or config file."""

    # Start with default configuration
    config = Config()

    # Load from config file if provided
    if args.config:
        if os.path.exists(args.config):
            file_config = Config.from_file(args.config)
            config = config.merge_with_defaults(file_config)
        else:
            print(f"Warning: Config file not found: {args.config}")

    # Override with command line arguments
    config.source_dir = os.path.abspath(args.source_dir)
    config.output_dir = os.path.abspath(args.output)

    if args.non_recursive:
        config.recursive_processing = False

    if args.no_summaries:
        config.generate_summaries = False

    if args.no_articles:
        config.generate_articles = False

    if args.no_backlinks:
        config.generate_backlinks = False

    if args.no_interactive:
        config.interactive_mode = False

    if args.verbose:
        config.verbose_output = True
        config.quiet_mode = False

    if args.quiet:
        config.quiet_mode = True
        config.verbose_output = False

    config.model_name = args.model
    config.temperature = args.temperature
    config.max_tokens = args.max_tokens
    config.max_file_size = args.max_file_size
    config.file_patterns = args.file_patterns
    config.min_confidence_threshold = args.min_confidence
    config.max_concepts_per_document = args.max_concepts

    if args.no_relations:
        config.enable_relation_extraction = False

    # Validate configuration
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    return config


def main() -> int:
    """Main entry point for the CLI."""

    parser = create_parser()
    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(args)

        # Create and run the compiler
        compiler = KnowledgeCompiler(config)

        if config.interactive_mode:
            results = compiler.run_interactive_session()
        else:
            results = compiler.compile()

        # Output summary if not in quiet mode
        if not config.quiet_mode:
            print(f"\nCompilation completed!")
            print(f"Files processed: {results.get('processed_files', 0)}")
            print(f"Concepts extracted: {results.get('extracted_concepts', 0)}")

            if 'confirmed_concepts' in results:
                print(f"Concepts confirmed: {results.get('confirmed_concepts', 0)}")
                print(f"Concepts filtered: {results.get('filtered_concepts', 0)}")

            if results.get('errors'):
                print(f"Errors: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"  - {error}")

            if results.get('warnings'):
                print(f"Warnings: {len(results['warnings'])}")
                for warning in results['warnings']:
                    print(f"  - {warning}")

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())