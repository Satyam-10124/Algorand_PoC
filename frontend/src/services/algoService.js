import algosdk from 'algosdk';

// Algod client configuration
const algodServer = 'https://testnet-api.algonode.cloud';
const algodToken = '';
const algodPort = '';
const algodClient = new algosdk.Algodv2(algodToken, algodServer, algodPort);

// App ID from your deployed contract
const appId = 744059516;


// Helper function to wait for transaction confirmation
export const waitForConfirmation = async (txId) => {
  const status = await algodClient.status().do();
  let lastRound = status['last-round'];
  
  while (true) {
    const pendingInfo = await algodClient.pendingTransactionInformation(txId).do();
    if (pendingInfo['confirmed-round'] && pendingInfo['confirmed-round'] > 0) {
      return pendingInfo;
    }
    
    lastRound++;
    await algodClient.statusAfterBlock(lastRound).do();
  }
};

// Function to opt-in to the application
export const optInToApp = async (peraWallet, accountAddress) => {
  try {
    const suggestedParams = await algodClient.getTransactionParams().do();
    
    const txn = algosdk.makeApplicationOptInTxn(
      accountAddress,
      suggestedParams,
      appId
    );
    
    const txnToSign = [{txn: txn, signers: [accountAddress]}];
    const signedTxn = await peraWallet.signTransaction([txnToSign]);
    const { txId } = await algodClient.sendRawTransaction(signedTxn).do();
    
    await waitForConfirmation(txId);
    return true;
  } catch (error) {
    console.error('Error opting in:', error);
    return false;
  }
};

// Function for verifiers to verify compliance
export const verifyCompliance = async (peraWallet, accountAddress) => {
  try {
    const suggestedParams = await algodClient.getTransactionParams().do();
    
    const txn = algosdk.makeApplicationNoOpTxn(
      accountAddress,
      suggestedParams,
      appId,
      [new TextEncoder().encode('verify')]
    );
    
    const txnToSign = [{txn: txn, signers: [accountAddress]}];
    const signedTxn = await peraWallet.signTransaction([txnToSign]);
    const { txId } = await algodClient.sendRawTransaction(signedTxn).do();
    
    await waitForConfirmation(txId);
    return { success: true, txId };
  } catch (error) {
    console.error('Error verifying compliance:', error);
    return { success: false, error: error.message };
  }
};

// Function to get compliance status (doesn't require wallet signing)
export const getComplianceStatus = async () => {
  try {
    const appInfo = await algodClient.getApplicationByID(appId).do();
    const globalState = appInfo['params']['global-state'];
    
    // Parse the global state
    const state = {};
    for (let i = 0; i < globalState.length; i++) {
      const key = Buffer.from(globalState[i].key, 'base64').toString();
      
      if (globalState[i].value.type === 1) {
        // Byte slice
        state[key] = Buffer.from(globalState[i].value.bytes, 'base64').toString();
      } else if (globalState[i].value.type === 2) {
        // Uint
        state[key] = globalState[i].value.uint;
      }
    }
    
    // Calculate days until expiration if applicable
    let daysUntilExpiration = null;
    if (state.expiration_date) {
      const now = Math.floor(Date.now() / 1000);
      const secondsLeft = state.expiration_date - now;
      daysUntilExpiration = Math.floor(secondsLeft / 86400); // 86400 seconds in a day
    }
    
    return {
      status: state.status || 'unknown',
      documentHash: state.document_hash || '',
      version: state.document_version || '',
      attestationDate: state.attestation_date ? new Date(state.attestation_date * 1000) : null,
      expirationDate: state.expiration_date ? new Date(state.expiration_date * 1000) : null,
      daysUntilExpiration
    };
  } catch (error) {
    console.error('Error fetching compliance status:', error);
    return null;
  }
};
