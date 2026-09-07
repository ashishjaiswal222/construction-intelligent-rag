import os

def get_run_config(user_id: str, project_id: str, doc_type: str = None) -> dict:
    """
    Returns the LangChain run configuration required to trace requests in LangSmith,
    tagging them with user and project metadata for cost-tracking and observability.
    """
    return {
        'configurable': {'thread_id': f'{user_id}-{project_id}'},
        'metadata': {
            'user_id': str(user_id),
            'project_id': str(project_id),
            'doc_type': doc_type or 'query',
            'app_version': os.environ.get('APP_VERSION', '1.0.0'),
            'environment': os.environ.get('ENVIRONMENT', 'development'),
        }
    }
