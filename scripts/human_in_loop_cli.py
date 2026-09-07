import os
import sys
import django
import requests
import json
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Setup Django environment so we can query the DB directly to find the queue
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from document_metadata.models.document_metadata import DocumentMetadata

console = Console()
BASE_URL = "http://127.0.0.1:8000/api/metadata"

def get_review_queue():
    """Finds documents that have low confidence (<= 0.3) and are not verified"""
    return DocumentMetadata.objects.filter(
        metadata_confidence__lte=0.3,
        manually_verified=False
    ).order_by('created_at')

def display_metadata(doc_id: str, data: dict):
    console.print(f"\n[bold blue]Document ID:[/bold blue] {doc_id}")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field")
    table.add_column("Current Value")
    
    for k, v in data.items():
        if k not in ['id', 'document_id', 'created_at', 'updated_at'] and v is not None and v != "":
            table.add_row(k, str(v))
            
    console.print(table)

def run_cli():
    console.print("\n[bold green]=== Human-in-the-Loop Terminal Review Queue ===[/bold green]")
    
    queue = get_review_queue()
    count = queue.count()
    
    if count == 0:
        console.print("[bold yellow]Queue is empty! All documents are confident or verified.[/bold yellow]")
        return
        
    console.print(f"Documents pending review: [bold red]{count}[/bold red]\n")
    
    for doc in queue:
        doc_id = str(doc.document_id)
        
        # 1. Fetch current metadata via API
        response = requests.get(f"{BASE_URL}/{doc_id}/")
        if response.status_code != 200:
            console.print(f"[red]Failed to fetch API for {doc_id}[/red]")
            continue
            
        data = response.json()
        
        console.print("--------------------------------------------------")
        display_metadata(doc_id, data)
        console.print(f"[bold yellow]Confidence Score:[/bold yellow] {data.get('metadata_confidence', 0.0)*100}%")
        
        # 2. Interactive Menu
        action = Prompt.ask(
            "\nAction", 
            choices=["verify", "override", "skip", "quit"],
            default="skip"
        )
        
        if action == "quit":
            break
            
        elif action == "verify":
            res = requests.patch(f"{BASE_URL}/{doc_id}/verify/", json={"verified": True})
            if res.status_code == 200:
                console.print("[bold green]Document Verified![/bold green]")
            else:
                console.print(f"[red]Failed to verify: {res.text}[/red]")
                
        elif action == "override":
            updates = {}
            while True:
                field = Prompt.ask("Enter field name to override (or 'done' to finish)")
                if field.lower() == 'done':
                    break
                value = Prompt.ask(f"Enter new value for {field}")
                updates[field] = value
                
            if updates:
                res = requests.patch(f"{BASE_URL}/{doc_id}/override/", json=updates)
                if res.status_code == 200:
                    console.print("[bold green]Override Successful! (Automatically verified)[/bold green]")
                    display_metadata(doc_id, res.json())
                else:
                    console.print(f"[red]Failed to override: {res.text}[/red]")

    console.print("\n[bold green]=== Review Session Ended ===[/bold green]")

if __name__ == "__main__":
    run_cli()
