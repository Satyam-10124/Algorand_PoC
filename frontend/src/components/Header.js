import React, { useContext, useState } from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Container, Dialog, DialogTitle, DialogContent, TextField, DialogActions, FormControl, InputLabel, Select, MenuItem, CircularProgress } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import UserContext from '../contexts/UserContext';
import { PeraWalletContext } from '../contexts/PeraWalletContext';
import axios from 'axios';

const Header = () => {
  const { user, setUser } = useContext(UserContext);
  const { isConnected, accountAddress, connecting, connectWallet, disconnectWallet } = useContext(PeraWalletContext);
  const [openLoginDialog, setOpenLoginDialog] = useState(false);
  const [loginDetails, setLoginDetails] = useState({
    privateKey: '',
    role: 'verifier'
  });
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  const handleLoginOpen = () => {
    setOpenLoginDialog(true);
    setLoginError('');
  };

  const handleLoginClose = () => {
    setOpenLoginDialog(false);
    setLoginError('');
  };

  const handleLogin = async () => {
    if (!loginDetails.privateKey) {
      setLoginError('Private key is required');
      return;
    }

    setLoginLoading(true);
    try {
      const response = await axios.post('/api/login/verifier', {
        private_key: loginDetails.privateKey
      });

      if (response.data.success) {
        setUser({
          connected: true,
          privateKey: loginDetails.privateKey,
          address: response.data.address,
          role: response.data.role
        });
        handleLoginClose();
      }
    } catch (err) {
      setLoginError(err.response?.data?.error || 'Invalid credentials');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleDisconnect = () => {
    setUser({
      connected: false,
      privateKey: '',
      address: '',
      role: null
    });
  };

  return (
    <AppBar position="static" color="primary">
      <Container maxWidth="lg">
        <Toolbar disableGutters>
          <Typography
            variant="h6"
            noWrap
            component={RouterLink}
            to="/"
            sx={{
              mr: 2,
              display: 'flex',
              fontWeight: 700,
              color: 'white',
              textDecoration: 'none',
            }}
          >
            CompliLedger
          </Typography>

          <Box sx={{ flexGrow: 1 }} />
          
          {isConnected ? (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {user.connected && user.role && (
                <Typography variant="body2" color="white" sx={{ mr: 2 }}>
                  {user.role === 'admin' ? '👑 Admin' : user.role === 'verifier' ? '✓ Verifier' : ''}
                </Typography>
              )}
              <Typography variant="body2" color="white" sx={{ mr: 2 }}>
                {accountAddress.slice(0, 8)}...{accountAddress.slice(-4)}
              </Typography>
              <Button 
                color="inherit" 
                variant="outlined" 
                onClick={disconnectWallet}
                sx={{ borderColor: 'white', color: 'white' }}
              >
                Disconnect
              </Button>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Button 
                color="inherit" 
                variant="outlined" 
                onClick={connectWallet}
                disabled={connecting}
                sx={{ borderColor: 'white', color: 'white', mr: 2 }}
                startIcon={connecting && <CircularProgress size={20} color="inherit" />}
              >
                {connecting ? 'Connecting...' : 'Connect Wallet'}
              </Button>
              
              <Button 
                color="inherit" 
                variant="outlined" 
                onClick={handleLoginOpen}
                sx={{ borderColor: 'white', color: 'white', mr: 1 }}
              >
                Verifier Login
              </Button>
            </Box>
          )}
        </Toolbar>
      </Container>

      {/* Verifier/Admin Login Dialog */}
      <Dialog open={openLoginDialog} onClose={handleLoginClose}>
        <DialogTitle>Verifier Login</DialogTitle>
        <DialogContent>
          {loginError && (
            <Typography color="error" variant="body2" sx={{ mb: 2 }}>
              {loginError}
            </Typography>
          )}
          <TextField
            autoFocus
            margin="dense"
            id="privateKey"
            label="Private Key"
            type="password"
            fullWidth
            variant="outlined"
            value={loginDetails.privateKey}
            onChange={(e) => setLoginDetails({...loginDetails, privateKey: e.target.value})}
            disabled={loginLoading}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleLoginClose}>Cancel</Button>
          <Button 
            onClick={handleLogin} 
            variant="contained" 
            color="primary"
            disabled={!loginDetails.privateKey || loginLoading}
          >
            Login
          </Button>
        </DialogActions>
      </Dialog>
    </AppBar>
  );
};

export default Header;
