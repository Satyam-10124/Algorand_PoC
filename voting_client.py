import base64
from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction
from algosdk.transaction import ApplicationCreateTxn, ApplicationCallTxn, ApplicationOptInTxn
import time

class VotingDAppClient:
    def __init__(self, algod_client, private_key):
        self.algod_client = algod_client
        self.private_key = private_key
        self.address = account.address_from_private_key(private_key)
        self.app_id = None
    
    def compile_program(self, source_code):
        """Compile TEAL source code to binary"""
        compile_response = self.algod_client.compile(source_code)
        return base64.b64decode(compile_response['result'])
    
    def deploy_contract(self, approval_source, clear_source):
        """Deploy the voting contract"""
        print("Deploying voting contract...")
        
        # Compile programs
        approval_program = self.compile_program(approval_source)
        clear_program = self.compile_program(clear_source)
        
        # Get network params
        params = self.algod_client.suggested_params()
        
        # Create application transaction
        txn = ApplicationCreateTxn(
            sender=self.address,
            sp=params,
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=approval_program,
            clear_program=clear_program,
            # The contract stores both integers (vote counts) and byte-slices (keys)
            global_schema=transaction.StateSchema(5, 6),  # 5 integers + 6 byte-slices
            local_schema=transaction.StateSchema(1, 1),   # 1 integer + 1 byte-slice
        )
        
        # Sign and send transaction
        signed_txn = txn.sign(self.private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        confirmed_txn = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        self.app_id = confirmed_txn["application-index"]
        
        print(f"Contract deployed! App ID: {self.app_id}")
        return self.app_id
    
    def opt_in(self, user_private_key=None):
        """Opt user into the application (required to vote)"""
        if user_private_key is None:
            user_private_key = self.private_key
        
        user_address = account.address_from_private_key(user_private_key)
        params = self.algod_client.suggested_params()
        
        # Create opt-in transaction
        txn = ApplicationOptInTxn(
            sender=user_address,
            sp=params,
            index=self.app_id
        )
        
        # Sign and send
        signed_txn = txn.sign(user_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        print(f"User {user_address} opted in successfully")
    
    def vote(self, candidate_number, voter_private_key=None):
        """Cast a vote for specified candidate (1, 2, or 3)"""
        if voter_private_key is None:
            voter_private_key = self.private_key
        
        voter_address = account.address_from_private_key(voter_private_key)
        params = self.algod_client.suggested_params()
        
        # Create application call transaction
        txn = ApplicationCallTxn(
            sender=voter_address,
            sp=params,
            index=self.app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"vote", str(candidate_number).encode()]
        )
        
        # Sign and send
        signed_txn = txn.sign(voter_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        confirmed_txn = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        print(f"Vote cast successfully for candidate {candidate_number}")
        return confirmed_txn
    
    def get_results(self):
        """Get current voting results"""
        app_info = self.algod_client.application_info(self.app_id)
        global_state = app_info['params']['global-state']
        
        results = {}
        for item in global_state:
            try:
                # Decode key from base64
                key = base64.b64decode(item['key']).decode('utf-8')
                
                # Process value based on its type
                value_type = item['value']['type']
                if value_type == 2:  # byte-slice type
                    # Special case for vote counts stored as type 2 with uint values
                    if key.endswith('_votes'):
                        value = item['value']['uint']  # Use the uint field for vote counts
                    else:
                        value = base64.b64decode(item['value']['bytes']).decode('utf-8') if item['value']['bytes'] else ""
                else:  # uint type
                    value = item['value']['uint']
                
                results[key] = value
            except Exception as e:
                print(f"Error processing global state item: {e}")
        
        return results
    
    def display_results(self):
        """Display formatted voting results"""
        results = self.get_results()
        
        print("\n=== VOTING RESULTS ===")
        print(f"Candidate 1: {results.get('candidate_1_votes', 0)} votes")
        print(f"Candidate 2: {results.get('candidate_2_votes', 0)} votes") 
        print(f"Candidate 3: {results.get('candidate_3_votes', 0)} votes")
        print(f"Total votes: {results.get('total_votes', 0)}")
        print(f"Voting ends at timestamp: {results.get('voting_end', 'N/A')}")
        print("=====================\n")
        
        return results
