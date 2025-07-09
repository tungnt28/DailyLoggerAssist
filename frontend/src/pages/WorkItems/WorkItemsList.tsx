import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  TextField,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Search,
  FilterList
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { setWorkItems, addWorkItem, updateWorkItem, deleteWorkItem } from '../../store/slices/workItemsSlice';
import { workItemsAPI } from '../../services/api';
import WorkItemForm from './WorkItemForm';

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

const WorkItemsList: React.FC = () => {
  const dispatch = useDispatch();
  const { items, loading, error } = useSelector((state: RootState) => state.workItems as any);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [openForm, setOpenForm] = useState(false);
  const [editingItem, setEditingItem] = useState<WorkItem | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const fetchWorkItems = useCallback(async () => {
    try {
      const response = await workItemsAPI.getWorkItems();
      dispatch(setWorkItems(response.data));
    } catch (error) {
      console.error('Failed to fetch work items:', error);
    }
  }, [dispatch]);

  useEffect(() => {
    fetchWorkItems();
  }, [fetchWorkItems]);

  const handleCreateWorkItem = async (workItemData: any) => {
    // Normalize null to undefined for backend compatibility
    const normalizedData = {
      ...workItemData,
      actual_hours: workItemData.actual_hours ?? undefined,
      tags: workItemData.tags ?? [],
    };
    try {
      const response = await workItemsAPI.createWorkItem(normalizedData);
      dispatch(addWorkItem(response.data));
      setOpenForm(false);
    } catch (error) {
      console.error('Failed to create work item:', error);
    }
  };

  const handleUpdateWorkItem = async (workItemData: any) => {
    if (!editingItem) return;
    // Normalize null to undefined for backend compatibility
    const normalizedData = {
      ...workItemData,
      actual_hours: workItemData.actual_hours ?? undefined,
      tags: workItemData.tags ?? [],
    };
    try {
      const response = await workItemsAPI.updateWorkItem(editingItem.id, normalizedData);
      dispatch(updateWorkItem(response.data));
      setEditingItem(null);
      setOpenForm(false);
    } catch (error) {
      console.error('Failed to update work item:', error);
    }
  };

  const handleDeleteWorkItem = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this work item?')) return;

    try {
      await workItemsAPI.deleteWorkItem(id);
      dispatch(deleteWorkItem(id));
    } catch (error) {
      console.error('Failed to delete work item:', error);
    }
  };

  const filteredItems = items.filter((item: WorkItem) => {
    const matchesSearch = item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !statusFilter || item.status === statusFilter;
    const matchesCategory = !categoryFilter || item.category === categoryFilter;
    const matchesPriority = !priorityFilter || item.priority === priorityFilter;
    
    return matchesSearch && matchesStatus && matchesCategory && matchesPriority;
  });

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

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Work Items
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setOpenForm(true)}
        >
          Add Work Item
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <Box sx={{ flex: 1, minWidth: 200 }}>
            <TextField
              fullWidth
              placeholder="Search work items..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Box>
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="in_progress">In Progress</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
            </Select>
          </FormControl>
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={categoryFilter}
              label="Category"
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="bug_fix">Bug Fix</MenuItem>
              <MenuItem value="feature_development">Feature Development</MenuItem>
              <MenuItem value="meeting">Meeting</MenuItem>
              <MenuItem value="general">General</MenuItem>
            </Select>
          </FormControl>
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Priority</InputLabel>
            <Select
              value={priorityFilter}
              label="Priority"
              onChange={(e) => setPriorityFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<FilterList />}
            onClick={() => {
              setSearchTerm('');
              setStatusFilter('');
              setCategoryFilter('');
              setPriorityFilter('');
            }}
          >
            Clear Filters
          </Button>
        </Box>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Work Items Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Description</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Estimated</TableCell>
                <TableCell>Actual</TableCell>
                <TableCell>Tags</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary">
                      Loading...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : filteredItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No work items found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredItems
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((item: WorkItem) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {item.description}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={item.category} size="small" />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.priority}
                          color={getPriorityColor(item.priority) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={item.status}
                          color={getStatusColor(item.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{formatTime(item.estimated_hours)}</TableCell>
                      <TableCell>
                        {item.actual_hours ? formatTime(item.actual_hours) : '-'}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {item.tags.slice(0, 2).map((tag, index) => (
                            <Chip key={index} label={tag} size="small" variant="outlined" />
                          ))}
                          {item.tags.length > 2 && (
                            <Chip label={`+${item.tags.length - 2}`} size="small" />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setEditingItem(item);
                                setOpenForm(true);
                              }}
                            >
                              <Edit />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteWorkItem(item.id)}
                            >
                              <Delete />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredItems.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      </Paper>

      {/* Work Item Form Dialog */}
      <Dialog
        open={openForm}
        onClose={() => {
          setOpenForm(false);
          setEditingItem(null);
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingItem ? 'Edit Work Item' : 'Add Work Item'}
        </DialogTitle>
        <DialogContent>
          <WorkItemForm
            workItem={editingItem ?? undefined}
            onSubmit={editingItem ? handleUpdateWorkItem : handleCreateWorkItem}
            onCancel={() => {
              setOpenForm(false);
              setEditingItem(null);
            }}
          />
        </DialogContent>
      </Dialog>
    </Container>
  );
};

export default WorkItemsList; 