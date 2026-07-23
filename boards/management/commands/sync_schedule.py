from django.core.management.base import BaseCommand
from boards.models import ScheduleSettings, Board
from boards.utils import send_signal, try_reconnect
from datetime import datetime

class Command(BaseCommand):
    help = 'Синхронизация реле по расписанию (для cron)'

    def handle(self, *args, **options):
        schedule = ScheduleSettings.load()

        if not schedule.auto_sync_enabled:
            self.stdout.write('Автосинхронизация отключена. Выход.')
            return

        if not schedule.is_active:
            self.stdout.write('Расписание неактивно. Выход.')
            return

        now = datetime.now().time()
        on = schedule.on_time
        off = schedule.off_time

        # Определяем, должно ли освещение быть включено
        if on <= off:
            should_be_on = on <= now <= off
        else:
            should_be_on = now >= on or now <= off

        # Выполняем включение/выключение
        for board in Board.objects.all():
            if not try_reconnect(board):
                continue
            try:
                if should_be_on:
                    # включаем оба реле
                    resp1 = send_signal(board.ip_address, '11')
                    board.relay1_state = (resp1[0] == '1')
                    board.relay2_state = (resp1[1] == '1')
                    board.save()
                    resp2 = send_signal(board.ip_address, '12')
                    board.relay1_state = (resp2[0] == '1')
                    board.relay2_state = (resp2[1] == '1')
                    board.save()
                else:
                    # выключаем оба реле
                    resp1 = send_signal(board.ip_address, '21')
                    board.relay1_state = (resp1[0] == '1')
                    board.relay2_state = (resp1[1] == '1')
                    board.save()
                    resp2 = send_signal(board.ip_address, '22')
                    board.relay1_state = (resp2[0] == '1')
                    board.relay2_state = (resp2[1] == '1')
                    board.save()
            except Exception as e:
                self.stderr.write(f'Ошибка платы {board.ip_address}: {e}')
                board.is_available = False
                board.relay1_state = None
                board.relay2_state = None
                board.save()

        status = "включён" if should_be_on else "выключен"
        self.stdout.write(f'Синхронизация выполнена. Свет {status}.')