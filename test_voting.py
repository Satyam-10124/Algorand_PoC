import sys
import json
import time
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.error import AlgodHTTPError
from voting_client import VotingDAppClient
from voting_contract import get_approval_program, get_clear_program

def create_test_accounts():
    """Create test accounts and print their details"""
    creator_private_key, creator_address = account.generate_account()
    voter1_private_key, voter1_address = account.generate_account()
    voter2_private_key, voter2_address = account.generate_account()
    voter3_private_key, voter3_address = account.generate_account()

    print("\n=== Test Accounts Generated ===")
    print(f"Creator: {creator_address}")
    print(f"Creator mnemonic: {mnemonic.from_private_key(creator_private_key)}")
    print(f"Voter 1: {voter1_address}")
    print(f"Voter 1 mnemonic: {mnemonic.from_private_key(voter1_private_key)}")
    print(f"Voter 2: {voter2_address}")
    print(f"Voter 2 mnemonic: {mnemonic.from_private_key(voter2_private_key)}")
    print(f"Voter 3: {voter3_address}")
    print(f"Voter 3 mnemonic: {mnemonic.from_private_key(voter3_private_key)}")
    print("\n⚠️ IMPORTANT: Fund these accounts with TestNet ALGOs before proceeding")
    print("You can get TestNet ALGOs from https://bank.testnet.algorand.network/")
    print("===========================================\n")
    
    return {
        "creator": (creator_private_key, creator_address),
        "voter1": (voter1_private_key, voter1_address),
        "voter2": (voter2_private_key, voter2_address),
        "voter3": (voter3_private_key, voter3_address)
    }

def save_accounts(accounts, filename="test_accounts.json"):
    """Save account mnemonics to a file"""
    account_data = {
        "creator": {
            "address": accounts["creator"][1],
            "mnemonic": mnemonic.from_private_key(accounts["creator"][0])
        },
        "voter1": {
            "address": accounts["voter1"][1],
            "mnemonic": mnemonic.from_private_key(accounts["voter1"][0])
        },
        "voter2": {
            "address": accounts["voter2"][1],
            "mnemonic": mnemonic.from_private_key(accounts["voter2"][0])
        },
        "voter3": {
            "address": accounts["voter3"][1],
            "mnemonic": mnemonic.from_private_key(accounts["voter3"][0])
        }
    }
    
    with open(filename, 'w') as f:
        json.dump(account_data, f, indent=2)
    
    print(f"Account information saved to {filename}")

def load_accounts(filename="test_accounts.json"):
    """Load account mnemonics from a file"""
    try:
        with open(filename, 'r') as f:
            account_data = json.load(f)
        
        accounts = {
            "creator": (mnemonic.to_private_key(account_data["creator"]["mnemonic"]), 
                       account_data["creator"]["address"]),
            "voter1": (mnemonic.to_private_key(account_data["voter1"]["mnemonic"]), 
                      account_data["voter1"]["address"]),
            "voter2": (mnemonic.to_private_key(account_data["voter2"]["mnemonic"]), 
                      account_data["voter2"]["address"]),
            "voter3": (mnemonic.to_private_key(account_data["voter3"]["mnemonic"]), 
                      account_data["voter3"]["address"])
        }
        
        print("Successfully loaded account information")
        return accounts
    except FileNotFoundError:
        print(f"No account file found at {filename}")
        return None
    except Exception as e:
        print(f"Error loading accounts: {e}")
        return None

def check_account_balances(algod_client, accounts):
    """Check if all accounts have sufficient balance"""
    print("\n=== ACCOUNT BALANCES ===")
    
    all_funded = True
    for name, (pk, addr) in accounts.items():
        try:
            account_info = algod_client.account_info(addr)
            balance = account_info.get('amount', 0) / 1000000  # Convert microAlgos to Algos
            if balance < 0.1:  # Minimum recommended balance
                print(f"⚠️  {name} ({addr}): {balance:.6f} ALGO - NEEDS FUNDING")
                all_funded = False
            else:
                print(f"✓ {name} ({addr}): {balance:.6f} ALGO - OK")
        except Exception as e:
            print(f"Error checking {name} balance: {e}")
            all_funded = False
    
    print("\nAll accounts need at least 0.1 ALGO for testing.")
    if not all_funded:
        print("⚠️  Please fund the accounts marked 'NEEDS FUNDING'")
        print("Use the Algorand TestNet Dispenser: https://bank.testnet.algorand.network")
    else:
        print("✓ All accounts have sufficient balance for testing!")
    print("===========================")

def main():
    """Main test function for Voting Contract"""
    # Connect to Algorand TestNet
    print("Connecting to Algorand TestNet...")
    algod_address = "https://testnet-api.algonode.cloud"
    algod_token = ""  # No token needed for AlgoNode public API
    algod_client = algod.AlgodClient(algod_token, algod_address)
    
    # Check connection
    try:
        algod_client.status()
        print("Successfully connected to Algorand TestNet!")
    except Exception as e:
        print(f"Error connecting to Algorand network: {e}")
        sys.exit(1)
    
    # Check for command line arguments
    force_new_accounts = '--new-accounts' in sys.argv
    check_balance = '--check-balance' in sys.argv
    
    # Load or create accounts
    accounts = None
    if not force_new_accounts:
        accounts = load_accounts()
    
    if not accounts:
        accounts = create_test_accounts()
        save_accounts(accounts)
        print("\n=== IMPORTANT FUNDING INSTRUCTIONS ===")
        print("1. Go to the Algorand TestNet Dispenser: https://bank.testnet.algorand.network")
        print("2. Fund each account with at least 1 ALGO each")
        print("3. Run this script again after funding all accounts")
        print("4. To check account balances, run: python test_voting.py --check-balance")
        print("=============================================\n")
        sys.exit(0)
    
    # Check balances if requested
    if check_balance:
        check_account_balances(algod_client, accounts)
        sys.exit(0)
    
    creator_pk, creator_addr = accounts["creator"]
    voter1_pk, voter1_addr = accounts["voter1"]
    voter2_pk, voter2_addr = accounts["voter2"]
    voter3_pk, voter3_addr = accounts["voter3"]
    
    # Create client instance with creator account
    voting_client = VotingDAppClient(algod_client, creator_pk)
    
    # Get TEAL programs
    approval_program_src = get_approval_program()
    clear_program_src = get_clear_program()
    
    # 1. Deploy contract
    print("\n=== STEP 1: Deploying Contract ===")
    try:
        app_id = voting_client.deploy_contract(approval_program_src, clear_program_src)
        print(f"Contract successfully deployed with App ID: {app_id}")
    except Exception as e:
        print(f"Error deploying contract: {e}")
        sys.exit(1)
    
    # 2. Opt-in users
    print("\n=== STEP 2: Opting In Users ===")
    try:
        # Creator opts in
        voting_client.opt_in()
        
        # Other voters opt in
        voting_client.opt_in(voter1_pk)
        voting_client.opt_in(voter2_pk)
        voting_client.opt_in(voter3_pk)
    except Exception as e:
        print(f"Error during opt-in: {e}")
        sys.exit(1)
    
    # 3. Cast votes
    print("\n=== STEP 3: Casting Votes ===")
    try:
        # Creator votes for candidate 1
        voting_client.vote(1)
        
        # Voter 1 votes for candidate 2
        voting_client.vote(2, voter1_pk)
        
        # Voter 2 votes for candidate 1 
        voting_client.vote(1, voter2_pk)
        
        # Voter 3 votes for candidate 3
        voting_client.vote(3, voter3_pk)
    except Exception as e:
        print(f"Error during voting: {e}")
        sys.exit(1)
    
    # 4. Display results
    print("\n=== STEP 4: Displaying Results ===")
    try:
        results = voting_client.display_results()
        
        # Determine the winner
        candidates = {
            "candidate_1": results.get("candidate_1_votes", 0),
            "candidate_2": results.get("candidate_2_votes", 0),
            "candidate_3": results.get("candidate_3_votes", 0)
        }
        
        max_votes = max(candidates.values())
        winners = [c.split('_')[1] for c, v in candidates.items() if v == max_votes]
        
        if len(winners) > 1:
            print(f"It's a tie between candidates {', '.join(winners)}!")
        else:
            print(f"The current winner is Candidate {winners[0]} with {max_votes} votes!")
    except Exception as e:
        print(f"Error getting results: {e}")
    
    print("\n=== TEST COMPLETED SUCCESSFULLY ===")
    print(f"Voting App ID: {voting_client.app_id}")
    print("You can continue to interact with this application using the app ID")

if __name__ == "__main__":
    main()
