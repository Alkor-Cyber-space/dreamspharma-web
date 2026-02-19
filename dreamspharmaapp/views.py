from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate, logout
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import random
import re
import string

from .models import CustomUser, KYC, OTP
from .serializers import (
    CustomUserSerializer, UserRegistrationSerializer, KYCSerializer, 
    KYCSubmitSerializer, SuperAdminLoginSerializer, RetailerLoginSerializer,
    ForgotPasswordSerializer, OTPVerifySerializer, PasswordResetSerializer,
    ChangePasswordSerializer
)


User = get_user_model()


# ProfileView for GET, POST, PUT
from rest_framework.permissions import IsAuthenticated


class ProfileView(APIView):
    """
    API endpoint for retrieving and updating retailer profile only.
    GET: Retrieve current retailer's profile or by user_id (superadmin only)
    PUT: Update current retailer's profile
    """
    permission_classes = [AllowAny]

    def get(self, request, user_id=None):
        user = request.user
        # If user_id is provided, only superadmin or the user themselves can fetch others' profiles
        if user_id is not None:
            # AnonymousUser has no role/id, so allow access for anyone if user is not authenticated
            if user.is_authenticated:
                if getattr(user, 'role', None) != 'SUPERADMIN' and getattr(user, 'id', None) != user_id:
                    return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            target_user = get_object_or_404(User, id=user_id)
        else:
            # If not authenticated, cannot get own profile
            if not user.is_authenticated:
                return Response({'error': 'Authentication required to access your own profile.'}, status=status.HTTP_401_UNAUTHORIZED)
            target_user = user
        if getattr(target_user, 'role', None) != 'RETAILER':
            return Response({'error': 'Only retailers have profiles at this endpoint.'}, status=status.HTTP_403_FORBIDDEN)
        # Try to get KYC info
        kyc = None
        try:
            kyc = target_user.kyc
        except Exception:
            pass
        profile = {
            'id': target_user.id,
            'name': target_user.first_name or target_user.username,
            'shop_name': kyc.shop_name if kyc else '',
            'shop_address': kyc.shop_address if kyc else '',
            'customer_name': kyc.customer_name if kyc else '',
            'email': target_user.email,
            'phone': target_user.phone_number or (kyc.customer_mobile if kyc else ''),
            'store_photo': request.build_absolute_uri(kyc.store_photo.url) if kyc and kyc.store_photo else ''
        }
        return Response(profile, status=status.HTTP_200_OK)

    def post(self, request):
        return Response({'error': 'Profile creation via this endpoint is not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def put(self, request, user_id=None):
        # Allow public update by user_id
        if user_id is None:
            return Response({'error': 'user_id is required in the URL.'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, id=user_id)
        if getattr(user, 'role', None) != 'RETAILER':
            return Response({'error': 'Only retailers can update their profile.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        kyc_fields = ['shop_name', 'shop_address', 'customer_name', 'store_photo', 'customer_mobile']
        kyc_data = {field: request.data.get(field) for field in kyc_fields if field in request.data}
        kyc = None
        try:
            kyc = user.kyc
        except Exception:
            pass
        # Update user fields
        if serializer.is_valid():
            serializer.save()
            # Update KYC fields if present
            if kyc and kyc_data:
                for field, value in kyc_data.items():
                    if value is not None:
                        setattr(kyc, field, value)
                kyc.save()
            # Build the same profile response as in GET
            profile = {
                'id': user.id,
                'name': user.first_name or user.username,
                'shop_name': kyc.shop_name if kyc else '',
                'shop_address': kyc.shop_address if kyc else '',
                'customer_name': kyc.customer_name if kyc else '',
                'email': user.email,
                'phone': user.phone_number or (kyc.customer_mobile if kyc else ''),
                'store_photo': self.request.build_absolute_uri(kyc.store_photo.url) if kyc and kyc.store_photo else ''
            }
            return Response(profile, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SuperAdminLoginView(APIView):
    """
    API endpoint for superadmin login.
    POST /api/auth/login/ - Login with username/email and password
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Login a superadmin with username/email and password.
        Returns access and refresh JWT tokens.
        
        Request Body:
        {
            "username": "admin_username or admin@example.com",
            "password": "password123"
        }
        """
        serializer = SuperAdminLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class RetailerLoginView(APIView):
    """
    API endpoint for retailer login with email and password.
    POST /api/retailer-auth/login/ - Step 1: Login with email + password
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Step 1: Login with email and password.
        
        First Login: System sends 4-digit OTP to email
        Subsequent Login: System returns JWT tokens directly
        
        Request Body:
        {
            "email": "retailer@example.com",
            "password": "password123"
        }
        
        Response (First Login):
        {
            "message": "Email and password verified. 4-digit OTP sent to your email.",
            "is_first_login": true,
            "otp_expires_in": 60,
            "email": "retailer@example.com"
        }
        
        Response (Subsequent Login):
        {
            "message": "Login successful!",
            "is_first_login": false,
            "access": "JWT_TOKEN",
            "refresh": "REFRESH_TOKEN"
        }
        """
        serializer = RetailerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        is_first_login = serializer.validated_data.get('is_first_login', False)
        
        # FIRST LOGIN: Generate and send OTP
        if is_first_login:
            # Generate and send OTP via email
            otp_obj = OTP.objects.create(user=user)
            otp_code = otp_obj.generate_otp()
            
            try:
                send_mail(
                    subject="Your Dream's Pharmacy First Login OTP",
                    message=f'Your 4-digit OTP for first login verification is: {otp_code}\n\nThis OTP is valid for 1 minute.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {e}")
            
            return Response({
                'message': 'Email and password verified. 4-digit OTP sent to your email.',
                'email': user.email
            }, status=status.HTTP_200_OK)
        
        # SUBSEQUENT LOGINS: Direct login without OTP
        else:
            # Update user status to LOGIN_ENABLED
            user.status = 'LOGIN_ENABLED'
            user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful!',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'is_first_login': False
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_200_OK)


class RetailerVerifyOTPView(APIView):
    """
    API endpoint for retailer OTP verification during first login.
    POST /api/retailer-auth/verify-otp/ - Step 2: Verify OTP (first login only)
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Step 2: Verify OTP for first login only.
        
        Request Body:
        {
            "otp_code": "1234"
        }
        
        Response (Success):
        {
            "message": "OTP verified successfully. You are now logged in.",
            "access": "JWT_TOKEN",
            "refresh": "REFRESH_TOKEN"
        }
        
        Response (Error - Invalid OTP):
        {
            "error": "Invalid OTP. Please try again."
        }
        """
        otp_code = request.data.get('otp_code')
        
        if not otp_code:
            return Response({
                'error': 'OTP code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find OTP by code (most recent one)
            otp_obj = OTP.objects.filter(otp_code=otp_code).latest('created_at')
            user = otp_obj.user
            
            # Check if OTP is expired
            if otp_obj.is_expired():
                return Response({
                    'error': 'Your OTP has expired. Please login again to request a new OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # OTP verified successfully
            otp_obj.is_verified = True
            otp_obj.save()
            
            # Mark first login as completed
            user.first_login_otp_verified = True
            user.status = 'LOGIN_ENABLED'
            user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'OTP verified successfully. You are now logged in.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        except OTP.DoesNotExist:
            return Response({
                'error': 'Invalid OTP. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(APIView):
    """
    API endpoint for user registration.
    Only creates RETAILER accounts.
    POST /api/auth/register/ - Register a new retailer
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Register a new retailer. KYC will be submitted in a separate step after OTP verification."""
       
        registration_serializer = UserRegistrationSerializer(data=request.data)
        if not registration_serializer.is_valid():
            return Response(registration_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
       
        user = registration_serializer.save()
        user.status = 'REGISTERED'
        user.save()
        
      
        otp_obj = OTP.objects.filter(user=user).latest('created_at')
        
        # Generate and send OTP via email
        otp_code = otp_obj.generate_otp()
        
        try:
            send_mail(
                subject="Your Dream's Pharmacy Registration OTP",
                message=f'Your 4-digit OTP for registration verification is: {otp_code}\n\nThis OTP is valid for 30 seconds.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
        
        return Response({
            'message': 'Registration successful! 4-digit OTP sent to your email.',
            'otp_expires_in': 60,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone_number': user.phone_number,
            },
        }, status=status.HTTP_201_CREATED)


class OTPRequestView(APIView):
    """
    API endpoint for requesting OTP via email.
    POST /api/otp/request_otp/ - Request OTP for registration or login via email
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Request OTP for registration or login via email."""
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email, role='RETAILER')
            
            # Allow OTP request for REGISTERED (resend during registration), OTP_VERIFIED (resend during KYC), and APPROVED (login) users
            allowed_statuses = ['REGISTERED', 'OTP_VERIFIED', 'APPROVED']
            if user.status not in allowed_statuses:
                return Response({
                    'error': f'Your account status: {user.get_status_display()}. Cannot request OTP at this stage.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Generate and send OTP via email
            otp_obj = OTP.objects.create(user=user)
            otp_code = otp_obj.generate_otp()
            
            try:
                send_mail(
                    subject="Your Dream's Pharmacy Login OTP",
                    message=f'Your 4-digit OTP for login is: {otp_code}\n\nThis OTP is valid for 1 minute.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {e}")
            
            return Response({
                'message': 'OTP sent to your email successfully',
                'email': email,
                'otp_expires_in': 60,
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found with this email'
            }, status=status.HTTP_404_NOT_FOUND)


class OTPVerifyView(APIView):
    """
    API endpoint for verifying OTP.
    POST /api/otp/verify_otp/ - Verify OTP and update user status based on workflow stage
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Verify OTP and update user status based on workflow stage"""
        otp_code = request.data.get('otp_code')
        
        if not otp_code:
            return Response({
                'error': 'OTP code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find OTP by code (most recent one)
            otp_obj = OTP.objects.filter(otp_code=otp_code).latest('created_at')
            user = otp_obj.user
            
            # Check if OTP is expired
            if otp_obj.is_expired():
                return Response({
                    'error': 'Your OTP has expired. Please generate a new OTP to continue.',
                    'otp_expires_in': 0
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if otp_obj.otp_code == otp_code:
                otp_obj.is_verified = True
                otp_obj.save()
                
                
                if user.status == 'REGISTERED':
                    user.status = 'OTP_VERIFIED'
                    user.save()
                    return Response({
                        'message': 'Your OTP has been verified. Please submit your KYC to continue.',
                        'otp_expires_in': otp_obj.get_expiry_time_remaining(),
                        'user': CustomUserSerializer(user).data,
                    }, status=status.HTTP_200_OK)
                
                
                elif user.status == 'APPROVED':
                    user.status = 'LOGIN_ENABLED'
                    user.save()
                    
                    refresh = RefreshToken.for_user(user)
                    
                    return Response({
                        'message': 'OTP verified successfully. You are now logged in.',
                        'otp_expires_in': otp_obj.get_expiry_time_remaining(),
                        'user': CustomUserSerializer(user).data,
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    }, status=status.HTTP_200_OK)
                
                else:
                    return Response({
                        'error': f'Cannot verify OTP. User status is {user.get_status_display()}. Expected REGISTERED or APPROVED.',
                        'otp_expires_in': otp_obj.get_expiry_time_remaining()
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': 'Invalid OTP',
                    'otp_expires_in': otp_obj.get_expiry_time_remaining()
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except OTP.DoesNotExist:
            return Response({
                'error': 'Invalid OTP. Please check and try again'
            }, status=status.HTTP_400_BAD_REQUEST)


class KYCSubmitView(APIView):
    """
    API endpoint for KYC submission with user ID in URL path.
    POST /api/kyc/submit/<user_id>/ - Submit KYC documents for approval
    Example: POST /api/kyc/submit/28/
    """
    permission_classes = [AllowAny]
    
    def post(self, request, user_id=None):
        """Submit KYC documents. User must have verified OTP first."""
        
        if request.user.is_authenticated:
            user = request.user
        else:
            if not user_id:
                return Response({
                    'error': 'User ID required in URL. Example: /api/kyc/submit/28/'
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'error': f'User with ID {user_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if user.role != 'RETAILER':
            return Response({
                'error': 'Only retailers can submit KYC'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if KYC already submitted FIRST
        if hasattr(user, 'kyc'):
            return Response({
                'error': 'KYC already submitted for this user',
                'kyc_status': user.kyc.status,
                'kyc': KYCSerializer(user.kyc).data
            }, status=status.HTTP_400_BAD_REQUEST)
       
        if user.status != 'OTP_VERIFIED':
            return Response({
                'error': f'You must verify OTP first before submitting KYC. Current status: {user.get_status_display()}',
                'workflow_stage': user.status,
                'next_step': 'Verify OTP at /api/otp/verify_otp/'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = KYCSubmitSerializer(data=request.data)
        if serializer.is_valid():
            kyc = KYC.objects.create(user=user, **serializer.validated_data)
            
           
            user.status = 'PENDING_APPROVAL'
            user.save()
            
            return Response({
                'message': 'KYC submitted successfully! Awaiting admin approval.',
                'workflow_stage': 'PENDING_APPROVAL',
                'kyc_status': kyc.get_status_display(),
                'kyc': KYCSerializer(kyc).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email, role='RETAILER')
        # Generate and save OTP
        otp_obj = OTP.objects.create(user=user)
        otp_code = otp_obj.generate_otp()
        # Send OTP via email
        try:
            send_mail(
                subject="Dream's Pharmacy Password Reset OTP",
                message=f'Your OTP for password reset is: {otp_code}\n\nThis OTP is valid for 1 minute.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({"error": f"Failed to send email: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)

class ResetOTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "OTP verified. You can now reset your password."}, status=status.HTTP_200_OK)

class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data['user']
        otp_obj = serializer.validated_data['otp_obj']
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        otp_obj.is_verified = True
        otp_obj.save()
        return Response({"message": "Password reset successful. You can now log in with your new password."}, status=status.HTTP_200_OK)
from django.contrib.auth import get_user_model
User = get_user_model()

class ChangePasswordView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request, user_id):
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)

            if not user.check_password(serializer.validated_data['oldpassword']):
                return Response({"oldpassword": "Old password incorrect"}, status=400)

            user.set_password(serializer.validated_data['newpassword'])
            user.save()

            return Response({"message": "Password changed successfully"})

        return Response(serializer.errors, status=400)


class SuperAdminChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'SUPERADMIN':
            return Response({"error": "Only Super Admins can change password here."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['oldpassword']):
                return Response(
                    {"oldpassword": "Old password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if serializer.validated_data['oldpassword'] == serializer.validated_data['newpassword']:
                return Response(
                    {"newpassword": "New password cannot be the same as old password."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['newpassword'])
            user.save()
            return Response(
                {"message": "Password changed successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HomeView(APIView):
    """
    Home endpoint for authenticated users.
    GET /api/home/ - Get welcome message with user details
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "message": f"Welcome {user.username}!",
            "email": user.email,
            "user_id": user.id,
            "role": user.role,
            "status": user.get_status_display()
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            logout(request)
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

