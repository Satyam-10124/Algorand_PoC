#!/usr/bin/env python3
# test_compliance.py - Test the compliance attestation contract

import base64
import json
import sys
import time
import os
from algosdk import account, mnemonic
from algosdk.v2client import algod
from document_compliance_client import ComplianceClient, wait_for_confirmation

def generate_account():
    private_key, address = account.generate_account()
    print(f"Generated account: {address}")
    print(f"Save this mnemonic: {mnemonic.from_private_key(private_key)}")
    return private_key, address

def main():
    # Check command line arguments
    if "--help" in sys.argv:
        print("Usage: python test_compliance.py [--new-accounts] [--check-balance]")
        return
        
    # Connect to Algorand testnet
    print("Connecting to Algorand TestNet...")
    algod_client = algod.AlgodClient("", "https://testnet-api.algonode.cloud")
    
    try:
        algod_client.status()
        print("Successfully connected to Algorand TestNet!")
    except Exception as e:
        print(f"Error connecting to Algorand network: {e}")
        return
    
    # Create or load accounts
    try:
        if "--new-accounts" in sys.argv or not os.path.exists("compliance_test_accounts.json"):
            print("Generating new test accounts...")
            admin_private_key, admin_address = generate_account()
            verifier_private_key, verifier_address = generate_account()
            
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
            
            with open("compliance_test_accounts.json", "w") as f:
                json.dump(accounts, f, indent=4)
                
            print("\nTest accounts generated and saved to compliance_test_accounts.json")
            print("\nIMPORTANT: Before continuing, fund these accounts with TestNet Algos from https://bank.testnet.algorand.network/")
            print(f"Admin address: {admin_address}")
            print(f"Verifier address: {verifier_address}")
            return
        else:
            with open("compliance_test_accounts.json", "r") as f:
                accounts = json.load(f)
                admin_address = accounts["admin"]["address"]
                admin_private_key = accounts["admin"]["private_key"]
                verifier_address = accounts["verifier"]["address"]
                verifier_private_key = accounts["verifier"]["private_key"]
                
            print("Successfully loaded account information")
    except Exception as e:
        print(f"Error handling accounts: {e}")
        return
    
    # Check account balances if requested
    if "--check-balance" in sys.argv:
        print("\nChecking account balances...")
        try:
            admin_info = algod_client.account_info(admin_address)
            verifier_info = algod_client.account_info(verifier_address)
            
            print(f"Admin account balance: {admin_info['amount'] / 1000000} ALGO")
            print(f"Verifier account balance: {verifier_info['amount'] / 1000000} ALGO")
            
            if admin_info['amount'] < 1000000 or verifier_info['amount'] < 1000000:
                print("\nWARNING: One or more accounts have less than 1 ALGO.")
                print("Please fund your accounts using the Algorand TestNet Dispenser.")
                print("https://bank.testnet.algorand.network/")
                return
        except Exception as e:
            print(f"Error checking balances: {e}")
            return
    
    # Create compliance client
    admin_client = ComplianceClient(algod_client, admin_private_key)
    verifier_client = ComplianceClient(algod_client, verifier_private_key)
    
    print("\n=== STEP 1: Deploying Compliance Contract ===")
    print("Compiling contract...")
    
    # Make sure we have the TEAL files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    approval_path = os.path.join(current_dir, "compliance_approval.teal")
    clear_path = os.path.join(current_dir, "compliance_clear.teal")
    
    if not os.path.exists(approval_path) or not os.path.exists(clear_path):
        print("Compiling PyTeal to TEAL...")
        # Import and directly run the compilation functions
        from document_compliance import approval_program, clear_state_program, compileTeal, Mode
        
        # Generate approval program TEAL
        with open(approval_path, "w") as f:
            compiled = compileTeal(approval_program(), Mode.Application, version=6)
            f.write(compiled)
        
        # Generate clear program TEAL
        with open(clear_path, "w") as f:
            compiled = compileTeal(clear_state_program(), Mode.Application, version=6)
            f.write(compiled)
            
        print("TEAL files generated")
    
    # Read compiled TEAL files
    with open(approval_path, "r") as f:
        approval_source = f.read()
        
    with open(clear_path, "r") as f:
        clear_source = f.read()
    
    print("Compiling TEAL to bytecode...")
    # Compile programs
    approval_program = admin_client.compile_program(approval_source)
    clear_program = admin_client.compile_program(clear_source)
    
    print("Deploying contract...")
    # Deploy contract
    app_id = admin_client.deploy_contract(approval_program, clear_program)
    print(f"Contract deployed! App ID: {app_id}")
    
    print("\n=== STEP 2: Opting In ===")
    print("Admin opting in...")
    admin_client.opt_in(app_id)
    print("Verifier opting in...")
    verifier_client.opt_in(app_id)
    
    print("\n=== STEP 3: Registering Compliance Document ===")
    # Create a sample SBOM document
    sbom_document = """
    {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
        "version": 1,
        "metadata": {
            "timestamp": "2022-01-01T18:25:43.511Z",
            "tools": [
                {
                    "vendor": "CompliLedger",
                    "name": "AlgoCompli",
                    "version": "1.0.0"
                }
            ],
            "authors": [
                {
                    "name": "Test User"
                }
            ],
            "component": {
                "type": "application",
                "name": "Test Compliance App",
                "version": "1.0.0"
            }
        }
    }
    """
    
    admin_client.register_document(app_id, sbom_document, "1.0.0")
    print("Compliance document registered successfully!")
    
    print("\n=== STEP 4: Assigning Verifier Role ===")
    admin_client.assign_verifier(app_id, verifier_address)
    print(f"Address {verifier_address} assigned as a verifier")
    
    print("\n=== STEP 5: Verifying Compliance ===")
    verifier_client.verify_compliance(app_id)
    print("Compliance verification performed")
    
    print("\n=== STEP 6: Checking Compliance Status ===")
    status = admin_client.get_compliance_status(app_id)
    print("\n=== COMPLIANCE RECORD ===")
    print(f"Status: {status['status']}")
    print(f"Document Hash: {status['document_hash']}")
    print(f"Version: {status['version']}")
    if status['attestation_date']:
        print(f"Attestation Date: {time.ctime(status['attestation_date'])}")
    if status['expiration_date']:
        print(f"Expiration Date: {time.ctime(status['expiration_date'])}")
    print("========================")
    
    print(f"\nCompliance App ID: {app_id}")
    print(f"You can view this contract at: https://testnet.explorer.perawallet.app/application/{app_id}")
    print("\n=== TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
