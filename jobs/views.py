from django.db import IntegrityError, connection
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect

from jobs.models import Job, Printing, PrintingJob

def index(request):
    job_name = request.GET.get('job_name', '').lower()
    jobs = Job.objects.filter(name__icontains=job_name).exclude(
        status='deleted')
    draft = Printing.objects.filter(author=request.user,
                                    status='draft').first()
    if draft:
        draft_jobs = PrintingJob.objects.filter(printing=draft).values_list(
            'id', flat=True)
    else:
        draft_jobs = []
    return render(
        request,
        'index.html',
        context={'jobs': jobs,
                 'draft': draft,
                 'draft_jobs': draft_jobs}
    )


def job_detail(request, pk):
    job = Job.objects.get(pk=pk)
    if job.status == 'deleted':
        return redirect('/')
    return render(
        request,
        'job.html',
        context={'job': job}
    )


def printing_detail(request, pk):
    printing = Printing.objects.get(pk=pk)
    if printing.status == 'deleted':
        return HttpResponse(status=404)
    jobs = Job.objects.filter(printingjob__printing_id=pk).annotate(
        quantity=F('printingjob__quantity')
    )
    return render(
        request,
        'printing.html',
        context={'printing': printing, 'jobs': jobs},
    )


def add_to_printing(request, pk):
    if request.method == 'POST':
        job = Job.objects.get(pk=pk)
        printing = Printing.objects.filter(status='draft',
                                           author=request.user).first()
        if not printing:
            printing = Printing.objects.create(
                author=request.user
            )

        try:
            PrintingJob.objects.create(
                job=job,
                printing=printing,
                quantity=1
            )
        except IntegrityError:
            PrintingJob.objects.filter(job=job, printing=printing).delete()
        return redirect('/')


def delete_printing(request, pk):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE jobs_printing SET status = 'deleted' WHERE id = %s",
                [pk]
            )
        return redirect('/')
