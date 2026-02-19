from django.urls import path
from . import views

urlpatterns = [
    # SuperAdmin Authentication
    path('auth/login/', views.SuperAdminLoginView.as_view(), name='superadmin-login'),
    # Retailer Authentication
    path('retailer-auth/login/', views.RetailerLoginView.as_view(), name='retailer-login'),
    path('retailer-auth/verify-otp/', views.RetailerVerifyOTPView.as_view(), name='retailer-verify-otp'),
    # User Registration
    path('auth/register/', views.UserRegistrationView.as_view(), name='user-register'),
    # OTP Management
    path('otp/request_otp/', views.OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify_otp/', views.OTPVerifyView.as_view(), name='otp-verify'),
    # Forgot Password & Reset
    path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/verify-reset-otp/', views.ResetOTPVerifyView.as_view(), name='verify-reset-otp'),
    path('auth/reset-password/', views.PasswordResetView.as_view(), name='reset-password'),
    # KYC Management
    path('kyc/submit/<int:user_id>/', views.KYCSubmitView.as_view(), name='kyc-submit'),
    # Home
    path('home/', views.HomeView.as_view(), name='home'),
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/<int:user_id>/', views.ProfileView.as_view(), name='profile-by-id'),
    # Change Password
    path('auth/change-password/<int:user_id>/', views.ChangePasswordView.as_view(), name='change-password'),
    path('auth/superadmin-change-password/', views.SuperAdminChangePasswordView.as_view(), name='superadmin-change-password'),
]