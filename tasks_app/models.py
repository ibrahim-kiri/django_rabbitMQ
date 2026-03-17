from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class TaskExecution(models.Model):
    """Track all task execution through RabbitMQ"""
    task_name = models.CharField(max_length=255)
    task_id = models.CharField(max_length=255, unique=True)
    queue_name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[
            ('queued', 'Queued'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('retry', 'Retrying'),
        ],
        default='queued'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    result_data = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.task_name} ({self.status})"
    

class EmailQueue(models.Model):
    """Email queue managed by RabbitMQ"""
    recipient = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    priority = models.IntegerField(default=5) # 1-10, higher = more urgent
    task_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('queued', 'Queued'),
            ('sending', 'Sending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        default='queued'
    )
    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', 'queued_at']

    def __str__(self):
        return f"{self.subject} to {self.recipient}"
    

class Report(models.Model):
    """Report generation tracked through RabbitMQ queues"""
    title = models.CharField(max_length=200)
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('user_activity', 'User Activity'),
            ('sales', 'Sales Report'),
            ('analytics', 'Analytics'),
        ]
    )
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    parameters = models.JSONField()
    task_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('generating', 'Generating'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.status})"

