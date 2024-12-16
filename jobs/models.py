from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Job(models.Model):
    name = models.CharField(max_length=100)
    info = models.TextField()
    price = models.PositiveIntegerField()
    image = models.URLField(max_length=200, blank=True, null=True)
    statuses = [
        ('visible', 'Показана'),
        ('deleted', 'Удалена')
    ]
    status = models.CharField(max_length=10, choices=statuses,
                              default='default')


class Printing(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='printings')
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                                  blank=True)
    statuses = [
        ('draft', 'Черновик'),
        ('deleted', 'Удалена'),
        ('complete', 'Завершена'),
        ('formed', 'Сформирована'),
        ('rejected', 'Отклонена'),
    ]
    status = models.CharField(max_length=10, choices=statuses, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(null=True, blank=True)
    complete_at = models.DateTimeField(null=True, blank=True)
    total_price = models.PositiveIntegerField(blank=True, null=True)


class PrintingJob(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    printing = models.ForeignKey(Printing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = (('job', 'printing'),)
