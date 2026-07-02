import os
import json
from .models import ReviewContext, ReviewResponseSchema
from .workspace import get_git_changes, create_workspace_snapshot
from .candidate_finder import find_candidates
from .llm_provider import GeminiProvider
from .validator import validate_obligations

def run_review_pipeline() -> ReviewContext:
    """Executes the complete ProjectMind review pipeline, including deterministic mapping and AI obligations generation."""
    # 1. Fetch Git changes
    diff_content, changed_files = get_git_changes()
    
    # 2. Build the workspace snapshot
    snapshot = create_workspace_snapshot()
    
    # 3. Find candidates
    candidates = find_candidates(changed_files, snapshot)
    
    # 4. Construct the context object
    context = ReviewContext(
        git_diff=diff_content,
        changed_files=changed_files,
        workspace_snapshot=snapshot,
        candidate_files=candidates
    )
    
    # 5. Build prompt
    prompt = build_prompt(context)
    context.prompt = prompt
    
    # 6. Call LLM Provider if API key is configured
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and diff_content.strip() and candidates:
        try:
            provider = GeminiProvider(api_key)
            response_text = provider.generate(prompt, schema=ReviewResponseSchema)
            context.llm_response = response_text
            
            # Parse structured JSON response
            raw_data = json.loads(response_text)
            raw_obligations = raw_data.get("obligations", [])
            
            # 7. Validate and sanitize obligations against workspace files
            workspace_files = list(snapshot.keys())
            validated = validate_obligations(raw_obligations, workspace_files)
            context.obligations = validated
        except Exception as e:
            # Fallback instead of crash on network or parsing failure
            context.llm_response = f"Error during AI reasoning: {e}"
            context.obligations = []
    
    # 8. Write explainability report
    write_explainability_report(context)
    
    return context

def build_prompt(context: ReviewContext) -> str:
    """Assembles the prompt string according to the strict Prompt Contract API."""
    prompt_lines = [
        "# Prompt Contract: ProjectMind Review Obligation Engine",
        "",
        "## Goal & Review Philosophy",
        "- **Goal**: Identify review obligations that a developer is likely to overlook after making the supplied code changes. The objective is not to summarize the diff or explain the code, but to predict which additional project artifacts deserve human review because they may now contain inconsistent assumptions.",
        "- **Philosophy**: ProjectMind does not attempt to determine whether code is correct. ProjectMind attempts to determine whether a human should review something before assuming the project remains coherent. The output must encourage thoughtful review, not automated trust.",
        "- **Core Principle**: **Review obligations are hypotheses for human verification, not assertions of fact.**",
        "",
        "## Required Inputs",
        "",
        "### 1. Git Diff",
        "```diff",
        context.git_diff if context.git_diff.strip() else "*No changes detected*",
        "```",
        "",
        "### 2. Changed Files Snapshot",
    ]
    
    if context.changed_files:
        for f in context.changed_files:
            meta = context.workspace_snapshot.get(f)
            if meta:
                prompt_lines.append(f"- **Path**: `{f}`")
                prompt_lines.append(f"  - **Role**: {meta.role}")
                prompt_lines.append(f"  - **Responsibility**: {meta.responsibility}")
                prompt_lines.append(f"  - **Config Keys**: {meta.configuration_keys}")
                prompt_lines.append(f"  - **Interfaces**: {meta.external_interfaces}")
    else:
         prompt_lines.append("*No files changed*")
            
    prompt_lines.append("")
    prompt_lines.append("### 3. Candidates Snapshot")
    if context.candidate_files:
        for c in context.candidate_files:
            meta = context.workspace_snapshot.get(c.path)
            if meta:
                prompt_lines.append(f"- **Path**: `{c.path}`")
                prompt_lines.append(f"  - **Role**: {meta.role}")
                prompt_lines.append(f"  - **Responsibility**: {meta.responsibility}")
                prompt_lines.append(f"  - **Config Keys**: {meta.configuration_keys}")
                prompt_lines.append(f"  - **Interfaces**: {meta.external_interfaces}")
                # Convert Dict[str, List[str]] reasons to readable string
                reasons_str = "; ".join(f"{cat}: {details}" for cat, details in c.reasons.items())
                prompt_lines.append(f"  - **Deterministic Reasons Mapped**: {reasons_str}")
    else:
         prompt_lines.append("*No candidate files identified*")
            
    prompt_lines.extend([
        "",
        "## Forbidden Behaviors",
        "DO NOT:",
        "- Generate code or rewrite files.",
        "- Invent project structure or hallucinate files outside the candidates list.",
        "- Speculate without evidence or recommend structural/architectural redesigns.",
        "- Produce duplicate obligations.",
        "- Restate deterministic reasons already provided (e.g. do not just output 'Shares PORT').",
        "- Output free-text explanations outside the required JSON structure.",
        "",
        "## Required Evaluation Steps",
        "- **Step 1 (Understand the change)**: Identify what underlying assumptions, configuration rules, or API contracts have changed in the diff.",
        "- **Step 2 (Trace system dependencies)**: Determine which project assumptions or interfaces could now be invalid or out of sync.",
        "- **Step 3 (Evaluate candidates independently)**: Analyze each candidate file's role, responsibility, configuration keys, and external interfaces against the diff to find conflicts.",
        "- **Step 4 (Validate evidence)**: Only produce an obligation if there is credible evidence (must cite at least one candidate file in `evidence_files`).",
        "- **Step 5 (Prioritize and Rank)**: Rank obligations by review urgency.",
    ])
    
    return "\n".join(prompt_lines)

def write_explainability_report(context: ReviewContext, filename: str = ".projectmind-report.md") -> None:
    """Generates an explainability log of the execution in Markdown format."""
    lines = []
    lines.append("# ProjectMind Execution & Explainability Report")
    lines.append("")
    
    # Git Diff
    lines.append("## 1. Git Diff")
    lines.append(f"**Changed Files Count:** {len(context.changed_files)}")
    lines.append(f"**Files list:** {', '.join(context.changed_files) if context.changed_files else 'None'}")
    lines.append("")
    if context.git_diff.strip():
        lines.append("```diff")
        lines.append(context.git_diff)
        lines.append("```")
    else:
        lines.append("*No active Git diff detected.*")
    lines.append("")
    
    # Workspace Snapshot
    lines.append("## 2. Workspace Snapshot")
    lines.append(f"**Total files analyzed:** {len(context.workspace_snapshot)}")
    lines.append("")
    lines.append("| File Path | Role | Responsibility | Techs | Concepts | Config Keys | Interfaces |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for path, meta in context.workspace_snapshot.items():
        techs = ", ".join(meta.technologies) if meta.technologies else "-"
        concepts = ", ".join(meta.concepts) if meta.concepts else "-"
        configs = ", ".join(meta.configuration_keys) if meta.configuration_keys else "-"
        interfaces = ", ".join(meta.external_interfaces) if meta.external_interfaces else "-"
        lines.append(f"| `{path}` | {meta.role} | {meta.responsibility} | {techs} | {concepts} | {configs} | {interfaces} |")
    lines.append("")
    
    # Candidate Selection
    lines.append("## 3. Candidate Selection")
    lines.append(f"**Selected Candidates Count:** {len(context.candidate_files)}")
    lines.append("")
    if context.candidate_files:
        lines.append("| Path | Score | Confidence | Inclusion Reasons |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for c in context.candidate_files:
            if c.score >= 0.8:
                conf = "HIGH"
            elif c.score >= 0.5:
                conf = "MEDIUM"
            else:
                conf = "LOW"
                
            reasons_parts = []
            for category, details in c.reasons.items():
                reasons_parts.append(f"**{category}**")
                for d in details:
                    reasons_parts.append(f"&nbsp;-&nbsp;{d}")
            reasons_html = "<br>".join(reasons_parts)
            
            lines.append(f"| `{c.path}` | {c.score:.2f} | **{conf}** | {reasons_html} |")
    else:
        lines.append("*No review candidates selected.*")
    lines.append("")
    
    # Prompt Construction
    lines.append("## 4. Prompt Construction")
    if context.prompt:
        lines.append("```markdown")
        lines.append(context.prompt)
        lines.append("```")
    else:
        lines.append("*Not executed.*")
    lines.append("")
    
    # LLM Response
    lines.append("## 5. LLM Response")
    if context.llm_response:
        lines.append("```json")
        lines.append(context.llm_response)
        lines.append("```")
    else:
        lines.append("*Not executed (requires GEMINI_API_KEY).*")
    lines.append("")
    
    # Final Review Obligations
    lines.append("## 6. Final Review Obligations")
    if context.obligations:
        lines.append("| Priority | Confidence | Title | Area | Reason | Evidence Files |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for o in context.obligations:
            ev_files = ", ".join(f"`{f}`" for f in o.evidence_files)
            lines.append(f"| **{o.priority}** | **{o.confidence}** | {o.title} | {o.area} | {o.reason} | {ev_files} |")
    else:
        lines.append("*No review obligations generated.*")
    lines.append("")
    
    # Write to file
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as e:
        print(f"Warning: Failed to write explainability report: {e}")
