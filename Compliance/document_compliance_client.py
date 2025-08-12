#!/usr/bin/env python3
# document_compliance_client.py - Client to interact with the compliance contract

from algosdk.v2client import algod
from algosdk import account, transaction
from algosdk.encoding import decode_address
import base64
import hashlib
import time

class ComplianceClient:
    def __init__(self, algod_client, private_key):
        self.algod_client = algod_client
        self.private_key = private_key
        self.public_key = account.address_from_private_key(private_key)
    
    def compile_program(self, source_code):
        compile_response = self.algod_client.compile(source_code)
        return base64.b64decode(compile_response['result'])
    
    def deploy_contract(self, approval_program, clear_program):
        # Set schema for global & local state
        global_schema = transaction.StateSchema(num_uints=2, num_byte_slices=5)
        local_schema = transaction.StateSchema(num_uints=1, num_byte_slices=0)
        
        # Get suggested parameters
        params = self.algod_client.suggested_params()
        
        # Create unsigned transaction
        txn = transaction.ApplicationCreateTxn(
            sender=self.public_key,
            sp=params,
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=approval_program,
            clear_program=clear_program,
            global_schema=global_schema,
            local_schema=local_schema
        )
        
        # Sign transaction
        signed_txn = txn.sign(self.private_key)
        tx_id = signed_txn.transaction.get_txid()
        
        # Submit transaction
        self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        wait_for_confirmation(self.algod_client, tx_id, 5)
        
        # Get the new application ID
        transaction_response = self.algod_client.pending_transaction_info(tx_id)
        app_id = transaction_response["application-index"]
        return app_id
    
    def opt_in(self, app_id):
        # Get suggested parameters
        params = self.algod_client.suggested_params()
        
        # Create unsigned transaction
        txn = transaction.ApplicationOptInTxn(
            sender=self.public_key,
            sp=params,
            index=app_id
        )
        
        # Sign transaction
        signed_txn = txn.sign(self.private_key)
        tx_id = signed_txn.transaction.get_txid()
        
        # Submit transaction
        self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        wait_for_confirmation(self.algod_client, tx_id, 5)
    
    def register_document(self, app_id, document_content, version):
        # Calculate document hash
        doc_hash = hashlib.sha256(document_content.encode()).hexdigest()
        
        # Set expiration date to 1 year from now
        expiry = int(time.time()) + 31536000  # 365 days in seconds
        
        # Get suggested parameters
        params = self.algod_client.suggested_params()
        
        # Create unsigned transaction
        txn = transaction.ApplicationNoOpTxn(
            sender=self.public_key,
            sp=params,
            index=app_id,
            app_args=[b"register", doc_hash.encode(), version.encode(), expiry.to_bytes(8, 'big')]
        )
        
        # Sign transaction
        signed_txn = txn.sign(self.private_key)
        tx_id = signed_txn.transaction.get_txid()
        
        # Submit transaction
        self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        wait_for_confirmation(self.algod_client, tx_id, 5)
        
    def assign_verifier(self, app_id, verifier_address):
        # Get suggested parameters
        params = self.algod_client.suggested_params()
        
        # Create unsigned transaction
        txn = transaction.ApplicationNoOpTxn(
            sender=self.public_key,
            sp=params,
            index=app_id,
            app_args=[b"assign_verifier", b"1"],  # Adding a second dummy argument to match contract expectation
            accounts=[verifier_address]
        )
        
        # Sign transaction
        signed_txn = txn.sign(self.private_key)
        tx_id = signed_txn.transaction.get_txid()
        
        # Submit transaction
        self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        wait_for_confirmation(self.algod_client, tx_id, 5)
    
    def verify_compliance(self, app_id):
        # Get suggested parameters
        params = self.algod_client.suggested_params()
        
        # Create unsigned transaction
        txn = transaction.ApplicationNoOpTxn(
            sender=self.public_key,
            sp=params,
            index=app_id,
            app_args=[b"verify"]
        )
        
        # Sign transaction
        signed_txn = txn.sign(self.private_key)
        tx_id = signed_txn.transaction.get_txid()
        
        # Submit transaction
        self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        wait_for_confirmation(self.algod_client, tx_id, 5)
    
    def get_compliance_status(self, app_id):
        # Get application information
        app_info = self.algod_client.application_info(app_id)
        global_state = app_info['params']['global-state']
        
        # Extract and decode values
        status = None
        doc_hash = None
        version = None
        attestation_date = None
        expiration_date = None
        
        for item in global_state:
            key = base64.b64decode(item['key']).decode()
            if key == "status":
                if item['value']['type'] == 1:  # bytes
                    status = base64.b64decode(item['value']['bytes']).decode()
            elif key == "document_hash":
                if item['value']['type'] == 1:  # bytes
                    doc_hash = base64.b64decode(item['value']['bytes']).decode()
            elif key == "document_version":
                if item['value']['type'] == 1:  # bytes
                    version = base64.b64decode(item['value']['bytes']).decode()
            elif key == "attestation_date":
                if item['value']['type'] == 2:  # uint
                    attestation_date = item['value']['uint']
            elif key == "expiration_date":
                if item['value']['type'] == 2:  # uint
                    expiration_date = item['value']['uint']
        
        return {
            "status": status,
            "document_hash": doc_hash,
            "version": version,
            "attestation_date": attestation_date,
            "expiration_date": expiration_date
        }

# Helper function to wait for confirmation
def wait_for_confirmation(client, txid, timeout):
    start_round = client.status()["last-round"] + 1
    current_round = start_round
    
    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(txid)
        except Exception:
            return False
            
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
            
        params = client.suggested_params()
        current_round = params.first
        client.status_after_block(current_round)
            
    raise Exception(f"Transaction {txid} not confirmed after {timeout} rounds")
