from django.contrib.auth.models import User
from rest_framework import serializers

from jobs.models import Job, Printing, PrintingJob


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['id', 'status', 'image']


class PrintingJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = PrintingJob
        fields = '__all__'


class PrintingListSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()

    class Meta:
        model = Printing
        fields = '__all__'
        read_only_fields = [
            'id', 'author', 'moderator', 'status', 'total_price'
        ]

    def get_author(self, obj):
        return obj.author.username

    def get_moderator(self, obj):
        if obj.moderator:
            return obj.moderator.username
        return None


class PrintingDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()
    jobs = PrintingJobSerializer(source='printingjob_set', many=True,
                                 read_only=True)

    class Meta:
        model = Printing
        fields = ['id', 'author', 'moderator', 'name', 'status',
                  'created_at', 'formed_at', 'complete_at', 'total_price',
                  'jobs']
        read_only_fields = ['id', 'author', 'moderator', 'status',
                            'created_at', 'formed_at', 'complete_at',
                            'total_price', 'jobs']

    def get_author(self, obj):
        return obj.author.username

    def get_moderator(self, obj):
        if obj.moderator:
            return obj.moderator.username
        return None


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
