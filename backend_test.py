#!/usr/bin/env python3
import requests
import json
import uuid
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
import time

# Load environment variables from frontend/.env to get the backend URL
load_dotenv("/app/frontend/.env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test data
test_properties = [
    {
        "address": "123 Rue de Paris, 75001 Paris",
        "monthly_rent": 1200.0,
        "description": "Appartement 2 pièces au centre-ville",
        "status": "disponible"
    },
    {
        "address": "45 Avenue Victor Hugo, 69003 Lyon",
        "monthly_rent": 950.0,
        "description": "Studio rénové proche des transports",
        "status": "disponible"
    },
    {
        "address": "8 Rue du Commerce, 33000 Bordeaux",
        "monthly_rent": 1500.0,
        "description": "Maison 3 chambres avec jardin",
        "status": "maintenance"
    }
]

test_tenants = [
    {
        "name": "Jean Dupont",
        "email": "jean.dupont@example.com",
        "phone": "+33612345678"
    },
    {
        "name": "Marie Martin",
        "email": "marie.martin@example.com",
        "phone": "+33687654321"
    }
]

# Helper functions
def print_separator():
    print("\n" + "="*80 + "\n")

def print_response(response, message=""):
    print(f"{message} Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

# Test functions
def test_properties_api():
    print_separator()
    print("TESTING PROPERTIES API")
    print_separator()
    
    # Test GET /properties (empty initially)
    response = requests.get(f"{API_URL}/properties")
    print_response(response, "Initial GET /properties:")
    assert response.status_code == 200, "Failed to get properties"
    
    # Test POST /properties
    created_properties = []
    for prop in test_properties:
        response = requests.post(f"{API_URL}/properties", json=prop)
        print_response(response, f"POST /properties ({prop['address']}):")
        assert response.status_code == 200, "Failed to create property"
        created_properties.append(response.json())
    
    # Test GET /properties (should have our test properties)
    response = requests.get(f"{API_URL}/properties")
    print_response(response, "GET /properties after creation:")
    assert response.status_code == 200, "Failed to get properties"
    assert len(response.json()) >= len(test_properties), "Not all properties were created"
    
    # Test GET /properties/{id}
    property_id = created_properties[0]["id"]
    response = requests.get(f"{API_URL}/properties/{property_id}")
    print_response(response, f"GET /properties/{property_id}:")
    assert response.status_code == 200, "Failed to get property by ID"
    assert response.json()["id"] == property_id, "Property ID mismatch"
    
    # Test PUT /properties/{id}
    update_data = {
        "address": created_properties[0]["address"],
        "monthly_rent": 1300.0,  # Updated rent
        "description": created_properties[0]["description"] + " (Updated)",
        "status": "occupé"
    }
    response = requests.put(f"{API_URL}/properties/{property_id}", json=update_data)
    print_response(response, f"PUT /properties/{property_id}:")
    assert response.status_code == 200, "Failed to update property"
    assert response.json()["monthly_rent"] == 1300.0, "Property update failed"
    assert response.json()["status"] == "occupé", "Property status update failed"
    
    # Test GET non-existent property
    fake_id = str(uuid.uuid4())
    response = requests.get(f"{API_URL}/properties/{fake_id}")
    print_response(response, f"GET /properties/{fake_id} (non-existent):")
    assert response.status_code == 404, "Should return 404 for non-existent property"
    
    # Test DELETE /properties/{id} for the last property
    property_to_delete = created_properties[-1]["id"]
    response = requests.delete(f"{API_URL}/properties/{property_to_delete}")
    print_response(response, f"DELETE /properties/{property_to_delete}:")
    assert response.status_code == 200, "Failed to delete property"
    
    # Verify deletion
    response = requests.get(f"{API_URL}/properties/{property_to_delete}")
    assert response.status_code == 404, "Property was not deleted"
    
    print("\n✅ Properties API tests passed successfully")
    return created_properties

def test_tenants_api(properties):
    print_separator()
    print("TESTING TENANTS API")
    print_separator()
    
    # Test GET /tenants (empty initially)
    response = requests.get(f"{API_URL}/tenants")
    print_response(response, "Initial GET /tenants:")
    assert response.status_code == 200, "Failed to get tenants"
    
    # Test POST /tenants
    created_tenants = []
    for i, tenant in enumerate(test_tenants):
        # Assign property to tenant if we have properties
        if i < len(properties):
            tenant["property_id"] = properties[i]["id"]
            tenant["monthly_rent"] = properties[i]["monthly_rent"]
            # Use ISO format string for date instead of date object
            tenant["start_date"] = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.post(f"{API_URL}/tenants", json=tenant)
        print_response(response, f"POST /tenants ({tenant['name']}):")
        assert response.status_code == 200, "Failed to create tenant"
        created_tenants.append(response.json())
    
    # Test GET /tenants (should have our test tenants)
    response = requests.get(f"{API_URL}/tenants")
    print_response(response, "GET /tenants after creation:")
    assert response.status_code == 200, "Failed to get tenants"
    assert len(response.json()) >= len(test_tenants), "Not all tenants were created"
    
    # Test GET /tenants/{id}
    tenant_id = created_tenants[0]["id"]
    response = requests.get(f"{API_URL}/tenants/{tenant_id}")
    print_response(response, f"GET /tenants/{tenant_id}:")
    assert response.status_code == 200, "Failed to get tenant by ID"
    assert response.json()["id"] == tenant_id, "Tenant ID mismatch"
    
    # Test PUT /tenants/{id}
    update_data = {
        "name": created_tenants[0]["name"],
        "email": "updated." + created_tenants[0]["email"],
        "phone": created_tenants[0]["phone"],
        "property_id": created_tenants[0]["property_id"],
        "monthly_rent": created_tenants[0]["monthly_rent"],
        "start_date": created_tenants[0]["start_date"]
    }
    response = requests.put(f"{API_URL}/tenants/{tenant_id}", json=update_data)
    print_response(response, f"PUT /tenants/{tenant_id}:")
    assert response.status_code == 200, "Failed to update tenant"
    assert response.json()["email"] == update_data["email"], "Tenant update failed"
    
    # Test GET non-existent tenant
    fake_id = str(uuid.uuid4())
    response = requests.get(f"{API_URL}/tenants/{fake_id}")
    print_response(response, f"GET /tenants/{fake_id} (non-existent):")
    assert response.status_code == 404, "Should return 404 for non-existent tenant"
    
    # Test DELETE /tenants/{id} for the last tenant
    tenant_to_delete = created_tenants[-1]["id"]
    response = requests.delete(f"{API_URL}/tenants/{tenant_to_delete}")
    print_response(response, f"DELETE /tenants/{tenant_to_delete}:")
    assert response.status_code == 200, "Failed to delete tenant"
    
    # Verify deletion
    response = requests.get(f"{API_URL}/tenants/{tenant_to_delete}")
    assert response.status_code == 404, "Tenant was not deleted"
    
    print("\n✅ Tenants API tests passed successfully")
    return created_tenants[:-1]  # Return all but the deleted tenant

def test_payments_api(tenants):
    print_separator()
    print("TESTING PAYMENTS API")
    print_separator()
    
    # Test GET /payments (empty initially)
    response = requests.get(f"{API_URL}/payments")
    print_response(response, "Initial GET /payments:")
    assert response.status_code == 200, "Failed to get payments"
    
    # Create test payments for each tenant
    created_payments = []
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    for tenant in tenants:
        # Create payments for current month and previous month
        for month_offset in [0, -1]:
            month = ((current_month + month_offset - 1) % 12) + 1  # Handle December -> January
            year = current_year if month <= current_month else current_year - 1
            
            payment_data = {
                "tenant_id": tenant["id"],
                "property_id": tenant["property_id"],
                "month": month,
                "year": year,
                "amount": tenant["monthly_rent"],
                "status": "en_attente"
            }
            
            response = requests.post(f"{API_URL}/payments", json=payment_data)
            print_response(response, f"POST /payments (Tenant: {tenant['name']}, Month: {month}/{year}):")
            assert response.status_code == 200, "Failed to create payment"
            created_payments.append(response.json())
    
    # Test GET /payments (should have our test payments)
    response = requests.get(f"{API_URL}/payments")
    print_response(response, "GET /payments after creation:")
    assert response.status_code == 200, "Failed to get payments"
    assert len(response.json()) >= len(created_payments), "Not all payments were created"
    
    # Test GET /payments/tenant/{tenant_id}
    tenant_id = tenants[0]["id"]
    response = requests.get(f"{API_URL}/payments/tenant/{tenant_id}")
    print_response(response, f"GET /payments/tenant/{tenant_id}:")
    assert response.status_code == 200, "Failed to get tenant payments"
    assert len(response.json()) > 0, "No payments found for tenant"
    
    # Test PUT /payments/{id}
    payment_id = created_payments[0]["id"]
    update_data = {
        "tenant_id": created_payments[0]["tenant_id"],
        "property_id": created_payments[0]["property_id"],
        "month": created_payments[0]["month"],
        "year": created_payments[0]["year"],
        "amount": created_payments[0]["amount"] + 50,  # Increase amount
        "status": "en_attente"
    }
    response = requests.put(f"{API_URL}/payments/{payment_id}", json=update_data)
    print_response(response, f"PUT /payments/{payment_id}:")
    assert response.status_code == 200, "Failed to update payment"
    assert response.json()["amount"] == update_data["amount"], "Payment update failed"
    
    # Test PUT /payments/{id}/mark-paid
    response = requests.put(f"{API_URL}/payments/{payment_id}/mark-paid")
    print_response(response, f"PUT /payments/{payment_id}/mark-paid:")
    assert response.status_code == 200, "Failed to mark payment as paid"
    assert response.json()["status"] == "payé", "Payment status not updated to paid"
    assert response.json()["paid_date"] is not None, "Paid date not set"
    
    # Test GET non-existent payment
    fake_id = str(uuid.uuid4())
    response = requests.get(f"{API_URL}/payments/{fake_id}")
    print_response(response, f"GET /payments/{fake_id} (non-existent):")
    assert response.status_code == 404, "Should return 404 for non-existent payment"
    
    # Test DELETE /payments/{id} for the last payment
    payment_to_delete = created_payments[-1]["id"]
    response = requests.delete(f"{API_URL}/payments/{payment_to_delete}")
    print_response(response, f"DELETE /payments/{payment_to_delete}:")
    assert response.status_code == 200, "Failed to delete payment"
    
    print("\n✅ Payments API tests passed successfully")
    return created_payments

def test_dashboard_api():
    print_separator()
    print("TESTING DASHBOARD API")
    print_separator()
    
    # Test GET /dashboard
    response = requests.get(f"{API_URL}/dashboard")
    print_response(response, "GET /dashboard:")
    assert response.status_code == 200, "Failed to get dashboard stats"
    
    # Verify dashboard data structure
    dashboard_data = response.json()
    assert "total_properties" in dashboard_data, "Dashboard missing total_properties"
    assert "total_tenants" in dashboard_data, "Dashboard missing total_tenants"
    assert "monthly_revenue" in dashboard_data, "Dashboard missing monthly_revenue"
    assert "pending_payments" in dashboard_data, "Dashboard missing pending_payments"
    assert "overdue_payments" in dashboard_data, "Dashboard missing overdue_payments"
    assert "occupancy_rate" in dashboard_data, "Dashboard missing occupancy_rate"
    
    # Verify data types
    assert isinstance(dashboard_data["total_properties"], int), "total_properties should be an integer"
    assert isinstance(dashboard_data["total_tenants"], int), "total_tenants should be an integer"
    assert isinstance(dashboard_data["monthly_revenue"], (int, float)), "monthly_revenue should be a number"
    assert isinstance(dashboard_data["pending_payments"], int), "pending_payments should be an integer"
    assert isinstance(dashboard_data["overdue_payments"], int), "overdue_payments should be an integer"
    assert isinstance(dashboard_data["occupancy_rate"], (int, float)), "occupancy_rate should be a number"
    
    print("\n✅ Dashboard API tests passed successfully")

def run_all_tests():
    try:
        print("\n🔍 Starting backend API tests...\n")
        
        # Test root endpoint
        response = requests.get(f"{API_URL}/")
        print_response(response, "GET /:")
        assert response.status_code == 200, "Root endpoint not working"
        
        # Run all tests in sequence
        properties = test_properties_api()
        tenants = test_tenants_api(properties)
        test_payments_api(tenants)
        test_dashboard_api()
        
        print_separator()
        print("🎉 ALL BACKEND API TESTS PASSED SUCCESSFULLY! 🎉")
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR DURING TESTING: {str(e)}")
        return False

if __name__ == "__main__":
    # Wait a moment to ensure the backend is fully started
    time.sleep(2)
    success = run_all_tests()
    sys.exit(0 if success else 1)