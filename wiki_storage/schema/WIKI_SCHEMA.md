# WIKI_SCHEMA

This document defines the metadata schema for Wiki pages.

## Required Fields

All Wiki pages must have the following metadata fields:

- `title` (string): Page title
- `type` (string): One of "topic", "concept", or "relation"

## Optional Fields

- `confidence` (float, 0-1): Confidence score for content
- `evidence_count` (int): Number of supporting evidence items
- `last_reviewed` (date): Last review date
- `tags` (list of string): Tags for categorization

## Validation Rules

1. All required fields must be present
2. Type must be one of the valid types
3. Confidence must be between 0 and 1 (if provided)
4. Tags must be a list (if provided)
