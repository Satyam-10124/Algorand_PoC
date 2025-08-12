# Algorand Document Compliance System - Flask API

This project implements a document compliance verification system on the Algorand blockchain using Flask API. It enables document registration, verification, and compliance status tracking with full blockchain traceability through transaction IDs.

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Project Architecture](#project-architecture)
5. [API Endpoints](#api-endpoints)
6. [Running the Application](#running-the-application)
7. [Testing](#testing)
8. [Transaction Tracking](#transaction-tracking)
9. [Troubleshooting](#troubleshooting)

## Features

- Document registration with blockchain verification
- Verifier assignment and compliance attestation
- Role-based access control (admin/verifier)
- Document compliance status tracking
- Expiration date handling
- Transaction hash tracking for all blockchain operations
- Comprehensive API testing framework
- Frontend integration ready

## Requirements

- Python 3.8+
- Flask web framework
- Algorand SDK (`py-algorand-sdk`)
- Public Algorand TestNet access
- React frontend (optional)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/Satyam-10124/Test_Algorand.git
cd Test_Algorand
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Configure Algorand credentials in `Compliance/compliance_test_accounts.json`
   
## Project Architecture

The project follows a comprehensive architecture that separates API endpoints, blockchain integration, and frontend:

- **Flask Backend (`app.py`)**: Provides RESTful API endpoints for document operations
- **Compliance Client (`Compliance/document_compliance_client_updated.py`)**: Handles Algorand blockchain interactions
- **Test Scripts**: Comprehensive testing frameworks (`test_api.py`, `test_api_with_txn.py`)
- **Frontend**: React-based UI (in the `frontend` directory)

## API Endpoints

| Endpoint | Method | Description | Role |
|---------|--------|-------------|------|
| `/api/admin/status` | GET | Check admin status | Any |
| `/api/verifier/status` | GET | Check verifier status | Any |
| `/api/document/register` | POST | Register document on blockchain | Admin |
| `/api/verifier/assign` | POST | Assign verifier to document | Admin |
| `/api/document/verify` | POST | Verify document compliance | Verifier |
| `/api/document/status` | GET | Get document compliance status | Any |
| `/api/document/hash` | POST | Generate document hash | Any |
| `/api/upload` | POST | Upload document file | Any |

## Running the Application

### Backend

```bash
# Start the Flask server
python app.py
```

The server will run on port 5047 by default (http://127.0.0.1:5047).

### Frontend

```bash
cd frontend
npm install
npm start
```

The React app will be available at http://localhost:3000.

## Testing

Run the comprehensive test suite to verify all API endpoints and blockchain transactions:

```bash
python test_api_with_txn.py
```

This test script will:
1. Test all API endpoints (admin, verifier, document operations)
2. Display transaction IDs for all blockchain operations
3. Provide explorer links for transaction verification
4. Report test results with pass/fail status

## Transaction Tracking

All blockchain operations return transaction IDs that can be viewed on the Algorand TestNet Explorer:

```
https://testnet.algoexplorer.io/tx/{transaction_id}
```

## Troubleshooting

- **Port Conflicts**: If you encounter port conflicts, modify the port number in `app.py`
- **Blockchain Connectivity**: Ensure connectivity to the Algorand TestNet node
- **API Errors**: Check the Flask server logs for detailed error messages
- **Insufficient Funds**: Ensure test accounts have sufficient Algos for transactions

## For More Information

See [Milestone.md](./Milestone.md) for detailed documentation of the project milestones and comprehensive user flows.




## License

MIT
