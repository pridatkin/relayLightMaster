from django.core.management import call_command

def sync_schedule_cron():
    """Функция для вызова management-команды sync_schedule."""
    call_command('sync_schedule')