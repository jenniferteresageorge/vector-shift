import { useState } from 'react';
import {
    Box,
    Button,
    CircularProgress,
    Card,
    CardContent,
    Typography
} from '@mui/material';
import axios from 'axios';

export const HubSpotIntegration = ({ user, org }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [isLoadingData, setIsLoadingData] = useState(false);

    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const response = await axios.post(`http://localhost:8000/integrations/hubspot/authorize`, {
                user_id: user,
                org_id: org
            });

            const authURL = response?.data.auth_url;
            if (!authURL) throw new Error("Failed to get authorization URL.");

            const newWindow = window.open(authURL, 'HubSpot Authorization', 'width=600, height=600');

            const pollTimer = window.setInterval(() => {
                if (newWindow?.closed !== false) { 
                    window.clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 500);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail || "Authorization failed.");
        }
    };

    const handleWindowClosed = async () => {
        try {
            const response = await axios.post(`http://localhost:8000/integrations/hubspot/credentials`, {
                user_id: user,
                org_id: org
            });

            const credentials = response.data;
            if (credentials?.access_token) {
                setIsConnected(true);
            }
            setIsConnecting(false);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail || "Failed to fetch credentials.");
        }
    };

    const fetchContacts = async () => {
        try {
            setIsLoadingData(true);
            const response = await axios.post(`http://localhost:8000/integrations/hubspot/get_hubspot_items`);
            
            console.log("✅ HubSpot Contacts (Frontend Log):", response.data);  // ✅ Logs to browser console

        } catch (e) {
            console.error("❌ Error fetching contacts (Frontend Log):", e?.response?.data?.detail || e);
            alert(e?.response?.data?.detail || "Failed to load contacts.");
        } finally {
            setIsLoadingData(false);
        }
    };

    return (
        <Card sx={{ mt: 2, boxShadow: 3 }}>
            <CardContent>
                <Typography variant="h6" align="center" gutterBottom>
                    HubSpot Integration
                </Typography>

                <Box display="flex" justifyContent="center">
                    <Button 
                        variant='contained' 
                        onClick={isConnected ? () => {} : handleConnectClick}
                        color={isConnected ? 'success' : 'primary'}
                        disabled={isConnecting}
                        sx={{ mb: 2, mx: 1 }}
                    >
                        {isConnected ? '✅ Connected' : isConnecting ? <CircularProgress size={20} /> : 'Connect to HubSpot'}
                    </Button>

                    {isConnected && (
                        <Button 
                            variant='contained' 
                            onClick={fetchContacts}
                            color='secondary'
                            disabled={isLoadingData}
                            sx={{ mb: 2, mx: 1 }}
                        >
                            {isLoadingData ? <CircularProgress size={20} /> : '📥 Load Contacts'}
                        </Button>
                    )}
                </Box>
            </CardContent>
        </Card>
    );
};
