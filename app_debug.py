#!/usr/bin/env python3
# app.py - Flask API for the compliance document system

from flask import Flask, request, jsonify, render_template
from Compliance.document_compliance_client import ComplianceClient
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.v2client import indexer
import os
import hashlib
import datetime
import json
import traceback
import sys

app = Flask(__name__, 
    static_folder='frontend/build/static',
    template_folder='frontend/build')

# Configure Flask for more verbose error logging
app.config['PROPAGATE_EXCEPTIONS'] = True

# Configuration
# Public TestNet node details
algod_address = "https://testnet-api.algonode.cloud"
algod_token = ""

# Initialize Algod client
print(f"Initializing Algod client with {algod_address}")
try:
    algod_client = algod.AlgodClient(algod_token, algod_address)
    # Test algod connection
    node_status = algod_client.status()
    print(f"Successfully connected to Algod. Node status: {node_status}")
except Exception as e:
    print(f"ERROR initializing Algod client: {str(e)}")
    print(traceback.format_exc())
    sys.exit(1)

# Initialize Indexer client for TestNet - we'll use this for account info
indexer_address = "https://testnet-idx.algonode.cloud"
indexer_token = ""
print(f"Initializing Indexer client with {indexer_address}")
try:
    indexer_client = indexer.IndexerClient(indexer_token, indexer_address)
    # Test indexer connection
    health = indexer_client.health()
    print(f"Successfully connected to Indexer. Health: {health}")
except Exception as e:
    print(f"ERROR initializing Indexer client: {str(e)}")
    print(traceback.format_exc())
    sys.exit(1)

# Load admin/verifier accounts from config
try:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Compliance/compliance_test_accounts.json")
    print(f"Loading accounts from {config_path}")
    with open(config_path) as f:
        admin_verifier_accounts = json.load(f)
    admin_private_key = admin_verifier_accounts.get('admin', {}).get('private_key', '')
    verifier_private_key = admin_verifier_accounts.get('verifier', {}).get('private_key', '')
    verifier_address = admin_verifier_accounts.get('verifier', {}).get('address', '')
    admin_address = admin_verifier_accounts.get('admin', {}).get('address', '')
    # Get App ID - in a production environment you would store this in a config file
    # For now we'll hardcode the App ID for the existing deployed contract
    APP_ID = 744059516  # Replace with your actual deployed app ID
    print(f"Successfully loaded accounts and APP_ID {APP_ID}")
    print(f"Admin address: {admin_address}")
    print(f"Verifier address: {verifier_address}")
    print(f"Admin key loaded: {'Yes' if admin_private_key else 'No'}")
    print(f"Verifier key loaded: {'Yes' if verifier_private_key else 'No'}")
except Exception as e:
    print(f"Error loading accounts: {str(e)}")
    print(traceback.format_exc())
    admin_private_key = ""
    verifier_private_key = ""
    verifier_address = ""
    admin_address = ""
    APP_ID = None

# Utility function to generate document hash
def generate_document_hash(content):
    """Generate SHA-256 hash of document content"""
    return hashlib.sha256(content.encode()).hexdigest()

# Routes for the API - focus on document handling and verification
@app.route('/api/document/hash', methods=['POST'])
def get_document_hash():
    """Get hash for a document without uploading to blockchain"""
    try:
        data = request.json
        document_content = data.get('document_content')
        
        if not document_content:
            return jsonify({"success": False, "error": "Document content is required"}), 400
            
        # Generate hash
        doc_hash = generate_document_hash(document_content)
        
        return jsonify({
            "success": True, 
            "document_hash": doc_hash,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        print(f"ERROR in get_document_hash: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
        
@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Handle document upload and generate hash"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Read file content
        content = file.read().decode('utf-8', errors='ignore')
        
        # Generate hash
        doc_hash = generate_document_hash(content)
        
        return jsonify({
            "success": True,
            "hash": doc_hash,
            "filename": file.filename,
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        print(f"ERROR in upload_document: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/document/register', methods=['POST'])
def register_document():
    """Register a document with the compliance contract - ADMIN ONLY"""
    try:
        print("Starting register_document endpoint...")
        data = request.json
        print(f"Request data: {data}")
        verifier_role = data.get('role')
        provided_key = data.get('private_key')
        document_content = data.get('document_content')
        version = data.get('version')
        
        print(f"Role: {verifier_role}, Content provided: {'Yes' if document_content else 'No'}, Version: {version}")
        
        # Only allow admin to register documents
        if verifier_role != 'admin' or provided_key != admin_private_key:
            print(f"Authentication failed. Role: {verifier_role}")
            return jsonify({"success": False, "error": "Unauthorized: Only admin can register documents"}), 403
            
        if not APP_ID:
            return jsonify({"success": False, "error": "No deployed app ID found"}), 400
        
        # Initialize client
        print("Initializing ComplianceClient...")
        client = ComplianceClient(algod_client, admin_private_key)
        
        # Register document
        print(f"Calling register_document with APP_ID: {APP_ID}")
        client.register_document(APP_ID, document_content, version)
        print("Document registered successfully")
        
        # Generate hash for reference
        doc_hash = generate_document_hash(document_content)
        
        return jsonify({
            "success": True,
            "document_hash": doc_hash
        })
    except Exception as e:
        print(f"ERROR in register_document: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/verifier/assign', methods=['POST'])
def assign_verifier():
    """Assign a verifier to the compliance contract - ADMIN ONLY"""
    try:
        print("Starting assign_verifier endpoint...")
        data = request.json
        print(f"Request data: {data}")
        verifier_role = data.get('role')
        provided_key = data.get('private_key')
        new_verifier_address = data.get('verifier_address')
        
        print(f"Role: {verifier_role}, Verifier address: {new_verifier_address}")
        
        # Only allow admin to assign verifiers
        if verifier_role != 'admin' or provided_key != admin_private_key:
            print(f"Authentication failed. Role: {verifier_role}")
            return jsonify({"success": False, "error": "Unauthorized: Only admin can assign verifiers"}), 403
            
        if not APP_ID:
            return jsonify({"success": False, "error": "No deployed app ID found"}), 400
            
        if not new_verifier_address:
            return jsonify({"success": False, "error": "Verifier address is required"}), 400
        
        # Initialize client
        print("Initializing ComplianceClient...")
        client = ComplianceClient(algod_client, admin_private_key)
        
        # Assign verifier
        print(f"Calling assign_verifier with APP_ID: {APP_ID} and verifier: {new_verifier_address}")
        client.assign_verifier(APP_ID, new_verifier_address)
        print("Verifier assigned successfully")
        
        return jsonify({
            "success": True,
            "verifier_address": new_verifier_address
        })
    except Exception as e:
        print(f"ERROR in assign_verifier: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/document/verify', methods=['POST'])
def verify_compliance():
    """Verify compliance of a document - VERIFIER ONLY"""
    try:
        print("Starting verify_compliance endpoint...")
        data = request.json
        print(f"Request data: {data}")
        verifier_role = data.get('role')
        provided_key = data.get('private_key')
        document_hash = data.get('document_hash')
        compliance_status = data.get('status', 'compliant')  # Default to compliant
        
        print(f"Role: {verifier_role}, Document hash: {document_hash}, Status: {compliance_status}")
        
        # Only allow verifiers to verify compliance
        if verifier_role != 'verifier' or provided_key != verifier_private_key:
            print(f"Authentication failed. Role: {verifier_role}")
            return jsonify({"success": False, "error": "Unauthorized: Only verifiers can verify compliance"}), 403
            
        if not APP_ID:
            return jsonify({"success": False, "error": "No deployed app ID found"}), 400
            
        if not document_hash:
            return jsonify({"success": False, "error": "Document hash is required"}), 400
            
        # Initialize client
        print("Initializing ComplianceClient...")
        client = ComplianceClient(algod_client, verifier_private_key)
        
        # Verify compliance
        print(f"Calling verify_compliance with APP_ID: {APP_ID}, hash: {document_hash}, status: {compliance_status}")
        client.verify_compliance(APP_ID, document_hash, compliance_status)
        print("Compliance verification successful")
        
        return jsonify({
            "success": True,
            "document_hash": document_hash,
            "status": compliance_status,
            "verifier": verifier_address
        })
    except Exception as e:
        print(f"ERROR in verify_compliance: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/document/status', methods=['GET'])
def get_compliance_status():
    """Get compliance status of the document - Public endpoint"""
    try:
        print("Starting get_compliance_status endpoint...")
        if not APP_ID:
            return jsonify({"success": False, "error": "No deployed app ID found"}), 400
            
        # Use admin key for read-only operations
        # In production, use a dedicated read-only account
        print("Initializing ComplianceClient...")
        client = ComplianceClient(algod_client, admin_private_key)
        
        # Get compliance status
        print(f"Calling get_compliance_status with APP_ID: {APP_ID}")
        status = client.get_compliance_status(APP_ID)
        print(f"Retrieved status: {status}")
        
        # Convert timestamp to human-readable format if available
        if status.get('attestation_date'):
            status['attestation_date_readable'] = datetime.datetime.fromtimestamp(
                status['attestation_date']).strftime('%Y-%m-%d %H:%M:%S')
        
        if status.get('expiration_date'):
            status['expiration_date_readable'] = datetime.datetime.fromtimestamp(
                status['expiration_date']).strftime('%Y-%m-%d %H:%M:%S')
            
            # Add days until expiration
            now = datetime.datetime.now().timestamp()
            if now < status['expiration_date']:
                days_remaining = (status['expiration_date'] - now) / (60 * 60 * 24)
                status['days_until_expiration'] = int(days_remaining)
            else:
                status['days_until_expiration'] = 0
        
        return jsonify({"success": True, "status": status})
    except Exception as e:
        print(f"ERROR in get_compliance_status: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
        
@app.route('/api/login/verifier', methods=['POST'])
def verifier_login():
    """Login as a verifier"""
    try:
        data = request.json
        provided_key = data.get('private_key')
        
        # Check if this is a valid verifier
        if provided_key == verifier_private_key:
            address = verifier_address
            role = 'verifier'
        elif provided_key == admin_private_key:
            address = admin_address
            role = 'admin'
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
            
        return jsonify({
            "success": True,
            "address": address,
            "role": role
        })
    except Exception as e:
        print(f"ERROR in verifier_login: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/account/status', methods=['GET'])
def account_status():
    """Check if an account is a verifier and if it's opted in to the compliance contract"""
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({"success": False, "error": "Address parameter is required"}), 400
            
        # Check if this is a verifier or admin account
        is_verifier = (address == verifier_address)
        is_admin = (address == admin_address)
        
        # Get account information from indexer
        account_info = indexer_client.account_info(address)
        
        # Check if account is opted into the app
        is_opted_in = False
        local_state = None
        
        if 'account' in account_info and 'apps-local-state' in account_info['account']:
            for app_state in account_info['account']['apps-local-state']:
                if app_state['id'] == APP_ID:
                    is_opted_in = True
                    local_state = app_state.get('key-value', [])
                    break
                    
        return jsonify({
            "success": True, 
            "address": address,
            "is_verifier": is_verifier,
            "is_admin": is_admin,
            "is_opted_in": is_opted_in,
            "account_info": account_info.get('account', {}),
            "local_state": local_state
        })
    except Exception as e:
        print(f"ERROR in account_status: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

# Serve React frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    return render_template('index.html')

if __name__ == '__main__':
    print("Starting Flask server with enhanced debugging...")
    app.run(debug=True, port=5044)
