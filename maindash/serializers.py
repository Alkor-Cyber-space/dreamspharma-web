from rest_framework import serializers
from django.contrib.auth import get_user_model
from dreamspharmaapp.models import KYC
from django.utils import timezone

User = get_user_model()


class RetailerKYCDetailSerializer(serializers.ModelSerializer):
    """Serializer for combining retailer registration and KYC details"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    user_status = serializers.CharField(source='user.get_status_display', read_only=True)
    created_at = serializers.DateTimeField(source='user.created_at', read_only=True)
    
    class Meta:
        model = KYC
        fields = [
            'user_id', 'username', 'first_name', 'email', 'phone_number',
            'user_status', 'created_at',
            'id', 'shop_name', 'shop_address', 'shop_email', 'shop_phone',
            'customer_address', 'gst_number', 'drug_license_number',
            'drug_license', 'id_proof', 'store_photo', 'status', 
            'submitted_at', 'approved_at', 'rejection_reason'
        ]
        read_only_fields = ['id', 'submitted_at', 'approved_at']


class ApproveKYCSerializer(serializers.Serializer):
    """Serializer for approving KYC"""
    kyc_id = serializers.IntegerField(required=True, help_text="KYC ID to approve")
    
    def validate_kyc_id(self, value):
        """Check if KYC exists"""
        try:
            KYC.objects.get(id=value)
        except KYC.DoesNotExist:
            raise serializers.ValidationError(f"KYC with id {value} does not exist")
        return value
    
    def save(self):
        """Approve KYC and update user status"""
        kyc_id = self.validated_data.get('kyc_id')
        kyc = KYC.objects.get(id=kyc_id)
        
        # Update KYC status
        kyc.status = 'APPROVED'
        kyc.approved_at = timezone.now()
        kyc.save()
        
        # Update user status
        user = kyc.user
        user.status = 'APPROVED'
        user.is_kyc_approved = True
        user.save()
        
        return kyc


class RejectKYCSerializer(serializers.Serializer):
    """Serializer for rejecting KYC with reason"""
    kyc_id = serializers.IntegerField(required=True, help_text="KYC ID to reject")
    rejection_reason = serializers.CharField(
        required=True, 
        max_length=500,
        help_text="Reason for rejecting KYC"
    )
    
    def validate_kyc_id(self, value):
        """Check if KYC exists"""
        try:
            KYC.objects.get(id=value)
        except KYC.DoesNotExist:
            raise serializers.ValidationError(f"KYC with id {value} does not exist")
        return value
    
    def validate_rejection_reason(self, value):
        """Validate rejection reason is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Rejection reason cannot be empty")
        return value
    
    def save(self):
        """Reject KYC with reason and update user status"""
        kyc_id = self.validated_data.get('kyc_id')
        rejection_reason = self.validated_data.get('rejection_reason')
        kyc = KYC.objects.get(id=kyc_id)
        
        # Update KYC status
        kyc.status = 'REJECTED'
        kyc.rejection_reason = rejection_reason
        kyc.save()
        
        # Update user status - revert to KYC_SUBMITTED
        user = kyc.user
        user.status = 'KYC_SUBMITTED'
        user.is_kyc_approved = False
        user.save()
        
        return kyc


        
