from django.contrib.auth.models import User
from django.db.models import Sum, F
from django.utils import timezone
from minio import Minio
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs import serializers
from jobs.models import Job, Printing, PrintingJob


def default_user():
    return User.objects.all().first()


def minio_connection():
    return Minio(
        endpoint='localhost:9000',
        access_key='minioadmin',
        secret_key='minioadmin',
        secure=False
    )


class JobsListView(APIView):
    def get(self, request):
        job_name = request.query_params.get('job_name', None)
        jobs = Job.objects.filter(status='visible')
        if job_name:
            jobs = jobs.filter(name__icontains=job_name)
        serializer = serializers.JobSerializer(jobs, many=True)

        draft = Printing.objects.filter(author=default_user(),
                                        status='draft').first()
        draft_count = 0
        if draft:
            draft_count = PrintingJob.objects.filter(printing=draft).count()

        return Response(data={
            'draft_id': draft.id if draft else None,
            'draft_count': draft_count,
            'jobs': serializer.data,
        })

    def post(self, request):
        serializer = serializers.JobSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobDetailView(APIView):
    def get(self, request, pk):
        job = Job.objects.filter(id=pk, status='visible').first()
        if job is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.JobSerializer(job)
        return Response(serializer.data)

    def put(self, request, pk):
        job = Job.objects.filter(id=pk, status='visible').first()
        if job is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = serializers.JobSerializer(job, data=request.data,
                                               partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        job = Job.objects.filter(id=pk, status='visible').first()
        if job is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        job.status = 'deleted'
        job.save()
        minio_connection().remove_objects('fablab', job.image)
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobImageView(APIView):
    def post(self, request, pk):
        job = Job.objects.filter(id=pk, status='visible').first()
        if job is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        image_file = request.FILES.get('image')
        if image_file is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        minio_client = minio_connection()
        file_name = f'job_{job.id}_{image_file.name}'
        minio_client.put_object(
            'fablab',
            file_name,
            data=image_file.file,
            length=image_file.size,
            content_type=image_file.content_type
        )

        file_url = f'localhost:9000/fablab/{file_name}'
        job.image = file_url
        job.save()
        serializer = serializers.JobSerializer(job)
        return Response(serializer.data)


class JobPrintingView(APIView):
    def post(self, request, pk):
        job = Job.objects.filter(id=pk, status='visible').first()
        if job is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        draft = Printing.objects.filter(author=default_user(),
                                        status='draft').first()
        if draft is None:
            draft = Printing(author=default_user(), status='draft')
            draft.save()

        pjob = PrintingJob(job=job, printing=draft)
        pjob.save()
        serializer = serializers.PrintingJobSerializer(pjob)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        draft = Printing.objects.filter(author=default_user(),
                                        status='draft').first()
        if draft is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        pjob = PrintingJob.objects.filter(job_id=pk, printing=draft).first()
        if pjob is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.PrintingJobSerializer(pjob, data=request.data,
                                                       partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        draft = Printing.objects.filter(author=default_user(),
                                        status='draft').first()
        if draft is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        pjob = PrintingJob.objects.filter(job_id=pk, printing=draft).first()
        if pjob is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        pjob.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class PrintingListView(APIView):
    def get(self, request):
        printings = Printing.objects.filter(
            author=default_user(),
            status__in=['complete', 'formed', 'rejected']
        )

        status = request.query_params.get('status', None)
        if status:
            printings = printings.filter(status=status)

        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        if start_date:
            printings = printings.filter(formed_at__gte=start_date)
        if end_date:
            printings = printings.filter(formed_at__lte=end_date)

        serializer = serializers.PrintingListSerializer(printings, many=True)
        return Response(serializer.data)


class PrintingDetailView(APIView):
    def get(self, request, pk):
        printing = Printing.objects.filter(id=pk).first()
        if printing is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.PrintingDetailSerializer(printing)
        return Response(serializer.data)

    def put(self, request, pk):
        printing = Printing.objects.filter(id=pk).first()
        if printing is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.PrintingDetailSerializer(printing,
                                                          data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        printing = Printing.objects.filter(id=pk).first()
        if printing is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        printing.status = 'deleted'
        printing.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FormPrintingView(APIView):
    def post(self, request, pk):
        printing = Printing.objects.filter(id=pk).first()
        if printing is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        errors = {}
        if printing.status != 'draft':
            errors['status_error'] = "Статус заявки должен быть 'draft'."
        if printing.name is None:
            errors['name_error'] = 'ФИО не указано в заявке.'
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        printing.status = 'formed'
        printing.formed_at = timezone.now()
        printing.save()
        serializer = serializers.PrintingListSerializer(printing)
        return Response(serializer.data)


class CompletePrintingView(APIView):
    def post(self, request, pk):
        printing = Printing.objects.filter(id=pk).first()
        if printing is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        action_status = request.data.get('status', None)
        errors = {}
        if printing.status != 'formed':
            errors['error'] = "Статус заявки должен быть 'formed'."
        if action_status not in ['complete', 'reject']:
            errors['status_error'] = "Некорректный статус. Допустимые значения: 'complete' или 'reject'."
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        if action_status == 'complete':
            printing.status = 'complete'
            total_price = PrintingJob.objects.filter(printing=printing).aggregate(
                total=Sum(F('job__price') * F('quantity'))
            )['total'] or 0
            printing.total_price = total_price
        elif action_status == 'reject':
            printing.status = 'rejected'

        printing.complete_at = timezone.now()
        printing.moderator = default_user()
        printing.save()
        serializer = serializers.PrintingListSerializer(printing)
        return Response(serializer.data)


class UserRegisterView(APIView):
    def post(self, request):
        serialzer = serializers.UserSerializer(data=request.data)
        if serialzer.is_valid():
            serialzer.save()
            return Response(serialzer.data, status=status.HTTP_201_CREATED)
        return Response(serialzer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserEditView(APIView):
    def put(self, request, pk):
        user = User.objects.filter(id=pk).first()
        if user is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serialzer = serializers.UserSerializer(user, data=request.data,
                                               partial=True)
        if serialzer.is_valid():
            serialzer.save()
            return Response(serialzer.data, status=status.HTTP_200_OK)
        return Response(serialzer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    def post(self, request):
        return Response({'status': 'Произведена аутентификация',
                         'info': 'Метод не реализуется в лаб. 3'})


class UserLogoutView(APIView):
    def post(self, request):
        return Response({'status': 'Произведена деавторизация',
                         'info': 'Метод не реализуется в лаб. 3'})
