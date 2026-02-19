from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, FileExtensionValidator
import random
import string

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('SUPERADMIN', 'Super Admin'),
        ('RETAILER', 'Retailer'),
    )
    
    STATUS_CHOICES = (
        ('REGISTERED', 'Registered'),
        ('OTP_VERIFIED', 'OTP Verified'),
        ('KYC_SUBMITTED', 'KYC Submitted'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved (by SuperAdmin)'),
        ('LOGIN_ENABLED', 'Login Enabled'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='RETAILER')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True, validators=[
        RegexValidator(r'^\d{10,15}$', 'Phone number must be 10-15 digits')
    ])

    is_kyc_approved = models.BooleanField(default=False)
    first_login_otp_verified = models.BooleanField(default=False, help_text="Tracks if user has completed first login OTP verification")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(email__isnull=False) | models.Q(phone_number__isnull=False),
                name='email_or_phone_required'
            )
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
       
        if self.is_superuser and self.role != 'SUPERADMIN':
            self.role = 'SUPERADMIN'
        elif not self.is_superuser and self.role == 'SUPERADMIN':
          
            self.role = 'RETAILER'
        super().save(*args, **kwargs)


class KYC(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='kyc')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
  
    shop_name = models.CharField(max_length=200)
    shop_address = models.TextField()
    shop_email = models.EmailField(blank=True, null=True)
    shop_phone = models.CharField(max_length=15, validators=[
        RegexValidator(r'^\d{10,15}$', 'Phone number must be 10-15 digits')
    ], blank=True, null=True)
    
  
    customer_address = models.TextField()
    
    
    gst_number = models.CharField(max_length=20, unique=True)
    drug_license_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
  
    drug_license = models.FileField(
        upload_to='kyc/drug_licenses/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    id_proof = models.FileField(
        upload_to='kyc/id_proofs/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Aadhaar or other valid ID'
    )
    store_photo = models.FileField(
        upload_to='kyc/store_photos/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text='Front view of store - direct camera picture or document (PDF, JPG, JPEG, PNG)'
    )
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"KYC - {self.user.username} ({self.status})"


class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=4)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    OTP_EXPIRY_TIME = 60  # 60 seconds (1 minute)
    
    def is_expired(self):
        """Check if OTP has expired (5 minutes)"""
        from django.utils import timezone
        expiry_time = self.created_at + timezone.timedelta(seconds=self.OTP_EXPIRY_TIME)
        return timezone.now() > expiry_time
    
    def get_expiry_time_remaining(self):
        """Get remaining time in seconds before OTP expires"""
        from django.utils import timezone
        expiry_time = self.created_at + timezone.timedelta(seconds=self.OTP_EXPIRY_TIME)
        remaining = (expiry_time - timezone.now()).total_seconds()
        return max(0, int(remaining))
    
    def generate_otp(self):
        self.otp_code = ''.join(random.choices(string.digits, k=4))
        self.email = self.user.email
        self.is_verified = False
        self.save()
        return self.otp_code
    
    def __str__(self):
        return f"OTP - {self.email}"



