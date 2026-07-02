import os
from typing import List, Dict
from .models import Candidate, FileMetadata

def find_candidates(changed_files: List[str], snapshot: Dict[str, FileMetadata]) -> List[Candidate]:
    """Deterministically identifies candidate files that may have review obligations based on changed files."""
    candidates = {}
    changed_set = set(changed_files)
    
    for changed_path in changed_files:
        changed_meta = snapshot.get(changed_path)
        if not changed_meta:
            continue
            
        changed_dir = os.path.dirname(changed_path)
        changed_base = os.path.basename(changed_path).split(".")[0]

        for path, meta in snapshot.items():
            # Never recommend the changed files themselves
            if path in changed_set:
                continue

            score = 0.0
            reasons = {}

            # Helper to add a structured reason
            def add_reason(category: str, detail: str):
                if category not in reasons:
                    reasons[category] = []
                reasons[category].append(detail)

            # Heuristic 1: Test file matching
            # e.g., auth.py vs test_auth.py or auth.test.ts
            is_test_for_changed = (
                meta.role == "Test Suite" and (changed_base in path or path.split(".")[0] in changed_path)
            )
            if is_test_for_changed:
                score = max(score, 0.70)  # MEDIUM: Obvious but necessary
                add_reason("Direct test suite", f"Validates modifications in '{changed_path}'")

            # Heuristic 2: Shared configuration keys (e.g. PORT, DATABASE_URL)
            shared_config = set(changed_meta.configuration_keys).intersection(meta.configuration_keys)
            if shared_config:
                # Prioritize key configs and server logic as HIGH review obligations
                is_high_priority_target = meta.role in ("Infrastructure Config", "Environment Template") or "server" in path.lower()
                if is_high_priority_target:
                    score = max(score, 0.90)  # HIGH
                    add_reason("Shared configuration (High Priority)", f"Keys {list(shared_config)} map to '{path}'")
                else:
                    score = max(score, 0.65)  # MEDIUM (indirect configuration dependencies like seed scripts)
                    add_reason("Shared configuration", f"Keys {list(shared_config)}")

            # Heuristic 3: Shared primary entities (e.g. classes, models)
            shared_entities = set(changed_meta.primary_entities).intersection(meta.primary_entities)
            if shared_entities:
                score = max(score, 0.80)  # HIGH: Code entities mismatch risk
                add_reason("Shared entities", f"Classes/structures {list(shared_entities)}")

            # Heuristic 4: Shared external interfaces (e.g. ports, routing endpoints)
            shared_interfaces = set(changed_meta.external_interfaces).intersection(meta.external_interfaces)
            if shared_interfaces:
                score = max(score, 0.85)  # HIGH: API contract mismatch risk
                add_reason("Shared external interfaces", f"Routes/ports {list(shared_interfaces)}")

            # Heuristic 5: Shared directory proximity (excluding root directory)
            path_dir = os.path.dirname(path)
            if changed_dir and path_dir == changed_dir:
                score = max(score, 0.40)  # LOW: Proximity is weak semantic evidence
                add_reason("Same directory", f"Located in '{changed_dir}'")

            # Heuristic 6: Concept overlap
            shared_concepts = set(changed_meta.concepts).intersection(meta.concepts)
            if shared_concepts:
                # Cap documentation-only concept matches to LOW
                if meta.role == "Documentation":
                    score = max(score, 0.35)  # LOW
                    add_reason("Shared documentation concepts", f"Matched {list(shared_concepts)}")
                else:
                    score = max(score, 0.50)  # MEDIUM
                    add_reason("Shared concepts", f"Matched {list(shared_concepts)}")

            # Heuristic 7: Tech overlap (only if no higher connection is found)
            shared_techs = set(changed_meta.technologies).intersection(meta.technologies)
            if shared_techs and meta.role != "Documentation" and score < 0.30:
                score = max(score, 0.20)  # LOW
                add_reason("Same technology stack", f"Uses {list(shared_techs)}")

            if score > 0.0:
                if path in candidates:
                    existing = candidates[path]
                    new_score = max(existing.score, score)
                    
                    # Merge structured reasons
                    merged_reasons = dict(existing.reasons)
                    for cat, details in reasons.items():
                        if cat in merged_reasons:
                            merged_reasons[cat] = sorted(list(set(merged_reasons[cat] + details)))
                        else:
                            merged_reasons[cat] = details
                            
                    candidates[path] = Candidate(path=path, score=new_score, reasons=merged_reasons)
                else:
                    candidates[path] = Candidate(path=path, score=score, reasons=reasons)

    # Sort candidates by score descending, then alphabetically by path for determinism
    sorted_candidates = sorted(candidates.values(), key=lambda c: (-c.score, c.path))
    return sorted_candidates
