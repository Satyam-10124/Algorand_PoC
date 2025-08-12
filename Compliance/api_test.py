#!/usr/bin/env python3
# api_test.py - Test the compliance attestation contract via Flask API

import requests
import json
import time
import os
import argparse
import hashlib
import sys
import base64
from algosdk import account, mnemonic

# Configuration
API_BASE_URL = "http://localhost:5002"  # Make sure this matches your Flask app port
ACCOUNTS_FILE = "compliance_test_accounts.json"
SAMPLE_DOCUMENT = "sample_compliance_document.txt"

def generate_accounts():
    """Generate and save test accounts for admin and verifier"""
    admin_private_key, admin_address = account.generate_account()
    verifier_private_key, verifier_address = account.generate_account()
    
    accounts = {
        "admin": {
            "address": admin_address,
            "private_key": admin_private_key,
            "mnemonic": mnemonic.from_private_key(admin_private_key)
        },
        "verifier": {
            "address": verifier_address,
            "private_key": verifier_private_key,
            "mnemonic": mnemonic.from_private_key(verifier_private_key)
        }
    }
    
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)
    
    print(f"Generated accounts and saved to {ACCOUNTS_FILE}")
    print(f"Admin address: {admin_address}")
    print(f"Verifier address: {verifier_address}")
    
    return accounts

def load_accounts():
    """Load test accounts from file"""
    if not os.path.exists(ACCOUNTS_FILE):
        print(f"Accounts file {ACCOUNTS_FILE} not found. Generating new accounts.")
        return generate_accounts()
    
    with open(ACCOUNTS_FILE, "r") as f:
        accounts = json.load(f)
    
    print("Successfully loaded account information")
    return accounts

def check_api_status():
    """Check if the Flask API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/contract-stats")
        if response.status_code == 200:
            print("✅ Flask API is running")
            return True
        else:
            print(f"❌ Flask API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Flask API at {API_BASE_URL}")
        print("Make sure the Flask application is running (python3 flask_app/api.py)")
        return False

def create_sample_document():
    """Create a sample compliance document for testing"""
    document_content = """
    {
        "document_type": "Compliance Certificate",
        "issuer": "Test Organization",
        "subject": "Test Product",
        "version": "1.0.0",
        "issued_date": "2025-08-11",
        "valid_until": "2026-08-11",
        "compliance_standards": [
            "ISO 27001",
            "GDPR",
            "SOC 2"
        ],
        "certificate_id": "CERT-2025-08-11-001",
        "verification_url": "https://example.com/verify/CERT-2025-08-11-001",
        "digital_signature": "ab12cd34ef56gh78ij90"
    }
    """
    
    with open(SAMPLE_DOCUMENT, "w") as f:
        f.write(document_content)
    
    # Calculate document hash
    doc_hash = hashlib.sha256(document_content.encode()).hexdigest()
    
    print(f"Created sample document: {SAMPLE_DOCUMENT}")
    print(f"Document hash: {doc_hash}")
    
    return document_content, doc_hash

def run_test():
    """Execute the full test workflow using the Flask API"""
    # Step 1: Check API connection
    if not check_api_status():
        return False
    
    # Step 2: Load accounts
    accounts = load_accounts()
    admin_address = accounts["admin"]["address"]
    verifier_address = accounts["verifier"]["address"]
    
    # Step 3: Create sample document
    document_content, doc_hash = create_sample_document()
    
    print("\n=== STEP 1: Creating Compliance Contract ===")
    response = requests.post(f"{API_BASE_URL}/contracts")
    if response.status_code != 200:
        print(f"❌ Failed to create contract: {response.status_code}")
        return False
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ Contract creation error: {result.get('error', 'Unknown error')}")
        return False
    
    app_id = result.get("app_id")
    print(f"✅ Contract created with App ID: {app_id}")
    
    # Wait for transaction confirmation
    print("Waiting for transaction confirmation...")
    time.sleep(5)
    
    print("\n=== STEP 2: Opt-In to Contract ===")
    # Admin is automatically opted in during contract creation
    print("✅ Admin automatically opted in during contract creation")
    
    # Opt-in verifier account
    response = requests.post(f"{API_BASE_URL}/contracts/{app_id}/opt-in", json={
        "address": verifier_address
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to opt-in verifier: {response.status_code}")
        return False
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ Verifier opt-in error: {result.get('error', 'Unknown error')}")
        return False
    
    print(f"✅ Verifier opted in to contract")
    time.sleep(5)
    
    print("\n=== STEP 3: Registering Document ===")
    with open(SAMPLE_DOCUMENT, 'rb') as f:
        files = {'document': (SAMPLE_DOCUMENT, f, 'application/json')}
        response = requests.post(
            f"{API_BASE_URL}/contracts/{app_id}/documents",
            data={
                'document_name': 'Test Compliance Document',
                'version': '1.0.0',
                'expiration_days': '365'
            },
            files=files
        )
    
    if response.status_code != 200:
        print(f"❌ Failed to register document: {response.status_code}")
        return False
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ Document registration error: {result.get('error', 'Unknown error')}")
        return False
    
    print(f"✅ Document registered successfully")
    time.sleep(5)
    
    print("\n=== STEP 4: Assigning Verifier ===")
    response = requests.post(f"{API_BASE_URL}/contracts/{app_id}/verifiers", json={
        "verifier_address": verifier_address
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to assign verifier: {response.status_code}")
        return False
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ Verifier assignment error: {result.get('error', 'Unknown error')}")
        return False
    
    print(f"✅ Verifier assigned successfully")
    time.sleep(5)
    
    print("\n=== STEP 5: Marking Document as Compliant ===")
    response = requests.post(f"{API_BASE_URL}/contracts/{app_id}/verify", json={
        "address": verifier_address,
        "document_hash": doc_hash
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to mark document as compliant: {response.status_code}")
        return False
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ Compliance marking error: {result.get('error', 'Unknown error')}")
        return False
    
    print(f"✅ Document marked as compliant")
    time.sleep(5)
    
    print("\n=== STEP 6: Retrieving Contract Details ===")
    response = requests.get(f"{API_BASE_URL}/contracts/{app_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to retrieve contract details: {response.status_code}")
        return False
    
    # Note: This returns HTML, not JSON, since the API returns the contract template
    # Just check if we get a successful response
    print(f"✅ Successfully retrieved contract details")
    
    print("\n=== STEP 7: Checking Document Preview ===")
    # Get the filename from the contracts endpoint
    response = requests.get(f"{API_BASE_URL}/api/contract/{app_id}")
    if response.status_code != 200:
        print(f"❌ Failed to retrieve contract API details: {response.status_code}")
    else:
        contract_data = response.json()
        if contract_data.get("documents"):
            for doc in contract_data.get("documents", []):
                filename = doc.get("filename")
                if filename:
                    doc_preview_url = f"{API_BASE_URL}/documents/{filename}/preview"
                    response = requests.get(doc_preview_url)
                    if response.status_code == 200:
                        print(f"✅ Successfully retrieved document preview for {filename}")
                    else:
                        print(f"❌ Failed to retrieve document preview: {response.status_code}")
    
    print("\n=== STEP 8: Checking Dashboard Stats ===")
    response = requests.get(f"{API_BASE_URL}/api/contract-stats")
    
    if response.status_code != 200:
        print(f"❌ Failed to retrieve dashboard stats: {response.status_code}")
        return False
    
    stats = response.json()
    print(f"Dashboard Statistics:")
    print(f"  Total Contracts: {stats.get('total_contracts', 'N/A')}")
    print(f"  Compliant Documents: {stats.get('compliant_documents', 'N/A')}")
    print(f"  Pending Documents: {stats.get('pending_documents', 'N/A')}")
    
    print("\n=== TEST COMPLETED SUCCESSFULLY ===")
    print(f"Contract App ID: {app_id}")
    print(f"View contract details at: {API_BASE_URL}/contracts/{app_id}")
    print(f"View blockchain explorer: https://testnet.explorer.perawallet.app/application/{app_id}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Test the Algorand Compliance API")
    parser.add_argument("--new-accounts", action="store_true", help="Generate new test accounts")
    parser.add_argument("--check-api", action="store_true", help="Only check if API is running")
    args = parser.parse_args()
    
    if args.new_accounts:
        generate_accounts()
        return
    
    if args.check_api:
        check_api_status()
        return
    
    run_test()

if __name__ == "__main__":
    main()
