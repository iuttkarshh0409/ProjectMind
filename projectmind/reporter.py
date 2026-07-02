from .models import ReviewContext, ReviewReport

def build_report(context: ReviewContext) -> ReviewReport:
    """Converts a ReviewContext into a presentation-ready ReviewReport."""
    return ReviewReport(
        changed_files_count=len(context.changed_files),
        total_files_analyzed=len(context.workspace_snapshot),
        candidates=context.candidate_files,
        obligations=context.obligations
    )

def render_terminal(report: ReviewReport) -> None:
    """Renders the ReviewReport to the terminal console with clean text layouts."""
    # Terminal formatting colors using ANSI escapes
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print(f"{BOLD}projectmind review{RESET}")
    print("Detected:")
    print(f"{CYAN}{report.changed_files_count} changed files{RESET}")
    print()
    print("Workspace analyzed.")
    print()
    print("Potential review candidates:")
    print(f"{YELLOW}{len(report.candidates)} files{RESET}")
    
    # Render Deterministic Candidates if no obligations are generated yet (e.g. Milestone 1.5 or LLM disabled)
    if report.candidates and not report.obligations:
        print()
        print(f"{BOLD}Candidates List:{RESET}")
        for c in report.candidates:
            if c.score >= 0.8:
                conf = "HIGH"
                color = RED
            elif c.score >= 0.5:
                conf = "MEDIUM"
                color = YELLOW
            else:
                conf = "LOW"
                color = CYAN
                
            print(f"\n{BOLD}{c.path}{RESET}")
            print(f"Confidence: {color}{BOLD}{conf}{RESET}")
            print("Reason:")
            for category, details in c.reasons.items():
                print(f"  - {category}")
                for d in details:
                    print(f"      {d}")

    # Render AI Obligations if present
    if report.obligations:
        print()
        print("=" * 50)
        print(f"{BOLD}REVIEW OBLIGATIONS{RESET}")
        print("=" * 50)
        
        # Sort obligations: HIGH first, then MEDIUM, then LOW
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_obligations = sorted(report.obligations, key=lambda o: priority_order.get(o.priority, 3))
        
        for o in sorted_obligations:
            # Color coding
            if o.priority == "HIGH":
                p_color = RED
            elif o.priority == "MEDIUM":
                p_color = YELLOW
            else:
                p_color = CYAN
                
            if o.confidence == "HIGH":
                c_color = RED
            elif o.confidence == "MEDIUM":
                c_color = YELLOW
            else:
                c_color = CYAN
                
            print(f"\n{p_color}{BOLD}[{o.priority}]{RESET} {BOLD}{o.title}{RESET}")
            print(f"Confidence: {c_color}{BOLD}{o.confidence}{RESET}")
            print(f"Area: {o.area}")
            print(f"Reason:\n  {o.reason}")
            print("Evidence:")
            for f in o.evidence_files:
                print(f"  - {f}")
            
    print()
    print(f"{GREEN}Ready for AI reasoning.{RESET}" if not report.obligations else f"{GREEN}Review complete.{RESET}")
