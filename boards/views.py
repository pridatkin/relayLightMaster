from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import Board
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