#!/usr/bin/env python3
# test_api.py - Test script for the Flask API endpoints

import requests
import json
import os
import time
import hashlib
import sys

# Configuration
BASE_URL = "http://localhost:5045"
API_PREFIX = "/api"

# Test document data
TEST_DOCUMENT_CONTENT = "This is a test document for the compliance system"
TEST_DOCUMENT_HASH = hashlib.sha256(TEST_DOCUMENT_CONTENT.encode()).hexdigest()

# Load admin/verifier accounts from config
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, "Compliance/compliance_test_accounts.json")) as f:
        accounts = json.load(f)
    admin_private_key = accounts.get('admin', {}).get('private_key', '')
    verifier_private_key = accounts.get('verifier', {}).get('private_key', '')
    verifier_address = accounts.get('verifier', {}).get('address', '')
    admin_address = accounts.get('admin', {}).get('address', '')
except Exception as e:
    print(f"Error loading accounts: {str(e)}")
    admin_private_key = ""
    verifier_private_key = ""
    verifier_address = ""
    admin_address = ""


def test_get_document_hash():
    """Test the /api/document/hash endpoint"""
    print("\n--- Testing get_document_hash endpoint ---")
    
    endpoint = f"{BASE_URL}{API_PREFIX}/document/hash"
    payload = {"document_content": TEST_DOCUMENT_CONTENT}
    
    try:
        response = requests.post(endpoint, json=payload)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Test PASSED")
            # Verify hash is correct
            if result.get("document_hash") == TEST_DOCUMENT_HASH:
                print("✅ Hash verification PASSED")
            else:
                print("❌ Hash verification FAILED")
        else:
            print("❌ Test FAILED")
            
        return result.get("document_hash") if result.get("success") else None
    except Exception as e:
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None


def test_upload_document():
    """Test the /api/upload endpoint"""
    print("\n--- Testing upload_document endpoint ---")
    
    endpoint = f"{BASE_URL}{API_PREFIX}/upload"
    
    # Create a temporary file for testing
    temp_file_path = "temp_test_doc.txt"
    with open(temp_file_path, "w") as f:
        f.write(TEST_DOCUMENT_CONTENT)
    
    try:
        with open(temp_file_path, "rb") as f:
            files = {"file": ("test_document.txt", f)}
            response = requests.post(endpoint, files=files)
            
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Test PASSED")
            # Verify hash is correct
            if result.get("hash") == TEST_DOCUMENT_HASH:
                print("✅ Hash verification PASSED")
            else:
                print("❌ Hash verification FAILED")
        else:
            print("❌ Test FAILED")
            
        # Clean up the temporary file
        os.remove(temp_file_path)
        return result.get("hash") if result.get("success") else None
    except Exception as e:
        # Clean up in case of exception
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None


def test_login_verifier():
    """Test the /api/login/verifier endpoint"""
    print("\n--- Testing verifier_login endpoint ---")
    
    endpoint = f"{BASE_URL}{API_PREFIX}/login/verifier"
    
    # Test admin login
    admin_payload = {"private_key": admin_private_key}
    verifier_payload = {"private_key": verifier_private_key}
    invalid_payload = {"private_key": "invalid_key"}
    
    results = {}
    
    try:
        # Test admin login
        print("Testing admin login:")
        admin_response = requests.post(endpoint, json=admin_payload)
        admin_result = admin_response.json()
        
        print(f"Status Code: {admin_response.status_code}")
        print(f"Response: {json.dumps(admin_result, indent=2)}")
        
        if admin_response.status_code == 200 and admin_result.get("success"):
            print("✅ Admin login test PASSED")
            results["admin"] = admin_result
        else:
            print("❌ Admin login test FAILED")
        
        # Test verifier login
        print("\nTesting verifier login:")
        verifier_response = requests.post(endpoint, json=verifier_payload)
        verifier_result = verifier_response.json()
        
        print(f"Status Code: {verifier_response.status_code}")
        print(f"Response: {json.dumps(verifier_result, indent=2)}")
        
        if verifier_response.status_code == 200 and verifier_result.get("success"):
            print("✅ Verifier login test PASSED")
            results["verifier"] = verifier_result
        else:
            print("❌ Verifier login test FAILED")
        
        # Test invalid login
        print("\nTesting invalid login:")
        invalid_response = requests.post(endpoint, json=invalid_payload)
        invalid_result = invalid_response.json()
        
        print(f"Status Code: {invalid_response.status_code}")
        print(f"Response: {json.dumps(invalid_result, indent=2)}")
        
        if invalid_response.status_code == 401 and not invalid_result.get("success"):
            print("✅ Invalid login test PASSED")
        else:
            print("❌ Invalid login test FAILED")
            
        return results
    except Exception as e:
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None


def test_account_status():
    """Test the /api/account/status endpoint"""
    print("\n--- Testing account_status endpoint ---")
    
    endpoint = f"{BASE_URL}{API_PREFIX}/account/status"
    
    try:
        # Test admin account
        print("Testing admin account status:")
        admin_url = f"{endpoint}?address={admin_address}"
        admin_response = requests.get(admin_url)
        admin_result = admin_response.json()
        
        print(f"Status Code: {admin_response.status_code}")
        print(f"Response: {json.dumps(admin_result, indent=2)}")
        
        if admin_response.status_code == 200 and admin_result.get("success"):
            print("✅ Admin account status test PASSED")
            if admin_result.get("is_admin"):
                print("✅ Admin role verification PASSED")
            else:
                print("❌ Admin role verification FAILED")
        else:
            print("❌ Admin account status test FAILED")
        
        # Test verifier account
        print("\nTesting verifier account status:")
        verifier_url = f"{endpoint}?address={verifier_address}"
        verifier_response = requests.get(verifier_url)
        verifier_result = verifier_response.json()
        
        print(f"Status Code: {verifier_response.status_code}")
        print(f"Response: {json.dumps(verifier_result, indent=2)}")
        
        if verifier_response.status_code == 200 and verifier_result.get("success"):
            print("✅ Verifier account status test PASSED")
            if verifier_result.get("is_verifier"):
                print("✅ Verifier role verification PASSED")
            else:
                print("❌ Verifier role verification FAILED")
        else:
            print("❌ Verifier account status test FAILED")
            
        return {
            "admin": admin_result,
            "verifier": verifier_result
        }
    except Exception as e:
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None


def test_register_document():
    """Test the /api/document/register endpoint"""
    print("\n--- Testing register_document endpoint ---")
    
    endpoint = f"{BASE_URL}{API_PREFIX}/document/register"
    
    document_data = {
        "document_content": TEST_DOCUMENT_CONTENT,  # Need content, not hash
        "private_key": admin_private_key,  # Only admin can register documents
        "role": "admin",  # Add required role parameter
        "version": "1.0.0"  # Match the version parameter name in the API
    }
    
    # First check if admin is already logged in
    print("Verifying admin account status before registration...")
    admin_status_url = f"{BASE_URL}{API_PREFIX}/account/status?address={admin_address}"
    admin_status_response = requests.get(admin_status_url)
    admin_status = admin_status_response.json()
    
    if not admin_status.get("is_admin", False):
        print("Warning: Account doesn't have admin privileges")
    
    try:
        response = requests.post(endpoint, json=document_data)
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


def test_assign_verifier():
    """Test the /api/verifier/assign endpoint"""
    print("\n--- Testing assign_verifier endpoint ---")
    
    endpoint = f"{BASE_URL}{API_PREFIX}/verifier/assign"
    
    # Verify verifier account status first
    print("Verifying verifier account status before assignment...")
    verifier_status_url = f"{BASE_URL}{API_PREFIX}/account/status?address={verifier_address}"
    verifier_status_response = requests.get(verifier_status_url)
    verifier_status = verifier_status_response.json()
    
    is_opted_in = verifier_status.get("is_opted_in", False)
    print(f"Verifier opted in status: {is_opted_in}")
    
    # Data for assigning verifier
    assign_data = {
        "private_key": admin_private_key,  # Only admin can assign verifiers
        "verifier_address": verifier_address,
        "role": "admin"  # Add required role parameter
    }
    
    try:
        response = requests.post(endpoint, json=assign_data)
        
        # Check for empty response which might indicate server closed connection
        if not response.text.strip():
            print("❌ Test FAILED: Empty response received")
            print("This might be due to the server closing the connection or timing out")
            return None
            
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
        # If we got a JSON decode error, it might be because the response is empty
        if "JSONDecodeError" in str(e) or "Expecting value" in str(e):
            print("The server may have returned an empty or invalid response.")
            print("This could be due to a timeout or connection issue with the blockchain.")
        return None


def test_verify_compliance():
    """Test the /api/document/verify endpoint"""
    print("\n--- Testing verify_compliance endpoint ---")
    
    endpoint = f"{BASE_URL}{API_PREFIX}/document/verify"
    
    # First check if the verifier is properly assigned
    print("Verifying verifier account status...")
    verifier_status_url = f"{BASE_URL}{API_PREFIX}/account/status?address={verifier_address}"
    verifier_status_response = requests.get(verifier_status_url)
    verifier_status = verifier_status_response.json()
    
    is_verifier = verifier_status.get("is_verifier", False)
    is_opted_in = verifier_status.get("is_opted_in", False)
    
    print(f"Is verified account: {is_verifier}")
    print(f"Is opted in to app: {is_opted_in}")
    
    if not is_verifier or not is_opted_in:
        print("Warning: Account may not have proper verifier permissions")
    
    # Data for verifying document
    verify_data = {
        "private_key": verifier_private_key,  # Only verifier can verify documents
        "document_hash": TEST_DOCUMENT_HASH,
        "role": "verifier",  # Add required role parameter
        "is_compliant": True,
        "attestation_date": int(time.time())
    }
    
    try:
        response = requests.post(endpoint, json=verify_data)
        
        # Check for empty response
        if not response.text.strip():
            print("❌ Test FAILED: Empty response received")
            print("This might be due to the server closing the connection or timing out")
            return None
            
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


def test_get_compliance_status():
    """Test the /api/document/status endpoint"""
    print("\n--- Testing get_compliance_status endpoint ---")
    
    endpoint = f"{BASE_URL}{API_PREFIX}/document/status"
    
    try:
        # First check if blockchain is accessible via account status API
        print("Verifying blockchain connectivity via account status...")
        admin_status_url = f"{BASE_URL}{API_PREFIX}/account/status?address={admin_address}"
        admin_status_response = requests.get(admin_status_url)
        admin_status = admin_status_response.json()
        
        if not admin_status.get("success"):
            print("Warning: Blockchain connection might be unstable")
        
        # Set increased timeout to prevent hanging if the blockchain is slow
        print("Requesting compliance status with increased timeout...")
        response = requests.get(endpoint, timeout=30)
        
        # Check for empty response
        if not response.text.strip():
            print("❌ Test FAILED: Empty response received")
            print("This might be due to the server closing the connection or timing out")
            return None
            
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
            
        return result
    except requests.exceptions.Timeout:
        print("❌ Test FAILED: Request timed out after 10 seconds")
        print("This might indicate slow blockchain processing or connection issues")
        return None
    except Exception as e:
        print(f"❌ Test FAILED with exception: {str(e)}")
        return None


def run_all_tests():
    """Run all API tests sequentially"""
    print("==========================================")
    print("STARTING API TESTS")
    print("==========================================")
    
    # Parse command line arguments for selective test running
    selected_tests = []
    if len(sys.argv) > 1:
        selected_tests = sys.argv[1:]
        print(f"Running selected tests: {', '.join(selected_tests)}")
    
    results = {}
    
    # Test document hash generation
    if not selected_tests or "hash" in selected_tests:
        results["document_hash"] = test_get_document_hash()
    
    # Test document upload
    if not selected_tests or "upload" in selected_tests:
        results["upload"] = test_upload_document()
    
    # Test login functionality
    if not selected_tests or "login" in selected_tests:
        results["login"] = test_login_verifier()
    
    # Test account status
    if not selected_tests or "status" in selected_tests:
        results["account_status"] = test_account_status()
    
    # Test document registration - admin only
    # This is a blockchain operation
    if not selected_tests or "register" in selected_tests:
        results["register"] = test_register_document()
    
    # Test verifier assignment - admin only  
    # This is a blockchain operation
    if not selected_tests or "assign" in selected_tests:
        results["assign_verifier"] = test_assign_verifier()
    
    # Test verification - verifier only
    # This is a blockchain operation
    if not selected_tests or "verify" in selected_tests:
        results["verify"] = test_verify_compliance()
    
    # Test getting compliance status
    # This reads from the blockchain
    if not selected_tests or "compliance" in selected_tests:
        results["compliance_status"] = test_get_compliance_status()
    
    return results
    
    print("\n==========================================")
    print("\nAPI TEST SUMMARY")
    print("==========================================")
    
    tests = [
        ("Document Hash Generation", results.get("document_hash") is not None, "hash"),
        ("Document Upload", results.get("upload") is not None, "upload"),
        ("Verifier/Admin Login", results.get("login") is not None, "login"),
        ("Account Status Check", results.get("account_status") is not None, "status"),
        ("Document Registration", results.get("register") and results.get("register").get("success", False), "register"),
        ("Verifier Assignment", results.get("assign_verifier") and results.get("assign_verifier").get("success", False), "assign"),
        ("Document Verification", results.get("verify") and results.get("verify").get("success", False), "verify"),
        ("Compliance Status Check", results.get("compliance_status") and results.get("compliance_status").get("success", False), "compliance")
    ]
    
    # Filter tests based on command line arguments
    if selected_tests:
        filtered_tests = [test for test in tests if test[2] in selected_tests]
        if filtered_tests:
            tests = filtered_tests
    
    passed = 0
    for name, result, _ in tests:
        if result is None:  # Test wasn't run
            status = "⏭️ SKIPPED"
        else:
            status = "✅ PASSED" if result else "❌ FAILED"
            if result:
                passed += 1
        
        print(f"{name}: {status}")
    
    run_count = sum(1 for _, result, _ in tests if result is not None)
    if run_count > 0:
        print(f"\nPassed {passed}/{run_count} tests")
    else:
        print("\nNo tests were run")


if __name__ == "__main__":
    print("=== Algorand Compliance API Test Script ===\n")
    print("Usage: python3 test_api.py [test_name1] [test_name2] ...")
    print("Available tests: hash, upload, login, status, register, assign, verify, compliance")
    print("If no specific tests are provided, all tests will run sequentially.\n")
    
    results = run_all_tests()
