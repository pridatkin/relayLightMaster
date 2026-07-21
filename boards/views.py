from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time
from .models import Board, ScheduleSettings
from .utils import check_board, send_signal

def board_list(request):
    boards = Board.objects.all()
    return render(request, 'boards/board_list.html', {'boards': boards})

def board_add(request):
    if request.method == 'POST':
        board = Board(
            ip_address=request.POST['ip_address'],
            description=request.POST['description'],
            relay1_description=request.POST['relay1_description'],
            relay2_description=request.POST['relay2_description'],
        )
        # При добавлении можно сразу проверить доступность
        status = check_board(board.ip_address)
        board.is_available = status['available']
        if status['available']:
            board.relay1_state = status['relay1']
            board.relay2_state = status['relay2']
        board.save()
        messages.success(request, "Плата добавлена")
        return redirect('board_list')
    return render(request, 'boards/board_form.html', {'board': None})

def board_edit(request, pk):
    board = get_object_or_404(Board, pk=pk)
    if request.method == 'POST':
        board.ip_address = request.POST['ip_address']
        board.description = request.POST['description']
        board.relay1_description = request.POST['relay1_description']
        board.relay2_description = request.POST['relay2_description']
        # Можно сразу обновить доступность и состояния
        status = check_board(board.ip_address)
        board.is_available = status['available']
        if status['available']:
            board.relay1_state = status['relay1']
            board.relay2_state = status['relay2']
        else:
            board.relay1_state = None
            board.relay2_state = None
        board.save()
        messages.success(request, "Плата обновлена")
        return redirect('board_list')
    return render(request, 'boards/board_form.html', {'board': board})

def board_delete(request, pk):
    board = get_object_or_404(Board, pk=pk)
    board.delete()
    messages.success(request, "Плата удалена")
    return redirect('board_list')

def board_check_all(request):
    """Обновляет доступность и состояния реле для всех плат."""
    boards = Board.objects.all()
    for board in boards:
        status = check_board(board.ip_address)
        board.is_available = status['available']
        if status['available']:
            board.relay1_state = status['relay1']
            board.relay2_state = status['relay2']
        else:
            board.relay1_state = None
            board.relay2_state = None
        board.save()
    messages.success(request, "Состояния обновлены")
    return redirect('board_list')

def toggle_relay(request, board_id, relay_num):
    """Переключает реле (1 или 2) на противоположное состояние."""
    board = get_object_or_404(Board, pk=board_id)
    if not board.is_available:
        messages.error(request, "Плата недоступна")
        return redirect('board_list')

    # Определяем текущее состояние и новый сигнал
    if relay_num == 1:
        current_state = board.relay1_state
        # 1 включить, 2 выключить, вторая цифра – номер реле
        signal = '11' if not current_state else '21'
    elif relay_num == 2:
        current_state = board.relay2_state
        signal = '12' if not current_state else '22'
    else:
        messages.error(request, "Неверный номер реле")
        return redirect('board_list')

    try:
        response = send_signal(board.ip_address, signal)
        # Ответ должен содержать новое состояние, обновляем оба реле
        board.relay1_state = (response[0] == '1')
        board.relay2_state = (response[1] == '1')
        board.is_available = True
        board.save()
        messages.success(request, f"Реле {relay_num} переключено")
    except Exception as e:
        messages.error(request, f"Ошибка связи: {e}")
        # Помечаем плату как недоступную
        board.is_available = False
        board.relay1_state = None
        board.relay2_state = None
        board.save()
    return redirect('board_list')

def turn_all_on(request):
    """Включает реле 1 и 2 на всех доступных платах."""
    _turn_all_on(request)
    messages.success(request, "Все реле включены")
    return redirect('board_list')

def turn_all_off(request):
    """Выключает реле 1 и 2 на всех доступных платах."""
    _turn_all_off(request)
    messages.success(request, "Все реле выключены")
    return redirect('board_list')

def schedule_settings(request):
    """Редактирование глобального расписания."""
    schedule = ScheduleSettings.load()
    if request.method == 'POST':
        schedule.is_active = 'is_active' in request.POST
        schedule.on_time = request.POST.get('on_time', '08:00')
        schedule.off_time = request.POST.get('off_time', '22:00')
        schedule.save()
        messages.success(request, "Расписание сохранено")
        return redirect('board_list')
    return render(request, 'boards/schedule_form.html', {'schedule': schedule})

def sync_schedule(request):
    """
    Синхронизирует состояния всех реле согласно расписанию.
    Если расписание активно и текущее время в интервале между on_time и off_time,
    включает всё, иначе выключает всё.
    """
    schedule = ScheduleSettings.load()
    if not schedule.is_active:
        messages.warning(request, "Расписание неактивно. Сначала включите его.")
        return redirect('board_list')

    now = datetime.now().time()
    on = schedule.on_time
    off = schedule.off_time

    # Определяем, нужно ли сейчас включать свет
    if on <= off:
        print(on)
        print(now)
        print(off)
        # Интервал внутри одних суток, напр. 08:00 - 22:00
        should_be_on = on <= now <= off
    else:
        # Интервал переходит через полночь, напр. 22:00 - 08:00
        should_be_on = now >= on or now <= off

    if should_be_on:
        # Вызываем логику включения всех реле (определена ниже)
        _turn_all_on(request)
        messages.success(request, "По расписанию свет включён")
    else:
        _turn_all_off(request)
        messages.success(request, "По расписанию свет выключен")

    return redirect('board_list')

def _turn_all_on(request):
    """Внутренняя функция включения всех доступных реле (без редиректа)."""
    for board in Board.objects.all():
        if not board.is_available:
            continue
        try:
            resp1 = send_signal(board.ip_address, '11')
            board.relay1_state = (resp1[0] == '1')
            board.relay2_state = (resp1[1] == '1')
            board.save()
            resp2 = send_signal(board.ip_address, '12')
            board.relay1_state = (resp2[0] == '1')
            board.relay2_state = (resp2[1] == '1')
            board.save()
        except Exception:
            board.is_available = False
            board.relay1_state = None
            board.relay2_state = None
            board.save()

def _turn_all_off(request):
    """Внутренняя функция выключения всех доступных реле."""
    for board in Board.objects.all():
        if not board.is_available:
            continue
        try:
            resp1 = send_signal(board.ip_address, '21')
            board.relay1_state = (resp1[0] == '1')
            board.relay2_state = (resp1[1] == '1')
            board.save()
            resp2 = send_signal(board.ip_address, '22')
            board.relay1_state = (resp2[0] == '1')
            board.relay2_state = (resp2[1] == '1')
            board.save()
        except Exception:
            board.is_available = False
            board.relay1_state = None
            board.relay2_state = None
            board.save()