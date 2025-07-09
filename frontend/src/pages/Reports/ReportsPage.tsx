import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { setReports } from '../../store/slices/reportsSlice';
import { reportsAPI } from '../../services/api';

interface Report {
  id: string;
  type: string;
  title: string;
  data: any;
  generated_at: string;
  date_range: {
    start: string;
    end: string;
  };
}

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
      id={`report-tabpanel-${index}`}
      aria-labelledby={`report-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ReportsPage: React.FC = () => {
  const dispatch = useDispatch();
  const { error } = useSelector((state: RootState) => state.reports as any);
  
  const [selectedReportType, setSelectedReportType] = useState('productivity');
  const [dateRange, setDateRange] = useState('week');
  const [tabValue, setTabValue] = useState(0);
  const [generatedReports, setGeneratedReports] = useState<Report[]>([]);

  const fetchReports = useCallback(async () => {
    try {
      const response = await reportsAPI.getReports();
      dispatch(setReports(response.data));
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    }
  }, [dispatch]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const generateReport = async () => {
    try {
      const response = await reportsAPI.generateReport({
        type: selectedReportType,
        date_range: dateRange,
      });
      const newReport = response.data;
      setGeneratedReports([newReport, ...generatedReports]);
    } catch (error) {
      console.error('Failed to generate report:', error);
    }
  };

  // Sample data for charts
  const productivityData = [
    { day: 'Mon', hours: 8.5, tasks: 12 },
    { day: 'Tue', hours: 7.2, tasks: 10 },
    { day: 'Wed', hours: 9.1, tasks: 15 },
    { day: 'Thu', hours: 6.8, tasks: 8 },
    { day: 'Fri', hours: 8.9, tasks: 13 },
    { day: 'Sat', hours: 4.2, tasks: 6 },
    { day: 'Sun', hours: 2.1, tasks: 3 },
  ];

  const categoryData = [
    { name: 'Bug Fixes', value: 35, color: '#ff6b6b' },
    { name: 'Features', value: 25, color: '#4ecdc4' },
    { name: 'Meetings', value: 20, color: '#45b7d1' },
    { name: 'Research', value: 15, color: '#96ceb4' },
    { name: 'Documentation', value: 5, color: '#feca57' },
  ];

  const weeklyTrends = [
    { week: 'Week 1', productivity: 85, efficiency: 78 },
    { week: 'Week 2', productivity: 88, efficiency: 82 },
    { week: 'Week 3', productivity: 92, efficiency: 85 },
    { week: 'Week 4', productivity: 87, efficiency: 80 },
    { week: 'Week 5', productivity: 90, efficiency: 83 },
  ];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Reports & Analytics
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Report Type</InputLabel>
            <Select
              value={selectedReportType}
              label="Report Type"
              onChange={(e) => setSelectedReportType(e.target.value)}
            >
              <MenuItem value="productivity">Productivity</MenuItem>
              <MenuItem value="efficiency">Efficiency</MenuItem>
              <MenuItem value="category">Category Analysis</MenuItem>
              <MenuItem value="trends">Trends</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Date Range</InputLabel>
            <Select
              value={dateRange}
              label="Date Range"
              onChange={(e) => setDateRange(e.target.value)}
            >
              <MenuItem value="week">This Week</MenuItem>
              <MenuItem value="month">This Month</MenuItem>
              <MenuItem value="quarter">This Quarter</MenuItem>
              <MenuItem value="year">This Year</MenuItem>
            </Select>
          </FormControl>
          <Button variant="contained" onClick={generateReport}>
            Generate Report
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="report tabs">
          <Tab label="Overview" />
          <Tab label="Productivity" />
          <Tab label="Categories" />
          <Tab label="Trends" />
          <Tab label="Generated Reports" />
        </Tabs>

        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Card sx={{ flex: 1, minWidth: 200 }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Hours This Week
                </Typography>
                <Typography variant="h4">
                  47.8h
                </Typography>
                <Typography variant="body2" color="success.main">
                  +12% from last week
                </Typography>
              </CardContent>
            </Card>
            <Card sx={{ flex: 1, minWidth: 200 }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Tasks Completed
                </Typography>
                <Typography variant="h4">
                  67
                </Typography>
                <Typography variant="body2" color="success.main">
                  +8% from last week
                </Typography>
              </CardContent>
            </Card>
            <Card sx={{ flex: 1, minWidth: 200 }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Productivity Score
                </Typography>
                <Typography variant="h4">
                  87%
                </Typography>
                <Typography variant="body2" color="warning.main">
                  -3% from last week
                </Typography>
              </CardContent>
            </Card>
            <Card sx={{ flex: 1, minWidth: 200 }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Efficiency Rate
                </Typography>
                <Typography variant="h4">
                  92%
                </Typography>
                <Typography variant="body2" color="success.main">
                  +5% from last week
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </TabPanel>

        {/* Productivity Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Daily Productivity Overview
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={productivityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Bar yAxisId="left" dataKey="hours" fill="#8884d8" name="Hours Worked" />
                <Bar yAxisId="right" dataKey="tasks" fill="#82ca9d" name="Tasks Completed" />
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </TabPanel>

        {/* Categories Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            <Box sx={{ flex: 1, minWidth: 400 }}>
              <Typography variant="h6" gutterBottom>
                Work Distribution by Category
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
            <Box sx={{ flex: 1, minWidth: 400 }}>
              <Typography variant="h6" gutterBottom>
                Category Breakdown
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Category</TableCell>
                      <TableCell>Percentage</TableCell>
                      <TableCell>Hours</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {categoryData.map((row) => (
                      <TableRow key={row.name}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Box
                              sx={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                backgroundColor: row.color,
                              }}
                            />
                            {row.name}
                          </Box>
                        </TableCell>
                        <TableCell>{row.value}%</TableCell>
                        <TableCell>{Math.round((row.value / 100) * 47.8)}h</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          </Box>
        </TabPanel>

        {/* Trends Tab */}
        <TabPanel value={tabValue} index={3}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Weekly Trends
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={weeklyTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="productivity"
                  stroke="#8884d8"
                  strokeWidth={2}
                  name="Productivity Score"
                />
                <Line
                  type="monotone"
                  dataKey="efficiency"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  name="Efficiency Rate"
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </TabPanel>

        {/* Generated Reports Tab */}
        <TabPanel value={tabValue} index={4}>
          <Typography variant="h6" gutterBottom>
            Generated Reports
          </Typography>
          {generatedReports.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No reports generated yet. Use the controls above to generate a new report.
            </Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Report Type</TableCell>
                    <TableCell>Date Range</TableCell>
                    <TableCell>Generated</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {generatedReports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell>
                        <Chip label={report.type} color="primary" />
                      </TableCell>
                      <TableCell>
                        {formatDate(report.date_range.start)} - {formatDate(report.date_range.end)}
                      </TableCell>
                      <TableCell>{formatDate(report.generated_at)}</TableCell>
                      <TableCell>
                        <Button size="small" variant="outlined">
                          Download
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default ReportsPage; 