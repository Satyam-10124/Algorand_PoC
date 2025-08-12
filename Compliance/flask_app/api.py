import os
import json
import hashlib
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import sys
import time
import datetime

# Add parent directory to path to import compliance modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_compliance_client import ComplianceClient
from document_compliance import approval_program, clear_state_program, compileTeal, Mode
from algosdk import account, mnemonic
from algosdk.v2client import algod

app = Flask(__name__)
app.secret_key = "compliance_app_secret_key"  # For flash messages

# Custom template filter for timestamps
@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    if not timestamp:
        return "N/A"
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Directory to store uploaded documents
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'documents')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Connect to Algorand TestNet
algod_address = "https://testnet-api.algonode.cloud"
algod_client = algod.AlgodClient("", algod_address)

# File path for accounts
ACCOUNTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'compliance_test_accounts.json')

# Load accounts
def load_accounts():
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # If accounts file doesn't exist, return empty dict
        return {}

# Helper function to get client for a specific role
def get_client(role='admin'):
    accounts = load_accounts()
    if role in accounts and "private_key" in accounts[role]:
        return ComplianceClient(algod_client, accounts[role]["private_key"])
    return None

# Deploy contract and generate TEAL files
def deploy_contract():
    admin_client = get_client('admin')
    if not admin_client:
        return None, "Admin account not found or invalid"
    
    try:
        # Generate TEAL files
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        approval_path = os.path.join(current_dir, "compliance_approval.teal")
        clear_path = os.path.join(current_dir, "compliance_clear.teal")
        
        # Generate TEAL from PyTeal
        with open(approval_path, "w") as f:
            compiled = compileTeal(approval_program(), Mode.Application, version=6)
            f.write(compiled)
        
        with open(clear_path, "w") as f:
            compiled = compileTeal(clear_state_program(), Mode.Application, version=6)
            f.write(compiled)
        
        # Read compiled TEAL
        with open(approval_path, "r") as f:
            approval_source = f.read()
        
        with open(clear_path, "r") as f:
            clear_source = f.read()
        
        # Compile programs
        approval_program_compiled = admin_client.compile_program(approval_source)
        clear_program_compiled = admin_client.compile_program(clear_source)
        
        # Deploy contract
        app_id = admin_client.deploy_contract(approval_program_compiled, clear_program_compiled)
        return app_id, None
    except Exception as e:
        return None, str(e)

# Calculate hash for a file
def calculate_file_hash(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
        return hashlib.sha256(content).hexdigest()

# API Routes

@app.route('/')
def index():
    # Load existing contracts
    contracts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contracts.json')
    contracts = []
    if os.path.exists(contracts_file):
        with open(contracts_file, 'r') as f:
            contracts = json.load(f)
    
    # Load account addresses
    accounts = load_accounts()
    admin_address = accounts.get('admin', {}).get('address', 'Not found')
    verifier_address = accounts.get('verifier', {}).get('address', 'Not found')
    
    # Calculate dashboard statistics
    compliant_count = 0
    pending_count = 0
    verifier_count = 1  # Default to at least one (the admin)
    
    # Get compliance status for each contract if available
    admin_client = get_client('admin')
    if admin_client:
        for contract in contracts:
            app_id = contract.get("app_id")
            if app_id:
                try:
                    status = admin_client.get_compliance_status(app_id)
                    if status.get("is_compliant", False):
                        compliant_count += 1
                    else:
                        pending_count += 1
                except Exception:
                    pending_count += 1
            
            # Check documents counts too
            for doc in contract.get("documents", []):
                if doc.get("is_compliant", False):
                    compliant_count += 1
                else:
                    pending_count += 1
    
    # Add deployment date for display in UI
    current_time = time.time()
    deployment_date = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d')
    
    return render_template('index.html', 
                          contracts=contracts, 
                          admin_address=admin_address,
                          verifier_address=verifier_address,
                          compliant_count=compliant_count,
                          pending_count=pending_count,
                          verifier_count=verifier_count,
                          deployment_date=deployment_date)

@app.route('/contracts', methods=['POST'])
def create_contract():
    app_id, error = deploy_contract()
    if error:
        flash(f"Error deploying contract: {error}", "danger")
        return redirect(url_for('index'))
    
    # Save contract ID to a file
    contracts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contracts.json')
    contracts = []
    if os.path.exists(contracts_file):
        with open(contracts_file, 'r') as f:
            contracts = json.load(f)
    
    contract_info = {
        "app_id": app_id,
        "created_at": time.time(),
        "documents": []
    }
    contracts.append(contract_info)
    
    with open(contracts_file, 'w') as f:
        json.dump(contracts, f)
    
    flash(f"Contract deployed successfully. App ID: {app_id}", "success")
    return redirect(url_for('index'))

@app.route('/contracts/<int:app_id>')
def view_contract(app_id):
    admin_client = get_client('admin')
    if not admin_client:
        flash("Admin account not found", "danger")
        return redirect(url_for('index'))
    
    try:
        status = admin_client.get_compliance_status(app_id)
        
        # Load account addresses
        accounts = load_accounts()
        admin_address = accounts.get('admin', {}).get('address', 'Not found')
        verifier_address = accounts.get('verifier', {}).get('address', 'Not found')
        
        # Load documents for this contract
        contracts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contracts.json')
        contracts = []
        if os.path.exists(contracts_file):
            with open(contracts_file, 'r') as f:
                contracts = json.load(f)
        
        contract = next((c for c in contracts if c["app_id"] == app_id), None)
        documents = contract.get("documents", []) if contract else []
        
        return render_template('contract.html', app_id=app_id, status=status, 
                             admin_address=admin_address,
                             verifier_address=verifier_address,
                             documents=documents,
                             explorer_url=f"https://testnet.explorer.perawallet.app/application/{app_id}")
    except Exception as e:
        flash(f"Error retrieving contract status: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/contracts/<int:app_id>/opt-in', methods=['POST'])
def contract_opt_in(app_id):
    role = request.form.get('role', 'admin')
    client = get_client(role)
    
    if not client:
        flash(f"{role.capitalize()} account not found", "danger")
        return redirect(url_for('view_contract', app_id=app_id))
    
    try:
        client.opt_in(app_id)
        flash(f"{role.capitalize()} opted in successfully", "success")
    except Exception as e:
        flash(f"Error opting in: {str(e)}", "danger")
    
    return redirect(url_for('view_contract', app_id=app_id))

@app.route('/contracts/<int:app_id>/documents', methods=['POST'])
def register_document(app_id):
    # Check if the admin client is available
    admin_client = get_client('admin')
    if not admin_client:
        flash("Admin account not found", "danger")
        return redirect(url_for('view_contract', app_id=app_id))
    
    # Check if a file was submitted
    if 'document' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('view_contract', app_id=app_id))
    
    file = request.files['document']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('view_contract', app_id=app_id))
    
    # Save the file locally
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Calculate file hash
    file_hash = calculate_file_hash(file_path)
    
    # Get document details
    version = request.form.get('version', '1.0.0')
    expiry_days = int(request.form.get('expiry_days', '365'))
    expiry_timestamp = int(time.time()) + (expiry_days * 24 * 60 * 60)
    
    try:
        # Register document in the contract
        admin_client.register_document(app_id, file_hash, version, expiry_timestamp)
        
        # Update contracts.json to include this document
        contracts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contracts.json')
        contracts = []
        if os.path.exists(contracts_file):
            with open(contracts_file, 'r') as f:
                contracts = json.load(f)
        
        for contract in contracts:
            if contract["app_id"] == app_id:
                if "documents" not in contract:
                    contract["documents"] = []
                    
                document_info = {
                    "hash": file_hash,
                    "filename": filename,
                    "version": version,
                    "registered_at": time.time(),
                    "expiry_timestamp": expiry_timestamp
                }
                contract["documents"].append(document_info)
                break
        
        with open(contracts_file, 'w') as f:
            json.dump(contracts, f)
        
        flash('Document registered successfully', 'success')
    except Exception as e:
        flash(f'Error registering document: {str(e)}', 'danger')
    
    return redirect(url_for('view_contract', app_id=app_id))

@app.route('/contracts/<int:app_id>/verifiers', methods=['POST'])
def assign_verifier(app_id):
    admin_client = get_client('admin')
    if not admin_client:
        flash("Admin account not found", "danger")
        return redirect(url_for('view_contract', app_id=app_id))
    
    verifier_address = request.form.get('verifier_address')
    if not verifier_address:
        flash("Verifier address required", "danger")
        return redirect(url_for('view_contract', app_id=app_id))
    
    try:
        admin_client.assign_verifier(app_id, verifier_address)
        flash(f"Address {verifier_address} assigned as verifier", "success")
    except Exception as e:
        flash(f"Error assigning verifier: {str(e)}", "danger")
    
    return redirect(url_for('view_contract', app_id=app_id))

@app.route('/contracts/<int:app_id>/verify', methods=['POST'])
def verify_compliance(app_id):
    verifier_client = get_client('verifier')
    if not verifier_client:
        flash("Verifier account not found", "danger")
        return redirect(url_for('view_contract', app_id=app_id))
    
    try:
        verifier_client.verify_compliance(app_id)
        flash("Compliance verification completed", "success")
    except Exception as e:
        flash(f"Error verifying compliance: {str(e)}", "danger")
    
    return redirect(url_for('view_contract', app_id=app_id))

@app.route('/documents/<filename>')
def download_document(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/documents/<filename>/preview')
def preview_document(filename):
    # In a production app, this would render an actual preview
    # For this implementation, we'll just show basic metadata
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        flash("Document not found", "danger")
        return redirect(url_for('index'))
    
    # Calculate file hash to verify it matches what's on the blockchain
    file_hash = calculate_file_hash(file_path)
    
    # Get file stats
    stats = os.stat(file_path)
    file_size = stats.st_size
    last_modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    # Try to determine file type
    file_ext = os.path.splitext(filename)[1].lower()
    file_type = "Unknown"
    if file_ext in [".txt", ".md"]:
        file_type = "Text Document"
    elif file_ext in [".pdf"]:
        file_type = "PDF Document"
    elif file_ext in [".doc", ".docx"]:
        file_type = "Word Document"
    elif file_ext in [".jpg", ".jpeg", ".png", ".gif"]:
        file_type = "Image"
    
    preview_data = {
        "filename": filename,
        "hash": file_hash,
        "size": f"{file_size / 1024:.2f} KB",
        "type": file_type,
        "last_modified": last_modified
    }
    
    return render_template('preview.html', document=preview_data)

@app.route('/api/transactions/<int:app_id>')
def get_transactions(app_id):
    """API endpoint to fetch recent blockchain transactions for a contract"""
    # In a production app, this would query the Algorand indexer API
    # For this demo, we'll return simulated transactions
    
    # Sample transaction data
    transactions = [
        {
            "type": "Contract Deployment",
            "status": "confirmed",
            "timestamp": int(time.time()) - 3600,
            "txid": f"TX{app_id}DEPLOY",
            "sender": "Admin",
            "app_id": app_id
        },
        {
            "type": "Document Registration",
            "status": "confirmed",
            "timestamp": int(time.time()) - 1800,
            "txid": f"TX{app_id}DOC1",
            "sender": "Admin",
            "app_id": app_id
        },
        {
            "type": "Verifier Assignment",
            "status": "pending",
            "timestamp": int(time.time()) - 300,
            "txid": f"TX{app_id}VERIFY",
            "sender": "Admin",
            "app_id": app_id
        }
    ]
    
    return jsonify({"transactions": transactions})

@app.route('/api/contract-stats')
def get_contract_stats():
    """API endpoint to fetch statistics for the compliance contracts dashboard"""
    # Load existing contracts
    contracts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contracts.json')
    contracts = []
    if os.path.exists(contracts_file):
        with open(contracts_file, 'r') as f:
            contracts = json.load(f)
    
    # Calculate statistics
    total_contracts = len(contracts)
    total_documents = sum(len(contract.get("documents", [])) for contract in contracts)
    
    # Count compliant documents
    compliant_count = 0
    pending_count = 0
    admin_client = get_client('admin')
    
    if admin_client:
        for contract in contracts:
            app_id = contract.get("app_id")
            if app_id:
                try:
                    status = admin_client.get_compliance_status(app_id)
                    if status.get("is_compliant", False):
                        compliant_count += 1
                    else:
                        pending_count += 1
                except:
                    pending_count += 1
    
    stats = {
        "total_contracts": total_contracts,
        "total_documents": total_documents,
        "compliant_documents": compliant_count,
        "pending_documents": pending_count
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
