import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface WorkItem {
  id: string;
  user_id: string;
  message_id?: string;
  jira_ticket_id?: string;
  description: string;
  time_spent_minutes: number;
  confidence_score: number;
  category: string;
  priority: string;
  estimated_hours: number;
  actual_hours?: number;
  tags: string[];
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  created_at: string;
  updated_at?: string;
}

export interface WorkItemsState {
  items: WorkItem[];
  currentItem: WorkItem | null;
  loading: boolean;
  error: string | null;
  filters: {
    status?: string;
    category?: string;
    priority?: string;
    dateRange?: {
      start: string;
      end: string;
    };
  };
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
}

const initialState: WorkItemsState = {
  items: [],
  currentItem: null,
  loading: false,
  error: null,
  filters: {},
  pagination: {
    page: 1,
    limit: 10,
    total: 0,
  },
};

const workItemsSlice = createSlice({
  name: 'workItems',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setWorkItems: (state, action: PayloadAction<WorkItem[]>) => {
      state.items = action.payload;
      state.loading = false;
      state.error = null;
    },
    addWorkItem: (state, action: PayloadAction<WorkItem>) => {
      state.items.unshift(action.payload);
    },
    updateWorkItem: (state, action: PayloadAction<WorkItem>) => {
      const index = state.items.findIndex(item => item.id === action.payload.id);
      if (index !== -1) {
        state.items[index] = action.payload;
      }
      if (state.currentItem?.id === action.payload.id) {
        state.currentItem = action.payload;
      }
    },
    deleteWorkItem: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter(item => item.id !== action.payload);
      if (state.currentItem?.id === action.payload) {
        state.currentItem = null;
      }
    },
    setCurrentItem: (state, action: PayloadAction<WorkItem | null>) => {
      state.currentItem = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<WorkItemsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setPagination: (state, action: PayloadAction<Partial<WorkItemsState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    updateWorkItemStatus: (state, action: PayloadAction<{ id: string; status: WorkItem['status'] }>) => {
      const item = state.items.find(item => item.id === action.payload.id);
      if (item) {
        item.status = action.payload.status;
      }
      if (state.currentItem?.id === action.payload.id) {
        state.currentItem.status = action.payload.status;
      }
    },
    bulkUpdateWorkItems: (state, action: PayloadAction<Partial<WorkItem>[]>) => {
      action.payload.forEach(update => {
        const item = state.items.find(item => item.id === update.id);
        if (item) {
          Object.assign(item, update);
        }
      });
    },
  },
});

export const {
  setLoading,
  setError,
  setWorkItems,
  addWorkItem,
  updateWorkItem,
  deleteWorkItem,
  setCurrentItem,
  setFilters,
  clearFilters,
  setPagination,
  updateWorkItemStatus,
  bulkUpdateWorkItems,
} = workItemsSlice.actions;

export default workItemsSlice.reducer; 