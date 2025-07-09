import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Report {
  id: string;
  user_id: string;
  report_type: 'daily' | 'weekly' | 'monthly' | 'custom';
  report_date: string;
  template: string;
  content: string;
  metadata: {
    total_work_items: number;
    total_time_hours: number;
    categories: Record<string, number>;
    priorities: Record<string, number>;
    jira_tickets_updated: number;
  };
  quality_score: number;
  status: 'generating' | 'completed' | 'failed';
  created_at: string;
  updated_at?: string;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  template_type: 'daily' | 'weekly' | 'monthly' | 'custom';
  content_template: string;
  is_default: boolean;
  user_id?: string;
}

export interface Analytics {
  productivity_trends: {
    date: string;
    hours_worked: number;
    work_items_completed: number;
    efficiency_score: number;
  }[];
  category_breakdown: {
    category: string;
    hours: number;
    items: number;
    percentage: number;
  }[];
  weekly_summary: {
    week_start: string;
    total_hours: number;
    total_items: number;
    average_daily_hours: number;
    efficiency_score: number;
  };
  time_distribution: {
    hour: number;
    productivity_score: number;
    work_items: number;
  }[];
}

export interface ReportsState {
  reports: Report[];
  currentReport: Report | null;
  templates: ReportTemplate[];
  analytics: Analytics | null;
  loading: boolean;
  error: string | null;
  generatingReport: boolean;
  filters: {
    report_type?: string;
    date_range?: {
      start: string;
      end: string;
    };
    template?: string;
  };
}

const initialState: ReportsState = {
  reports: [],
  currentReport: null,
  templates: [],
  analytics: null,
  loading: false,
  error: null,
  generatingReport: false,
  filters: {},
};

const reportsSlice = createSlice({
  name: 'reports',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setReports: (state, action: PayloadAction<Report[]>) => {
      state.reports = action.payload;
      state.loading = false;
      state.error = null;
    },
    addReport: (state, action: PayloadAction<Report>) => {
      state.reports.unshift(action.payload);
    },
    updateReport: (state, action: PayloadAction<Report>) => {
      const index = state.reports.findIndex(report => report.id === action.payload.id);
      if (index !== -1) {
        state.reports[index] = action.payload;
      }
      if (state.currentReport?.id === action.payload.id) {
        state.currentReport = action.payload;
      }
    },
    deleteReport: (state, action: PayloadAction<string>) => {
      state.reports = state.reports.filter(report => report.id !== action.payload);
      if (state.currentReport?.id === action.payload) {
        state.currentReport = null;
      }
    },
    setCurrentReport: (state, action: PayloadAction<Report | null>) => {
      state.currentReport = action.payload;
    },
    setTemplates: (state, action: PayloadAction<ReportTemplate[]>) => {
      state.templates = action.payload;
    },
    addTemplate: (state, action: PayloadAction<ReportTemplate>) => {
      state.templates.push(action.payload);
    },
    updateTemplate: (state, action: PayloadAction<ReportTemplate>) => {
      const index = state.templates.findIndex(template => template.id === action.payload.id);
      if (index !== -1) {
        state.templates[index] = action.payload;
      }
    },
    deleteTemplate: (state, action: PayloadAction<string>) => {
      state.templates = state.templates.filter(template => template.id !== action.payload);
    },
    setAnalytics: (state, action: PayloadAction<Analytics>) => {
      state.analytics = action.payload;
    },
    setGeneratingReport: (state, action: PayloadAction<boolean>) => {
      state.generatingReport = action.payload;
    },
    setFilters: (state, action: PayloadAction<Partial<ReportsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    updateReportStatus: (state, action: PayloadAction<{ id: string; status: Report['status'] }>) => {
      const report = state.reports.find(report => report.id === action.payload.id);
      if (report) {
        report.status = action.payload.status;
      }
      if (state.currentReport?.id === action.payload.id) {
        state.currentReport.status = action.payload.status;
      }
    },
  },
});

export const {
  setLoading,
  setError,
  setReports,
  addReport,
  updateReport,
  deleteReport,
  setCurrentReport,
  setTemplates,
  addTemplate,
  updateTemplate,
  deleteTemplate,
  setAnalytics,
  setGeneratingReport,
  setFilters,
  clearFilters,
  updateReportStatus,
} = reportsSlice.actions;

export default reportsSlice.reducer; 