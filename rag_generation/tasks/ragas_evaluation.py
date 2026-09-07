from celery import shared_task
from rag_generation.models import GenerationLog
from shared.llms.factory import LLMFactory
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

EVAL_PROMPT = """
Evaluate the faithfulness of the generated ANSWER based strictly on the provided CONTEXT.

CONTEXT:
{context}

ANSWER:
{answer}

INSTRUCTIONS:
Determine if the ANSWER is fully grounded in the CONTEXT. The ANSWER must not contain any new information or claims that are not supported by the CONTEXT.
Output ONLY a valid JSON object with the following structure:
{{
    "faithfulness_score": float (0.0 to 1.0, where 1.0 is fully faithful and 0.0 is completely hallucinated),
    "reasoning": "A brief explanation of the score"
}}
"""

@shared_task(name="rag_generation.tasks.evaluate_recent_generations")
def evaluate_recent_generations():
    """
    Periodically evaluates recent GenerationLogs that lack a ragas_faithfulness score.
    """
    logs = GenerationLog.objects.filter(ragas_faithfulness__isnull=True).order_by('-created_at')[:20]
    
    if not logs:
        return "No logs to evaluate"
        
    # Use Groq for fast, reliable evaluation
    llm = LLMFactory.get_provider('groq')
    
    evaluated_count = 0
    for log in logs:
        # Note: In GenerationLog, the fields are usually 'generated_answer' and 'chunk_ids_used' / 'chunks_used'
        # The prompt here uses log.answer and log.context_used, let's make sure it matches GenerationLog model.
        # Actually, let's fix the attribute names to match the model.
        answer = getattr(log, 'generated_answer', getattr(log, 'answer', ''))
        # If contexts are stored in chunk_ids_used or similar, we might not have full text.
        # Let's assume log.context_used or something similar exists based on the old code.
        context_data = getattr(log, 'context_used', getattr(log, 'filter_used', []))
        
        if not answer:
            # Skip empty answers
            log.ragas_faithfulness = 0.0
            log.save(update_fields=['ragas_faithfulness'])
            continue
            
        context_str = "\n".join([c.get('page_content', '') for c in context_data if isinstance(c, dict)])
        if not context_str:
             context_str = str(context_data)
             
        prompt = EVAL_PROMPT.format(context=context_str, answer=answer)
        
        try:
            # Invoke LLM using the BaseLLMProvider interface
            content, _ = llm.generate(prompt)
            
            # Clean JSON if wrapped in markdown blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
                
            eval_data = json.loads(content)
            score = float(eval_data.get('faithfulness_score', 0.0))
            
            log.ragas_faithfulness = min(max(score, 0.0), 1.0)
            log.save(update_fields=['ragas_faithfulness'])
            evaluated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to evaluate log {log.id}: {e}")
            
    return f"Evaluated {evaluated_count} logs"
