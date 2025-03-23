import { useState } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Autocomplete,
    TextField,
} from '@mui/material';
import { AirtableIntegration } from './integrations/airtable';
import { NotionIntegration } from './integrations/notion';
import { HubSpotIntegration } from './integrations/hubspot';
import { DataForm } from './data-form';

const integrationMapping = {
    'Notion': NotionIntegration,
    'Airtable': AirtableIntegration,
    'HubSpot': HubSpotIntegration,
};

export const IntegrationForm = () => {
    const [integrationParams, setIntegrationParams] = useState({});
    const [user, setUser] = useState('test_user');
    const [org, setOrg] = useState('test_org');
    const [currType, setCurrType] = useState(null);
    const CurrIntegration = integrationMapping[currType];

  return (
    <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <Card sx={{ minWidth: 400, p: 2, boxShadow: 3 }}>
            <CardContent>
                <Typography variant="h5" align="center" gutterBottom>
                    Integration Setup
                </Typography>

                <TextField
                    label="User"
                    fullWidth
                    value={user}
                    onChange={(e) => setUser(e.target.value)}
                    sx={{ mt: 2 }}
                />
                <TextField
                    label="Organization"
                    fullWidth
                    value={org}
                    onChange={(e) => setOrg(e.target.value)}
                    sx={{ mt: 2 }}
                />
                <Autocomplete
                    id="integration-type"
                    options={Object.keys(integrationMapping)}
                    fullWidth
                    sx={{ mt: 2 }}
                    renderInput={(params) => <TextField {...params} label="Integration Type" />}
                    onChange={(e, value) => setCurrType(value)}
                />

                {currType && 
                <Box sx={{ mt: 3 }}>
                    <CurrIntegration user={user} org={org} integrationParams={integrationParams} setIntegrationParams={setIntegrationParams} />
                </Box>
                }

                {integrationParams?.credentials && 
                <Box sx={{ mt: 3 }}>
                    <DataForm integrationType={integrationParams?.type} credentials={integrationParams?.credentials} />
                </Box>
                }
            </CardContent>
        </Card>
    </Box>
  );
}
