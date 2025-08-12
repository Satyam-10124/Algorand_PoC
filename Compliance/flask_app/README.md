# Algorand Compliance Web Application

A Flask-based frontend and API for the Algorand Compliance Smart Contract.

## Features

- Deploy compliance contracts on Algorand TestNet
- Register documents with version control and expiration dates
- Assign verifier roles to addresses
- Verify document compliance status
- Download registered documents
- View contract status on the blockchain

## Setup and Installation

1. Make sure you have the required Python packages:

```bash
pip install flask algosdk pyteal
```

2. Ensure that the compliance smart contract code is in the parent directory:
   - `document_compliance.py` - PyTeal contract
   - `document_compliance_client.py` - Client library

3. Ensure you have a `compliance_test_accounts.json` file in the parent directory with admin and verifier accounts.

## Running the Application

From the `flask_app` directory, run:

```bash
python api.py
```

The server will start at http://127.0.0.1:5000/ by default.

## API Endpoints

### Web UI Endpoints

- `GET /` - Home page with list of contracts
- `GET /contracts/<app_id>` - View contract details and status
- `POST /contracts` - Deploy a new contract
- `POST /contracts/<app_id>/opt-in` - Opt-in to a contract
- `POST /contracts/<app_id>/documents` - Register a new document
- `POST /contracts/<app_id>/verifiers` - Assign a verifier
- `POST /contracts/<app_id>/verify` - Verify compliance
- `GET /documents/<filename>` - Download a document

## Usage Workflow

1. Deploy a new compliance contract from the home page
2. On the contract page:
   - Opt-in both admin and verifier accounts
   - Register a document with the admin account
   - Assign the verifier role to the verifier account
   - Verify compliance with the verifier account
   - View compliance status and document details

## Directory Structure

- `/flask_app/` - Main application directory
  - `/api.py` - Flask application and API endpoints
  - `/templates/` - HTML templates
  - `/static/` - CSS and other static files
  - `/documents/` - Uploaded document storage
  
## Document Storage

Documents uploaded through the UI are stored locally in the `/documents/` directory. The SHA-256 hash of each document is calculated and stored on the blockchain.

## Security Notes

- This is a demo application and not intended for production use without security enhancements
- Private keys should be securely managed in a production environment
- Consider adding user authentication for a production application
