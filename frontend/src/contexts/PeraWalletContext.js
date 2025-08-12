import { createContext, useState, useEffect, useCallback } from 'react';
import { PeraWalletConnect } from '@perawallet/connect';
import { toast } from 'react-toastify';

export const PeraWalletContext = createContext();

// Initialize the Pera Wallet connector
const peraWallet = new PeraWalletConnect({
  chainId: 416002 // For TestNet
  // For MainNet use: 416001
});

export const PeraWalletProvider = ({ children }) => {
  const [accountAddress, setAccountAddress] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);

  // Handle session disconnected
  const handleDisconnect = useCallback(() => {
    setAccountAddress(null);
    setIsConnected(false);
    localStorage.removeItem('walletconnect');
    toast.info('Wallet disconnected');
  }, []);

  // Handle session connection
  const handleConnect = useCallback((accounts) => {
    if (accounts.length) {
      setAccountAddress(accounts[0]);
      setIsConnected(true);
      toast.success('Wallet connected successfully!');
    }
    setConnecting(false);
  }, []);

  // Connect wallet
  const connectWallet = useCallback(async () => {
    try {
      setConnecting(true);
      await peraWallet.connect();
    } catch (error) {
      console.log('Wallet connection failed:', error);
      toast.error('Wallet connection failed');
      setConnecting(false);
    }
  }, []);

  // Disconnect wallet
  const disconnectWallet = useCallback(async () => {
    try {
      await peraWallet.disconnect();
      handleDisconnect();
    } catch (error) {
      console.log('Wallet disconnection failed:', error);
    }
  }, [handleDisconnect]);

  // Set up event listeners
  useEffect(() => {
    peraWallet.reconnectSession().then((accounts) => {
      if (accounts.length) {
        handleConnect(accounts);
      }
    });

    // Subscribe to session events
    peraWallet.connector?.on('disconnect', handleDisconnect);
    peraWallet.connector?.on('session_update', ({ accounts }) => handleConnect(accounts));

    return () => {
      peraWallet.connector?.off('disconnect', handleDisconnect);
      peraWallet.connector?.off('session_update');
    };
  }, [handleConnect, handleDisconnect]);

  return (
    <PeraWalletContext.Provider
      value={{
        isConnected,
        accountAddress,
        connecting,
        connectWallet,
        disconnectWallet,
        peraWallet
      }}
    >
      {children}
    </PeraWalletContext.Provider>
  );
};
