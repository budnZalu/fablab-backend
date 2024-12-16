from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from django.db import models


class NewUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, password,
                                **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(verbose_name="Пароль")
    is_staff = models.BooleanField(default=False,
                                   verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False,
                                       verbose_name="Является ли пользователь админом?")

    USERNAME_FIELD = 'email'

    objects = NewUserManager()


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
                              default='visible')


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
    duration = models.PositiveIntegerField(blank=True, null=True, default=1)

    class Meta:
        unique_together = (('job', 'printing'),)
