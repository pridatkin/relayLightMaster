from django.db import models

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