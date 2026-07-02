from projectmind.models import ReviewObligation
from projectmind.validator import validate_obligations

def test_validate_obligations_filtering():
    raw_obligations = [
        {
            "priority": "HIGH",
            "confidence": "HIGH",
            "title": "Update Client OAuth Handling",
            "area": "Security",
            "reason": "OAuth endpoint modified",
            "evidence_files": ["src/auth.ts", "missing.ts"]
        },
        {
            "priority": "INVALID",
            "confidence": "INVALID",
            "title": "Update Documentation Layout",
            "area": "Docs",
            "reason": "Readme changes",
            "evidence_files": ["README.md"]
        },
        {
            "priority": "MEDIUM",
            "confidence": "MEDIUM",
            "title": "Fix Auth Test Suite",
            "area": "Tests",
            "reason": "",  # Empty reason should get filtered out
            "evidence_files": ["tests/auth.test.ts"]
        },
        {
            "priority": "HIGH",
            "confidence": "HIGH",
            "title": "No Evidence Obligation",
            "area": "System",
            "reason": "No evidence file matching",
            "evidence_files": []  # Empty evidence should get filtered out (No Evidence Rule)
        }
    ]
    
    workspace_files = ["src/auth.ts", "README.md"]
    valid = validate_obligations(raw_obligations, workspace_files)
    
    # Only the first two obligations should pass (first has valid evidence, second has README, third has empty reason, fourth has no evidence)
    assert len(valid) == 2
    
    # Check first obligation attributes
    assert valid[0].priority == "HIGH"
    assert valid[0].confidence == "HIGH"
    assert valid[0].title == "Update Client OAuth Handling"
    assert valid[0].evidence_files == ["src/auth.ts"]  # missing.ts is dropped
    
    # Check second obligation attributes fallbacks
    assert valid[1].priority == "LOW"  # INVALID falls back to LOW
    assert valid[1].confidence == "LOW"  # INVALID falls back to LOW
    assert valid[1].evidence_files == ["README.md"]
