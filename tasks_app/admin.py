from django.contrib import admin
from .models import TaskExecution, EmailQueue, Report

# Register your models here.
@admin.register(TaskExecution)
class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'queue_name', 'status', 'started_at', 'retry_count')
    list_filter = ('status', 'queue_name', 'started_at')
    search_fields = ('task_name', 'task_id')
    readonly_fields = ('task_id', 'started_at', 'completed_at')

@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ('subject', 'recipient', 'priority', 'status', 'queued_at')
    list_filter = ('status', 'priority')
    search_fields = ('recipient', 'subject')
    ordering = ['-priority', 'queued_at']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'report_type')
    search_fields = ('title',)
