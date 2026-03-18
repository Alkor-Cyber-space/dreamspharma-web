from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, logout
from django.shortcuts import get_object_or_404
from django.utils import timezone
from dreamspharmaapp.models import KYC, SalesOrder, Brand, ItemMaster, ProductInfo
from .serializers import (
    RetailerKYCDetailSerializer, ApproveKYCSerializer, RejectKYCSerializer, DashboardStatisticsSerializer, ChangePasswordSerializer, SuperAdminProfileSerializer, SuperAdminProfileImageSerializer, AddCategorySerializer
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class SuperAdminGetAllRetailersView(APIView):
    """
    API endpoint for superadmin to get all retailers' KYC plus registration details.
    GET /api/superadmin/retailers/ - Get all retailers' KYC and registration details
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all retailers with their KYC and registration details"""
        # Check if user is a superadmin
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only Super Admin can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all retailers with KYC submitted
        retailers_kyc = KYC.objects.select_related('user').all().order_by('-submitted_at')
        
        if not retailers_kyc.exists():
            return Response({
                'message': 'No retailers with KYC found',
                'count': 0,
                'results': []
            }, status=status.HTTP_200_OK)
        
        serializer = RetailerKYCDetailSerializer(retailers_kyc, many=True)
        
        return Response({
            'message': 'All retailers KYC and registration details',
            'count': retailers_kyc.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class ApproveKYCView(APIView):
    """
    API endpoint for superadmin to approve KYC.
    POST /api/superadmin/kyc/approve/<user_id>/ - Approve a retailer's KYC
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Approve KYC for a retailer"""
        # Check if user is a superadmin
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only Super Admin can approve KYC'
            }, status=status.HTTP_403_FORBIDDEN)
        
        data = {'user_id': user_id}
        serializer = ApproveKYCSerializer(data=data)
        
        if serializer.is_valid():
            kyc = serializer.save()
            kyc_serializer = RetailerKYCDetailSerializer(kyc)
            
            return Response({
                'message': 'KYC approved successfully',
                'kyc': kyc_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Failed to approve KYC',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class RejectKYCView(APIView):
    """
    API endpoint for superadmin to reject KYC.
    POST /api/superadmin/kyc/reject/<user_id>/ - Reject a retailer's KYC with reason
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Reject KYC for a retailer"""
        # Check if user is a superadmin
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only Super Admin can reject KYC'
            }, status=status.HTTP_403_FORBIDDEN)
        
        data = {'user_id': user_id, **request.data}
        serializer = RejectKYCSerializer(data=data)
        
        if serializer.is_valid():
            kyc = serializer.save()
            kyc_serializer = RetailerKYCDetailSerializer(kyc)
            
            return Response({
                'message': 'KYC rejected successfully',
                'kyc': kyc_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Failed to reject KYC',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DashboardStatisticsView(APIView):
    """
    API endpoint for superadmin to get dashboard statistics.
    GET /api/superadmin/dashboard/statistics/ - Get dashboard statistics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard statistics for superadmin"""
        # Check if user is a superadmin
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only Super Admin can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Calculate statistics
        total_retailers = User.objects.filter(role='RETAILER').count()
        pending_kyc = KYC.objects.filter(status='PENDING').count()
        total_orders = SalesOrder.objects.count()
        
        # Prepare data
        stats_data = {
            'total_retailers': total_retailers,
            'pending_kyc': pending_kyc,
            'total_orders': total_orders,
        }
        
        serializer = DashboardStatisticsSerializer(stats_data)
        
        return Response({
            'message': 'Dashboard statistics fetched successfully',
            'statistics': serializer.data
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    API endpoint for super admin to change password.
    POST /api/superadmin/change-password/ - Change password for logged-in super admin
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change password for super admin"""
        # Check if user is a superadmin
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only Super Admin can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                serializer.save(user=request.user)
                return Response({
                    'message': 'Password changed successfully'
                }, status=status.HTTP_200_OK)
            except serializers.ValidationError as e:
                return Response({
                    'error': str(e.detail[0])
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'error': 'Password change failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class GetSuperAdminProfileView(APIView):
    """
    API endpoint for super admin to get profile information.
    GET /api/superadmin/profile/ - Get super admin profile info (username, email, phone, image)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get profile information for super admin"""
        # Check if user is a superadmin
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only Super Admin can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SuperAdminProfileSerializer(request.user)
        
        return Response({
            'message': 'Profile information fetched successfully',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)


class ProfileImageView(APIView):
    """
    Profile Image Management - Upload and Delete
    POST: Upload profile image
    DELETE: Delete profile image
    """
    permission_classes = [IsAuthenticated]

    def _check_superadmin(self, request):
        """Check if user is SUPERADMIN"""
        return request.user.role == 'SUPERADMIN'

    def post(self, request):
        """Upload profile image for super admin"""
        if request.user.role != 'SUPERADMIN':
            return Response({
                'code': '403',
                'type': 'uploadProfileImage',
                'message': 'Forbidden - Only SUPERADMIN can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SuperAdminProfileImageSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"[PROFILE_IMAGE_UPLOADED] User: {request.user.username}")
                
                return Response({
                    'code': '200',
                    'type': 'uploadProfileImage',
                    'message': 'Profile image uploaded successfully',
                    'data': {
                        'profile_image': serializer.data['profile_image']
                    }
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error uploading profile image: {str(e)}")
                return Response({
                    'code': '500',
                    'type': 'uploadProfileImage',
                    'message': f'Error uploading image: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'code': '400',
            'type': 'uploadProfileImage',
            'message': 'Image upload failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Update profile image for super admin"""
        if request.user.role != 'SUPERADMIN':
            return Response({
                'code': '403',
                'type': 'updateProfileImage',
                'message': 'Forbidden - Only SUPERADMIN can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SuperAdminProfileImageSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"[PROFILE_IMAGE_UPDATED] User: {request.user.username}")
                
                return Response({
                    'code': '200',
                    'type': 'updateProfileImage',
                    'message': 'Profile image updated successfully',
                    'data': {
                        'profile_image': serializer.data['profile_image']
                    }
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Error updating profile image: {str(e)}")
                return Response({
                    'code': '500',
                    'type': 'updateProfileImage',
                    'message': f'Error updating image: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'code': '400',
            'type': 'updateProfileImage',
            'message': 'Image update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete profile image for super admin"""
        if request.user.role != 'SUPERADMIN':
            return Response({
                'code': '403',
                'type': 'deleteProfileImage',
                'message': 'Forbidden - Only SUPERADMIN can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not request.user.profile_image:
            return Response({
                'code': '404',
                'type': 'deleteProfileImage',
                'message': 'No profile image found to delete'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            if request.user.profile_image.storage.exists(request.user.profile_image.name):
                request.user.profile_image.storage.delete(request.user.profile_image.name)
            
            request.user.profile_image = None
            request.user.save()
            
            logger.info(f"[PROFILE_IMAGE_DELETED] User: {request.user.username}")
            
            return Response({
                'code': '200',
                'type': 'deleteProfileImage',
                'message': 'Profile image deleted successfully'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error deleting profile image: {str(e)}")
            return Response({
                'code': '500',
                'type': 'deleteProfileImage',
                'message': f'Error deleting image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SuperAdminLogoutView(APIView):
    """
    API endpoint for super admin to logout.
    POST /api/superadmin/logout/ - Logout super admin
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout super admin"""
        # Check if user is a superadmin
        if request.user.role != 'SUPERADMIN':
            return Response({
                'error': 'Only Super Admin can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        logout(request)
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_205_RESET_CONTENT)


class AddCategoryView(APIView):
    """
    Brand/Category Management
    GET: List all categories or get by ID
    POST: Create a new category/brand
    PUT: Update existing category or create if not exists
    DELETE: Delete a category
    SUPERADMIN ONLY
    """
    permission_classes = [IsAuthenticated]
    
    def _check_superadmin(self, request):
        """Check if user is SUPERADMIN"""
        if getattr(request.user, 'role', None) != 'SUPERADMIN':
            return False
        return True
    
    def get(self, request, category_id=None):
        """Get all categories or specific category by ID"""
        if not self._check_superadmin(request):
            return Response({
                'code': '403',
                'type': 'getCategory',
                'message': 'Forbidden - Only SUPERADMIN can view categories'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            if category_id:
                # Get specific brand by ID from URL
                brand = Brand.objects.get(id=category_id)
                return Response({
                    'code': '200',
                    'type': 'getCategory',
                    'message': 'Brand retrieved successfully',
                    'data': {
                        'id': brand.id,
                        'name': brand.name,
                        'icon': request.build_absolute_uri(brand.logo.url) if brand.logo else None,
                        'is_active': brand.is_active,
                        'created_at': brand.created_at
                    }
                }, status=status.HTTP_200_OK)
            else:
                # Get all brands
                brands = Brand.objects.all().order_by('-created_at')
                brands_data = [{
                    'id': b.id,
                    'name': b.name,
                    'icon': request.build_absolute_uri(b.logo.url) if b.logo else None,
                    'is_active': b.is_active,
                    'created_at': b.created_at
                } for b in brands]
                
                return Response({
                    'code': '200',
                    'type': 'getCategory',
                    'message': f'Found {len(brands_data)} brands',
                    'count': len(brands_data),
                    'data': brands_data
                }, status=status.HTTP_200_OK)
        
        except Brand.DoesNotExist:
            return Response({
                'code': '404',
                'type': 'getCategory',
                'message': f'Brand with ID {category_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error retrieving category: {str(e)}")
            return Response({
                'code': '500',
                'type': 'getCategory',
                'message': f'Error retrieving category: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Create a new category/brand"""
        if not self._check_superadmin(request):
            return Response({
                'code': '403',
                'type': 'addCategory',
                'message': 'Forbidden - Only SUPERADMIN can add categories'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = AddCategorySerializer(data=request.data)
        if serializer.is_valid():
            try:
                brand = serializer.save()
                
                logger.info(f"[BRAND_CREATED] Name: {brand.name} | Created by: {request.user.username}")
                
                return Response({
                    'code': '200',
                    'type': 'addCategory',
                    'message': 'Brand created successfully',
                    'data': {
                        'id': brand.id,
                        'name': brand.name,
                        'icon': request.build_absolute_uri(brand.logo.url) if brand.logo else None,
                        'is_active': brand.is_active,
                        'created_at': brand.created_at
                    }
                }, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                logger.error(f"Error creating category: {str(e)}")
                return Response({
                    'code': '500',
                    'type': 'addCategory',
                    'message': f'Error creating category: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'code': '400',
            'type': 'addCategory',
            'message': 'Invalid parameters',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, category_id=None):
        """Update existing category - ID in URL"""
        if not self._check_superadmin(request):
            return Response({
                'code': '403',
                'type': 'updateCategory',
                'message': 'Forbidden - Only SUPERADMIN can update categories'
            }, status=status.HTTP_403_FORBIDDEN)
        
        name = request.data.get('name')
        
        # ID is required for PUT (update only)
        if not category_id:
            return Response({
                'code': '400',
                'type': 'updateCategory',
                'message': 'Category ID is required in URL. Use /add-category/{id}/'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not name:
            return Response({
                'code': '400',
                'type': 'updateCategory',
                'message': 'Category name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get existing brand
            brand = Brand.objects.get(id=category_id)
            old_name = brand.name
            
            # Only check for duplicates if name is being changed
            if name.lower() != old_name.lower():
                # Check if new name already exists (for other brands)
                if Brand.objects.filter(name__iexact=name).exclude(id=category_id).exists():
                    return Response({
                        'code': '400',
                        'type': 'updateCategory',
                        'message': f'Another brand with name "{name}" already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update brand
            brand.name = name
            brand.is_active = request.data.get('is_active', brand.is_active)
            
            if 'logo' in request.FILES:
                brand.logo = request.FILES['logo']
            
            brand.save()
            
            logger.info(f"[BRAND_UPDATED] ID: {category_id} | Old Name: {old_name} | New Name: {name} | Updated by: {request.user.username}")
            
            return Response({
                'code': '200',
                'type': 'updateCategory',
                'message': 'Brand updated successfully',
                'data': {
                    'id': brand.id,
                    'name': brand.name,
                    'icon': request.build_absolute_uri(brand.logo.url) if brand.logo else None,
                    'is_active': brand.is_active,
                    'created_at': brand.created_at
                }
            }, status=status.HTTP_200_OK)
        
        except Brand.DoesNotExist:
            return Response({
                'code': '404',
                'type': 'updateCategory',
                'message': f'Brand with ID {category_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error updating category: {str(e)}")
            return Response({
                'code': '500',
                'type': 'updateCategory',
                'message': f'Error updating category: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, category_id=None):
        """Delete a category - ID in URL"""
        if not self._check_superadmin(request):
            return Response({
                'code': '403',
                'type': 'deleteCategory',
                'message': 'Forbidden - Only SUPERADMIN can delete categories'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ID is required in URL
        if not category_id:
            return Response({
                'code': '400',
                'type': 'deleteCategory',
                'message': 'Category ID is required in URL. Use /add-category/{id}/'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            brand = Brand.objects.get(id=category_id)
            brand_name = brand.name
            
            # Check if brand is used in any products
            if ProductInfo.objects.filter(brand_id=category_id).exists():
                return Response({
                    'code': '409',
                    'type': 'deleteCategory',
                    'message': f'Cannot delete brand "{brand_name}" - it is assigned to {ProductInfo.objects.filter(brand_id=category_id).count()} product(s)'
                }, status=status.HTTP_409_CONFLICT)
            
            brand.delete()
            
            logger.info(f"[BRAND_DELETED] ID: {category_id} | Name: {brand_name} | Deleted by: {request.user.username}")
            
            return Response({
                'code': '200',
                'type': 'deleteCategory',
                'message': f'Brand "{brand_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
        
        except Brand.DoesNotExist:
            return Response({
                'code': '404',
                'type': 'deleteCategory',
                'message': f'Brand with ID {category_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error deleting category: {str(e)}")
            return Response({
                'code': '500',
                'type': 'deleteCategory',
                'message': f'Error deleting category: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AssignBrandToProductView(APIView):
    """
    Assign brand/category to a product
    POST/PUT: Assign brand to product
    SUPERADMIN ONLY
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Assign brand to product"""
        # Check if user is SUPERADMIN
        if getattr(request.user, 'role', None) != 'SUPERADMIN':
            return Response({
                'code': '403',
                'type': 'assignBrandToProduct',
                'message': 'Forbidden - Only SUPERADMIN can assign brands to products'
            }, status=status.HTTP_403_FORBIDDEN)
        
        item_code = request.data.get('c_item_code')
        brand_id = request.data.get('brand_id')
        
        if not item_code or not brand_id:
            return Response({
                'code': '400',
                'type': 'assignBrandToProduct',
                'message': 'c_item_code and brand_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the item
            item = ItemMaster.objects.get(item_code=item_code)
            
            # Get or create ProductInfo
            product_info, created = ProductInfo.objects.get_or_create(item=item)
            
            # Get the brand/category
            brand = Brand.objects.get(id=brand_id)
            
            # Assign brand to product
            product_info.brand = brand
            product_info.save()
            
            logger.info(f"[BRAND_ASSIGNED] Item: {item_code} | Brand: {brand.name} | Brand ID: {brand_id} | Assigned by: {request.user.username}")
            
            return Response({
                'code': '200',
                'type': 'assignBrandToProduct',
                'message': 'Brand assigned to product successfully',
                'data': {
                    'c_item_code': item_code,
                    'brand_id': brand.id,
                    'brand_name': brand.name,
                    'brand_logo': request.build_absolute_uri(brand.logo.url) if brand.logo else ''
                }
            }, status=status.HTTP_200_OK)
        
        except ItemMaster.DoesNotExist:
            return Response({
                'code': '404',
                'type': 'assignBrandToProduct',
                'message': f'Item with code {item_code} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Brand.DoesNotExist:
            return Response({
                'code': '404',
                'type': 'assignBrandToProduct',
                'message': f'Brand with ID {brand_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error assigning brand to product: {str(e)}")
            return Response({
                'code': '500',
                'type': 'assignBrandToProduct',
                'message': f'Error assigning brand: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        """PUT method - same as POST"""
        return self.post(request)
