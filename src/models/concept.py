from dataclasses import dataclass
from typing import List, Dict
# Import ConceptType from core to avoid duplication
from src.core.concept_model import ConceptType

@dataclass
class CandidateConcept:
    name: str
    type: ConceptType
    confidence: float
    context: str
    source_section: str
    source_file: str

@dataclass
class Concept:
    name: str
    type: ConceptType
    definition: str
    criteria: str
    applications: List[Dict[str, str]]
    cases: List[str]
    formulas: List[str]
    related_concepts: List[str]
    backlinks: List[Dict[str, str]]