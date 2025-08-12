from algosdk.v2client import algod
from algosdk import account, mnemonic, transaction
import time
import json
import os

# Define wait_for_confirmation function 
def wait_for_confirmation(client, txid):
    """Wait until the transaction is confirmed or rejected, or until timeout"""
    last_round = client.status().get('last-round')
    while True:
        txinfo = client.pending_transaction_info(txid)
        if txinfo.get('confirmed-round', 0) > 0:
            print(f"Transaction confirmed in round {txinfo['confirmed-round']}")
            return txinfo
        elif txinfo.get('pool-error', ''):
            print(f"Transaction failed with pool error: {txinfo['pool-error']}")
            return None
        last_round += 1
        client.status_after_block(last_round)
        time.sleep(1)  # Avoid spamming the API

# -------- CONFIG --------
ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"  # Free public endpoint
ALGOD_TOKEN = ""  # No token needed for AlgoNode public API
APP_ID = 744053057  # From app.py

# Load accounts from the JSON file
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Compliance/compliance_test_accounts.json")) as f:
        accounts = json.load(f)
    
    admin_mnemonic = accounts.get('admin', {}).get('mnemonic', '')
    verifier_address = accounts.get('verifier', {}).get('address', '')
    
    print(f"Using admin to assign verifier {verifier_address}")
except Exception as e:
    print(f"Error loading accounts: {str(e)}")
    exit(1)

# -------- CONNECT TO ALGOD --------
algod_client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

# Recover admin account
admin_private_key = mnemonic.to_private_key(admin_mnemonic)
admin_address = account.address_from_private_key(admin_private_key)
print(f"Using admin account: {admin_address}")

# -------- ASSIGN VERIFIER --------
print("\nAssigning verifier...")
params = algod_client.suggested_params()

# Create assign_verifier transaction
txn = transaction.ApplicationNoOpTxn(
    sender=admin_address,
    sp=params,
    index=APP_ID,
    app_args=[b"assign_verifier", b"1"],  # Based on ComplianceClient.assign_verifier
    accounts=[verifier_address]  # The account to assign as verifier
)

# Sign and send the transaction
signed_txn = txn.sign(admin_private_key)
txid = algod_client.send_transaction(signed_txn)
print(f"Transaction sent with ID: {txid}")

# Wait for confirmation
print("Waiting for confirmation...")
confirmed_txn = wait_for_confirmation(algod_client, txid)

if confirmed_txn:
    print("Verifier assigned successfully!")
    print(f"Now the account {verifier_address} can call verify_compliance()")
else:
    print("Failed to assign verifier")
