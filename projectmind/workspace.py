import os
import subprocess
from typing import List, Tuple, Dict
from .models import FileMetadata

def get_git_changes() -> Tuple[str, List[str]]:
    """Runs git commands to fetch the current diff and changed files, normalized to current directory."""
    try:
        # Check if we are in a git repository
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repo or git is not installed
        return "", []

    # Get git toplevel directory
    toplevel_proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    git_root = toplevel_proc.stdout.strip()
    cwd = os.getcwd()

    ignored_patterns = {".projectmind-report.md", ".projectmind", ".pytest_cache", "coverage", "__pycache__", "dist", "build"}

    # Get changed files (staged and unstaged)
    status_proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    changed_files = []
    if status_proc.returncode == 0:
        for line in status_proc.stdout.splitlines():
            if len(line) > 3:
                # Format: XY file_path -> take file_path
                file_path = line[3:].strip()
                # Handle renamed files (e.g., "R  old -> new")
                if " -> " in file_path:
                    file_path = file_path.split(" -> ")[1].strip()
                
                # Make path relative to CWD
                abs_path = os.path.join(git_root, file_path)
                rel_path = os.path.relpath(abs_path, cwd).replace(os.sep, "/")
                
                # Skip ProjectMind generated artifacts and caches
                if any(pat in rel_path for pat in ignored_patterns):
                    continue

                # Only include files inside the current working directory
                if not rel_path.startswith(".."):
                    changed_files.append(rel_path)

    # Get diff (staged and unstaged changes against HEAD) relative to CWD
    diff_proc = subprocess.run(["git", "diff", "HEAD", "--", "."], capture_output=True, text=True)
    diff_content = diff_proc.stdout

    # Fallback to plain diff if HEAD doesn't exist yet (e.g., initial empty commit)
    if diff_proc.returncode != 0:
        fallback_proc = subprocess.run(["git", "diff", "--", "."], capture_output=True, text=True)
        diff_content = fallback_proc.stdout

    return diff_content, changed_files

def create_workspace_snapshot(root_dir: str = ".") -> Dict[str, FileMetadata]:
    """Scans the directory deterministically to construct a lightweight workspace snapshot."""
    snapshot = {}
    ignored_dirs = {".git", "node_modules", ".venv", "__pycache__", ".projectmind", "dist", "build", ".pytest_cache", "coverage"}

    for root, dirs, files in os.walk(root_dir):
        # Exclude ignored directories in-place to prevent os.walk from scanning them
        dirs[:] = [d for d in dirs if d not in ignored_dirs]

        for file in files:
            # Skip ProjectMind generated reports
            if file == ".projectmind-report.md":
                continue
            file_path = os.path.relpath(os.path.join(root, file), root_dir)
            file_path = file_path.replace(os.sep, "/") # Normalize paths for cross-platform matching
            
            # Skip binary and lock files to keep metadata scanner fast
            if file.endswith((".png", ".jpg", ".ico", ".pdf", ".zip", "-lock.json", ".lock")):
                continue

            snapshot[file_path] = _parse_file_metadata(file_path)

    return snapshot

def _parse_file_metadata(file_path: str) -> FileMetadata:
    """Helper to deterministically infer file metadata from structure, extensions, and content regex."""
    import re
    filename = os.path.basename(file_path).lower()
    
    # Defaults
    role = "Code Module"
    responsibility = "General implementation module"
    primary_entities = []
    configuration_keys = []
    external_interfaces = []
    techs = []
    concepts = []
    
    # Match by extension
    if filename.endswith(".py"):
        techs.append("Python")
    elif filename.endswith((".js", ".jsx")):
        techs.append("JavaScript")
    elif filename.endswith((".ts", ".tsx")):
        techs.append("TypeScript")
    elif filename == "docker-compose.yml":
        role = "Infrastructure Config"
        responsibility = "Orchestrates containerized services and dependencies"
        techs.append("Docker")
        concepts.append("Orchestration")
    elif filename == "package.json":
        role = "Dependency Manifest"
        responsibility = "Declares Node.js dependencies and project scripts"
        techs.append("Node.js")
        concepts.append("Dependencies")
    elif filename == "pyproject.toml":
        role = "Project Configuration"
        responsibility = "Declares Python dependencies and project build settings"
        techs.append("Python")
        concepts.append("Dependencies")
    elif filename.endswith(".md"):
        role = "Documentation"
        responsibility = "Provides overview, setup instructions, or specifications"
        concepts.append("Documentation")
    elif filename.startswith(".env"):
        role = "Environment Template"
        responsibility = "Defines local/production environment variable structures"
        concepts.append("Configuration")

    # Match by folder/path semantics
    parts = file_path.split("/")
    if "tests" in parts or "test" in parts or filename.startswith("test_") or filename.endswith((".test.ts", ".test.js")):
        role = "Test Suite"
        responsibility = "Validates the correctness of target modules"
        concepts.append("Testing")
    elif "routes" in parts or "controllers" in parts or "api" in parts:
        role = "API Entrypoint / Controller"
        responsibility = "Exposes HTTP routes and coordinates incoming requests"
        concepts.append("Routing")
    elif "models" in parts or "db" in parts or "schemas" in parts:
        role = "Data Model / Database Handler"
        responsibility = "Defines schema structures and interfaces with the database"
        concepts.append("Database")
    elif "auth" in parts or "security" in parts:
        role = "Security / Authentication Manager"
        responsibility = "Handles user credentials, tokens, and session rules"
        concepts.append("Authentication")

    # Read the file content to extract custom fields and regex patterns
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
            # Split into lines for head parsing
            lines = content.splitlines()
            head = lines[:15]
            for line in head:
                if "role:" in line.lower():
                    role = line.split(":", 1)[1].strip().strip("#* ")
                if "responsibility:" in line.lower():
                    responsibility = line.split(":", 1)[1].strip().strip("#* ")
                if "techs:" in line.lower() or "technologies:" in line.lower():
                    extracted_techs = line.split(":", 1)[1].strip().strip("#* ")
                    techs.extend([t.strip() for t in extracted_techs.split(",")])
                if "concepts:" in line.lower():
                    extracted_concepts = line.split(":", 1)[1].strip().strip("#* ")
                    concepts.extend([c.strip() for c in extracted_concepts.split(",")])

            # Class/Entity Extraction: `class User` or `interface DbConfig`
            entities = re.findall(r"(?:class|interface|type)\s+([A-Za-z0-9_]+)", content)
            primary_entities.extend(entities)

            # Env/Config Keys Extraction: process.env.JWT_SECRET or os.getenv("PORT") or PORT=3000
            env_keys = re.findall(r"process\.env\.([A-Za-z0-9_]+)", content)
            env_keys_py = re.findall(r"os\.(?:getenv|environ\.get)\s*\(\s*['\"]([A-Za-z0-9_]+)['\"]", content)
            env_keys_py_bracket = re.findall(r"os\.environ\s*\[\s*['\"]([A-Za-z0-9_]+)['\"]", content)
            raw_env_keys = re.findall(r"^([A-Za-z0-9_]+)\s*=", content, re.MULTILINE) if filename.startswith(".env") else []
            
            # Docker Compose env vars e.g. - DATABASE_URL=xxx
            docker_env_keys = re.findall(r"-\s*([A-Za-z0-9_]+)\s*=", content) if filename == "docker-compose.yml" else []
            
            # Uppercase variables references (e.g. PORT)
            uppercase_vars = re.findall(r"\b([A-Z_][A-Z0-9_]{2,})\b", content)

            configuration_keys.extend(env_keys + env_keys_py + env_keys_py_bracket + raw_env_keys + docker_env_keys + uppercase_vars)

            # Route/Interface Extraction: app.post('/chat', ...) or router.get('/users', ...) or ports mappings
            routes = re.findall(r"(?:app|router)\.(?:get|post|put|delete)\(['\"]([^'\"\s]+)['\"]", content)
            external_interfaces.extend(routes)
            
            if filename == "docker-compose.yml":
                ports = re.findall(r"ports:\s*\n?\s*-\s*['\"]?(\d+:\d+)['\"]?", content)
                external_interfaces.extend([f"port:{p}" for p in ports])
    except Exception:
        pass

    # Deduplicate and sort all lists
    techs = sorted(list(set(t for t in techs if t)))
    concepts = sorted(list(set(c for c in concepts if c)))
    primary_entities = sorted(list(set(e for e in primary_entities if e)))
    configuration_keys = sorted(list(set(k for k in configuration_keys if k)))
    external_interfaces = sorted(list(set(i for i in external_interfaces if i)))

    return FileMetadata(
        path=file_path,
        role=role,
        responsibility=responsibility,
        primary_entities=primary_entities,
        configuration_keys=configuration_keys,
        external_interfaces=external_interfaces,
        technologies=techs,
        concepts=concepts,
        confidence=1.0
    )
