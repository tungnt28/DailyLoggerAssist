import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Switch,
  TextField,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Alert,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { updateUser } from '../../store/slices/authSlice';
import { userAPI } from '../../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SettingsPage: React.FC = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth as any);
  
  const [tabValue, setTabValue] = useState(0);
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: true,
      dailyDigest: false,
      weeklyReport: true,
      workItemUpdates: true,
      systemAlerts: true
    },
    preferences: {
      theme: 'light',
      language: 'en',
      timezone: 'UTC',
      dateFormat: 'MM/DD/YYYY',
      timeFormat: '12h'
    },
    privacy: {
      profileVisibility: 'public',
      showEmail: false,
      showPhone: false,
      allowAnalytics: true
    }
  });
  const [profile, setProfile] = useState({
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    bio: user?.bio || ''
  });
  const [successMessage, setSuccessMessage] = useState('');

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleNotificationChange = (key: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: event.target.checked
      }
    }));
  };

  const handlePreferenceChange = (key: string) => (event: any) => {
    setSettings(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [key]: event.target.value
      }
    }));
  };

  const handlePrivacyChange = (key: string) => (event: any) => {
    setSettings(prev => ({
      ...prev,
      privacy: {
        ...prev.privacy,
        [key]: event.target.value
      }
    }));
  };

  const handleProfileChange = (key: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setProfile(prev => ({
      ...prev,
      [key]: event.target.value
    }));
  };

  const saveSettings = async () => {
    try {
      await userAPI.updateSettings(settings);
      setSuccessMessage('Settings saved successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const saveProfile = async () => {
    try {
      const response = await userAPI.updateProfile(profile);
      dispatch(updateUser(response.data));
      setSuccessMessage('Profile updated successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SettingsIcon sx={{ mr: 2, fontSize: 32 }} />
        <Typography variant="h4" component="h1">
          Settings
        </Typography>
      </Box>

      {/* Success Message */}
      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
          <Tab label="Profile" />
          <Tab label="Notifications" />
          <Tab label="Preferences" />
          <Tab label="Privacy" />
        </Tabs>

        {/* Profile Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <TextField
                fullWidth
                label="First Name"
                value={profile.firstName}
                onChange={handleProfileChange('firstName')}
                margin="normal"
              />
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <TextField
                fullWidth
                label="Last Name"
                value={profile.lastName}
                onChange={handleProfileChange('lastName')}
                margin="normal"
              />
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={profile.email}
                onChange={handleProfileChange('email')}
                margin="normal"
              />
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <TextField
                fullWidth
                label="Phone"
                value={profile.phone}
                onChange={handleProfileChange('phone')}
                margin="normal"
              />
            </Box>
            <Box sx={{ width: '100%' }}>
              <TextField
                fullWidth
                label="Bio"
                multiline
                rows={4}
                value={profile.bio}
                onChange={handleProfileChange('bio')}
                margin="normal"
                placeholder="Tell us about yourself..."
              />
            </Box>
            <Box sx={{ width: '100%' }}>
              <Button variant="contained" onClick={saveProfile}>
                Save Profile
              </Button>
            </Box>
          </Box>
        </TabPanel>

        {/* Notifications Tab */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Notification Preferences
          </Typography>
          <List>
            <ListItem>
              <ListItemText
                primary="Email Notifications"
                secondary="Receive notifications via email"
              />
              <ListItemSecondaryAction>
                <Switch
                  edge="end"
                  checked={settings.notifications.email}
                  onChange={handleNotificationChange('email')}
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText
                primary="Push Notifications"
                secondary="Receive push notifications in the browser"
              />
              <ListItemSecondaryAction>
                <Switch
                  edge="end"
                  checked={settings.notifications.push}
                  onChange={handleNotificationChange('push')}
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText
                primary="Daily Digest"
                secondary="Receive a daily summary of your activities"
              />
              <ListItemSecondaryAction>
                <Switch
                  edge="end"
                  checked={settings.notifications.dailyDigest}
                  onChange={handleNotificationChange('dailyDigest')}
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText
                primary="Weekly Reports"
                secondary="Receive weekly productivity reports"
              />
              <ListItemSecondaryAction>
                <Switch
                  edge="end"
                  checked={settings.notifications.weeklyReport}
                  onChange={handleNotificationChange('weeklyReport')}
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText
                primary="Work Item Updates"
                secondary="Get notified when work items are updated"
              />
              <ListItemSecondaryAction>
                <Switch
                  edge="end"
                  checked={settings.notifications.workItemUpdates}
                  onChange={handleNotificationChange('workItemUpdates')}
                />
              </ListItemSecondaryAction>
            </ListItem>
            <Divider />
            <ListItem>
              <ListItemText
                primary="System Alerts"
                secondary="Receive important system notifications"
              />
              <ListItemSecondaryAction>
                <Switch
                  edge="end"
                  checked={settings.notifications.systemAlerts}
                  onChange={handleNotificationChange('systemAlerts')}
                />
              </ListItemSecondaryAction>
            </ListItem>
          </List>
          <Box sx={{ mt: 2 }}>
            <Button variant="contained" onClick={saveSettings}>
              Save Notification Settings
            </Button>
          </Box>
        </TabPanel>

        {/* Preferences Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Theme</InputLabel>
                <Select
                  value={settings.preferences.theme}
                  label="Theme"
                  onChange={handlePreferenceChange('theme')}
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="auto">Auto</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Language</InputLabel>
                <Select
                  value={settings.preferences.language}
                  label="Language"
                  onChange={handlePreferenceChange('language')}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Spanish</MenuItem>
                  <MenuItem value="fr">French</MenuItem>
                  <MenuItem value="de">German</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={settings.preferences.timezone}
                  label="Timezone"
                  onChange={handlePreferenceChange('timezone')}
                >
                  <MenuItem value="UTC">UTC</MenuItem>
                  <MenuItem value="EST">Eastern Time</MenuItem>
                  <MenuItem value="PST">Pacific Time</MenuItem>
                  <MenuItem value="CET">Central European Time</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Date Format</InputLabel>
                <Select
                  value={settings.preferences.dateFormat}
                  label="Date Format"
                  onChange={handlePreferenceChange('dateFormat')}
                >
                  <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                  <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
                  <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Time Format</InputLabel>
                <Select
                  value={settings.preferences.timeFormat}
                  label="Time Format"
                  onChange={handlePreferenceChange('timeFormat')}
                >
                  <MenuItem value="12h">12-hour</MenuItem>
                  <MenuItem value="24h">24-hour</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ width: '100%' }}>
              <Button variant="contained" onClick={saveSettings}>
                Save Preferences
              </Button>
            </Box>
          </Box>
        </TabPanel>

        {/* Privacy Tab */}
        <TabPanel value={tabValue} index={3}>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Profile Visibility</InputLabel>
                <Select
                  value={settings.privacy.profileVisibility}
                  label="Profile Visibility"
                  onChange={handlePrivacyChange('profileVisibility')}
                >
                  <MenuItem value="public">Public</MenuItem>
                  <MenuItem value="private">Private</MenuItem>
                  <MenuItem value="team">Team Only</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Show Email</InputLabel>
                <Select
                  value={settings.privacy.showEmail ? 'yes' : 'no'}
                  label="Show Email"
                  onChange={(e) => handlePrivacyChange('showEmail')({ target: { value: e.target.value === 'yes' } })}
                >
                  <MenuItem value="yes">Yes</MenuItem>
                  <MenuItem value="no">No</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Show Phone</InputLabel>
                <Select
                  value={settings.privacy.showPhone ? 'yes' : 'no'}
                  label="Show Phone"
                  onChange={(e) => handlePrivacyChange('showPhone')({ target: { value: e.target.value === 'yes' } })}
                >
                  <MenuItem value="yes">Yes</MenuItem>
                  <MenuItem value="no">No</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ flex: 1, minWidth: 300 }}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Allow Analytics</InputLabel>
                <Select
                  value={settings.privacy.allowAnalytics ? 'yes' : 'no'}
                  label="Allow Analytics"
                  onChange={(e) => handlePrivacyChange('allowAnalytics')({ target: { value: e.target.value === 'yes' } })}
                >
                  <MenuItem value="yes">Yes</MenuItem>
                  <MenuItem value="no">No</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ width: '100%' }}>
              <Button variant="contained" onClick={saveSettings}>
                Save Privacy Settings
              </Button>
            </Box>
          </Box>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default SettingsPage; 