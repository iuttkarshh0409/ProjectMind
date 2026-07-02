from projectmind.models import FileMetadata
from projectmind.candidate_finder import find_candidates

def test_find_candidates_direct_test():
    # Setup test file metadata
    snapshot = {
        "src/auth.ts": FileMetadata(
            path="src/auth.ts",
            role="Code Module",
            responsibility="Authentication logic",
            primary_entities=["AuthManager"],
            configuration_keys=["JWT_SECRET"],
            external_interfaces=[],
            technologies=["TypeScript"],
            concepts=["Authentication"],
            confidence=1.0
        ),
        "tests/auth.test.ts": FileMetadata(
            path="tests/auth.test.ts",
            role="Test Suite",
            responsibility="Validates auth logic",
            primary_entities=[],
            configuration_keys=[],
            external_interfaces=[],
            technologies=["TypeScript"],
            concepts=["Testing"],
            confidence=1.0
        ),
        "src/db.ts": FileMetadata(
            path="src/db.ts",
            role="Data Model / Database Handler",
            responsibility="Handles DB connection",
            primary_entities=["Database"],
            configuration_keys=["DATABASE_URL"],
            external_interfaces=[],
            technologies=["TypeScript"],
            concepts=["Database"],
            confidence=1.0
        ),
    }
    
    # Change src/auth.ts
    changed = ["src/auth.ts"]
    candidates = find_candidates(changed, snapshot)
    
    # Assert that tests/auth.test.ts is identified as a candidate with a score of 0.70 (calibrated)
    assert len(candidates) > 0
    test_candidate = next((c for c in candidates if c.path == "tests/auth.test.ts"), None)
    assert test_candidate is not None
    assert test_candidate.score == 0.70
    assert "Direct test suite" in test_candidate.reasons
    assert len(test_candidate.reasons["Direct test suite"]) > 0

def test_find_candidates_same_directory():
    snapshot = {
        "src/controllers/auth.ts": FileMetadata(
            path="src/controllers/auth.ts",
            role="API Entrypoint / Controller",
            responsibility="Auth handler",
            primary_entities=[],
            configuration_keys=[],
            external_interfaces=[],
            technologies=["TypeScript"],
            concepts=["Authentication"],
            confidence=1.0
        ),
        "src/controllers/users.ts": FileMetadata(
            path="src/controllers/users.ts",
            role="API Entrypoint / Controller",
            responsibility="User handler",
            primary_entities=[],
            configuration_keys=[],
            external_interfaces=[],
            technologies=["TypeScript"],
            concepts=["User Management"],
            confidence=1.0
        ),
        "src/db/connection.ts": FileMetadata(
            path="src/db/connection.ts",
            role="Data Model / Database Handler",
            responsibility="DB pool connection",
            primary_entities=[],
            configuration_keys=[],
            external_interfaces=[],
            technologies=["SQL"],
            concepts=["Database"],
            confidence=1.0
        ),
    }
    
    changed = ["src/controllers/auth.ts"]
    candidates = find_candidates(changed, snapshot)
    
    # src/controllers/users.ts should be matched because of proximity, src/db/connection.ts shouldn't
    user_candidate = next((c for c in candidates if c.path == "src/controllers/users.ts"), None)
    db_candidate = next((c for c in candidates if c.path == "src/db/connection.ts"), None)
    
    assert user_candidate is not None
    assert user_candidate.score == 0.40  # Proximity score calibrated to 0.40
    assert "Same directory" in user_candidate.reasons
    assert db_candidate is None
