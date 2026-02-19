from django.urls import path
from . import views

urlpatterns = [
    # SuperAdmin - Get all retailers KYC and registration details
    path('superadmin/retailers/', views.SuperAdminGetAllRetailersView.as_view(), name='superadmin-get-all-retailers'),
    
    # SuperAdmin - Approve KYC
    path('superadmin/kyc/approve/', views.ApproveKYCView.as_view(), name='superadmin-approve-kyc'),
    
    # SuperAdmin - Reject KYC
    path('superadmin/kyc/reject/', views.RejectKYCView.as_view(), name='superadmin-reject-kyc'),
]
