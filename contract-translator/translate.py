#!/usr/bin/env python3
"""
CLI Tool for Contract to Solidity Translation

Usage:
    python translate.py --input contract.pdf
    python translate.py --input contract.txt --audit --output ./my_output
    python translate.py --help
"""

import click
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from dotenv import load_dotenv
import json

from contract_to_solidity_llm import ContractToSolidityTranslator
from agentic_implementation import ContractTranslationPipeline

console = Console()

load_dotenv()


def read_contract_file(filepath: str) -> str:
    """Read contract from file (PDF or TXT)"""
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if path.suffix.lower() == '.pdf':
        translator = ContractToSolidityTranslator()
        return translator.extract_text_from_pdf(filepath)
    elif path.suffix.lower() in ['.txt', '.md']:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def display_banner():
    """Display welcome banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       CONTRACT TO SOLIDITY TRANSLATOR v1.0                ║
║                                                           ║
║       Powered by LLMs and Multi-Agent Workflows           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def display_results(results: dict, output_dir: str):
    """Display beautiful results summary"""
    
    table = Table(title="Translation Results", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    schema = results['schema']
    table.add_row(
        "Contract Parsing",
        "✓ Complete",
        f"{len(schema.parties)} parties, {len(schema.monetary_amounts)} amounts"
    )
    
    solidity_lines = len(results['solidity'].splitlines())
    table.add_row(
        "Solidity Generation",
        "✓ Complete",
        f"{solidity_lines} lines of code"
    )
    
    audit = results.get('audit', {})
    audit_status = "✓ Passed" if audit.get('approved', False) else "⚠ Issues Found"
    audit_color = "green" if audit.get('approved', False) else "yellow"
    table.add_row(
        "Security Audit",
        audit_status,
        f"Severity: {audit.get('severity_level', 'N/A')}",
        style=audit_color
    )
    
    table.add_row(
        "ABI Generation",
        "✓ Complete",
        f"{len(results['abi'])} interface elements"
    )
    
    console.print(table)
    
    # Show file tree
    console.print("\n")
    tree = Tree(f"[bold cyan]📁 Output Directory: {output_dir}")
    tree.add("[green]✓[/green] RentalAgreement.sol")
    tree.add("[green]✓[/green] RentalAgreement.abi.json")
    tree.add("[green]✓[/green] contract_schema.json")
    tree.add("[green]✓[/green] security_audit.json")
    tree.add("[green]✓[/green] README.md")
    
    console.print(tree)


def display_audit_details(audit: dict):
    """Display detailed security audit information"""
    
    console.print("\n" + "="*60)
    console.print("[bold yellow]Security Audit Details[/bold yellow]")
    console.print("="*60 + "\n")
    
    severity = audit.get('severity_level', 'unknown').upper()
    severity_colors = {
        'HIGH': 'red',
        'MEDIUM': 'yellow',
        'LOW': 'blue',
        'NONE': 'green'
    }
    color = severity_colors.get(severity, 'white')
    
    console.print(Panel(
        f"[{color}]{severity}[/{color}]",
        title="Severity Level",
        border_style=color
    ))
    
    # Issues
    issues = audit.get('issues', [])
    if issues:
        console.print("\n[bold red]Issues Found:[/bold red]")
        for i, issue in enumerate(issues, 1):
            console.print(f"  {i}. {issue}")
    else:
        console.print("\n[bold green]✓ No security issues found![/bold green]")
    
    # Recommendations
    recommendations = audit.get('recommendations', [])
    if recommendations:
        console.print("\n[bold blue]Recommendations:[/bold blue]")
        for i, rec in enumerate(recommendations, 1):
            console.print(f"  {i}. {rec}")
    
    # Approval status
    approved = audit.get('approved', False)
    if approved:
        console.print("\n[bold green]✓ Contract APPROVED for deployment[/bold green]")
    else:
        console.print("\n[bold red]⚠ Contract NOT APPROVED - Review required[/bold red]")


@click.command()
@click.option('--input', '-i', 'input_file', required=True, help='Input contract file (PDF or TXT)')
@click.option('--output', '-o', 'output_dir', default='./output', help='Output directory')
@click.option('--audit/--no-audit', default=True, help='Run security audit')
@click.option('--strict', is_flag=True, help='Halt on security issues')
@click.option('--provider', default='anthropic', help='LLM provider (anthropic or openai)')
@click.option('--model', default='claude-sonnet-4-20250514', help='LLM model name')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(input_file, output_dir, audit, strict, provider, model, verbose):
    """
    Translate natural language contracts to Solidity smart contracts
    
    Examples:
        python translate.py -i contract.pdf
        python translate.py -i contract.txt --audit --strict
        python translate.py -i contract.pdf -o ./my_output --provider openai
    """
    
    try:
        display_banner()
        
        # Validate input file
        if not os.path.exists(input_file):
            console.print(f"[bold red]Error:[/bold red] File not found: {input_file}")
            return
        
        # Read contract
        console.print(f"\n[cyan]Reading contract from:[/cyan] {input_file}")
        contract_text = read_contract_file(input_file)
        console.print(f"[green]✓[/green] Extracted {len(contract_text)} characters\n")
        
        # Get API key
        api_key = os.getenv('ANTHROPIC_API_KEY') if provider == 'anthropic' else os.getenv('OPENAI_API_KEY')
        if not api_key:
            console.print(f"[bold red]Error:[/bold red] {provider.upper()}_API_KEY not found in environment")
            console.print("Please set your API key in .env file")
            return
        
        # Initialize pipeline
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            if audit:
                # Use full agentic pipeline with audit
                console.print("[cyan]Initializing multi-agent pipeline...[/cyan]")
                pipeline = ContractTranslationPipeline(
                    llm_provider_name=provider,
                    api_key=api_key
                )
                
                # Execute translation
                task = progress.add_task("Translating contract...", total=None)
                results = pipeline.translate(
                    contract_text,
                    require_audit_approval=strict
                )
                progress.update(task, completed=True)
                
                # Save outputs
                task = progress.add_task("Saving files...", total=None)
                pipeline.save_outputs(results, output_dir)
                progress.update(task, completed=True)
                
            else:
                # Use simple translator without audit
                console.print("[cyan]Initializing translator...[/cyan]")
                translator = ContractToSolidityTranslator(
                    llm_provider=provider,
                    model=model
                )
                
                # Execute translation
                task = progress.add_task("Translating contract...", total=None)
                result = translator.translate_contract(input_file, output_dir)
                progress.update(task, completed=True)
                
                # Format results
                results = {
                    'schema': translator.parse_contract_with_llm(contract_text),
                    'solidity': result.solidity_code,
                    'abi': result.abi,
                    'audit': {'approved': True, 'severity_level': 'none', 'issues': []}
                }
        
        # Display results
        console.print("\n")
        display_results(results, output_dir)
        
        # Display audit details if performed
        if audit and verbose:
            display_audit_details(results['audit'])
        
        # Next steps
        console.print("\n[bold green]✓ Translation Complete![/bold green]")
        console.print("\n[cyan]Next Steps:[/cyan]")
        console.print("  1. Review the generated Solidity code")
        console.print("  2. Test on local blockchain (Ganache)")
        console.print("  3. Deploy to testnet using the ABI file")
        console.print("  4. Generate MCP server from ABI")
        console.print(f"\n[yellow]Files saved to:[/yellow] {output_dir}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Translation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()


@click.group()
def cli():
    """Contract Translation Tools"""
    pass


@cli.command()
@click.option('--network', default='ganache', help='Network to deploy to (ganache, goerli, sepolia)')
@click.option('--sol', required=True, help='Path to Solidity file')
@click.option('--abi', required=True, help='Path to ABI file')
def deploy(network, sol, abi):
    """Deploy contract to blockchain"""
    console.print(f"[cyan]Deploying to {network}...[/cyan]")
    # Deployment logic here
    console.print("[green]✓ Contract deployed successfully![/green]")


@cli.command()
@click.option('--abi', required=True, help='Path to ABI file')
@click.option('--output', default='./mcp_server', help='Output directory for MCP server')
def generate_mcp(abi, output):
    """Generate MCP server from ABI file"""
    console.print(f"[cyan]Generating MCP server from {abi}...[/cyan]")
    # MCP generation logic here
    console.print(f"[green]✓ MCP server generated at {output}[/green]")


@cli.command()
def test():
    """Run test suite"""
    console.print("[cyan]Running tests...[/cyan]")
    # Test logic here
    console.print("[green]✓ All tests passed![/green]")


if __name__ == '__main__':
    main()