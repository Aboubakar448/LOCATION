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
    return created_properties[:-1]  # Return all but the deleted property

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
                "status": "en_attente",
                # Use ISO format string for date instead of date object
                "paid_date": None
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
        "status": "en_attente",
        "paid_date": None
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
    
    # Test GET non-existent payment - Note: There's no direct GET endpoint for a single payment
    # Instead, we'll test with a non-existent tenant ID which should return an empty list
    fake_id = str(uuid.uuid4())
    response = requests.get(f"{API_URL}/payments/tenant/{fake_id}")
    print_response(response, f"GET /payments/tenant/{fake_id} (non-existent tenant):")
    assert response.status_code == 200, "Should return 200 with empty list for non-existent tenant"
    assert len(response.json()) == 0, "Should return empty list for non-existent tenant"
    
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

def test_settings_and_currencies_api():
    print_separator()
    print("TESTING SETTINGS AND CURRENCIES API")
    print_separator()
    
    # Test GET /settings (should return default settings initially)
    response = requests.get(f"{API_URL}/settings")
    print_response(response, "Initial GET /settings:")
    assert response.status_code == 200, "Failed to get settings"
    initial_settings = response.json()
    assert "currency" in initial_settings, "Settings missing currency field"
    assert "app_name" in initial_settings, "Settings missing app_name field"
    assert initial_settings["currency"] == "EUR", "Default currency should be EUR"
    
    # Test PUT /settings to update currency to USD
    update_data = {
        "currency": "USD",
        "app_name": initial_settings["app_name"]
    }
    response = requests.put(f"{API_URL}/settings", json=update_data)
    print_response(response, "PUT /settings (update currency to USD):")
    assert response.status_code == 200, "Failed to update settings"
    assert response.json()["currency"] == "USD", "Currency update failed"
    
    # Test PUT /settings to update app name
    new_app_name = "Gestion Immobilière Pro"
    update_data = {
        "currency": "USD",  # Keep the USD currency
        "app_name": new_app_name
    }
    response = requests.put(f"{API_URL}/settings", json=update_data)
    print_response(response, "PUT /settings (update app name):")
    assert response.status_code == 200, "Failed to update settings"
    assert response.json()["app_name"] == new_app_name, "App name update failed"
    
    # Test GET /settings to verify persistence
    response = requests.get(f"{API_URL}/settings")
    print_response(response, "GET /settings after updates:")
    assert response.status_code == 200, "Failed to get settings"
    updated_settings = response.json()
    assert updated_settings["currency"] == "USD", "Currency update not persisted"
    assert updated_settings["app_name"] == new_app_name, "App name update not persisted"
    
    # Test GET /currencies
    response = requests.get(f"{API_URL}/currencies")
    print_response(response, "GET /currencies:")
    assert response.status_code == 200, "Failed to get currencies"
    currencies = response.json()["currencies"]
    assert len(currencies) >= 8, "Not all currencies are available"
    
    # Verify all required currencies are present
    currency_codes = [c["code"] for c in currencies]
    required_currencies = ["EUR", "USD", "XOF", "MAD", "TND", "GBP", "CHF", "CAD"]
    for code in required_currencies:
        assert code in currency_codes, f"Currency {code} is missing"
    
    # Test changing to each available currency
    for currency in currencies:
        code = currency["code"]
        update_data = {
            "currency": code,
            "app_name": new_app_name
        }
        response = requests.put(f"{API_URL}/settings", json=update_data)
        print_response(response, f"PUT /settings (update currency to {code}):")
        assert response.status_code == 200, f"Failed to update currency to {code}"
        assert response.json()["currency"] == code, f"Currency update to {code} failed"
    
    # Reset to EUR for other tests
    update_data = {
        "currency": "EUR",
        "app_name": "Gestion Location Immobilière"  # Reset to original name
    }
    response = requests.put(f"{API_URL}/settings", json=update_data)
    assert response.status_code == 200, "Failed to reset settings"
    
    print("\n✅ Settings and Currencies API tests passed successfully")

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
    assert "currency" in dashboard_data, "Dashboard missing currency"
    assert "currency_symbol" in dashboard_data, "Dashboard missing currency_symbol"
    
    # Verify data types
    assert isinstance(dashboard_data["total_properties"], int), "total_properties should be an integer"
    assert isinstance(dashboard_data["total_tenants"], int), "total_tenants should be an integer"
    assert isinstance(dashboard_data["monthly_revenue"], (int, float)), "monthly_revenue should be a number"
    assert isinstance(dashboard_data["pending_payments"], int), "pending_payments should be an integer"
    assert isinstance(dashboard_data["overdue_payments"], int), "overdue_payments should be an integer"
    assert isinstance(dashboard_data["occupancy_rate"], (int, float)), "occupancy_rate should be a number"
    assert isinstance(dashboard_data["currency"], str), "currency should be a string"
    assert isinstance(dashboard_data["currency_symbol"], str), "currency_symbol should be a string"
    
    # Test dashboard with different currencies
    currencies_to_test = ["USD", "XOF", "MAD"]
    for currency in currencies_to_test:
        # Update settings to change currency
        update_data = {
            "currency": currency,
            "app_name": "Gestion Location Immobilière"
        }
        settings_response = requests.put(f"{API_URL}/settings", json=update_data)
        assert settings_response.status_code == 200, f"Failed to update currency to {currency}"
        
        # Get dashboard with new currency
        response = requests.get(f"{API_URL}/dashboard")
        print_response(response, f"GET /dashboard with {currency} currency:")
        assert response.status_code == 200, "Failed to get dashboard stats"
        dashboard_data = response.json()
        
        # Verify currency is reflected in dashboard
        assert dashboard_data["currency"] == currency, f"Dashboard currency not updated to {currency}"
        
        # Verify currency symbol matches the expected symbol
        currency_symbols = {
            "EUR": "€", "USD": "$", "XOF": "CFA", "MAD": "DH", 
            "TND": "DT", "GBP": "£", "CHF": "CHF", "CAD": "C$"
        }
        expected_symbol = currency_symbols.get(currency)
        assert dashboard_data["currency_symbol"] == expected_symbol, f"Currency symbol for {currency} is incorrect"
    
    # Reset to EUR for other tests
    update_data = {
        "currency": "EUR",
        "app_name": "Gestion Location Immobilière"
    }
    requests.put(f"{API_URL}/settings", json=update_data)
    
    print("\n✅ Dashboard API tests passed successfully")

def test_receipts_api(tenants, payments):
    print_separator()
    print("TESTING RECEIPTS API")
    print_separator()
    
    # Test GET /receipts (empty initially or with existing receipts)
    response = requests.get(f"{API_URL}/receipts")
    print_response(response, "Initial GET /receipts:")
    assert response.status_code == 200, "Failed to get receipts"
    initial_receipts_count = len(response.json())
    
    # Create test receipts for each payment that is marked as paid
    created_receipts = []
    
    # First, mark some payments as paid if they aren't already
    paid_payments = []
    for i, payment in enumerate(payments[:2]):  # Use only the first two payments
        if payment["status"] != "payé":
            response = requests.put(f"{API_URL}/payments/{payment['id']}/mark-paid")
            assert response.status_code == 200, f"Failed to mark payment {payment['id']} as paid"
            paid_payments.append(response.json())
        else:
            paid_payments.append(payment)
    
    # Now create receipts for the paid payments
    for payment in paid_payments:
        receipt_data = {
            "tenant_id": payment["tenant_id"],
            "payment_id": payment["id"],
            "payment_method": "Virement bancaire",
            "notes": "Test receipt"
        }
        
        response = requests.post(f"{API_URL}/receipts", json=receipt_data)
        print_response(response, f"POST /receipts (Payment ID: {payment['id']}):")
        assert response.status_code == 200, "Failed to create receipt"
        created_receipts.append(response.json())
    
    # Test GET /receipts (should have our test receipts)
    response = requests.get(f"{API_URL}/receipts")
    print_response(response, "GET /receipts after creation:")
    assert response.status_code == 200, "Failed to get receipts"
    assert len(response.json()) >= initial_receipts_count + len(created_receipts), "Not all receipts were created"
    
    # Verify receipt number format (REC-YYYYMM-XXXX)
    for receipt in created_receipts:
        assert "receipt_number" in receipt, "Receipt is missing receipt_number"
        receipt_number = receipt["receipt_number"]
        assert receipt_number.startswith("REC-"), f"Receipt number {receipt_number} doesn't start with 'REC-'"
        assert len(receipt_number) >= 12, f"Receipt number {receipt_number} is too short"
        
        # Extract year and month from receipt number
        year_month = receipt_number.split("-")[1]
        assert len(year_month) == 6, f"Year-month part of receipt number {receipt_number} is not 6 digits"
        
        # Extract sequence number
        sequence = receipt_number.split("-")[2]
        assert len(sequence) == 4, f"Sequence part of receipt number {receipt_number} is not 4 digits"
        assert sequence.isdigit(), f"Sequence part of receipt number {receipt_number} is not a number"
    
    # Test GET /receipts/tenant/{tenant_id}
    tenant_id = tenants[0]["id"]
    response = requests.get(f"{API_URL}/receipts/tenant/{tenant_id}")
    print_response(response, f"GET /receipts/tenant/{tenant_id}:")
    assert response.status_code == 200, "Failed to get tenant receipts"
    tenant_receipts = response.json()
    
    # Verify tenant receipts
    for receipt in tenant_receipts:
        assert receipt["tenant_id"] == tenant_id, f"Receipt {receipt['id']} has wrong tenant_id"
        
        # Verify receipt details
        assert "amount" in receipt, "Receipt is missing amount"
        assert "currency" in receipt, "Receipt is missing currency"
        assert "currency_symbol" in receipt, "Receipt is missing currency_symbol"
        assert "payment_date" in receipt, "Receipt is missing payment_date"
        assert "period_month" in receipt, "Receipt is missing period_month"
        assert "period_year" in receipt, "Receipt is missing period_year"
        assert "property_address" in receipt, "Receipt is missing property_address"
        assert "tenant_name" in receipt, "Receipt is missing tenant_name"
    
    # Test GET /receipts/{receipt_id}
    receipt_id = created_receipts[0]["id"]
    response = requests.get(f"{API_URL}/receipts/{receipt_id}")
    print_response(response, f"GET /receipts/{receipt_id}:")
    assert response.status_code == 200, "Failed to get receipt by ID"
    assert response.json()["id"] == receipt_id, "Receipt ID mismatch"
    
    # Test GET non-existent receipt
    fake_id = str(uuid.uuid4())
    response = requests.get(f"{API_URL}/receipts/{fake_id}")
    print_response(response, f"GET /receipts/{fake_id} (non-existent):")
    assert response.status_code == 404, "Should return 404 for non-existent receipt"
    
    # Test DELETE /receipts/{receipt_id} for the last receipt
    receipt_to_delete = created_receipts[-1]["id"]
    response = requests.delete(f"{API_URL}/receipts/{receipt_to_delete}")
    print_response(response, f"DELETE /receipts/{receipt_to_delete}:")
    assert response.status_code == 200, "Failed to delete receipt"
    
    # Verify deletion
    response = requests.get(f"{API_URL}/receipts/{receipt_to_delete}")
    assert response.status_code == 404, "Receipt was not deleted"
    
    print("\n✅ Receipts API tests passed successfully")
    return created_receipts

def run_all_tests():
    try:
        print("\n🔍 Starting backend API tests...\n")
        
        # Test root endpoint
        response = requests.get(f"{API_URL}/")
        print_response(response, "GET /:")
        assert response.status_code == 200, "Root endpoint not working"
        
        # Test settings and currencies first
        test_settings_and_currencies_api()
        
        # Run all other tests in sequence
        properties = test_properties_api()
        tenants = test_tenants_api(properties)
        payments = test_payments_api(tenants)
        test_dashboard_api()
        
        # Test the new receipts system
        test_receipts_api(tenants, payments)
        
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