import React, { useState, useContext, useEffect } from 'react';
import { Container, Typography, Box, Paper, Tabs, Tab, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Alert, CircularProgress, Grid, Card, CardContent } from '@mui/material';
import { CloudUpload as UploadIcon, Verified as VerifiedIcon, Search as SearchIcon } from '@mui/icons-material';
import UserContext from '../contexts/UserContext';
import { PeraWalletContext } from '../contexts/PeraWalletContext';
import { optInToApp, verifyCompliance, getComplianceStatus } from '../services/algoService';
import { toast } from 'react-toastify';
import axios from 'axios';

// Tab panel component
function TabPanel(props) {
  const { children, value, index, ...other } = props;
  
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Dashboard = () => {
  const { user, setUser } = useContext(UserContext);
  const { isConnected, accountAddress, peraWallet } = useContext(PeraWalletContext);
  const [tabValue, setTabValue] = useState(0);
  const [complianceStatus, setComplianceStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [accountInfo, setAccountInfo] = useState(null);
  const [isVerifier, setIsVerifier] = useState(false);
  const [isOptedIn, setIsOptedIn] = useState(false);
  const APP_ID = 744059516; // Contract App ID

  // Dialogs state
  const [openUploadDialog, setOpenUploadDialog] = useState(false);
  const [openVerifyDialog, setOpenVerifyDialog] = useState(false);
  const [openStatusDialog, setOpenStatusDialog] = useState(false);

  // Document state
  const [documentData, setDocumentData] = useState({
    content: '',
    file: null,
    hash: ''
  });
  const [verifyDocumentHash, setVerifyDocumentHash] = useState('');
  const [statusDocumentHash, setStatusDocumentHash] = useState('');

  // Handle tab changes
  const handleChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Check account status when connected
  useEffect(() => {
    if (isConnected && accountAddress) {
      checkAccountStatus();
      fetchComplianceStatus();
    }
  }, [isConnected, accountAddress]);

  // Check if account is opted in and if it's a verifier
  const checkAccountStatus = async () => {
    if (!isConnected || !accountAddress) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`/api/account/status?address=${accountAddress}`);
      if (response.data.success) {
        setAccountInfo(response.data.account_info);
        setIsVerifier(response.data.is_verifier);
        setIsOptedIn(response.data.is_opted_in);
        
        // If user is a verifier, update user context
        if (response.data.is_verifier) {
          setUser({
            ...user,
            connected: true,
            address: accountAddress,
            role: 'verifier'
          });
        }
      }
    } catch (err) {
      console.error('Error checking account status:', err);
      toast.error('Failed to check account status');
    } finally {
      setLoading(false);
    }
  };

  // Fetch compliance status
  const fetchComplianceStatus = async () => {
    setLoading(true);
    try {
      const status = await getComplianceStatus();
      if (status) {
        setComplianceStatus(status);
      }
    } catch (err) {
      console.error('Error fetching compliance status:', err);
      toast.error('Failed to fetch compliance status');
    } finally {
      setLoading(false);
    }
  };

  // Handle opt-in to the Compliance contract
  const handleOptIn = async () => {
    if (!isConnected) {
      toast.error('Please connect your wallet first');
      return;
    }
    
    setLoading(true);
    try {
      const result = await optInToApp(peraWallet, accountAddress);
      if (result) {
        toast.success('Successfully opted in to the compliance contract');
        setIsOptedIn(true);
      } else {
        toast.error('Failed to opt-in to contract');
      }
    } catch (err) {
      console.error('Error opting in:', err);
      toast.error(`Error: ${err.message || 'Failed to opt-in to contract'}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle document upload
  const handleUploadDialogOpen = () => {
    setDocumentData({ content: '', file: null, hash: '' });
    setOpenUploadDialog(true);
  };

  const handleUploadDialogClose = () => {
    setOpenUploadDialog(false);
  };

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files[0]) {
      setDocumentData({ ...documentData, file: event.target.files[0] });
    }
  };

  const handleContentChange = (event) => {
    setDocumentData({ ...documentData, content: event.target.value });
  };

  // Upload document to generate hash
  const uploadDocument = async () => {
    if (!documentData.content && !documentData.file) {
      toast.error('Please enter document content or upload a file');
      return;
    }
    
    setLoading(true);
    try {
      const formData = new FormData();
      
      if (documentData.file) {
        formData.append('file', documentData.file);
      } else if (documentData.content) {
        const blob = new Blob([documentData.content], { type: 'text/plain' });
        formData.append('file', blob, 'document.txt');
      }
      
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.success) {
        toast.success('Document uploaded and hash generated');
        setDocumentData({ ...documentData, hash: response.data.hash });
        handleUploadDialogClose();
      }
    } catch (err) {
      console.error('Error uploading document:', err);
      toast.error(`Error: ${err.message || 'Failed to upload document'}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle verify compliance as a verifier
  const handleVerifyCompliance = async () => {
    if (!isConnected || !isVerifier) {
      toast.error('You must be connected with a verifier account');
      return;
    }
    
    if (!isOptedIn) {
      toast.error('You need to opt-in to the contract first');
      return;
    }
    
    setLoading(true);
    try {
      const result = await verifyCompliance(peraWallet, accountAddress);
      if (result.success) {
        toast.success('Successfully verified compliance');
        fetchComplianceStatus(); // Refresh status
      } else {
        toast.error(`Failed to verify: ${result.error}`);
      }
    } catch (err) {
      console.error('Error verifying compliance:', err);
      toast.error(`Error: ${err.message || 'Failed to verify compliance'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg">
      {(loading || error || successMessage) && (
        <Box sx={{ mb: 2 }}>
          {loading && (
            <Alert severity="info" icon={<CircularProgress size={20} />}>
              Loading...
            </Alert>
          )}
          {error && (
            <Alert severity="error">{error}</Alert>
          )}
          {successMessage && (
            <Alert severity="success">{successMessage}</Alert>
          )}
        </Box>
      )}

      {isConnected ? (
        <Box sx={{ width: '100%' }}>
          <Paper sx={{ mb: 2 }}>
            <Tabs 
              value={tabValue} 
              onChange={handleChange}
              indicatorColor="primary"
              textColor="primary"
              centered
            >
              <Tab label="Dashboard" />
              <Tab label="Document Registration" />
              <Tab label="Verification" />
            </Tabs>
          </Paper>
          
          <TabPanel value={tabValue} index={0}>
            <Typography variant="h5" gutterBottom>
              Compliance Dashboard
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Contract Status
                    </Typography>
                    
                    {complianceStatus ? (
                      <Box>
                        <Typography variant="body1">
                          Status: {complianceStatus.status}
                        </Typography>
                        <Typography variant="body1">
                          Document Hash: {complianceStatus.documentHash && complianceStatus.documentHash.slice(0, 16)}...{complianceStatus.documentHash && complianceStatus.documentHash.slice(-4)}
                        </Typography>
                        <Typography variant="body1">
                          Version: {complianceStatus.version}
                        </Typography>
                        <Typography variant="body1">
                          Attestation Date: {complianceStatus.attestationDate ? complianceStatus.attestationDate.toLocaleString() : 'None'}
                        </Typography>
                        <Typography variant="body1">
                          Expiration Date: {complianceStatus.expirationDate ? complianceStatus.expirationDate.toLocaleString() : 'None'}
                        </Typography>
                        {complianceStatus.daysUntilExpiration !== null && (
                          <Typography variant="body1">
                            Days until expiration: {complianceStatus.daysUntilExpiration}
                          </Typography>
                        )}
                      </Box>
                    ) : (
                      <Typography variant="body1">
                        No compliance status available.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Actions
                    </Typography>
                    
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Button
                        variant="contained"
                        color="primary"
                        fullWidth
                        startIcon={<UploadIcon />}
                        onClick={handleUploadDialogOpen}
                      >
                        Upload Document
                      </Button>
                      
                      {!isOptedIn && (
                        <Button
                          variant="contained"
                          color="secondary"
                          fullWidth
                          onClick={handleOptIn}
                          disabled={loading || !isConnected}
                        >
                          Opt-in to Contract
                        </Button>
                      )}
                      
                      {isVerifier && isOptedIn && (
                        <Button
                          variant="contained"
                          color="success"
                          fullWidth
                          startIcon={<VerifiedIcon />}
                          onClick={handleVerifyCompliance}
                          disabled={loading || !isConnected}
                        >
                          Verify Compliance
                        </Button>
                      )}
                      
                      <Button
                        variant="outlined"
                        color="primary"
                        fullWidth
                        startIcon={<SearchIcon />}
                        onClick={() => setOpenStatusDialog(true)}
                      >
                        Check Document Status
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <Typography variant="h5" gutterBottom>
              Document Registration
            </Typography>
            <Typography variant="body1" paragraph>
              Only admin accounts can register documents to the compliance system.
              Document registration will store the document hash and status on the blockchain.
            </Typography>
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            <Typography variant="h5" gutterBottom>
              Verification
            </Typography>
            <Typography variant="body1" paragraph>
              Verifier accounts can verify the compliance status of documents.
              This will update the document's compliance status on the blockchain.
            </Typography>
          </TabPanel>
        </Box>
      ) : (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Welcome to CompliLedger
          </Typography>
          <Typography variant="body1" paragraph>
            Connect your wallet to interact with the compliance document system.
          </Typography>
          <Typography variant="body1" paragraph>
            You can upload documents, check compliance status, and more.
          </Typography>
        </Paper>
      )}
      
      {/* Document Upload Dialog */}
      <Dialog open={openUploadDialog} onClose={handleUploadDialogClose}>
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            Upload a document to generate its hash for compliance verification.
          </Typography>
          
          <Box sx={{ my: 2 }}>
            <Button
              variant="contained"
              component="label"
              fullWidth
              sx={{ mb: 2 }}
            >
              Select File
              <input
                type="file"
                hidden
                onChange={handleFileChange}
              />
            </Button>
            
            {documentData.file && (
              <Typography variant="body2">
                Selected: {documentData.file.name}
              </Typography>
            )}
            
            <Typography variant="body2" sx={{ mt: 2, mb: 1 }}>
              Or enter document content:
            </Typography>
            
            <TextField
              multiline
              rows={4}
              fullWidth
              variant="outlined"
              placeholder="Enter document content here..."
              value={documentData.content}
              onChange={handleContentChange}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleUploadDialogClose}>Cancel</Button>
          <Button
            onClick={uploadDocument}
            variant="contained"
            color="primary"
            disabled={!documentData.content && !documentData.file}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Status Check Dialog */}
      <Dialog open={openStatusDialog} onClose={() => setOpenStatusDialog(false)}>
        <DialogTitle>Check Document Status</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            Enter a document hash to check its compliance status.
          </Typography>
          
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Enter document hash"
            value={statusDocumentHash}
            onChange={(e) => setStatusDocumentHash(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenStatusDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="primary"
            disabled={!statusDocumentHash}
            onClick={() => {
              // Implementation for status check
              fetchComplianceStatus();
              setOpenStatusDialog(false);
            }}
          >
            Check Status
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Dashboard;
