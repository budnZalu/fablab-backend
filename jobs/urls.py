from rest_framework import routers
from django.urls import path, include

from jobs import views

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='user')

urlpatterns = [
    path('jobs/', views.JobsListView.as_view(), name='jobs_list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='jobs_detail'),
    path('jobs/<int:pk>/printing/', views.JobPrintingView.as_view(), name='jobs_printing'),
    path('jobs/<int:pk>/image/', views.JobImageView.as_view(), name='edit_image'),
    path('printings/', views.PrintingListView.as_view(), name='printings_list'),
    path('printings/<int:pk>/', views.PrintingDetailView.as_view(), name='printings_detail'),
    path('printings/<int:pk>/form/', views.FormPrintingView.as_view(), name='form_printing'),
    path('printings/<int:pk>/complete/', views.CompletePrintingView.as_view(), name='complete_printing'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', include(router.urls)),
]
