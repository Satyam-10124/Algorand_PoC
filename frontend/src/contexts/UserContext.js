import { createContext } from 'react';

// Create a context to manage user state across components
const UserContext = createContext({
  user: {
    connected: false,
    address: '',
    privateKey: '',
    role: null // 'admin', 'verifier', or null for public user
  },
  setUser: () => {}
});

export default UserContext;
