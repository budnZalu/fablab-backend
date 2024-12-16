from django.urls import path

from jobs import views

urlpatterns = [
    path('jobs/', views.JobsListView.as_view(), name='jobs_list'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='jobs_detail'),
    path('jobs/<int:pk>/printing/', views.JobPrintingView.as_view(), name='jobs_printing'),
    path('jobs/<int:pk>/image/', views.JobImageView.as_view(), name='edit_image'),
    path('printings/', views.PrintingListView.as_view(), name='printings_list'),
    path('printings/<int:pk>/', views.PrintingDetailView.as_view(), name='printings_detail'),
    path('printings/<int:pk>/form/', views.FormPrintingView.as_view(), name='form_printing'),
    path('printings/<int:pk>/complete/', views.CompletePrintingView.as_view(), name='complete_printing'),
    path('users/register/', views.UserRegisterView.as_view(), name='users_register'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='users_edit'),
    path('users/login/', views.UserLoginView.as_view(), name='users_login'),
    path('users/logout/', views.UserLogoutView.as_view(), name='users_logout'),
]
