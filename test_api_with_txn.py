#!/usr/bin/env python3
# test_api_with_txn.py - Test the Flask API endpoints and display transaction IDs

import requests
import json
import sys
import time
import hashlib
from pprint import pprint

# Server URL and port - change this as needed
SERVER = "http://127.0.0.1"
PORT = 5047  # Updated port to match Flask server
BASE_URL = f"{SERVER}:{PORT}"

# Accounts setup from the config file
try:
    with open("Compliance/compliance_test_accounts.json", "r") as f:
        accounts = json.load(f)
    
    # Admin account
    ADMIN_PRIVATE_KEY = accounts["admin"]["private_key"]
    ADMIN_ADDRESS = accounts["admin"]["address"]
    
    # Verifier account
    VERIFIER_PRIVATE_KEY = accounts["verifier"]["private_key"]
    VERIFIER_ADDRESS = accounts["verifier"]["address"]
    
    # App ID
    APP_ID = 744059516  # This should match the value in app.py
    
    print("✓ Loaded account configurations")
except Exception as e:
    print(f"Error loading accounts: {e}")
    sys.exit(1)

# Helper function to generate document hash
def generate_document_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()

def check_admin_status():
    """Check if the admin address has admin role"""
    endpoint = f"{BASE_URL}/api/admin/status"
    try:
        response = requests.get(endpoint, params={"address": ADMIN_ADDRESS})
        result = response.json()
        
        print("Admin Status Check:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("is_admin", False):
            print("✅ Admin status check PASSED\n")
            return True
        else:
            print("❌ Admin status check FAILED\n")
            return False
    except Exception as e:
        print(f"❌ Admin status check FAILED with exception: {str(e)}\n")
        return False

def check_verifier_status():
    """Check if the verifier address has verifier role"""
    endpoint = f"{BASE_URL}/api/verifier/status"
    try:
        response = requests.get(endpoint, params={"address": VERIFIER_ADDRESS})
        result = response.json()
        
        print("Verifier Status Check:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("is_verifier", False):
            print("✅ Verifier status check PASSED\n")
            return True
        else:
            print("❌ Verifier status check FAILED\n")
            return False
    except Exception as e:
        print(f"❌ Verifier status check FAILED with exception: {str(e)}\n")
        return False

def test_register_document():
    """Test the document registration endpoint with admin role"""
    print("\n=== Testing Document Registration ===")
    endpoint = f"{BASE_URL}/api/document/register"
    
    # Check admin status first
    admin_status = requests.get(f"{BASE_URL}/api/admin/status", params={"address": ADMIN_ADDRESS}).json()
    if not admin_status.get("is_admin", False):
        print("Warning: Account doesn't have admin privileges")
    
    # Prepare document data
    document_data = {
        "private_key": ADMIN_PRIVATE_KEY,
        "role": "admin",  # Important: specify role
        "content": "This is a test document for compliance verification v1.0",
        "version": "1.0"
    }
    
    try:
        response = requests.post(endpoint, json=document_data)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Test PASSED")
            
            # Display transaction ID and explorer link if available
            if result.get("txn_id"):
                print(f"\n🔗 Blockchain Transaction ID: {result.get('txn_id')}")
                print(f"🔍 Explorer Link: https://testnet.algoexplorer.io/tx/{result.get('txn_id')}\n")
        else:
            print("❌ Test FAILED")
            
        return result
    except Exception as e:
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None

def test_assign_verifier():
    """Test the assign verifier endpoint with admin role"""
    print("\n=== Testing Assign Verifier ===")
    endpoint = f"{BASE_URL}/api/verifier/assign"
    
    # Data for request
    data = {
        "private_key": ADMIN_PRIVATE_KEY,
        "role": "admin",  # Important: specify role
        "verifier_address": VERIFIER_ADDRESS
    }
    
    try:
        response = requests.post(endpoint, json=data)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Test PASSED")
            
            # Display transaction ID and explorer link if available
            if result.get("txn_id"):
                print(f"\n🔗 Blockchain Transaction ID: {result.get('txn_id')}")
                print(f"🔍 Explorer Link: https://testnet.algoexplorer.io/tx/{result.get('txn_id')}\n")
        else:
            print("❌ Test FAILED")
            
        return result
    except Exception as e:
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None

def test_verify_compliance():
    """Test the verify compliance endpoint with verifier role"""
    print("\n=== Testing Document Verification ===")
    endpoint = f"{BASE_URL}/api/document/verify"
    
    # First register a document to get a hash
    register_result = test_register_document()
    if not register_result or not register_result.get("success"):
        print("Cannot test verification - document registration failed")
        return None
    
    # Get document hash from registration response
    document_hash = register_result.get("document_hash")
    
    # Data for verification
    verification_data = {
        "private_key": VERIFIER_PRIVATE_KEY,
        "role": "verifier",  # Important: specify role
        "document_hash": document_hash,
        "is_compliant": True  # Mark as compliant
    }
    
    try:
        # Allow some time for blockchain to process the registration
        print("Waiting 5 seconds before verification to allow for blockchain processing...")
        time.sleep(5)
        
        response = requests.post(endpoint, json=verification_data)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Test PASSED")
            
            # Display transaction ID and explorer link if available
            if result.get("txn_id"):
                print(f"\n🔗 Blockchain Transaction ID: {result.get('txn_id')}")
                print(f"🔍 Explorer Link: https://testnet.algoexplorer.io/tx/{result.get('txn_id')}\n")
        else:
            print("❌ Test FAILED")
            
        return result
    except Exception as e:
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None

def test_get_compliance_status():
    """Test getting the compliance status"""
    print("\n=== Testing Get Compliance Status ===")
    
    # First ensure we have verified a document
    verification_result = None
    try:
        # Try to get status first, if it fails, we'll do verification
        status_endpoint = f"{BASE_URL}/api/document/status"
        response = requests.get(status_endpoint, params={"app_id": APP_ID})
        
        if response.status_code != 200:
            print("No verified document found, running verification test first...")
            verification_result = test_verify_compliance()
            if not verification_result or not verification_result.get("success"):
                print("Verification failed, cannot test status endpoint")
                return None
    except:
        # If exception, we'll also try verification
        print("Error checking status, running verification test first...")
        verification_result = test_verify_compliance()
    
    # Now get status
    status_endpoint = f"{BASE_URL}/api/document/status"
    
    try:
        # Allow some time for blockchain to process the verification
        print("Waiting 5 seconds before status check to allow for blockchain processing...")
        time.sleep(5)
        
        response = requests.get(status_endpoint, params={"app_id": APP_ID})
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
            
        return result
    except Exception as e:
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None

def run_all_tests():
    """Run all API tests in sequence"""
    print("\n======= Starting API Tests =======")
    print(f"Using API endpoint: {BASE_URL}")
    print("App ID:", APP_ID)
    print("==============================\n")
    
    # Check admin and verifier status
    admin_ok = check_admin_status()
    verifier_ok = check_verifier_status()
    
    if not admin_ok:
        print("⚠️ Warning: Admin account may not be properly set up")
    
    if not verifier_ok:
        print("⚠️ Warning: Verifier account may not be properly set up")
        
    # Run blockchain operation tests
    results = {
        "register_document": test_register_document(),
        "assign_verifier": test_assign_verifier(),
        "verify_compliance": test_verify_compliance(),
        "get_compliance_status": test_get_compliance_status()
    }
    
    # Print summary
    print("\n======= Test Results Summary =======")
    for test_name, result in results.items():
        if result and result.get("success"):
            print(f"✅ {test_name}: PASSED")
            # Print transaction ID if available
            if result.get("txn_id"):
                print(f"   🔗 TXN: {result.get('txn_id')}")
                print(f"   🔍 Explorer: https://testnet.algoexplorer.io/tx/{result.get('txn_id')}")
        else:
            print(f"❌ {test_name}: FAILED")
    print("===================================")

if __name__ == "__main__":
    # Process command line arguments to run specific tests
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        if test_name == "admin":
            check_admin_status()
        elif test_name == "verifier":
            check_verifier_status()
        elif test_name == "register":
            test_register_document()
        elif test_name == "assign":
            test_assign_verifier()
        elif test_name == "verify":
            test_verify_compliance()
        elif test_name == "status":
            test_get_compliance_status()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: admin, verifier, register, assign, verify, status")
    else:
        run_all_tests()
