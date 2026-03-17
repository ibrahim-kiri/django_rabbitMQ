from django.urls import path
from . import views

app_name = 'tasks_app'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('send-email/', views.send_email_task, name='send_email'),
    path('process-data/', views.process_data_task, name='process_data'),
    path('generate-report/', views.generate_report_task, name='generate_report'),
    path('run-workflow/', views.run_workflow_task, name='run_workflow'),
]