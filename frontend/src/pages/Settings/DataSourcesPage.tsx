import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  BugReport as JiraIcon,
  Chat as TeamsIcon,
  Email as EmailIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as ConnectedIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { dataSourceAPI } from '../../services/api';

interface DataSource {
  id: string;
  name: string;
  type: 'jira' | 'teams' | 'email';
  status: 'connected' | 'disconnected' | 'error';
  lastSync?: string;
  config: {
    url?: string;
    username?: string;
    projectKey?: string;
    email?: string;
    server?: string;
  };
}

interface DataSourceForm {
  name: string;
  type: 'jira' | 'teams' | 'email';
  url?: string;
  username?: string;
  password?: string;
  projectKey?: string;
  email?: string;
  server?: string;
  port?: number;
}

const schema = yup.object({
  name: yup.string().required('Name is required'),
  type: yup.string().oneOf(['jira', 'teams', 'email']).required('Type is required'),
  url: yup.string().when('type', {
    is: 'jira',
    then: (schema) => schema.required('Jira URL is required').url('Must be a valid URL'),
  }),
  username: yup.string().when('type', {
    is: 'jira',
    then: (schema) => schema.required('Username is required'),
  }),
  password: yup.string().when('type', {
    is: 'jira',
    then: (schema) => schema.required('Password is required'),
  }),
  projectKey: yup.string().when('type', {
    is: 'jira',
    then: (schema) => schema.required('Project key is required'),
  }),
  email: yup.string().when('type', {
    is: 'email',
    then: (schema) => schema.required('Email is required').email('Must be a valid email'),
  }),
  server: yup.string().when('type', {
    is: 'email',
    then: (schema) => schema.required('Server is required'),
  }),
  port: yup.number().when('type', {
    is: 'email',
    then: (schema) => schema.required('Port is required').min(1).max(65535),
  }),
}).required();

const DataSourcesPage: React.FC = () => {
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<DataSource | null>(null);
  const [error, setError] = useState('');

  const {
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<DataSourceForm>({
    resolver: yupResolver(schema) as any,
    defaultValues: {
      type: 'jira',
    },
  });

  const selectedType = watch('type');

  useEffect(() => {
    loadDataSources();
  }, []);

  const loadDataSources = async () => {
    setLoading(true);
    try {
      const response = await dataSourceAPI.getDataSources();
      setDataSources(response.data);
    } catch (err: any) {
      setError('Failed to load data sources');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSource = () => {
    setEditingSource(null);
    reset({
      type: 'jira',
    });
    setDialogOpen(true);
  };

  const handleEditSource = (source: DataSource) => {
    setEditingSource(source);
    reset({
      name: source.name,
      type: source.type,
      url: source.config.url,
      username: source.config.username,
      projectKey: source.config.projectKey,
      email: source.config.email,
      server: source.config.server,
    });
    setDialogOpen(true);
  };

  const handleDeleteSource = async (id: string) => {
    try {
      await dataSourceAPI.deleteDataSource(id);
      setDataSources(dataSources.filter(source => source.id !== id));
    } catch (err: any) {
      setError('Failed to delete data source');
    }
  };

  const handleTestConnection = async (source: DataSource) => {
    try {
      const response = await dataSourceAPI.testConnection(source.id);
      if (response.data.success) {
        // Update the source status to connected
        setDataSources(dataSources.map(s => 
          s.id === source.id ? { ...s, status: 'connected' } : s
        ));
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      setError('Failed to test connection');
    }
  };

  const onSubmit = async (data: DataSourceForm) => {
    try {
      const sourceData = {
        name: data.name,
        type: data.type,
        config: {
          url: data.url,
          username: data.username,
          password: data.password,
          projectKey: data.projectKey,
          email: data.email,
          server: data.server,
          port: data.port,
        }
      };

      if (editingSource) {
        // Update existing source
        const response = await dataSourceAPI.updateDataSource(editingSource.id, sourceData);
        setDataSources(dataSources.map(source => 
          source.id === editingSource.id ? response.data : source
        ));
      } else {
        // Add new source
        const response = await dataSourceAPI.createDataSource(sourceData);
        setDataSources([...dataSources, response.data]);
      }
      setDialogOpen(false);
      reset();
    } catch (err: any) {
      setError('Failed to save data source');
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'jira':
        return <JiraIcon />;
      case 'teams':
        return <TeamsIcon />;
      case 'email':
        return <EmailIcon />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <ConnectedIcon />;
      case 'error':
        return <ErrorIcon />;
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Data Sources
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddSource}
          >
            Add Data Source
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 3 }}>
            {dataSources.map((source) => (
              <Card key={source.id}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {getTypeIcon(source.type)}
                    <Typography variant="h6" sx={{ ml: 1 }}>
                      {source.name}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Chip
                      label={source.status}
                      color={getStatusColor(source.status) as any}
                      size="small"
                      icon={getStatusIcon(source.status) || undefined}
                    />
                    {source.lastSync && (
                      <Typography variant="caption" sx={{ ml: 1 }}>
                        Last sync: {new Date(source.lastSync).toLocaleDateString()}
                      </Typography>
                    )}
                  </Box>

                  <Typography variant="body2" color="text.secondary">
                    {source.config.url && `URL: ${source.config.url}`}
                    {source.config.email && `Email: ${source.config.email}`}
                  </Typography>
                </CardContent>
                
                <CardActions>
                  <Button
                    size="small"
                    onClick={() => handleTestConnection(source)}
                  >
                    Test Connection
                  </Button>
                  <Tooltip title="Edit">
                    <IconButton
                      size="small"
                      onClick={() => handleEditSource(source)}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDeleteSource(source.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </CardActions>
              </Card>
            ))}
          </Box>
        )}
      </Box>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingSource ? 'Edit Data Source' : 'Add Data Source'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit(onSubmit as any)} sx={{ mt: 2 }}>
            <Controller
              name="name"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Name"
                  margin="normal"
                  error={!!errors.name}
                  helperText={errors.name?.message}
                />
              )}
            />

            <Controller
              name="type"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth margin="normal">
                  <InputLabel>Type</InputLabel>
                  <Select {...field} label="Type">
                    <MenuItem value="jira">Jira</MenuItem>
                    <MenuItem value="teams">Microsoft Teams</MenuItem>
                    <MenuItem value="email">Email</MenuItem>
                  </Select>
                </FormControl>
              )}
            />

            {selectedType === 'jira' && (
              <>
                <Controller
                  name="url"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Jira URL"
                      margin="normal"
                      placeholder="https://company.atlassian.net"
                      error={!!errors.url}
                      helperText={errors.url?.message}
                    />
                  )}
                />

                <Controller
                  name="username"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Username/Email"
                      margin="normal"
                      error={!!errors.username}
                      helperText={errors.username?.message}
                    />
                  )}
                />

                <Controller
                  name="password"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Password/API Token"
                      type="password"
                      margin="normal"
                      error={!!errors.password}
                      helperText={errors.password?.message}
                    />
                  )}
                />

                <Controller
                  name="projectKey"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Project Key"
                      margin="normal"
                      placeholder="PROJ"
                      error={!!errors.projectKey}
                      helperText={errors.projectKey?.message}
                    />
                  )}
                />
              </>
            )}

            {selectedType === 'teams' && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Microsoft Teams integration will use OAuth 2.0 authentication.
                Click "Save" to initiate the OAuth flow.
              </Typography>
            )}

            {selectedType === 'email' && (
              <>
                <Controller
                  name="email"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Email Address"
                      margin="normal"
                      error={!!errors.email}
                      helperText={errors.email?.message}
                    />
                  )}
                />

                <Controller
                  name="server"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="IMAP Server"
                      margin="normal"
                      placeholder="mail.company.com"
                      error={!!errors.server}
                      helperText={errors.server?.message}
                    />
                  )}
                />

                <Controller
                  name="port"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Port"
                      type="number"
                      margin="normal"
                      defaultValue={993}
                      error={!!errors.port}
                      helperText={errors.port?.message}
                    />
                  )}
                />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit(onSubmit as any)} variant="contained">
            {editingSource ? 'Update' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DataSourcesPage; 