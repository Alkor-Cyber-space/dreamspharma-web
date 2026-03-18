"""
ERP Token Service - Handles automatic token generation and caching
No manual token generation needed - this service runs in the background
"""

import logging
import base64
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .models import APIToken

logger = logging.getLogger(__name__)

# Cache key for ERP token
ERP_TOKEN_CACHE_KEY = 'erp_api_token'
ERP_TOKEN_EXPIRY_CACHE_KEY = 'erp_api_token_expiry'


def generate_erp_token_from_server():
    """
    [TARGET] Generate ERP token by calling the ERP server
    Returns: token string or None
    """
    try:
        erp_url = f"{settings.ERP_BASE_URL}/ws_c2_services_generate_token"
        
        payload = {
            "c2Code": settings.ERP_C2_CODE,
            "storeId": settings.ERP_STORE_ID,
            "prodCode": settings.ERP_PROD_CODE,
            "securityKey": settings.ERP_SECURITY_KEY
        }
        
        logger.info(f"[ERP_TOKEN] [REFRESH] Generating new token from ERP server...")
        logger.info(f"[ERP_TOKEN] Request URL: {erp_url}")
        
        response = requests.post(erp_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '200' and data.get('apiKey'):
                token = data.get('apiKey')
                logger.info(f"[ERP_TOKEN] [SUCCESS] Token generated successfully!")
                return token
            else:
                logger.error(f"[ERP_TOKEN] [FAILED] ERP returned error: {data.get('message')}")
                return None
        else:
            logger.error(f"[ERP_TOKEN] [FAILED] ERP Server error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"[ERP_TOKEN] [FAILED] Connection timeout - ERP server not responding")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"[ERP_TOKEN] [FAILED] Connection error - Failed to reach ERP server at {settings.ERP_BASE_URL}")
        return None
    except Exception as e:
        logger.error(f"[ERP_TOKEN] [FAILED] Error generating token: {str(e)}")
        return None


def get_cached_erp_token():
    """
    [TARGET] Get ERP token from cache, generate if expired or not found
    Returns: token string or None
    """
    # Try to get from cache first
    cached_token = cache.get(ERP_TOKEN_CACHE_KEY)
    cached_expiry = cache.get(ERP_TOKEN_EXPIRY_CACHE_KEY)
    
    if cached_token and cached_expiry:
        # Check if token is still valid (with 1 hour buffer)
        expiry_time = datetime.fromisoformat(cached_expiry)
        if timezone.now() < (expiry_time - timedelta(hours=1)):
            logger.info(f"[ERP_TOKEN] [SUCCESS] Using cached token (valid until {cached_expiry})")
            return cached_token
    
    # Token not in cache or expired - generate new one
    logger.info(f"[ERP_TOKEN] [NOTE] Token not found in cache or expired. Generating new token...")
    token = generate_erp_token_from_server()
    
    if token:
        # Cache for 24 hours (ERP tokens typically valid for 24 hours)
        cache_timeout = 24 * 60 * 60  # 24 hours in seconds
        new_expiry = timezone.now() + timedelta(hours=24)
        
        cache.set(ERP_TOKEN_CACHE_KEY, token, cache_timeout)
        cache.set(ERP_TOKEN_EXPIRY_CACHE_KEY, new_expiry.isoformat(), cache_timeout)
        
        logger.info(f"[ERP_TOKEN] [DB] Token cached for 24 hours")
        return token
    
    logger.error(f"[ERP_TOKEN] [FAILED] Failed to generate new token")
    return None


def save_token_to_db(token):
    """
    [DB] Save token to database for backup/audit purposes
    """
    try:
        api_token, created = APIToken.objects.get_or_create(
            c2_code=settings.ERP_C2_CODE,
            defaults={
                'store_id': settings.ERP_STORE_ID,
                'prod_code': settings.ERP_PROD_CODE,
                'security_key': settings.ERP_SECURITY_KEY,
                'api_key': token,
                'is_active': True
            }
        )
        
        if not created:
            # Update existing token
            api_token.api_key = token
            api_token.is_active = True
            api_token.save()
            logger.info(f"[ERP_TOKEN] [DB] Updated token in database")
        else:
            logger.info(f"[ERP_TOKEN] [DB] Created new token record in database")
            
    except Exception as e:
        logger.error(f"[ERP_TOKEN] [FAILED] Error saving token to DB: {str(e)}")


def refresh_erp_token():
    """
    [REFRESH] Background task - Refresh/regenerate ERP token periodically
    Call this from a scheduled task (APScheduler or Celery)
    
    Usage:
        # In apps.py ready() method or scheduled job:
        from .erp_token_service import refresh_erp_token
        refresh_erp_token()
    """
    logger.info(f"[ERP_TOKEN] [SCHEDULED] Starting scheduled token refresh...")
    
    token = generate_erp_token_from_server()
    
    if token:
        # Update cache
        cache_timeout = 24 * 60 * 60
        new_expiry = timezone.now() + timedelta(hours=24)
        
        cache.set(ERP_TOKEN_CACHE_KEY, token, cache_timeout)
        cache.set(ERP_TOKEN_EXPIRY_CACHE_KEY, new_expiry.isoformat(), cache_timeout)
        
        # Save to DB
        save_token_to_db(token)
        
        logger.info(f"[ERP_TOKEN] [SUCCESS] Token refresh completed successfully")
        return True
    else:
        logger.error(f"[ERP_TOKEN] [FAILED] Token refresh failed")
        return False


def get_erp_token_for_request():
    """
    [TARGET] MAIN FUNCTION - Get token for any ERP API request
    This is what views should call instead of asking frontend for token
    
    Returns: token string (never None - uses fallback logic)
    """
    # Try cache first
    token = get_cached_erp_token()
    if token:
        return token
    
    # Fallback: Check database for last known good token
    try:
        api_token_obj = APIToken.objects.filter(
            c2_code=settings.ERP_C2_CODE,
            is_active=True
        ).latest('created_at')
        
        if api_token_obj:
            logger.warning(f"[ERP_TOKEN] [WARNING] Using fallback token from database (cache miss)")
            return api_token_obj.api_key
    except APIToken.DoesNotExist:
        pass
    
    logger.critical(f"[ERP_TOKEN] [FAILED] CRITICAL ERROR: No valid token available!")
    return None


# ==================== INITIALIZATION ====================

def initialize_erp_token():
    """
    [INIT] Initialize ERP token on app startup
    Call this in apps.py ready() method
    
    Usage:
        class DreamspharmaappConfig(AppConfig):
            def ready(self):
                from .erp_token_service import initialize_erp_token
                initialize_erp_token()
    """
    logger.info(f"[ERP_TOKEN] [INIT] Initializing ERP token service...")
    
    token = get_cached_erp_token()
    if token:
        save_token_to_db(token)
        logger.info(f"[ERP_TOKEN] [SUCCESS] ERP token service initialized successfully")
    else:
        logger.error(f"[ERP_TOKEN] [FAILED] Failed to initialize ERP token")
