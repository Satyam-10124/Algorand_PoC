import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container, Typography } from '@mui/material';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Dashboard from './components/Dashboard';
import Header from './components/Header';
import Footer from './components/Footer';
import UserContext from './contexts/UserContext';
import { PeraWalletProvider } from './contexts/PeraWalletContext';

function App() {
  // State for user session
  const [user, setUser] = useState({
    connected: false,
    address: '',
    privateKey: '', // Note: In production, consider more secure methods for handling private keys
    role: null // 'admin', 'verifier', or null for public user
  });

  return (
    <PeraWalletProvider>
      <UserContext.Provider value={{ user, setUser }}>
        <Box 
          sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            minHeight: '100vh',
            background: '#f5f5f5'
          }}
        >
          <Header />
          
          <Container component="main" sx={{ mt: 4, mb: 4, flex: 1 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              {/* Add more routes as needed */}
            </Routes>
          </Container>
          
          <Footer />
        </Box>
        <ToastContainer position="bottom-right" />
      </UserContext.Provider>
    </PeraWalletProvider>
  );
}

export default App;
