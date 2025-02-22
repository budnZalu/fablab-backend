from django.contrib import admin

from jobs.models import Job, Printing, PrintingJob


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('name', 'info')


@admin.register(Printing)
class PrintingAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'name')


@admin.register(PrintingJob)
class PrintingJobAdmin(admin.ModelAdmin):
    list_display = ('printing', 'job')
