import React from 'react';
import { Box, Container, Typography, Link } from '@mui/material';

const Footer = () => {
  return (
    <Box
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.grey[200],
      }}
    >
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          {'© '}
          <Link color="inherit" href="#">
            CompliLedger
          </Link>{' '}
          {new Date().getFullYear()}
          {' - Document Compliance System based on Algorand'}
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer;
