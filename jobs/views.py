import uuid

import redis
from django.contrib.auth import get_user_model, authenticate, logout
from django.db.models import Sum, F
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from minio import Minio
from rest_framework import status, viewsets
from rest_framework.decorators import permission_classes, \
    authentication_classes, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs import serializers
from jobs.models import Job, Printing, PrintingJob
from jobs.permissions import IsManager, IsAdmin

User = get_user_model()


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


def minio_connection():
    return Minio(
        endpoint='localhost:9000',
        access_key='minioadmin',
        secret_key='minioadmin',
        secure=False
    )


redis_storage = redis.StrictRedis(host='localhost', port=6379)


class JobsListView(APIView):
    def get(self, request):
        job_name = request.query_params.get('job_name', None)
        jobs = Job.objects.filter(status='visible')
        if job_name:
            jobs = jobs.filter(name__icontains=job_name)
        serializer = serializers.JobSerializer(jobs, many=True)
        draft = None
        if request.user:
            draft = Printing.objects.filter(author=request.user,
                                            status='draft').first()

        draft_count = 0
        if draft:
            draft_count = PrintingJob.objects.filter(printing=draft).count()

        return Response(data={
            'draft_id': draft.id if draft else None,
            'draft_count': draft_count,
            'jobs': serializer.data,
        })

    @swagger_auto_schema(request_body=serializers.JobSerializer)
    @method_permission_classes((IsManager,))
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

    @swagger_auto_schema(request_body=serializers.JobSerializer)
    @method_permission_classes((IsManager,))
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

    @method_permission_classes((IsManager,))
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

        draft = Printing.objects.filter(author=request.user,
                                        status='draft').first()
        if draft is None:
            draft = Printing(author=request.user, status='draft')
            draft.save()

        pjob = PrintingJob(job=job, printing=draft)
        pjob.save()
        serializer = serializers.PrintingJobSerializer(pjob)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        draft = Printing.objects.filter(author=request.user,
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
        draft = Printing.objects.filter(author=request.user,
                                        status='draft').first()
        if draft is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        pjob = PrintingJob.objects.filter(job_id=pk, printing=draft).first()
        if pjob is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        pjob.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class PrintingListView(APIView):
    @method_permission_classes((IsAuthenticated,))
    def get(self, request):
        printings = Printing.objects.filter(
            status__in=['complete', 'formed', 'rejected']
        )

        user = request.user
        if not user.is_staff:
            printings = printings.filter(author=user)

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
        printing = Printing.objects.filter(id=pk, author=request.user).first()

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
    @method_permission_classes((IsManager,))
    def post(self, request, pk):
        printing = Printing.objects.filter(id=pk).first()
        if printing is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        action_status = request.data.get('status', None)
        errors = {}
        if printing.status != 'formed':
            errors['error'] = "Статус заявки должен быть 'formed'."
        if action_status not in ['complete', 'reject']:
            errors[
                'status_error'] = "Некорректный статус. Допустимые значения: 'complete' или 'reject'."
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        if action_status == 'complete':
            printing.status = 'complete'
            total_price = \
            PrintingJob.objects.filter(printing=printing).aggregate(
                total=Sum(F('job__price'))
            )['total'] or 0
            printing.total_price = total_price
        elif action_status == 'reject':
            printing.status = 'rejected'

        printing.complete_at = timezone.now()
        printing.moderator = request.user
        printing.save()
        serializer = serializers.PrintingListSerializer(printing)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    model_class = User

    def create(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(
                email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.model_class.objects.create_user(
                email=serializer.data['email'],
                password=serializer.data['password'],
                is_superuser=False,
                is_staff=False)
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]


@authentication_classes([])
@csrf_exempt
@swagger_auto_schema(method='post', request_body=serializers.UserSerializer)
@api_view(['Post'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data['email']
    password = request.data['password']
    user = authenticate(request, email=email, password=password)
    if user is not None:
        random_key = str(uuid.uuid4())
        redis_storage.set(random_key, user.id)

        response = Response("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)

        return response
    else:
        return Response("{'status': 'error', 'error': 'Login failed!'}")


def logout_view(request):
    logout(request._request)
    return Response({'status': 'Success'})
