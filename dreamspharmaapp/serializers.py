from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import KYC, OTP
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'email', 'role', 'status', 'created_at']
        read_only_fields = ['id', 'created_at', 'status']


class SuperAdminLoginSerializer(serializers.Serializer):
    """Serializer for SuperAdmin login"""
    username = serializers.CharField(required=True, help_text="Username or email")
    password = serializers.CharField(write_only=True, required=True, help_text="Password")
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        # Try to find user by username or email with SUPERADMIN role
        user = None
        try:
            user = User.objects.get(username=username, role='SUPERADMIN')
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username, role='SUPERADMIN')
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid username or email. No Super Admin account found")
        
        # Authenticate the user with the correct username
        authenticated_user = authenticate(username=user.username, password=password)
        if authenticated_user is None:
            raise serializers.ValidationError("Incorrect password")
        
        # Check if user is actually a superadmin
        if authenticated_user.role != 'SUPERADMIN':
            raise serializers.ValidationError("Only superadmin accounts can login here")
        
        data['user'] = authenticated_user
        return data


class RetailerLoginSerializer(serializers.Serializer):
    """Serializer for Retailer login with email and password"""
    email = serializers.EmailField(required=True, help_text="Registered email", error_messages={
        'required': 'Email is required',
        'invalid': 'Enter a valid email address',
        'blank': 'Email cannot be blank'
    })
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=8,
        help_text="Password",
        error_messages={
            'required': 'Password is required',
            'blank': 'Password cannot be blank',
            'max_length': 'Password too long',
            'min_length': 'Password must be at least 8 characters'
        }
    )
    
    def validate_email(self, value):
        """Validate email exists and belongs to a retailer"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Email cannot be empty")
        
        # Check if email format is valid
        if '@' not in value or '.' not in value:
            raise serializers.ValidationError("Enter a valid email address")
        
        return value.lower()
    
    def validate_password(self, value):
        """Validate password is not empty and has minimum length"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Password cannot be empty")
        
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        
        return value
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Email and password are required")
        
        # Try to find user by email with RETAILER role
        try:
            user = User.objects.get(email=email, role='RETAILER')
        except User.DoesNotExist:
            raise serializers.ValidationError("Email is not registered or not a retailer account")
        
        # Check if user is approved by admin or login enabled
        if user.status not in ['APPROVED', 'LOGIN_ENABLED']:
            raise serializers.ValidationError(
                f"Your account status is {user.get_status_display()}. Only APPROVED or LOGIN ENABLED accounts can login."
            )
        
        # Check if user has submitted KYC
        if not hasattr(user, 'kyc'):
            raise serializers.ValidationError(
                "KYC not submitted. Please submit your KYC documents first."
            )
        
        # Check if KYC is approved by admin
        if user.kyc.status != 'APPROVED':
            raise serializers.ValidationError(
                f"Your KYC status is {user.kyc.get_status_display()}. Only retailers with APPROVED KYC can login."
            )
        
        # Authenticate the user with password
        authenticated_user = authenticate(username=user.username, password=password)
        if authenticated_user is None:
            raise serializers.ValidationError("Password is incorrect. Please try again.")
        
        data['user'] = authenticated_user
        data['is_first_login'] = not authenticated_user.first_login_otp_verified
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    phone_number = serializers.CharField(required=True, min_length=10, max_length=15)

    class Meta:
        model = User
        fields = ['first_name', 'email', 'phone_number', 'password', 'password2']
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match"})

        email = data.get('email')
        phone_number = data.get('phone_number')

        if not email:
            raise serializers.ValidationError({"email": "Email is required"})
        if not phone_number:
            raise serializers.ValidationError({"phone_number": "Phone number is required"})

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email already exists"})
        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({"phone_number": "Phone number already exists"})

        # Optionally, add phone number format validation here
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        phone_number = validated_data.pop('phone_number', None)

        base_username = validated_data.get('first_name', 'user').lower()
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            password=validated_data['password'],
            phone_number=phone_number,
            role='RETAILER'
        )
        # Create OTP record for the user
        OTP.objects.create(user=user)
        return user


class KYCSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = KYC
        fields = [
            'id', 'username', 'shop_name', 'shop_address', 'shop_email', 'shop_phone',
            'customer_address', 'gst_number', 'drug_license_number',
            'drug_license', 'id_proof', 'store_photo', 'status', 
            'submitted_at', 'approved_at', 'rejection_reason'
        ]
        read_only_fields = ['id', 'submitted_at', 'approved_at', 'status']


class KYCSubmitSerializer(serializers.ModelSerializer):
    drug_license = serializers.FileField(required=True)
    id_proof = serializers.FileField(required=True)
    store_photo = serializers.FileField(required=True)
    
    class Meta:
        model = KYC
        fields = [
            'shop_name', 'shop_address', 'shop_email', 'shop_phone', 'customer_address',
            'gst_number', 'drug_license_number', 'drug_license',
            'id_proof', 'store_photo'
        ]


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value, role='RETAILER').exists():
            raise serializers.ValidationError("No retailer found with this email.")
        return value


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    otp_code = serializers.CharField(max_length=4)

    def validate(self, data):
        email = data.get('email')
        otp_code = data.get('otp_code')
        
        # If email is provided (forgot password flow), verify user by email
        if email:
            try:
                user = User.objects.get(email=email, role='RETAILER')
            except User.DoesNotExist:
                raise serializers.ValidationError({"email": "No retailer found with this email."})
            try:
                otp_obj = OTP.objects.filter(user=user, otp_code=otp_code, is_verified=False).latest('created_at')
            except OTP.DoesNotExist:
                raise serializers.ValidationError({"otp_code": "Invalid or expired OTP."})
        else:
            # No email provided (registration flow), find OTP by code only
            try:
                otp_obj = OTP.objects.filter(otp_code=otp_code, is_verified=False).latest('created_at')
                user = otp_obj.user
            except OTP.DoesNotExist:
                raise serializers.ValidationError({"otp_code": "Invalid or expired OTP."})
        
        if otp_obj.is_expired():
            raise serializers.ValidationError({"otp_code": "OTP has expired."})
        data['user'] = user
        data['otp_obj'] = otp_obj
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=4)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        # Reuse OTP validation
        otp_serializer = OTPVerifySerializer(data={
            'email': data['email'],
            'otp_code': data['otp_code']
        })
        otp_serializer.is_valid(raise_exception=True)
        data['user'] = otp_serializer.validated_data['user']
        data['otp_obj'] = otp_serializer.validated_data['otp_obj']
        return data


class ChangePasswordSerializer(serializers.Serializer):
    oldpassword = serializers.CharField(write_only=True, required=True)
    newpassword = serializers.CharField(write_only=True, required=True)
    confirmpassword = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['newpassword'] != data['confirmpassword']:
            raise serializers.ValidationError(
                {"confirmpassword": "New password and confirm password do not match."}
            )
        if data['oldpassword'] == data['newpassword']:
            raise serializers.ValidationError(
                {"newpassword": "New password cannot be the same as old password."}
            )
        return data



