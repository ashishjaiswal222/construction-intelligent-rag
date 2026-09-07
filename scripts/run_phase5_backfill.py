import os
import sys
import django
import time
from rich.console import Console

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from document_classification.models import Document
from document_metadata.tasks.extract_metadata_task import extract_metadata_task

console = Console()

def run_backfill():
    console.print("\n[bold blue]=== Starting Phase 5 Metadata Backfill ===[/bold blue]")
    
    # We will pick 3 documents that have successfully completed phase 3 (have refined content)
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT DISTINCT p.document_id 
            FROM document_processing_processingjob p 
            JOIN document_processing_page pg ON pg.processing_job_id = p.id 
            JOIN refined_content rc ON rc.page_id = pg.id 
            LIMIT 3
        ''')
        rows = cursor.fetchall()
        
    doc_ids = [row[0] for row in rows]
    
    if not doc_ids:
        console.print("[red]No documents found in the database with refined content.[/red]")
        return
        
    for doc_id in doc_ids:
        doc_id_str = str(doc_id)
        console.print(f"\n[bold]Processing Document ID:[/bold] {doc_id_str}")
        
        start_time = time.time()
        
        # We run the task synchronously here for testing
        try:
            # extract_metadata_task is a Celery task. We call the underlying function
            # by calling the Python function directly, but because it's wrapped in @shared_task,
            # we can just call it like a normal function, or use .apply()
            extract_metadata_task(doc_id_str)
            
            elapsed = time.time() - start_time
            console.print(f"[bold green]Successfully extracted metadata for {doc_id_str} in {elapsed:.2f}s[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Failed to process {doc_id_str}: {e}[/bold red]")
            
    console.print("\n[bold green]=== Backfill Complete ===[/bold green]")

if __name__ == "__main__":
    run_backfill()
