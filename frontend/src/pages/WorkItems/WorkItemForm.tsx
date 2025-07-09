import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

const schema = yup.object({
  description: yup.string().required('Description is required'),
  category: yup.string().required('Category is required'),
  priority: yup.string().required('Priority is required'),
  status: yup.string().required('Status is required'),
  estimated_hours: yup.number()
    .required('Estimated hours is required')
    .min(0.1, 'Must be at least 0.1 hours')
    .max(24, 'Cannot exceed 24 hours'),
  actual_hours: yup.number()
    .notRequired()
    .min(0, 'Cannot be negative')
    .max(24, 'Cannot exceed 24 hours'),
  tags: yup.array().of(yup.string()).notRequired(),
}).required();

type WorkItemFormData = yup.InferType<typeof schema>;

interface WorkItemFormProps {
  workItem?: Partial<WorkItemFormData>;
  onSubmit: (data: WorkItemFormData) => void;
  onCancel: () => void;
}

const WorkItemForm: React.FC<WorkItemFormProps> = ({ workItem, onSubmit, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tagInput, setTagInput] = useState('');

  const {
    control,
    handleSubmit,
    formState: { errors },
    setValue,
    watch
  } = useForm({
    resolver: yupResolver(schema),
    defaultValues: {
      description: workItem?.description || '',
      category: workItem?.category || '',
      priority: workItem?.priority || '',
      status: workItem?.status || '',
      estimated_hours: workItem?.estimated_hours || 1,
      actual_hours: workItem?.actual_hours ?? undefined,
      tags: workItem?.tags ?? [],
    },
  });

  const watchedTags = watch('tags');

  const handleAddTag = () => {
    const tags = watchedTags ?? [];
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setValue('tags', [...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const tags = watchedTags ?? [];
    setValue('tags', tags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleAddTag();
    }
  };

  const handleFormSubmit = async (data: WorkItemFormData) => {
    setLoading(true);
    setError('');

    try {
      await onSubmit(data);
    } catch (err: any) {
      setError(err.message || 'Failed to save work item');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit(handleFormSubmit)}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Controller
        name="description"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            fullWidth
            label="Description"
            multiline
            rows={3}
            margin="normal"
            error={!!errors.description}
            helperText={errors.description?.message}
            placeholder="Describe the work item..."
          />
        )}
      />

      <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
        <Controller
          name="category"
          control={control}
          render={({ field }) => (
            <FormControl fullWidth sx={{ minWidth: 200 }}>
              <InputLabel>Category</InputLabel>
              <Select
                {...field}
                label="Category"
                error={!!errors.category}
              >
                <MenuItem value="bug_fix">Bug Fix</MenuItem>
                <MenuItem value="feature_development">Feature Development</MenuItem>
                <MenuItem value="meeting">Meeting</MenuItem>
                <MenuItem value="research">Research</MenuItem>
                <MenuItem value="documentation">Documentation</MenuItem>
                <MenuItem value="testing">Testing</MenuItem>
                <MenuItem value="general">General</MenuItem>
              </Select>
            </FormControl>
          )}
        />

        <Controller
          name="priority"
          control={control}
          render={({ field }) => (
            <FormControl fullWidth sx={{ minWidth: 200 }}>
              <InputLabel>Priority</InputLabel>
              <Select
                {...field}
                label="Priority"
                error={!!errors.priority}
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
              </Select>
            </FormControl>
          )}
        />

        <Controller
          name="status"
          control={control}
          render={({ field }) => (
            <FormControl fullWidth sx={{ minWidth: 200 }}>
              <InputLabel>Status</InputLabel>
              <Select
                {...field}
                label="Status"
                error={!!errors.status}
              >
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
                <MenuItem value="on_hold">On Hold</MenuItem>
              </Select>
            </FormControl>
          )}
        />
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
        <Controller
          name="estimated_hours"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              type="number"
              label="Estimated Hours"
              fullWidth
              sx={{ minWidth: 200 }}
              inputProps={{ min: 0.1, max: 24, step: 0.1 }}
              error={!!errors.estimated_hours}
              helperText={errors.estimated_hours?.message}
            />
          )}
        />

        <Controller
          name="actual_hours"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              type="number"
              label="Actual Hours (Optional)"
              fullWidth
              sx={{ minWidth: 200 }}
              inputProps={{ min: 0, max: 24, step: 0.1 }}
              error={!!errors.actual_hours}
              helperText={errors.actual_hours?.message}
            />
          )}
        />
      </Box>

      <Box sx={{ mt: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Tags
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          {(watchedTags ?? []).filter((tag): tag is string => !!tag).map((tag, index) => (
            <Chip
              key={index}
              label={tag}
              onDelete={() => handleRemoveTag(tag)}
              color="primary"
              variant="outlined"
            />
          ))}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Add a tag..."
            size="small"
            sx={{ flex: 1 }}
          />
          <Button
            type="button"
            variant="outlined"
            onClick={handleAddTag}
            disabled={!tagInput.trim()}
          >
            Add
          </Button>
        </Box>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mt: 4, justifyContent: 'flex-end' }}>
        <Button
          type="button"
          variant="outlined"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Saving...' : (workItem ? 'Update' : 'Create')}
        </Button>
      </Box>
    </Box>
  );
};

export default WorkItemForm; 