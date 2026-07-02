from dataclasses import dataclass, field
from typing import List, Dict
from pydantic import BaseModel, Field as PydanticField

@dataclass
class FileMetadata:
    path: str
    role: str
    responsibility: str
    primary_entities: List[str]
    configuration_keys: List[str]
    external_interfaces: List[str]
    technologies: List[str]
    concepts: List[str]
    confidence: float

@dataclass
class Candidate:
    path: str
    score: float
    reasons: Dict[str, List[str]]

@dataclass
class ReviewObligation:
    priority: str  # HIGH, MEDIUM, LOW
    confidence: str  # HIGH, MEDIUM, LOW
    title: str
    area: str
    reason: str
    evidence_files: List[str]

@dataclass
class ReviewContext:
    git_diff: str
    changed_files: List[str]
    workspace_snapshot: Dict[str, FileMetadata]
    candidate_files: List[Candidate] = field(default_factory=list)
    prompt: str = ""
    llm_response: str = ""
    obligations: List[ReviewObligation] = field(default_factory=list)

@dataclass
class ReviewReport:
    changed_files_count: int
    total_files_analyzed: int
    candidates: List[Candidate]
    obligations: List[ReviewObligation] = field(default_factory=list)


# Pydantic Schemas for Gemini Structured JSON output
class ObligationSchema(BaseModel):
    priority: str = PydanticField(..., description="Urgency: HIGH, MEDIUM, or LOW.")
    confidence: str = PydanticField(..., description="How confident ProjectMind is that the obligation is worth human review, not how certain it is that the code is incorrect (HIGH, MEDIUM, or LOW).")
    title: str = PydanticField(..., description="Short descriptive title of the review task.")
    area: str = PydanticField(..., description="Project area or subsystem affected (e.g. Authentication, Seeder script).")
    reason: str = PydanticField(..., description="Must explain WHY it needs review and WHAT to verify. Do NOT explain HOW to fix.")
    evidence_files: List[str] = PydanticField(..., description="List of at least one candidate file contributing to this obligation.")

class ReviewResponseSchema(BaseModel):
    obligations: List[ObligationSchema] = PydanticField(default_factory=list, description="List of predicted review obligations.")
