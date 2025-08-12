# Algorand Compliance DApp Documentation

## Project Overview

The Algorand Compliance DApp is a decentralized application built on the Algorand blockchain that manages document compliance workflows. It allows for document registration, verifier assignment, document verification, and compliance status tracking. The system consists of a Flask backend API that interacts with an Algorand smart contract deployed on the TestNet and a React frontend for user interaction.

## System Architecture

### Components

1. **Frontend**
   - React.js application
   - Material UI for styling
   - Connects to the backend API for document operations
   - Uses Pera Wallet for Algorand blockchain interactions

2. **Backend**
   - Flask API server
   - Handles document registration, verification, and status queries
   - Interfaces with Algorand blockchain via algosdk

3. **Blockchain**
   - Algorand TestNet
   - Smart contract (App ID: 744059516)
   - Stores document hashes, compliance status, and role-based permissions

### Technical Stack

- **Frontend**: React.js, Material UI, React Router
- **Backend**: Python, Flask
- **Blockchain**: Algorand (TestNet), PyTeal (smart contract)
- **Authentication**: Private key-based authentication
- **API Communication**: REST API endpoints

## Setup and Installation

### Prerequisites

- Node.js and npm for frontend
- Python 3.x for backend
- Algorand account with TestNet Algos

### Installation Steps

1. **Clone the repository**
   ```
   git clone https://github.com/Satyam-10124/Test_Algorand.git
   cd Test_Algorand
   ```

2. **Backend Setup**
   ```
   # Install backend dependencies
   pip install -r requirements.txt
   
   # Start the Flask server (default port 5045)
   python app.py
   ```

3. **Frontend Setup**
   ```
   cd frontend
   npm install
   npm start
   ```

## User Roles and Authentication

The system supports three user roles:

1. **Admin**
   - Can register documents
   - Can assign verifiers to documents
   - Has full access to all system features

2. **Verifier**
   - Can verify document compliance
   - Can view document status
   - Limited to verification operations

3. **Public**
   - Can check compliance status of documents
   - Limited to read-only operations

Authentication is performed using private keys for admin and verifier roles. The system validates the keys against predefined accounts in the configuration.

## API Endpoints

### Public Endpoints

1. **GET /** - Frontend React application
2. **GET /api/document/hash** - Generate document hash
3. **POST /api/upload** - Upload and hash a document
4. **GET /api/document/status?document_hash=[hash]** - Check document compliance status (public)

### Admin Endpoints

1. **POST /api/document/register** - Register a document on the blockchain (admin only)
2. **POST /api/verifier/assign** - Assign verifier to a document (admin only)

### Verifier Endpoints

1. **POST /api/document/verify** - Verify document compliance (verifier only)

### Account Management Endpoints

1. **POST /api/login** - Authenticate using private key and determine role
2. **GET /api/account/status** - Check account status and role

## User Flows

### Admin User Flow

1. **Login**
   - Navigate to the application
   - Enter admin private key
   - Submit for authentication
   - System recognizes admin role and grants appropriate permissions

2. **Document Registration**
   - Navigate to Register Document section
   - Enter or upload document content
   - Submit for registration
   - System generates hash and registers document on blockchain
   - Confirmation of registration displayed

3. **Assign Verifier**
   - Navigate to Assign Verifier section
   - Enter document hash
   - Select verifier address
   - Submit assignment request
   - System assigns verifier on blockchain
   - Confirmation of assignment displayed

4. **Check Document Status**
   - Navigate to Document Status section
   - Enter document hash
   - Submit status request
   - System retrieves and displays document status

### Verifier User Flow

1. **Login**
   - Navigate to the application
   - Enter verifier private key
   - Submit for authentication
   - System recognizes verifier role and grants appropriate permissions

2. **Verify Document**
   - Navigate to Verify Document section
   - Enter document hash
   - Select compliance status (compliant/non-compliant)
   - Submit verification
   - System records verification on blockchain
   - Confirmation of verification displayed

3. **Check Document Status**
   - Navigate to Document Status section
   - Enter document hash
   - Submit status request
   - System retrieves and displays document status

### Public User Flow

1. **Access Application**
   - Navigate to the application
   - No login required for public functions

2. **Generate Document Hash**
   - Navigate to Generate Hash section
   - Enter or upload document content
   - Submit for hash generation
   - System generates and displays document hash

3. **Check Document Status**
   - Navigate to Document Status section
   - Enter document hash
   - Submit status request
   - System retrieves and displays document status

## Blockchain Interactions

### Document Registration
1. Admin initiates document registration with document hash
2. Backend creates Algorand transaction to call the smart contract
3. Document hash is stored in the smart contract's global state
4. Initial status is set to "pending"

### Verifier Assignment
1. Admin initiates verifier assignment with document hash and verifier address
2. Backend verifies that verifier has opted into the application
3. Backend creates transaction to update the smart contract
4. Verifier address is associated with the document

### Document Verification
1. Verifier initiates verification with document hash and compliance status
2. Backend verifies that the caller is an authorized verifier
3. Backend creates transaction to update document status
4. Document status is updated to "compliant" or "non-compliant"
5. Verification timestamp is recorded

## Testing

### API Testing
The system includes a comprehensive test script (`test_api.py`) that tests all API endpoints:

1. **Basic Authentication Tests**
   - Admin account status
   - Verifier account status
   - Role verification

2. **Document Operation Tests**
   - Document registration
   - Verifier assignment
   - Document verification
   - Compliance status retrieval

Run the test script with:
```
python test_api.py
```

### Blockchain Debugging
For debugging blockchain interactions:

1. Run the enhanced debug server:
```
python app_debug.py
```

2. Monitor the console for detailed error logs and transaction traces

## Security Considerations

1. **Private Key Management**
   - Private keys should be stored securely
   - In a production environment, consider more secure authentication mechanisms

2. **Access Control**
   - Role-based access control prevents unauthorized operations
   - All blockchain operations are authenticated

3. **Data Integrity**
   - Document hashes ensure data integrity
   - Blockchain provides immutable record of all operations

## Deployment Considerations

1. **Mainnet Deployment**
   - Update Algorand client to use Mainnet
   - Deploy smart contract to Mainnet
   - Update application ID in configuration

2. **Production Security**
   - Implement proper key management solutions
   - Add HTTPS for API communication
   - Consider additional authentication methods

## Troubleshooting

### Common Issues

1. **Blockchain Connectivity Issues**
   - Ensure Algorand node is accessible
   - Check TestNet connection if using public nodes
   - Verify correct API endpoint configuration

2. **Transaction Failures**
   - Ensure accounts have sufficient Algo balance
   - Verify correct app ID configuration
   - Check role permissions

3. **Frontend Connection Issues**
   - Verify proxy configuration matches backend port
   - Check API endpoint responses
   - Monitor browser console for errors

## Demo Credentials

For testing and demonstration purposes, use the following accounts:

### Admin Account
```
Address: AESO5BABKSE5M725CPRZZEGD3NTYHYAL6NU44VRRX4C2D2KWJUBATOLBZM
Private Key: GjgY9dItFUl1Ztx1bqiazjRh6MbQkE/SHkWv3AUaXwMBJO6EAVSJ1n9dE+OckMPbZ4PgC/NpzlYxvwWh6VZNAg==
```

### Verifier Account
```
Address: 36GR5YRE6CC746JYSUMRC4XX5F3FWJEUG3OJKLCEV2Q3TF5FWKPVOOVZM4
Private Key: QgsVuMbGAUoYTmkaCB/SGdTh7LxFmimJ0gsoxGMNE0jfjR7iJPCF/nk4lRkRcvfpdlsklDbclSxErqG5l6Wynw==
```

**Note:** In a production environment, never expose private keys in documentation or code. These keys are provided here only for development and testing purposes.
