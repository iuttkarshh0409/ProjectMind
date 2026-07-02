from typing import List, Dict, Any
from .models import ReviewObligation

def validate_obligations(raw_obligations: List[Dict[str, Any]], workspace_files: List[str]) -> List[ReviewObligation]:
    """Validates the raw LLM output against the system schema and file boundaries."""
    valid_obligations = []
    workspace_set = set(workspace_files)

    for item in raw_obligations:
        priority = str(item.get("priority", "LOW")).upper()
        if priority not in ("HIGH", "MEDIUM", "LOW"):
            priority = "LOW"

        area = str(item.get("area", "General"))
        title = str(item.get("title", "Review Obligation"))
        reason = str(item.get("reason", ""))
        
        confidence = str(item.get("confidence", "LOW")).upper()
        if confidence not in ("HIGH", "MEDIUM", "LOW"):
            confidence = "LOW"
        
        # Don't add empty reasons
        if not reason.strip():
            continue

        raw_evidence = item.get("evidence_files", [])
        if not isinstance(raw_evidence, list):
            raw_evidence = []
            
        # Filter evidence to make sure the files actually exist in the workspace snapshot
        valid_evidence = [path for path in raw_evidence if path in workspace_set]

        # No Evidence Rule: Must cite at least one valid candidate file
        if not valid_evidence:
            continue

        valid_obligations.append(ReviewObligation(
            priority=priority,
            confidence=confidence,
            title=title,
            area=area,
            reason=reason,
            evidence_files=valid_evidence
        ))

    return valid_obligations
