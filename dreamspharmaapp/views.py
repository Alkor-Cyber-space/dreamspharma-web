from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
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
    KYCSubmitSerializer
)

User = get_user_model()


class SuperAdminLoginView(viewsets.ViewSet):
    """
    API endpoint for superadmin login.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Login with username/email and password"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username, role='SUPERADMIN')
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username, role='SUPERADMIN')
            except User.DoesNotExist:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = authenticate(username=user.username, password=password)
        if user is None:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only superadmins can login here'
            }, status=status.HTTP_403_FORBIDDEN)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': CustomUserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class UserRegistrationView(viewsets.ViewSet):
    """
    API endpoint for user registration.
    Only creates RETAILER accounts.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
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
                message=f'Your 6-digit OTP for registration verification is: {otp_code}\n\nThis OTP is valid for 10 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
        
        return Response({
            'message': 'Registration successful! 6-digit OTP sent to your email.',
            'otp_expires_in': 30,
            'user': {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'email': user.email,
                'role': user.role,
                'status': user.status,
            },
        }, status=status.HTTP_201_CREATED)


class OTPManagementView(viewsets.ViewSet):
    """
    API endpoints for OTP generation and verification via EMAIL or PHONE.
    """
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def request_otp(self, request):
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
                    message=f'Your 6-digit OTP for login is: {otp_code}\n\nThis OTP is valid for 10 minutes.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {e}")
            
            return Response({
                'message': 'OTP sent to your email successfully',
                'email': email,
                'otp_expires_in': 30,
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found with this email'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_otp(self, request):
        """Verify OTP and update user status based on workflow stage"""
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')
        
        if not email or not otp_code:
            return Response({
                'error': 'Email and OTP code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email, role='RETAILER')
            otp_obj = OTP.objects.filter(user=user).latest('created_at')
            
            # Check if OTP is expired
            if otp_obj.is_expired():
                return Response({
                    'error': 'Your OTP has expired Please generate a new OTP to continue.',
                    'otp_expires_in': 0
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if otp_obj.otp_code == otp_code:
                otp_obj.is_verified = True
                otp_obj.save()
                
                
                if user.status == 'REGISTERED':
                    user.status = 'OTP_VERIFIED'
                    user.save()
                    return Response({
                        'message': 'Your OTP has been verified Please submit your KYC to continue.',
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
        
        except (User.DoesNotExist, OTP.DoesNotExist):
            return Response({
                'error': 'Please check your email and OTP, then try again'
            }, status=status.HTTP_400_BAD_REQUEST)


class KYCManagementView(viewsets.ViewSet):
    """
    API endpoints for KYC submission and management.
    Retailers submit KYC, SuperAdmins approve/reject.
    """
    
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def submit_kyc(self, request, pk=None):
        """Submit KYC documents. User must have verified OTP first. URL: /api/kyc/submit_kyc/{user_id}/"""
        # Get user from URL parameter or JWT token
        user_id = pk
        
        if request.user.is_authenticated:
            user = request.user
        else:
            if not user_id:
                return Response({
                    'error': 'User ID required in URL. Format: /api/kyc/submit_kyc/{user_id}/'
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        if user.role != 'RETAILER':
            return Response({
                'error': 'Only retailers can submit KYC'
            }, status=status.HTTP_403_FORBIDDEN)
       
        if user.status != 'OTP_VERIFIED':
            return Response({
                'error': f'You must verify OTP first before submitting KYC. Current status: {user.get_status_display()}',
                'workflow_stage': user.status,
                'next_step': 'Verify OTP at /api/otp/verify_otp/'
            }, status=status.HTTP_403_FORBIDDEN)
      
        if hasattr(user, 'kyc'):
            return Response({
                'error': 'KYC already submitted. Status: ' + user.kyc.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = KYCSubmitSerializer(data=request.data)
        if serializer.is_valid():
            kyc = KYC.objects.create(user=user, **serializer.validated_data)
            
           
            user.status = 'PENDING_APPROVAL'
            user.save()
            
            return Response({
                'message': 'KYC submitted successfully! Awaiting admin approval.',
                'workflow_stage': 'PENDING_APPROVAL',
                'user_status': user.get_status_display(),
                'kyc': KYCSerializer(kyc).data,
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_kyc(self, request):
        """Get current user's KYC status"""
        try:
            kyc = KYC.objects.get(user=request.user)
            return Response(KYCSerializer(kyc).data, status=status.HTTP_200_OK)
        except KYC.DoesNotExist:
            return Response({
                'message': 'KYC not submitted yet'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending_kyc(self, request):
        """SuperAdmin: Get all pending KYCs"""
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only superadmins can view pending KYCs'
            }, status=status.HTTP_403_FORBIDDEN)
        
        pending_kycs = KYC.objects.filter(status='PENDING')
        serializer = KYCSerializer(pending_kycs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def approve_kyc(self, request):
        """SuperAdmin: Approve KYC"""
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only superadmins can approve KYCs'
            }, status=status.HTTP_403_FORBIDDEN)
        
        kyc_id = request.data.get('kyc_id')
        if not kyc_id:
            return Response({
                'error': 'kyc_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            kyc = KYC.objects.get(id=kyc_id)
            kyc.status = 'APPROVED'
            kyc.approved_at = timezone.now()
            kyc.save()
            
         
            kyc.user.is_kyc_approved = True
           
            kyc.user.status = 'APPROVED'
            kyc.user.save()
            
            return Response({
                'message': 'KYC approved successfully. User can now login with OTP.',
                'workflow_stage': 'APPROVED',
                'user_status': kyc.user.get_status_display(),
                'next_step': 'User can now request OTP for login at /api/otp/request_otp/',
                'kyc': KYCSerializer(kyc).data,
                'user': CustomUserSerializer(kyc.user).data
            }, status=status.HTTP_200_OK)
        
        except KYC.DoesNotExist:
            return Response({
                'error': 'KYC not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def reject_kyc(self, request):
        """SuperAdmin: Reject KYC"""
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only superadmins can reject KYCs'
            }, status=status.HTTP_403_FORBIDDEN)
        
        kyc_id = request.data.get('kyc_id')
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not kyc_id:
            return Response({
                'error': 'kyc_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            kyc = KYC.objects.get(id=kyc_id)
            kyc.status = 'REJECTED'
            kyc.rejection_reason = rejection_reason
            kyc.save()
            
            return Response({
                'message': 'KYC rejected',
                'kyc': KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)
        
        except KYC.DoesNotExist:
            return Response({
                'error': 'KYC not found'
            }, status=status.HTTP_404_NOT_FOUND)

