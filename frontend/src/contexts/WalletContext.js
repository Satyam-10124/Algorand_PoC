import { createContext } from 'react';

// Create a context to manage wallet state across components
const WalletContext = createContext({
  wallet: {
    connected: false,
    address: '',
    privateKey: '',
    appId: null
  },
  setWallet: () => {}
});

export default WalletContext;
