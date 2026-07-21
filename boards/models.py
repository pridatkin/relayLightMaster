from django.db import models
from django.core.exceptions import ValidationError

class Board(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="IP-адрес")
    description = models.CharField("Описание платы", max_length=200)
    is_available = models.BooleanField("Доступна", default=False)

    # Описания реле
    relay1_description = models.CharField("Описание реле 1", max_length=200, blank=True)
    relay2_description = models.CharField("Описание реле 2", max_length=200, blank=True)

    # Состояния реле (True = вкл, False = выкл, None = неизвестно)
    relay1_state = models.BooleanField("Состояние реле 1", null=True, blank=True, default=None)
    relay2_state = models.BooleanField("Состояние реле 2", null=True, blank=True, default=None)

    class Meta:
        verbose_name = "Плата"
        verbose_name_plural = "Платы"

    def __str__(self):
        return f"{self.description} ({self.ip_address})"
    
class ScheduleSettings(models.Model):
    """Глобальные настройки расписания (только одна запись)."""
    is_active = models.BooleanField("Расписание включено", default=False)
    on_time = models.TimeField("Время включения", default="08:00")
    off_time = models.TimeField("Время выключения", default="22:00")

    class Meta:
        verbose_name = "Расписание"
        verbose_name_plural = "Расписание"

    def save(self, *args, **kwargs):
        # Гарантируем существование только одной записи
        if not self.pk and ScheduleSettings.objects.exists():
            raise ValidationError("Может существовать только одна запись расписания")
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Получить единственный экземпляр или создать с умолчаниями."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Настройки расписания"
