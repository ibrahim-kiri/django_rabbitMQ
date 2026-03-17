from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import TaskExecution, EmailQueue, Report
from .tasks import (
    send_priority_email,
    send_bulk_emails,
    process_large_dataset,
    generate_user_report,
    run_workflow,
    run_parallel_processing,
)

# Create your views here.
@require_http_methods(['POST'])
def send_email_task(request):
    """Send a priority email through RabbitMQ"""
    result = send_priority_email.enqueue(
        email=request.POST.get('email', 'test@example.com'),
        subject='Test Email from RabbitMQ',
        message='This email was sent through RabbitMQ!'
    )

    return JsonResponse({
        'status': 'success',
        'task_id': result.id,
        'queue': 'emails',
        'message': 'Email queued in RabbitMQ'
    })

@require_http_methods(['POST'])
def process_data_task(request):
    """Process data through RabbitMQ processing queue"""
    data_id = request.POST.get('data_id', 'dataset_001')

    result = process_large_dataset.enqueue(data_id=data_id)

    return JsonResponse({
        'status': 'success',
        'task_id': result.id,
        'queue': 'processing',
        'message': 'Data processing queued in RabbitMQ'
    })

@require_http_methods(['POST'])
def generate_report_task(request):
    """Generate report through RabbitMQ reports queue"""
    report = Report.objects.create(
        title='User Activity Report',
        report_type='user_activity',
        requested_by=request.user if request.user.is_authenticated else None,
        parameters={'date_range': '30_days'}
    )

    result = generate_user_report.enqueue(report_id=report.id)

    report.task_id = result.id
    report.save()

    return JsonResponse({
        'status': 'success',
        'task_id': result.id,
        'report_id': report.id,
        'queue': 'reports',
        'message': 'Report generation queued in RabbitMQ'
    })

@require_http_methods(['POST'])
def run_workflow_task(request):
    """Run a chained workflow through RabbiMQ"""
    result = run_workflow()

    return JsonResponse({
        'status': 'success',
        'task_id': result.id,
        'message': 'Workflow started in RabbitMQ',
        'type': 'chain'
    })

def dashboard(request):
    """Dashboard showing RabbitMQ task activity"""
    task_executions = TaskExecution.objects.all()[:20]
    email_queue = EmailQueue.objects.all()[:10]
    reports = Report.objects.all()[:10]

    stats = {
        'pending_emails': EmailQueue.objects.filter(status='queued').count(),
        'processing_tasks': TaskExecution.objects.filter(status='processing').count(),
        'pending_reports': Report.objects.filter(status='pending').count(),
    }

    return render(request, 'tasks_app/dashboard.html', {
        'task_executions': task_executions,
        'email_queue': email_queue,
        'reports': reports,
        'stats': stats,
    })
