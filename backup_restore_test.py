#!/usr/bin/env python3
import requests
import json
import uuid
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
import time
import random

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

# Helper functions
def print_separator():
    print("\n" + "="*80 + "\n")

def print_response(response, message=""):
    print(f"{message} Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

def create_test_data():
    """Create test data for backup/restore testing"""
    print_separator()
    print("CREATING TEST DATA FOR BACKUP/RESTORE TESTING")
    print_separator()
    
    # Create test properties
    properties = []
    for i in range(3):
        property_data = {
            "address": f"Test Property {i+1}, Rue de Test {random.randint(1, 100)}",
            "monthly_rent": 1000 + (i * 200),
            "description": f"Test property {i+1} for backup/restore testing",
            "status": "disponible"
        }
        response = requests.post(f"{API_URL}/properties", json=property_data)
        assert response.status_code == 200, f"Failed to create test property {i+1}"
        properties.append(response.json())
    
    # Create test tenants
    tenants = []
    for i in range(2):
        tenant_data = {
            "name": f"Test Tenant {i+1}",
            "email": f"tenant{i+1}@test.com",
            "phone": f"+336{random.randint(10000000, 99999999)}",
            "property_id": properties[i]["id"],
            "monthly_rent": properties[i]["monthly_rent"],
            "start_date": datetime.now().strftime("%Y-%m-%d")
        }
        response = requests.post(f"{API_URL}/tenants", json=tenant_data)
        assert response.status_code == 200, f"Failed to create test tenant {i+1}"
        tenants.append(response.json())
    
    # Create test payments
    payments = []
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    for tenant in tenants:
        for month_offset in [0, -1]:
            month = ((current_month + month_offset - 1) % 12) + 1
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
            assert response.status_code == 200, f"Failed to create test payment for tenant {tenant['name']}"
            payments.append(response.json())
    
    # Mark one payment as paid
    if payments:
        response = requests.put(f"{API_URL}/payments/{payments[0]['id']}/mark-paid")
        assert response.status_code == 200, "Failed to mark payment as paid"
        payments[0] = response.json()
    
    # Create a receipt for the paid payment
    receipts = []
    if payments and payments[0]["status"] == "payé":
        receipt_data = {
            "tenant_id": payments[0]["tenant_id"],
            "payment_id": payments[0]["id"],
            "payment_method": "Virement bancaire",
            "notes": "Test receipt for backup/restore testing"
        }
        
        response = requests.post(f"{API_URL}/receipts", json=receipt_data)
        assert response.status_code == 200, "Failed to create test receipt"
        receipts.append(response.json())
    
    # Update settings
    settings_data = {
        "currency": "EUR",
        "app_name": "Test Backup/Restore App"
    }
    response = requests.put(f"{API_URL}/settings", json=settings_data)
    assert response.status_code == 200, "Failed to update settings"
    
    print("\n✅ Test data created successfully")
    return {
        "properties": properties,
        "tenants": tenants,
        "payments": payments,
        "receipts": receipts
    }

def test_backup_endpoint(test_data):
    """Test the backup endpoint"""
    print_separator()
    print("TESTING BACKUP ENDPOINT")
    print_separator()
    
    # Get backup data
    response = requests.get(f"{API_URL}/backup")
    print_response(response, "GET /backup:")
    assert response.status_code == 200, "Failed to get backup data"
    
    backup_data = response.json()
    
    # Verify backup structure
    assert "backup_date" in backup_data, "Backup missing backup_date"
    assert "app_version" in backup_data, "Backup missing app_version"
    assert "properties" in backup_data, "Backup missing properties"
    assert "tenants" in backup_data, "Backup missing tenants"
    assert "payments" in backup_data, "Backup missing payments"
    assert "receipts" in backup_data, "Backup missing receipts"
    assert "settings" in backup_data, "Backup missing settings"
    assert "total_records" in backup_data, "Backup missing total_records"
    
    # Verify total_records structure
    total_records = backup_data["total_records"]
    assert "properties" in total_records, "total_records missing properties count"
    assert "tenants" in total_records, "total_records missing tenants count"
    assert "payments" in total_records, "total_records missing payments count"
    assert "receipts" in total_records, "total_records missing receipts count"
    
    # Verify data types
    assert isinstance(backup_data["backup_date"], str), "backup_date should be a string"
    assert isinstance(backup_data["app_version"], str), "app_version should be a string"
    assert isinstance(backup_data["properties"], list), "properties should be a list"
    assert isinstance(backup_data["tenants"], list), "tenants should be a list"
    assert isinstance(backup_data["payments"], list), "payments should be a list"
    assert isinstance(backup_data["receipts"], list), "receipts should be a list"
    assert isinstance(backup_data["settings"], dict), "settings should be a dictionary"
    assert isinstance(total_records, dict), "total_records should be a dictionary"
    
    # Verify that our test data is included in the backup
    property_ids = [p["id"] for p in backup_data["properties"]]
    tenant_ids = [t["id"] for t in backup_data["tenants"]]
    payment_ids = [p["id"] for p in backup_data["payments"]]
    receipt_ids = [r["id"] for r in backup_data["receipts"]]
    
    for prop in test_data["properties"]:
        assert prop["id"] in property_ids, f"Property {prop['id']} not found in backup"
    
    for tenant in test_data["tenants"]:
        assert tenant["id"] in tenant_ids, f"Tenant {tenant['id']} not found in backup"
    
    for payment in test_data["payments"]:
        assert payment["id"] in payment_ids, f"Payment {payment['id']} not found in backup"
    
    for receipt in test_data["receipts"]:
        assert receipt["id"] in receipt_ids, f"Receipt {receipt['id']} not found in backup"
    
    # Verify that the counts match
    assert total_records["properties"] == len(backup_data["properties"]), "Property count mismatch"
    assert total_records["tenants"] == len(backup_data["tenants"]), "Tenant count mismatch"
    assert total_records["payments"] == len(backup_data["payments"]), "Payment count mismatch"
    assert total_records["receipts"] == len(backup_data["receipts"]), "Receipt count mismatch"
    
    print("\n✅ Backup endpoint test passed successfully")
    return backup_data

def delete_test_data(test_data):
    """Delete some test data to verify restore functionality"""
    print_separator()
    print("DELETING SOME TEST DATA")
    print_separator()
    
    # Delete one property
    if test_data["properties"]:
        property_to_delete = test_data["properties"][-1]["id"]
        response = requests.delete(f"{API_URL}/properties/{property_to_delete}")
        print_response(response, f"DELETE /properties/{property_to_delete}:")
        assert response.status_code == 200, "Failed to delete property"
    
    # Delete one tenant
    if test_data["tenants"]:
        tenant_to_delete = test_data["tenants"][-1]["id"]
        response = requests.delete(f"{API_URL}/tenants/{tenant_to_delete}")
        print_response(response, f"DELETE /tenants/{tenant_to_delete}:")
        assert response.status_code == 200, "Failed to delete tenant"
    
    # Delete one payment
    if test_data["payments"]:
        payment_to_delete = test_data["payments"][-1]["id"]
        response = requests.delete(f"{API_URL}/payments/{payment_to_delete}")
        print_response(response, f"DELETE /payments/{payment_to_delete}:")
        assert response.status_code == 200, "Failed to delete payment"
    
    # Delete one receipt
    if test_data["receipts"]:
        receipt_to_delete = test_data["receipts"][-1]["id"]
        response = requests.delete(f"{API_URL}/receipts/{receipt_to_delete}")
        print_response(response, f"DELETE /receipts/{receipt_to_delete}:")
        assert response.status_code == 200, "Failed to delete receipt"
    
    # Update settings
    settings_data = {
        "currency": "USD",
        "app_name": "Changed App Name"
    }
    response = requests.put(f"{API_URL}/settings", json=settings_data)
    assert response.status_code == 200, "Failed to update settings"
    
    print("\n✅ Test data partially deleted successfully")

def test_restore_endpoint(backup_data, original_test_data):
    """Test the restore endpoint"""
    print_separator()
    print("TESTING RESTORE ENDPOINT")
    print_separator()
    
    # Restore from backup
    response = requests.post(f"{API_URL}/restore", json=backup_data)
    print_response(response, "POST /restore:")
    assert response.status_code == 200, "Failed to restore from backup"
    
    # Verify response structure
    restore_response = response.json()
    assert "message" in restore_response, "Restore response missing message"
    assert "restored_records" in restore_response, "Restore response missing restored_records"
    assert "restore_date" in restore_response, "Restore response missing restore_date"
    
    # Verify that all data has been restored
    # Check properties
    response = requests.get(f"{API_URL}/properties")
    assert response.status_code == 200, "Failed to get properties after restore"
    restored_properties = response.json()
    property_ids = [p["id"] for p in restored_properties]
    
    for prop in original_test_data["properties"]:
        assert prop["id"] in property_ids, f"Property {prop['id']} not restored"
    
    # Check tenants
    response = requests.get(f"{API_URL}/tenants")
    assert response.status_code == 200, "Failed to get tenants after restore"
    restored_tenants = response.json()
    tenant_ids = [t["id"] for t in restored_tenants]
    
    for tenant in original_test_data["tenants"]:
        assert tenant["id"] in tenant_ids, f"Tenant {tenant['id']} not restored"
    
    # Check payments
    response = requests.get(f"{API_URL}/payments")
    assert response.status_code == 200, "Failed to get payments after restore"
    restored_payments = response.json()
    payment_ids = [p["id"] for p in restored_payments]
    
    for payment in original_test_data["payments"]:
        assert payment["id"] in payment_ids, f"Payment {payment['id']} not restored"
    
    # Check receipts
    response = requests.get(f"{API_URL}/receipts")
    assert response.status_code == 200, "Failed to get receipts after restore"
    restored_receipts = response.json()
    receipt_ids = [r["id"] for r in restored_receipts]
    
    for receipt in original_test_data["receipts"]:
        assert receipt["id"] in receipt_ids, f"Receipt {receipt['id']} not restored"
    
    # Check settings
    response = requests.get(f"{API_URL}/settings")
    assert response.status_code == 200, "Failed to get settings after restore"
    restored_settings = response.json()
    
    # Verify settings were restored
    assert restored_settings["currency"] == backup_data["settings"]["currency"], "Settings currency not restored"
    assert restored_settings["app_name"] == backup_data["settings"]["app_name"], "Settings app_name not restored"
    
    print("\n✅ Restore endpoint test passed successfully")

def test_edge_cases():
    """Test edge cases for backup/restore functionality"""
    print_separator()
    print("TESTING EDGE CASES")
    print_separator()
    
    # Test 1: Restore with empty backup data
    empty_backup = {
        "backup_date": datetime.now().isoformat(),
        "app_version": "1.0",
        "properties": [],
        "tenants": [],
        "payments": [],
        "receipts": [],
        "settings": {},
        "total_records": {
            "properties": 0,
            "tenants": 0,
            "payments": 0,
            "receipts": 0
        }
    }
    
    response = requests.post(f"{API_URL}/restore", json=empty_backup)
    print_response(response, "POST /restore with empty backup:")
    assert response.status_code == 200, "Failed to restore from empty backup"
    
    # Test 2: Restore with missing collections
    incomplete_backup = {
        "backup_date": datetime.now().isoformat(),
        "app_version": "1.0",
        "properties": [],
        # Missing tenants
        "payments": [],
        "receipts": [],
        "settings": {},
        "total_records": {
            "properties": 0,
            "payments": 0,
            "receipts": 0
        }
    }
    
    response = requests.post(f"{API_URL}/restore", json=incomplete_backup)
    print_response(response, "POST /restore with incomplete backup:")
    assert response.status_code == 200, "Failed to handle incomplete backup"
    
    # Test 3: Restore with invalid data structure
    invalid_backup = {
        "backup_date": datetime.now().isoformat(),
        "app_version": "1.0",
        "properties": [{"invalid": "property"}],
        "tenants": [{"invalid": "tenant"}],
        "payments": [{"invalid": "payment"}],
        "receipts": [{"invalid": "receipt"}],
        "settings": {"invalid": "settings"},
        "total_records": {
            "properties": 1,
            "tenants": 1,
            "payments": 1,
            "receipts": 1
        }
    }
    
    response = requests.post(f"{API_URL}/restore", json=invalid_backup)
    print_response(response, "POST /restore with invalid backup:")
    # This might fail with 500 or succeed with 200 depending on how the backend handles invalid data
    # We're just checking that it doesn't crash the server
    
    print("\n✅ Edge cases tests completed")

def run_backup_restore_tests():
    try:
        print("\n🔍 Starting backup/restore API tests...\n")
        
        # Create test data
        test_data = create_test_data()
        
        # Test backup endpoint
        backup_data = test_backup_endpoint(test_data)
        
        # Delete some test data
        delete_test_data(test_data)
        
        # Test restore endpoint
        test_restore_endpoint(backup_data, test_data)
        
        # Test edge cases
        test_edge_cases()
        
        print_separator()
        print("🎉 ALL BACKUP/RESTORE API TESTS PASSED SUCCESSFULLY! 🎉")
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
    success = run_backup_restore_tests()
    sys.exit(0 if success else 1)