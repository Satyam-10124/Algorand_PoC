# Algorand Compliance Attestation Contract

A simple compliance document attestation and verification smart contract for Algorand blockchain, inspired by CompliLedger's approach to compliance automation.

## Project Overview

This project implements a basic compliance attestation smart contract on Algorand that allows organizations to:

1. Register compliance documents (like SBOMs or audit reports) on the blockchain
2. Track document versions and attestations
3. Assign authorized verifiers to check compliance status
4. Set expiration dates for compliance certifications

This is a simplified demonstration of how blockchain can be used for compliance verification and attestation, similar to what CompliLedger provides in a more comprehensive platform.

## Files in this Project

- `document_compliance.py`: PyTeal smart contract implementation
- `document_compliance_client.py`: Python client to interact with the contract
- `test_compliance.py`: End-to-end test script for the compliance workflow
- `compliance_approval.teal`: Compiled TEAL approval program (generated)
- `compliance_clear.teal`: Compiled TEAL clear state program (generated)
- `compliance_test_accounts.json`: Test accounts for Algorand TestNet (generated)

## Prerequisites

- Python 3.6+
- `py-algorand-sdk`
- `pyteal`

## Installation

1. Clone this repository or navigate to the project directory
2. Install required packages:

```bash
pip install py-algorand-sdk pyteal
```

## Usage

### 1. Generate Test Accounts

First, generate test accounts that will be used for deploying and interacting with the contract:

```bash
python test_compliance.py --new-accounts
```

This will create two accounts (admin and verifier) and save their information to `compliance_test_accounts.json`.

### 2. Fund Your Accounts

Before proceeding, you need to fund these accounts with TestNet Algos:

1. Visit the [Algorand TestNet Dispenser](https://bank.testnet.algorand.network/)
2. Enter the admin and verifier addresses (displayed after generating accounts)
3. Request funds (each account needs at least 1 ALGO)

### 3. Check Account Balances

Verify your accounts have sufficient balance:

```bash
python test_compliance.py --check-balance
```

### 4. Run the Full Test

Once your accounts are funded, run the full test:

```bash
python test_compliance.py
```

This will:
- Deploy the compliance contract
- Opt in both admin and verifier accounts
- Register a sample SBOM document
- Assign verifier role
- Perform compliance verification
- Display current compliance status

### 5. View on Algorand Explorer

After running the test, you'll see an App ID displayed. You can view your deployed contract on Algorand TestNet Explorer:

```
https://testnet.explorer.perawallet.app/application/YOUR_APP_ID
```

## Understanding the Contract

### Global State Storage

The contract stores the following in its global state:

- `document_hash`: SHA-256 hash of the compliance document
- `document_version`: Version string of the document
- `attestation_date`: Timestamp when compliance was attested
- `expiration_date`: Timestamp when compliance certification expires
- `status`: Current compliance status (pending, compliant, expired)
- `admin`: Address of the contract administrator

### Local State Storage

Each account that opts into the contract can store:

- `verifier_role`: Whether the account is authorized to verify compliance

### Key Operations

1. **Register Document**: Admin can register a compliance document by providing its hash, version, and expiration date
2. **Assign Verifier**: Admin can authorize other accounts as compliance verifiers
3. **Verify Compliance**: Authorized verifiers can check and update compliance status
4. **View Document Status**: Check if documents are compliant, pending, or expired
5. **Opt-in to Contract**: Required for verifiers before they can mark compliance

### Web Interface

A Flask-based web interface is included to provide easy access to the compliance contract:

#### Setup and Running

```bash
# Navigate to the Flask application directory
cd flask_app

# Run the application
python3 api.py

# Access the web interface
# Open your browser and go to: http://127.0.0.1:5002
```

#### Frontend Features

- **Dashboard**: View statistics about contracts, documents, and compliance status
- **Contract Management**: Deploy and monitor compliance contracts
- **Document Registration**: Upload and register documents with automatic hash generation
- **Verifier Assignment**: Easily designate compliance verifiers through the UI
- **Compliance Marking**: Intuitive interface for verifiers to update compliance status
- **Transaction Monitoring**: Real-time tracking of blockchain transactions
- **Document Preview**: View registered documents directly in the browser

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home dashboard with contract listing |
| `/create-contract` | POST | Deploy a new compliance contract |
| `/contracts/<app_id>` | GET | View contract details |
| `/register-document/<app_id>` | POST | Register a new document |
| `/assign-verifier/<app_id>` | POST | Assign a verifier to a contract |
| `/mark-compliant/<app_id>/<doc_hash>` | POST | Mark document as compliant |
4. **Expiration Check**: Contract automatically marks compliance as expired when the expiration date passes

## CompliLedger Integration Concepts

While this is a simplified example, it demonstrates core concepts relevant to CompliLedger's platform:

1. **Document Attestation**: Provides tamper-proof evidence of compliance documents
2. **Time-Based Verification**: Implements expiration dates for compliance status
3. **Role-Based Access**: Separates administrative and verification roles
4. **Status Tracking**: Records and verifies compliance status over time
5. **Immutable Record**: Creates auditable evidence on Algorand blockchain

## Troubleshooting

### Common Errors

1. **Connection Error**: If you can't connect to Algorand TestNet, try using a different API endpoint in the client code
2. **Insufficient Balance**: Ensure both accounts have at least 1 ALGO before running tests
3. **Transaction Failed**: Check that your accounts are properly funded and that the right accounts are used for each operation
4. **Schema Mismatch**: If schema errors occur, verify the global and local state schemas match what the contract needs

## License

This project is provided as-is under MIT license.

## References

- [Algorand Developer Documentation](https://developer.algorand.org/)
- [PyTeal Documentation](https://pyteal.readthedocs.io/)
- [CompliLedger](https://www.compliledger.com/)
