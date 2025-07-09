import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  LinearProgress,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  Assignment,
  Schedule,
  CheckCircle,
  Warning,
  MoreVert,
  Add,
  Work,
  Timer,
  Analytics
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { setWorkItems } from '../../store/slices/workItemsSlice';
import { workItemsAPI } from '../../services/api';
import { Link } from 'react-router-dom';

interface WorkItem {
  id: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  estimated_hours: number;
  actual_hours?: number;
  tags: string[];
  created_at: string;
}

const Dashboard: React.FC = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth as any);
  const { items, loading, error } = useSelector((state: RootState) => state.workItems as any);
  
  const [recentWorkItems, setRecentWorkItems] = useState<WorkItem[]>([]);
  const [stats, setStats] = useState({
    totalHours: 0,
    completedTasks: 0,
    pendingTasks: 0,
    productivityScore: 0
  });

  const fetchWorkItems = useCallback(async () => {
    try {
      const response = await workItemsAPI.getWorkItems();
      dispatch(setWorkItems(response.data));
    } catch (error) {
      console.error('Failed to fetch work items:', error);
    }
  }, [dispatch]);

  const calculateStats = useCallback(() => {
    const totalHours = items.reduce((sum: number, item: WorkItem) => sum + (item.actual_hours || 0), 0);
    const completedTasks = items.filter((item: WorkItem) => item.status === 'completed').length;
    const pendingTasks = items.filter((item: WorkItem) => item.status === 'pending' || item.status === 'in_progress').length;
    const productivityScore = Math.round((completedTasks / items.length) * 100) || 0;

    setStats({
      totalHours,
      completedTasks,
      pendingTasks,
      productivityScore
    });
  }, [items]);

  useEffect(() => {
    fetchWorkItems();
  }, [fetchWorkItems]);

  useEffect(() => {
    if (items.length > 0) {
      calculateStats();
      setRecentWorkItems(items.slice(0, 5));
    }
  }, [items, calculateStats]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': return 'warning';
      case 'pending': return 'default';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const formatTime = (hours: number) => {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome back, {user?.first_name || 'User'}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's what's happening with your work today.
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Quick Actions */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          startIcon={<Add />}
          component={Link}
          to="/work-items"
        >
          Add Work Item
        </Button>
        <Button
          variant="outlined"
          startIcon={<Analytics />}
          component={Link}
          to="/reports"
        >
          View Reports
        </Button>
        <Button
          variant="outlined"
          startIcon={<Work />}
          component={Link}
          to="/work-items"
        >
          Manage Work Items
        </Button>
      </Box>

      {/* Stats Cards */}
      <Box sx={{ display: 'flex', gap: 3, mb: 4, flexWrap: 'wrap' }}>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Timer sx={{ mr: 1, color: 'primary.main' }} />
              <Typography color="textSecondary" variant="body2">
                Total Hours
              </Typography>
            </Box>
            <Typography variant="h4">
              {formatTime(stats.totalHours)}
            </Typography>
            <Typography variant="body2" color="success.main">
              This week
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
              <Typography color="textSecondary" variant="body2">
                Completed Tasks
              </Typography>
            </Box>
            <Typography variant="h4">
              {stats.completedTasks}
            </Typography>
            <Typography variant="body2" color="success.main">
              +{Math.round((stats.completedTasks / items.length) * 100)}% completion rate
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Schedule sx={{ mr: 1, color: 'warning.main' }} />
              <Typography color="textSecondary" variant="body2">
                Pending Tasks
              </Typography>
            </Box>
            <Typography variant="h4">
              {stats.pendingTasks}
            </Typography>
            <Typography variant="body2" color="warning.main">
              Need attention
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingUp sx={{ mr: 1, color: 'info.main' }} />
              <Typography color="textSecondary" variant="body2">
                Productivity Score
              </Typography>
            </Box>
            <Typography variant="h4">
              {stats.productivityScore}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={stats.productivityScore}
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>
      </Box>

      {/* Additional Stats */}
      <Box sx={{ display: 'flex', gap: 3, mb: 4, flexWrap: 'wrap' }}>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Work sx={{ mr: 1, color: 'primary.main' }} />
              <Typography color="textSecondary" variant="body2">
                Active Projects
              </Typography>
            </Box>
            <Typography variant="h4">
              {items.filter((item: WorkItem) => item.status === 'in_progress').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Currently in progress
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Warning sx={{ mr: 1, color: 'error.main' }} />
              <Typography color="textSecondary" variant="body2">
                High Priority
              </Typography>
            </Box>
            <Typography variant="h4">
              {items.filter((item: WorkItem) => item.priority === 'high').length}
            </Typography>
            <Typography variant="body2" color="error.main">
              Requires immediate attention
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Assignment sx={{ mr: 1, color: 'secondary.main' }} />
              <Typography color="textSecondary" variant="body2">
                Total Work Items
              </Typography>
            </Box>
            <Typography variant="h4">
              {items.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              All time
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Analytics sx={{ mr: 1, color: 'success.main' }} />
              <Typography color="textSecondary" variant="body2">
                Weekly Goal
              </Typography>
            </Box>
            <Typography variant="h4">
              {Math.round((stats.totalHours / 40) * 100)}%
            </Typography>
            <Typography variant="body2" color="success.main">
              {stats.totalHours}/40 hours
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Main Content */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {/* Recent Work Items */}
        <Box sx={{ flex: 1, minWidth: 600 }}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Recent Work Items
              </Typography>
              <Button
                component={Link}
                to="/work-items"
                size="small"
                endIcon={<MoreVert />}
              >
                View All
              </Button>
            </Box>
            
            {recentWorkItems.length === 0 ? (
              <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
                No work items yet. Create your first work item to get started!
              </Typography>
            ) : (
              <List>
                {recentWorkItems.map((item: WorkItem) => (
                  <ListItem key={item.id} divider>
                    <ListItemAvatar>
                      <Avatar>
                        <Assignment />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={item.description}
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                          <Chip
                            label={item.category}
                            size="small"
                            variant="outlined"
                          />
                          <Chip
                            label={item.priority}
                            color={getPriorityColor(item.priority) as any}
                            size="small"
                          />
                          <Chip
                            label={item.status}
                            color={getStatusColor(item.status) as any}
                            size="small"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {formatTime(item.estimated_hours)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Box>

        {/* Quick Actions & Tips */}
        <Box sx={{ flex: 1, minWidth: 300 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<Add />}
                fullWidth
                component={Link}
                to="/work-items"
              >
                Add New Work Item
              </Button>
              <Button
                variant="outlined"
                startIcon={<Analytics />}
                fullWidth
                component={Link}
                to="/reports"
              >
                Generate Report
              </Button>
              <Button
                variant="outlined"
                startIcon={<Work />}
                fullWidth
                component={Link}
                to="/work-items"
              >
                View All Work Items
              </Button>
            </Box>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>
              Tips
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              • Update your work items regularly to maintain accurate productivity tracking
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              • Use tags to categorize your work for better organization
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              • Set realistic time estimates to improve planning accuracy
            </Typography>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
};

export default Dashboard; 