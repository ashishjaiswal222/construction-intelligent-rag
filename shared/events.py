import django.dispatch

# Fired when a document is successfully uploaded and saved
document_uploaded = django.dispatch.Signal()

# Fired when classification completes successfully (Layer 1, 2, or 3)
classification_completed = django.dispatch.Signal()

# Fired when classification fails completely
classification_failed = django.dispatch.Signal()
