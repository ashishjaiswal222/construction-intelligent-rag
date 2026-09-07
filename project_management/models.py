import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    phase = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ('project_admin', 'Project Admin'),
        ('engineer', 'Engineer'),
        ('viewer', 'Viewer'),
        ('contractor', 'Contractor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='viewer')
    contractor_company = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.project.name}"

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    query_text = models.TextField(blank=True, null=True)
    documents_accessed = models.JSONField(default=list)
    response_length = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user.username if self.user else 'System'} at {self.timestamp}"

# Helper extension to User model via a manager or property is tricky without custom user model.
# We will just write a helper function to get roles.
def get_project_role(user, project_id):
    if user.is_superuser:
        return 'project_admin'
    try:
        membership = ProjectMembership.objects.get(user=user, project_id=project_id)
        return membership.role
    except ProjectMembership.DoesNotExist:
        return None

def has_project_access(user, project_id):
    if user.is_superuser:
        return True
    return ProjectMembership.objects.filter(user=user, project_id=project_id).exists()

User.add_to_class('get_project_role', get_project_role)
User.add_to_class('has_project_access', has_project_access)
