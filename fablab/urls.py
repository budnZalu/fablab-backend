from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from jobs import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('jobs/<int:pk>', views.job_detail, name='job'),
    path('jobs/<int:pk>/add', views.add_to_printing, name='add_to_printing'),
    path('printings/<int:pk>', views.printing_detail, name='printing'),
    path('printings/<int:pk>/delete', views.delete_printing, name='delete_printing'),
    path('printings/', views.printing_list, name='printing_list'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
