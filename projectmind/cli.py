import click
from .review_engine import run_review_pipeline
from .reporter import build_report, render_terminal

@click.group()
def cli():
    """ProjectMind - Change Impact & Review Obligation Engine"""
    pass

@cli.command()
def review():
    """Analyzes the current changes and identifies project review obligations."""
    context = run_review_pipeline()
    report = build_report(context)
    render_terminal(report)

def main():
    cli()

if __name__ == "__main__":
    main()
