from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'auth', views.SuperAdminLoginView, basename='auth')
router.register(r'auth/register', views.UserRegistrationView, basename='register')
router.register(r'otp', views.OTPManagementView, basename='otp')
router.register(r'kyc', views.KYCManagementView, basename='kyc')

urlpatterns = [
    path('', include(router.urls)),
]