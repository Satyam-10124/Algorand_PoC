#!/usr/bin/env python3
# document_compliance_client.py - Client to interact with the compliance contract

from algosdk.v2client import algod
from algosdk import account, transaction
from algosdk.encoding import decode_address
import base64
import hashlib
import time

def wait_for_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    
    Args:
        client (AlgodClient): The Algorand client
        transaction_id (str): The transaction ID to wait for
        timeout (int): Maximum number of rounds to wait
        
    Returns:
        dict: Pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception(f"Pool error: {pending_txn['pool-error']}")
        
        client.status_after_block(current_round)
        current_round += 1
    
    raise Exception(f"Transaction {transaction_id} not confirmed after {timeout} rounds")

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
        
        return app_id, tx_id
    
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
        
        return tx_id
    
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
        
        # Return transaction ID
        return tx_id
    
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
        
        # Return transaction ID
        return tx_id
    
    def verify_compliance(self, app_id, document_hash, is_compliant, attestation_date):
        # Get suggested parameters
        params = self.algod_client.suggested_params()
        
        # Create arguments based on compliance status
        app_args = [b"verify", document_hash.encode()]
        if is_compliant:
            app_args.append(b"compliant")
        else:
            app_args.append(b"non_compliant")
            
        # Add attestation date if provided
        if attestation_date:
            app_args.append(attestation_date.to_bytes(8, 'big'))
        
        # Create unsigned transaction
        txn = transaction.ApplicationNoOpTxn(
            sender=self.public_key,
            sp=params,
            index=app_id,
            app_args=app_args
        )
        
        # Sign transaction
        signed_txn = txn.sign(self.private_key)
        tx_id = signed_txn.transaction.get_txid()
        
        # Submit transaction
        self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        wait_for_confirmation(self.algod_client, tx_id, 5)
        
        # Return transaction ID
        return tx_id
    
    def get_compliance_status(self, app_id):
        # Get application information
        app_info = self.algod_client.application_info(app_id)
        
        # Parse global state
        global_state = app_info['params']['global-state'] if 'global-state' in app_info['params'] else []
        
        # Convert global state to dictionary
        status_dict = {}
        for item in global_state:
            key = base64.b64decode(item['key']).decode('utf-8')
            value = item['value']
            
            if value['type'] == 1:  # bytes
                if key == 'document_hash' or key == 'verifier_address':
                    # These are special cases that need to be decoded differently
                    try:
                        val_decoded = base64.b64decode(value['bytes']).decode('utf-8')
                        status_dict[key] = val_decoded
                    except:
                        # If it's not a valid UTF-8 string, keep the base64
                        status_dict[key] = value['bytes']
                else:
                    # Normal string values
                    try:
                        status_dict[key] = base64.b64decode(value['bytes']).decode('utf-8')
                    except:
                        status_dict[key] = value['bytes']
            else:  # uint
                status_dict[key] = value['uint']
        
        return status_dict
