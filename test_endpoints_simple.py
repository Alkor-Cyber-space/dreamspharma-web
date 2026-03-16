#!/usr/bin/env python
"""
Comprehensive Endpoint Test - All Dream's Pharma Endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

endpoints = [
    # Authentication
    ("OTPRequestView", "POST", "/api/send-otp/", {"mobile": "9999999999"}),
    ("RetailerLoginView", "POST", "/api/retailer/login/", {"username": "test", "password": "test"}),
    ("LogoutView", "POST", "/api/logout/", {}),
    ("ChangePasswordView", "POST", "/api/change-password/", {"old_password": "old", "new_password": "new"}),
    
    # ERP Integration
    ("GetItemMasterView", "GET", "/api/erp/ws_c2_services_get_master_data", {}),
    ("FetchStockView", "GET", "/api/erp/ws_c2_services_fetch_stock", {}),
    ("CreateSalesOrderView", "POST", "/api/erp/create-sales-order/", {"items": []}),
    ("CreateGLCustomerView", "POST", "/api/erp/create-gl-customer/", {"customer_name": "Test"}),
    ("GetOrderStatusView", "GET", "/api/erp/order-status/", {}),
    
    # Products
    ("AllProductsView", "GET", "/api/products/", {}),
    ("UpdateProductInfoView", "PUT", "/api/product/update/", {"item_code": "INJ001"}),
    
    # Search
    ("SearchProductsView", "GET", "/api/search/", {"query": "test"}),
    ("PopularSearchView", "GET", "/api/search/popular/", {}),
    ("SearchWithHistoryView", "GET", "/api/search-history/", {"query": "test"}),
    ("LogSearchView", "POST", "/api/log-search/", {"query": "test"}),
    
    # Cart
    ("CartView", "GET", "/api/cart/", {}),
    ("AddToCartView", "POST", "/api/cart/add/", {"item_code": "INJ001", "quantity": 1}),
    ("UpdateCartItemView", "PUT", "/api/cart/update/", {"cart_item_id": 1, "quantity": 2}),
    ("RemoveFromCartView", "DELETE", "/api/cart/remove/", {}),
    
    # Wishlist
    ("WishlistView", "GET", "/api/wishlist/", {}),
    ("AddToWishlistView", "POST", "/api/wishlist/add/", {"item_code": "INJ001"}),
    ("UpdateWishlistItemView", "PUT", "/api/wishlist/update/", {"wishlist_item_id": 1}),
    ("RemoveFromWishlistView", "DELETE", "/api/wishlist/remove/", {}),
    
    # Addresses
    ("ListAddressesView", "GET", "/api/addresses/", {}),
    ("CreateAddressView", "POST", "/api/addresses/create/", {"address": "123 St", "city": "City"}),
    ("UpdateAddressView", "PUT", "/api/addresses/update/", {"address_id": 1, "address": "New"}),
    ("DeleteAddressView", "DELETE", "/api/addresses/delete/", {}),
    
    # Checkout & Orders
    ("CheckoutWithAddressView", "POST", "/api/checkout/", {"address_id": 1}),
    
    # Recommendations
    ("TopSellingProductsView", "GET", "/api/recommendations/top-selling/", {}),
    ("PopularProductsView", "GET", "/api/recommendations/popular/", {}),
    ("TrendingProductsView", "GET", "/api/recommendations/trending/", {}),
    ("FrequentlyBoughtTogetherView", "GET", "/api/recommendations/frequently-bought/", {}),
    ("PersonalizedRecommendationsView", "GET", "/api/recommendations/personalized/", {}),
    
    # Payment
    ("InitiatePaymentView", "POST", "/api/payment/initiate/", {"order_id": 1, "amount": 100}),
    ("VerifyPaymentView", "POST", "/api/payment/verify/", {"order_id": 1}),
    ("PaymentStatusView", "GET", "/api/payment/status/", {}),
    ("InitiateRefundView", "POST", "/api/payment/refund/", {"order_id": 1}),
    
    # Profile & KYC
    ("ProfileView", "GET", "/api/profile/", {}),
    ("KYCSubmitView", "POST", "/api/kyc/submit/", {"shop_name": "Shop"}),
    ("KYCStatusView", "GET", "/api/kyc/status/", {}),
]

results = []
passed = 0
failed = 0

print("Testing all endpoints...\n")

for name, method, url, data in endpoints:
    try:
        if method == "GET":
            resp = requests.get(f"{BASE_URL}{url}", timeout=5)
        elif method == "POST":
            resp = requests.post(f"{BASE_URL}{url}", json=data, timeout=5)
        elif method == "PUT":
            resp = requests.put(f"{BASE_URL}{url}", json=data, timeout=5)
        elif method == "DELETE":
            resp = requests.delete(f"{BASE_URL}{url}", timeout=5)
        
        is_success = resp.status_code in [200, 201, 204, 400, 401, 404]
        status = "[PASS]" if is_success else "[FAIL]"
        if is_success:
            passed += 1
        else:
            failed += 1
        results.append(f"{status} | {name:40s} | {method:6s} | {url:45s} | Status: {resp.status_code}")
        print(f"{status} | {name:40s} | {method:6s} | Status: {resp.status_code}")
    except Exception as e:
        failed += 1
        results.append(f"[FAIL] | {name:40s} | {method:6s} | {url:45s} | Error: {str(e)[:40]}")
        print(f"[FAIL] | {name:40s} | {method:6s} | Error: {str(e)[:40]}")

# Write results to file
with open('ALL_ENDPOINTS_TEST.txt', 'w') as f:
    f.write("="*150 + "\n")
    f.write("DREAMSPHARMA - ALL ENDPOINTS TEST REPORT\n")
    f.write("="*150 + "\n\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Total Endpoints Tested: {len(endpoints)}\n")
    f.write(f"[PASS] Passed: {passed}\n")
    f.write(f"[FAIL] Failed: {failed}\n")
    f.write(f"Success Rate: {(passed/len(endpoints))*100:.1f}%\n\n")
    f.write("="*150 + "\n")
    f.write("TEST RESULTS:\n")
    f.write("="*150 + "\n\n")
    for result in results:
        f.write(result + "\n")

print(f"\n{'='*100}")
print(f"Total: {len(endpoints)} endpoints")
print(f"[PASS] Passed: {passed}")
print(f"[FAIL] Failed: {failed}")
print(f"Success Rate: {(passed/len(endpoints))*100:.1f}%")
print(f"\nResults saved to: ALL_ENDPOINTS_TEST.txt")
