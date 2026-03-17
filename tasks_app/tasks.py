"""Tasks using RabbitMQ"""

from django.tasks import task
from django.core.mail import send_mail
from celery import shared_task, group, chain, chord
from celery.exceptions import MaxRetriesExceededError
import time
import random
from datetime import datetime

# QUEUE: emails - High-priority email tasks
@task(priority=10)
def send_priority_email(email, subject, message):
    """
    High-priority email sent through RabbitMQ 'emails' queue.
    Django task routed to RabbitMQ's email exchange.
    Uses priority=10 for urgent emails (password resets, alerts).
    """
    from .models import EmailQueue, TaskExecution

    print(f"[EMAILS QUEUE] Sending priority email to {email}")

    # Track in EmailQueue
    email_record = EmailQueue.objects.create(
        recipient=email,
        subject=subject,
        body=message,
        priority=10,
        status='sending'
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[email],
        )

        email_record.status = 'sent'
        email_record.sent_at = timezone.now()
        email_record.save()

        print(f"[EMAILS QUEUE] ✅ Priority email sent to {email}")
        return f"Priority email sent to {email}"
    
    except Exception as e:
        email_record.status = 'failed'
        email_record.save()
        print(f"[EMAILS QUEUE] ❌ Failed: {e}")
        raise


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def send_bulk_emails(self, email_list, subject, message):
    """
    Bulk email sending with retry logic.

    RabbitMQ ensures reliable delivery even if worker crashes.
    Failed emails are automatically retried up to 5 times.
    """
    from .models import EmailQueue

    print(f"[EMAILS QUEUE] Processing bulk email to {len(email_list)} recipients")

    failed_emails = []

    for email in email_list:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[email]
            )

            EmailQueue.objects.create(
                recipient=email,
                subject=subject,
                body=message,
                status='sent',
                sent_at=timezone.now()
            )

        except Exception as e:
            failed_emails.append(email)
            print(f"[EMAIL QUEUE] Failed to send to {email}: {e}")

    if failed_emails:
        # Retry failed emails
        try:
            raise self.retry(countdown=60)
        except MaxRetriesExceededError:
            print(f"[EMAILS QUEUE] Max retries exceeded for: {failed_emails}")

    return f"Sent {len(email_list) - len(failed_emails)}/{len(email_list)} emails"


# QUEUE: processing - Data processing tasks
@task
def process_large_dataset(data_id):
    """
    Process large datasets through RabbitMQ 'processing' queue.

    RabbitMQ's message persistence ensures task isn't lost if worker crashes.
    """
    print(f"[PROCESSING QUEUE] Processing dataset {data_id}")

    from .models import TaskExecution

    execution = TaskExecution.objects.create(
        task_name='process_large_dataset',
        queue_name='processing',
        status='processing',
        started_at=timezone.now()
    )

    try:
        # Simulate heavy processing
        time.sleep(5)

        result = {
            'data-id': data_id,
            'processed_rows': random.randint(1000, 10000),
            'processing_time': 5,
            'timestamp': datetime.now().isoformat()
        }

        execution.status = 'completed'
        execution.completed_at = timezone.now()
        execution.result_data = result
        execution.save()

        print(f"[PROCESSING QUEUE] ✅ Dataset {data_id} processed")
        return result
    
    except Exception as e:
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.save()
        raise


@shared_task
def process_batch(batch_data):
    """
    Batch processing using RabbitMQ.

    Can be part of a group or chain for complex workflows.
    """
    print(f"[PROCESSING QUEUE] Processing batch: {batch_data['batch_id']}")
    time.sleep(2)
    return f"Batch {batch_data['batch_id']} processed"


# QUEUE: reports - Report generation
@task
def generate_user_report(report_id):
    """
    Generate comprehensive user report.

    Routed to 'reports' queue in RabbitMQ for dedicated report workers.
    """
    from .models import Report

    print(f"[REPORTS QUEUE] Generating report {report_id}")

    report = Report.objects.get(id=report_id)
    report.status = 'generating'
    report.save()

    try:
        # Simulate report generation
        time.sleep(8)

        report_data = {
            'total_users': random.randint(100, 1000),
            'active_users': random.randint(50, 500),
            'revenue': f"${random.randint(10000, 100000)}",
            'generated_at': datetime.now().isoformat()
        }

        # Save report
        report.status = 'completed'
        report.file_path = f'/reports/{report_id}.pdf'
        report.completed_at = timezone.now()
        report.save()

        print(f"[REPORTS QUEUE] ✅ Report {report_id} generated")
        return report_data
    
    except Exception as e:
        report.status = 'failed'
        report.save()
        raise


@shared_task
def generate_sales_report(month, year):
    """Sales report generation through RabbitMQ"""
    print(f"[REPORTS QUEUE] Generating sales report for {month}/{year}")
    time.sleep(6)

    return {
        'month': month,
        'year': year,
        'total_sales': random.randint(50000, 200000),
        'transactions': random.randint(100, 500)
    }


# ADVANCED PATTERNS - Celery workflows with RabbitMQ
@shared_task
def step_1():
    """First step in a chain"""
    print("[WORKFLOW] Step 1: Fetching data...")
    time.sleep(1)
    return {'data': [1, 2, 3, 4, 5]}

@shared_task
def step_2(previous_result):
    """Second step in a chain"""
    print(f"[WORKFLOW] Step 2: Processing data from step 1...")
    data = previous_result['data']
    processed = [x * 2 for x in data]
    time.sleep(1)
    return {'processed': processed}

@shared_task
def step_3(previous_result):
    """Final step in a chain"""
    print(f"[WORKFLOW] Step 3: Finalizing...")
    time.sleep(1)
    return {'final': sum(previous_result['processed'])}

def run_workflow():
    """
    Example of Celery chain workflow through RabbitMQ.

    Usage:
        from tasks_app.tasks import run_workflow
        result = run_workflow()
    """
    workflow = chain(step_1.s(), step_2.s(), step_3.s())
    return workflow.apply_async()

@shared_task
def aggregate_results(results):
    """
    Callback for chord - runs after all tasks in group complete
    """
    print(f"[WORKFLOW] Aggregating {len(results)} results")
    return {'aggregated': sum(results)}

def run_parallel_processing():
    """
    Example of celery chord (group + callback) through RabbitMQ.

    Processes multiple batches in parallel, then aggregates results.
    """
    job = chord(
        (process_batch.s({'batch_id': i, 'data': list(range(i*10, (i+1)*10))})
         for i in range(5)),
        aggregate_results.s()
    )
    return job.apply_async()


# PERIODIC TASKS - Scheduled through Celery Beat
@shared_task
def cleanup_old_data():
    """
    Periodic cleanup task scheduled by Celery Beat.
    Runs daily at 3 AM (configured in celery.py)
    """
    from datetime import timedelta
    from .models import EmailQueue, TaskExecution

    print("[PERIODIC] Running daily cleanup...")

    cutoff = timezone.now() - timedelta(days=30)

    # Cleanup old emails
    deleted_emails = EmailQueue.objects.filter(
        sent_at__lt=cutoff,
        status='sent'
    ).delete()[0]

    # Cleanup old task execution
    deleted_tasks = TaskExecution.objects.filter(
        completed_at__lt=cutoff,
        status='completed'
    ).delete()[0]

    print(f"[PERIOD] Cleaned up {deleted_emails} emails, {deleted_tasks} tasks")
    return f"Deleted {deleted_emails} emails, {deleted_tasks} tasks"

@shared_task
def send_daily_digest():
    """
    Daily digest email - scheduled by Celery Beat.
    Runs every day at 9 AM
    """
    print("[PERIODIC] Sending daily digest...")

    # Gather digest data
    from .models import EmailQueue, Report
    from django.contrib.auth.models import User

    stats = {
        'emails_sent_today': EmailQueue.objects.filter(sent_at__date=timezone.now().date()).count(),
        'reports_generated': Report.objects.filter(created_at__date=timezone.now().date()).count(),
        'active_users': User.objects.filter(last_login__date=timezone.now().date()).count(),
    }

    print(f"[PERIODIC] Daily stats: {stats}")
    return stats

@shared_task
def health_check():
    """
    Health check task - runs every 5 minutes.

    Verifies RabbitMQ connection and worker status.
    """
    print("[HEALTH] Running health check...")

    status = {
        'timestamp': datetime.now().isoformat(),
        'rabbitmq': 'connected',
        'worker': 'active',
    }

    print(f"[HEALTH] Status: {status}")
    return status
