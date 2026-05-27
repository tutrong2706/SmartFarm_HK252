import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import {
  ThemeProvider, createTheme, CssBaseline,
  Box, Typography, Button, Card, TextField,
  Select, MenuItem, FormControl, InputLabel,
  Chip, Grid, CircularProgress, Snackbar, Alert,
  Dialog, DialogTitle, DialogContent, DialogActions,
  Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, IconButton, Tooltip, Divider, Stack,
  Tabs, Tab, RadioGroup, FormControlLabel, Radio, Skeleton, OutlinedInput
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Schedule as ScheduleIcon,
  Report as ReportIcon,
  Add as AddIcon,
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as PendingIcon,
  Error as ErrorIcon,
  BarChart as BarChartIcon,
  TableChart as TableChartIcon,
  InsertChart as LineChartIcon,
  Assessment as GaugeIcon,
  FormatListBulleted as ListIcon,
  FilterList as FilterIcon,
  DragHandle as DragHandleIcon,
  Close as CloseIcon,
  TrendingUp as TrendingUpIcon,
  Insights as InsightsIcon,
  QueryStats as QueryStatsIcon,
  Preview as PreviewIcon,
  Edit as EditIcon
} from '@mui/icons-material'
import {
  DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors
} from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import {
  LineChart, BarChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer
} from 'recharts'

import AppShell from './AppShell'
import WidgetSortable from './components/WidgetSortable'
import html2canvas from 'html2canvas' // Thêm dòng này
const API = 'http://localhost:8000'

const COLORS = ['#2e7d32', '#1976d2', '#d32f2f', '#f57c00', '#7b1fa2', '#00796b']

const farmTheme = createTheme({
  palette: {
    primary: { main: '#2e7d32', light: '#4caf50', dark: '#1b5e20', contrastText: '#ffffff' },
    background: { default: '#f0f4f0', paper: '#ffffff' },
  },
  typography: { fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif, "Be Vietnam Pro"', },
  shape: { borderRadius: 12 },
})

const REPORT_FORMATS = [
  { value: 'csv', label: 'CSV', icon: <ListIcon fontSize="small" /> },
  { value: 'xlsx', label: 'Excel', icon: <TableChartIcon fontSize="small" /> },
  { value: 'pdf', label: 'PDF', icon: <ReportIcon fontSize="small" /> },
]

const STATUS_MAP = {
  pending: { label: 'Đang chờ', color: 'default', icon: <PendingIcon fontSize="small" /> },
  processing: { label: 'Đang xử lý', color: 'warning', icon: <PendingIcon fontSize="small" /> },
  completed: { label: 'Hoàn thành', color: 'success', icon: <CheckCircleIcon fontSize="small" /> },
  failed: { label: 'Lỗi', color: 'error', icon: <ErrorIcon fontSize="small" /> },
}

const metricLabels = { temperature: '🌡️ Nhiệt độ', humidity: '💧 Độ ẩm', light: '☀️ Ánh sáng' }

const WIDGET_TYPES = [
  { id: 'stat', label: '📊 Thống kê', icon: <QueryStatsIcon />, color: '#2e7d32' },
  { id: 'chart', label: '📈 Biểu đồ đường', icon: <LineChartIcon />, color: '#1976d2' },
  { id: 'barchart', label: '📊 Biểu đồ cột', icon: <BarChartIcon />, color: '#d32f2f' },
  { id: 'gauge', label: '🎯 Gauge', icon: <GaugeIcon />, color: '#f57c00' },
  { id: 'table', label: '📋 Bảng dữ liệu', icon: <TableChartIcon />, color: '#7b1fa2' },
  { id: 'summary', label: '📌 Tóm tắt', icon: <InsightsIcon />, color: '#00796b' },
]

const WIDGET_CONFIGS = {
  stat: {
    title: 'Thống kê',
    defaultConfig: { metric: 'temperature', aggregation: 'avg', sortOrder: 'desc', zoneIds: [] },
    metrics: ['temperature', 'humidity', 'light']
  },
  chart: {
    title: 'Biểu đồ đường',
    defaultConfig: { metrics: ['temperature'], sortOrder: 'asc', zoneIds: [] },
    metrics: ['temperature', 'humidity', 'light'],
    multiMetric: true
  },
  barchart: {
    title: 'Biểu đồ cột',
    defaultConfig: { metrics: ['temperature'], sortOrder: 'desc', zoneIds: [] },
    metrics: ['temperature', 'humidity', 'light'],
    multiMetric: true
  },
  gauge: {
    title: 'Gauge hiện tại',
    defaultConfig: { metric: 'temperature', zoneIds: [] },
    metrics: ['temperature', 'humidity', 'light']
  },
  table: {
    title: 'Bảng dữ liệu',
    defaultConfig: { metric: 'temperature', sortOrder: 'asc', limit: 50, zoneIds: [] },
    metrics: ['temperature', 'humidity', 'light']
  },
  summary: {
    title: 'Tóm tắt báo cáo',
    defaultConfig: { includeStats: true, sortOrder: 'desc', zoneIds: [] },
    metrics: ['temperature', 'humidity', 'light']
  }
}

function ReportWidget({ widget, onUpdate, onRemove, zones }) {
  const config = WIDGET_CONFIGS[widget.type]
  if (!config) return null

  const isChartType = widget.type === 'chart' || widget.type === 'barchart'

  return (
    <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 2, mb: 2, border: '1px solid #e0e0e0' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography fontWeight={700} color="primary.dark">{config.title}</Typography>
        <IconButton size="small" onClick={() => onRemove(widget.id)}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      <Grid container spacing={2}>
        {/* Metric Selection */}
        {widget.type !== 'summary' && (
          <>
            {isChartType ? (
              <Grid item xs={12}>
                <FormControl fullWidth size="small">
                  <InputLabel>Chỉ số (chọn nhiều)</InputLabel>
                  <Select
                    multiple
                    value={widget.config?.metrics || []}
                    onChange={e => onUpdate(widget.id, { ...widget.config, metrics: typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value })}
                    label="Chỉ số (chọn nhiều)"
                    renderValue={selected => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map(value => (
                          <Chip key={value} label={metricLabels[value]} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    {config.metrics.map(m => (
                      <MenuItem key={m} value={m}>{metricLabels[m]}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            ) : (
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Chỉ số</InputLabel>
                  <Select 
                    value={widget.config?.metric || config.defaultConfig.metric}
                    onChange={e => onUpdate(widget.id, { ...widget.config, metric: e.target.value })}
                    label="Chỉ số"
                  >
                    {config.metrics.map(m => (
                      <MenuItem key={m} value={m}>{metricLabels[m]}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            )}

            {widget.type !== 'gauge' && (
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Sắp xếp</InputLabel>
                  <Select 
                    value={widget.config?.sortOrder || config.defaultConfig.sortOrder || 'asc'}
                    onChange={e => onUpdate(widget.id, { ...widget.config, sortOrder: e.target.value })}
                    label="Sắp xếp"
                  >
                    <MenuItem value="asc">↑ Tăng dần</MenuItem>
                    <MenuItem value="desc">↓ Giảm dần</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}

            {widget.type === 'stat' && (
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Hàm tổng hợp</InputLabel>
                  <Select 
                    value={widget.config?.aggregation || 'avg'}
                    onChange={e => onUpdate(widget.id, { ...widget.config, aggregation: e.target.value })}
                    label="Hàm tổng hợp"
                  >
                    <MenuItem value="avg">Trung bình</MenuItem>
                    <MenuItem value="max">Tối đa</MenuItem>
                    <MenuItem value="min">Tối thiểu</MenuItem>
                    <MenuItem value="sum">Tổng</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}

            {widget.type === 'table' && (
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  label="Số hàng"
                  value={widget.config?.limit || 50}
                  onChange={e => onUpdate(widget.id, { ...widget.config, limit: parseInt(e.target.value) })}
                />
              </Grid>
            )}

            {/* Zone Selection */}
            <Grid item xs={12}>
              <FormControl fullWidth size="small">
                <InputLabel>Khu vực (tùy chọn)</InputLabel>
                <Select
                  multiple
                  value={widget.config?.zoneIds || []}
                  onChange={e => onUpdate(widget.id, { ...widget.config, zoneIds: typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value })}
                  label="Khu vực (tùy chọn)"
                  renderValue={selected => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.length === 0 ? (
                        <Typography variant="caption" sx={{ color: '#9e9e9e' }}>Tất cả khu vực</Typography>
                      ) : (
                        selected.map(zid => {
                          const z = zones.find(z => z.id === zid)
                          return <Chip key={zid} label={z ? z.name : 'Zone ' + zid} size="small" />
                        })
                      )}
                    </Box>
                  )}
                >
                  {zones.map(z => (
                    <MenuItem key={z.id} value={z.id}>{z.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </>
        )}

        {widget.type === 'summary' && (
          <Grid item xs={12}>
            <FormControlLabel
              control={<input type="checkbox" checked={widget.config?.includeStats !== false} onChange={e => onUpdate(widget.id, { ...widget.config, includeStats: e.target.checked })} />}
              label="Bao gồm số liệu thống kê"
            />
          </Grid>
        )}
      </Grid>
    </Box>
  )
}

// Mock data generator
const generateMockData = (days = 30) => {
  const data = []
  const start = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
  for (let i = 0; i < days; i++) {
    const date = new Date(start.getTime() + i * 24 * 60 * 60 * 1000)
    data.push({
      timestamp: date.toISOString().split('T')[0],
      date: date.toLocaleDateString('vi-VN'),
      temperature: parseFloat((20 + Math.random() * 15).toFixed(1)),
      humidity: parseFloat((40 + Math.random() * 50).toFixed(1)),
      light: parseFloat((100 + Math.random() * 900).toFixed(0)),
    })
  }
  return data
}

// Widget Preview Component
function PreviewWidgetRenderer({ widget, mockData, onEdit, isCapture = false }) {
  const config = WIDGET_CONFIGS[widget.type]
  if (!config) return null

  const metric = widget.config?.metric || config.defaultConfig.metric
  const sortOrder = widget.config?.sortOrder || 'asc'
  const aggregation = widget.config?.aggregation || 'avg'

  // Calculate statistics
  const values = mockData.map(d => parseFloat(d[metric]) || 0)
  const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2)
  const max = Math.max(...values).toFixed(2)
  const min = Math.min(...values).toFixed(2)
  const sum = values.reduce((a, b) => a + b, 0).toFixed(2)

  const cardStyle = isCapture ? {
    mb: 0,
    p: 3,
    border: '2px solid #1b5e20',
    bgcolor: '#ffffff',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    borderRadius: 2
  } : {
    mb: 2,
    p: 2,
    border: '1px solid #e8f5e9',
    bgcolor: '#ffffff'
  }

  const titleStyle = isCapture ? {
    fontWeight: 800,
    color: '#1b5e20',
    fontSize: '1.3rem',
    mb: 2,
    pb: 1.5,
    borderBottom: '3px solid #2e7d32'
  } : {
    fontWeight: 700,
    color: 'primary.dark',
    fontSize: '1.05rem'
  }

  return (
    <Card sx={cardStyle}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: isCapture ? 0 : 2 }}>
        <Typography sx={titleStyle}>
          {config.title}
        </Typography>
        {!isCapture && (
          <Button size="small" startIcon={<EditIcon />} onClick={onEdit} variant="text">
            Chỉnh sửa
          </Button>
        )}
      </Box>

      {widget.type === 'stat' && (
        <Box sx={{ textAlign: 'center', py: isCapture ? 5 : 3, bgcolor: isCapture ? '#f1f8e9' : '#ffffff', borderRadius: 1, px: 2, minHeight: isCapture ? 180 : 120, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
          <Typography variant={isCapture ? 'h6' : 'caption'} sx={{ color: '#666', fontWeight: 600, display: 'block', mb: isCapture ? 1.5 : 0.5 }}>
            {metricLabels[metric]}
          </Typography>
          <Typography sx={{ fontSize: isCapture ? '3.8rem' : '2.5rem', fontWeight: 900, color: '#1b5e20', my: isCapture ? 2 : 1 }}>
            {aggregation === 'avg' ? avg : aggregation === 'max' ? max : aggregation === 'min' ? min : sum}
          </Typography>
          <Typography variant={isCapture ? 'body2' : 'caption'} sx={{ color: '#888', fontWeight: 600 }}>
            {aggregation === 'avg' && 'Trung bình'}
            {aggregation === 'max' && 'Tối đa'}
            {aggregation === 'min' && 'Tối thiểu'}
            {aggregation === 'sum' && 'Tổng'}
          </Typography>
        </Box>
      )}

      {widget.type === 'chart' && (
        <Box sx={{ width: '100%', minHeight: isCapture ? 520 : 320, bgcolor: '#ffffff', borderRadius: 1, p: isCapture ? 2 : 0, display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' }}>
          {isCapture ? (
            /* TRẠNG THÁI CHỤP ẢNH */
            <LineChart width={920} height={480} data={mockData} margin={{ top: 20, right: 40, left: 60, bottom: 70 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d0d0d0" strokeWidth={1} />
              <XAxis dataKey="timestamp" tick={{ fontSize: 14, fill: '#666' }} angle={-45} textAnchor="end" height={80} />
              <YAxis tick={{ fontSize: 14, fill: '#666' }} width={60} />
              <RechartsTooltip formatter={value => parseFloat(value).toFixed(1)} contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: 4 }} />
              <Legend wrapperStyle={{ paddingTop: 25, fontSize: 14 }} />

              {(widget.config?.metrics || []).map((m, idx) => (
                <Line
                  isAnimationActive={false}
                  key={m}
                  type="monotone"
                  dataKey={m}
                  stroke={COLORS[idx % COLORS.length]}
                  strokeWidth={3}
                  dot={{ r: 5, fill: COLORS[idx % COLORS.length] }}
                  activeDot={{ r: 7 }}
                />
              ))}
            </LineChart>
          ) : (
            /* TRẠNG THÁI WEB */
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <RechartsTooltip formatter={value => parseFloat(value).toFixed(1)} />
                <Legend />

                {(widget.config?.metrics || []).map((m, idx) => (
                  <Line
                    key={m}
                    type="monotone"
                    dataKey={m}
                    stroke={COLORS[idx % COLORS.length]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </Box>
      )}

      {widget.type === 'barchart' && (
        <Box sx={{ width: '100%', minHeight: isCapture ? 520 : 320, bgcolor: '#ffffff', borderRadius: 1, p: isCapture ? 2 : 0, display: 'flex', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' }}>
          {isCapture ? (
            <BarChart width={920} height={480} data={mockData} margin={{ top: 20, right: 40, left: 60, bottom: 70 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d0d0d0" strokeWidth={1} />
              <XAxis dataKey="timestamp" tick={{ fontSize: 14, fill: '#666' }} angle={-45} textAnchor="end" height={80} />
              <YAxis tick={{ fontSize: 14, fill: '#666' }} width={60} />
              <RechartsTooltip contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: 4 }} />
              <Legend wrapperStyle={{ paddingTop: 25, fontSize: 14 }} />

              {(widget.config?.metrics || []).map((m, idx) => (
                <Bar
                  isAnimationActive={false}
                  key={m}
                  dataKey={m}
                  fill={COLORS[idx % COLORS.length]}
                />
              ))}
            </BarChart>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Legend />

                {(widget.config?.metrics || []).map((m, idx) => (
                  <Bar
                    key={m}
                    dataKey={m}
                    fill={COLORS[idx % COLORS.length]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          )}
        </Box>
      )}

      {widget.type === 'gauge' && (
        <Box sx={{ textAlign: 'center', py: isCapture ? 5 : 3, bgcolor: isCapture ? '#fffbf0' : '#ffffff', borderRadius: 1, px: 2, minHeight: isCapture ? 180 : 120, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
          <GaugeIcon sx={{ fontSize: isCapture ? 80 : 50, color: '#f57c00', mb: isCapture ? 2 : 1 }} />
          <Typography sx={{ fontSize: isCapture ? '3rem' : '1.8rem', fontWeight: 800, color: '#f57c00' }}>
            {avg}%
          </Typography>
          <Typography variant={isCapture ? 'body1' : 'caption'} sx={{ color: '#666', mt: isCapture ? 1 : 0, fontWeight: 600 }}>{metricLabels[metric]}</Typography>
        </Box>
      )}

      {widget.type === 'table' && (
        <Box sx={{ overflowX: 'auto', width: '100%', p: isCapture ? 2 : 0, bgcolor: isCapture ? '#f9f9f9' : '#ffffff', borderRadius: 1 }}>
          <Table size="medium" sx={{ minWidth: isCapture ? 900 : 600 }}>
            <TableHead>
              <TableRow sx={{ bgcolor: '#1b5e20', position: 'sticky', top: 0 }}>
                <TableCell sx={{ fontWeight: 800, fontSize: isCapture ? '1.1rem' : '0.85rem', color: '#fff', py: isCapture ? 1.5 : 0.9, px: isCapture ? 2 : 1 }}>Ngày</TableCell>
                <TableCell sx={{ fontWeight: 800, fontSize: isCapture ? '1.1rem' : '0.85rem', color: '#fff', py: isCapture ? 1.5 : 0.9, px: isCapture ? 2 : 1 }}>{metricLabels[metric]}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockData.slice(0, widget.config?.limit || (isCapture ? 28 : 10)).map((row, i) => (
                <TableRow key={i} sx={{ bgcolor: i % 2 === 0 ? '#fafafa' : '#ffffff', '&:hover': { bgcolor: isCapture ? '#e8f5e9' : '#f5f5f5' }, borderBottom: '1px solid #eee' }}>
                  <TableCell sx={{ fontSize: isCapture ? '1rem' : '0.8rem', py: isCapture ? 1.2 : 0.6, px: isCapture ? 2 : 1, fontWeight: 500 }}>{row.timestamp}</TableCell>
                  <TableCell sx={{ fontSize: isCapture ? '1rem' : '0.8rem', fontWeight: 700, color: '#1b5e20', py: isCapture ? 1.2 : 0.6, px: isCapture ? 2 : 1 }}>{row[metric]}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}

      {widget.type === 'summary' && (
        <Box sx={{ bgcolor: '#f1f8e9', p: isCapture ? 3.5 : 2.5, borderRadius: 2 }}>
          <Grid container spacing={isCapture ? 2.5 : 2}>
            {['Trung bình', 'Tối đa', 'Tối thiểu', 'Tổng'].map((label, idx) => {
              const values = [avg, max, min, sum]
              return (
                <Grid item xs={6} sm={3} key={label}>
                  <Box sx={{ bgcolor: '#ffffff', p: isCapture ? 2 : 1.2, borderRadius: 1.5, border: '2px solid #2e7d32', textAlign: 'center', minHeight: isCapture ? 100 : 70, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <Typography variant={isCapture ? 'body2' : 'caption'} sx={{ color: '#666', fontWeight: 700, display: 'block', mb: 1, fontSize: isCapture ? '0.95rem' : '0.7rem' }}>{label}</Typography>
                    <Typography sx={{ fontWeight: 900, fontSize: isCapture ? '1.5rem' : '1rem', color: '#1b5e20' }}>{values[idx]}</Typography>
                  </Box>
                </Grid>
              )
            })}
          </Grid>
        </Box>
      )}
    </Card>
  )
}

function ZoneChips({ zones, selectedIds, onToggle }) {
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.8 }}>
      {zones.map((z) => (
        <Chip
          key={z.id}
          label={z.name}
          size="small"
          clickable
          variant={selectedIds.includes(z.id) ? 'filled' : 'outlined'}
          color={selectedIds.includes(z.id) ? 'primary' : 'default'}
          onClick={() => onToggle(z.id)}
          sx={{ fontWeight: selectedIds.includes(z.id) ? 700 : 400 }}
        />
      ))}
      {zones.length === 0 && (
        <Typography variant="caption" color="text.disabled">Chưa có khu vực nào</Typography>
      )}
    </Box>
  )
}

function MetricChips({ metrics, selected, onToggle }) {
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.8 }}>
      {Object.entries(metricLabels).map(([key, label]) => (
        <Chip
          key={key}
          label={label}
          size="small"
          clickable
          variant={selected.includes(key) ? 'filled' : 'outlined'}
          color={selected.includes(key) ? 'primary' : 'default'}
          onClick={() => onToggle(key)}
          sx={{ fontWeight: selected.includes(key) ? 700 : 400 }}
        />
      ))}
    </Box>
  )
}

function ReportTable({ reports, zones, onDownload, onDelete }) {
  return (
    <TableContainer>
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            {['ID', 'Tên', 'Định dạng', 'Trạng thái', 'Khu vực', 'Chỉ số', 'Ngày tạo', 'Thao tác']
              .map((h) => (
                <TableCell key={h} sx={{ fontWeight: 800, bgcolor: '#f1f8e9', color: '#1b5e20', fontSize: '0.75rem', py: 1, whiteSpace: 'nowrap' }}>
                  {h}
                </TableCell>
              ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {reports.map((r) => {
            const st = STATUS_MAP[r.status] || STATUS_MAP.pending
            const zoneList = r.zone_ids && r.zone_ids.length
              ? r.zone_ids.map((zid) => {
                  const z = zones.find((z) => z.id === zid)
                  return z ? z.name : '#' + zid
                }).join(', ')
              : 'Tất cả'
            const metricStr = (r.metrics || []).map((m) => metricLabels[m] || m).join(' ')

            return (
              <TableRow key={r.id} hover>
                <TableCell sx={{ fontSize: '0.78rem', fontWeight: 700, color: '#9e9e9e' }}>#{r.id}</TableCell>
                <TableCell sx={{ fontSize: '0.82rem', fontWeight: 600 }}>{r.name}</TableCell>
                <TableCell>
                  <Chip label={r.format.toUpperCase()} size="small" sx={{ fontWeight: 700, fontSize: '0.68rem' }} />
                </TableCell>
                <TableCell>
                  <Chip label={st.label} size="small" color={st.color} icon={st.icon} sx={{ fontWeight: 700, fontSize: '0.68rem' }} />
                </TableCell>
                <TableCell sx={{ fontSize: '0.75rem', color: '#757575', maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {zoneList}
                </TableCell>
                <TableCell sx={{ fontSize: '0.75rem' }}>{metricStr || 'Tất cả'}</TableCell>
                <TableCell sx={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                  {new Date(r.created_at).toLocaleDateString('vi-VN')}
                </TableCell>
                <TableCell>
                  <Stack direction="row" gap={0.5}>
                    {r.status === 'completed' && r.file_path && (
                      <>
                        <Tooltip title="Tải xuống">
                          <IconButton size="small" color="success" onClick={() => onDownload(r.id, r.format)}>
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Xem trước">
                          <IconButton size="small" color="info" disabled>
                            <PreviewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                    {r.status === 'processing' && (
                      <Tooltip title="Đang xử lý...">
                        <CircularProgress size={24} />
                      </Tooltip>
                    )}
                    <Tooltip title="Xóa">
                      <IconButton size="small" color="error" onClick={() => onDelete(r.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default function ReportBuilder() {
  const navigate = useNavigate()
  const [zones, setZones] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ open: false, msg: '', severity: 'success' })
  const [tabValue, setTabValue] = useState(0)

  const [name, setName] = useState('')
  const [format, setFormat] = useState('csv')
  const [zoneIds, setZoneIds] = useState([])
  const [metrics, setMetrics] = useState(['temperature', 'humidity', 'light'])
  const [dateFrom, setDateFrom] = useState('2026-01-01T00:00')
  const [dateTo, setDateTo] = useState('2026-05-15T23:59')
  const [widgets, setWidgets] = useState([])
  const [widgetCounter, setWidgetCounter] = useState(0)

  const [reports, setReports] = useState([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewEditingWidgetId, setPreviewEditingWidgetId] = useState(null)
  const [scheduleOpen, setScheduleOpen] = useState(false)
  const [cronHour, setCronHour] = useState('0')
  const [cronMinute, setCronMinute] = useState('0')
  const [cronDayOfMonth, setCronDayOfMonth] = useState('*')
  const [cronMonth, setCronMonth] = useState('*')
  const [cronDayOfWeek, setCronDayOfWeek] = useState('*')

  const sensors = useSensors(
    useSensor(PointerSensor, { distance: 8 }),
    useSensor(KeyboardSensor)
  )

  const addWidget = (widgetType) => {
    const newWidget = {
      id: `widget-${widgetCounter}`,
      type: widgetType,
      config: { ...WIDGET_CONFIGS[widgetType].defaultConfig }
    }
    setWidgets([...widgets, newWidget])
    setWidgetCounter(widgetCounter + 1)
  }

  const updateWidget = (widgetId, newConfig) => {
    setWidgets(widgets.map(w => w.id === widgetId ? { ...w, config: newConfig } : w))
  }

  const removeWidget = (widgetId) => {
    setWidgets(widgets.filter(w => w.id !== widgetId))
  }

  const handleDragEnd = (event) => {
    const { active, over } = event
    if (active.id !== over.id) {
      const oldIndex = widgets.findIndex(w => w.id === active.id)
      const newIndex = widgets.findIndex(w => w.id === over.id)
      const newWidgets = [...widgets]
      newWidgets.splice(oldIndex, 1)
      newWidgets.splice(newIndex, 0, widgets[oldIndex])
      setWidgets(newWidgets)
    }
  }

  const exportWidgetConfig = () => {
    const config = {
      name,
      format,
      zoneIds,
      metrics,
      dateFrom,
      dateTo,
      widgets: widgets.map(({ id, type, config }) => ({ type, config }))
    }
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report-config-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
    notify('Đã xuất cấu hình báo cáo')
  }

  const fetchZones = useCallback(async () => {
    try {
      const res = await axios.get(API + '/api/zones/')
      setZones(res.data)
    } catch {
      notify('Không thể tải danh sách khu vực', 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchReports = useCallback(async () => {
    try {
      const res = await axios.get(API + '/api/reports/')
      setReports(res.data)
    } catch {
      notify('Không thể tải danh sách báo cáo', 'error')
    }
  }, [])

  useEffect(() => { fetchZones() }, [fetchZones])
  useEffect(() => { fetchReports() }, [fetchReports])

  const notify = (msg, severity) => setToast({ open: true, msg, severity: severity || 'success' })

  const handleGenerate = async () => {
    if (!name.trim()) return notify('Vui lòng nhập tên báo cáo!', 'warning')
    if (!dateFrom || !dateTo) return notify('Vui lòng chọn khoảng ngày!', 'warning')
    
    setToast({ open: true, msg: 'Đang chuẩn bị hình ảnh, vui lòng đợi...', severity: 'info' })

    try {
      let payloadWidgets = []

      if (tabValue === 1 && widgets.length > 0) {
        // NGHIÊM KHẮC: Cho trình duyệt nghỉ 500ms để render DOM ngầm trước khi chụp
        await new Promise(resolve => setTimeout(resolve, 500));

        for (const w of widgets) {
          const element = document.getElementById(`capture-widget-${w.id}`)
          let base64Image = null

          if (element) {
            const canvas = await html2canvas(element, { 
              scale: 1, // HẠ XUỐNG 1: Dung lượng nhẹ hơn 4 lần, API xử lý cực nhanh
              logging: false,
              useCORS: true,
              backgroundColor: '#ffffff' // Ép nền trắng tránh lỗi nền đen
            })
            base64Image = canvas.toDataURL('image/jpeg', 0.8) // Dùng JPEG chuẩn 80% thay vì PNG nặng nề
          }

          payloadWidgets.push({
            type: w.type,
            config: w.config,
            image_data: base64Image
          })
        }
      }

      const payload = {
        name, format, date_from: dateFrom, date_to: dateTo,
      }
      
      if (tabValue === 1 && widgets.length > 0) {
        payload.widgets = payloadWidgets
      } else {
        payload.zone_ids = zoneIds.length > 0 ? zoneIds : null
        payload.metrics = metrics.length > 0 ? metrics : null
      }
      
      await axios.post(API + '/api/reports/generate', payload)
      notify('Báo cáo đang được xử lý thành công ở Backend!')
      setName('')
      fetchReports()
    } catch (err) {
      // Ép hiển thị lỗi chính xác từ Backend nếu có
      const errMsg = typeof err.response?.data?.detail === 'string' 
        ? err.response.data.detail 
        : 'Có lỗi quá tải khi tạo báo cáo';
      notify(errMsg, 'error')
    }
  }

  const handleDownload = async (reportId, reportFormat) => {
    try {
      const res = await axios.get(API + '/api/reports/' + reportId + '/download', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'report_' + reportId + '.' + reportFormat)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      notify('Không thể tải file báo cáo', 'error')
    }
  }

  const handleDeleteReport = async (reportId) => {
    if (!window.confirm('Xóa báo cáo này?')) return
    try {
      await axios.delete(API + '/api/reports/' + reportId)
      notify('Đã xóa báo cáo')
      fetchReports()
    } catch {
      notify('Không thể xóa báo cáo', 'error')
    }
  }

  const handleSchedule = async () => {
    try {
      await axios.post(API + '/api/reports/schedule', {
        name: name || 'Báo cáo tự động ' + new Date().toLocaleDateString('vi-VN'),
        format, date_from: dateFrom, date_to: dateTo,
        zone_ids: zoneIds.length > 0 ? zoneIds : null,
        metrics: metrics.length > 0 ? metrics : null,
        cron_year: '*', cron_month: cronMonth, cron_day: cronDayOfMonth,
        cron_week: '*', cron_day_of_week: cronDayOfWeek,
        cron_hour: cronHour, cron_minute: cronMinute, cron_second: '0',
      })
      notify('Đã đặt lịch báo cáo!')
      setScheduleOpen(false)
      fetchReports()
    } catch (err) {
      notify(err.response?.data?.detail || 'Có lỗi khi đặt lịch', 'error')
    }
  }

  const toggleZone = (zoneId) => {
    setZoneIds(prev => prev.includes(zoneId) ? prev.filter(id => id !== zoneId) : [...prev, zoneId])
  }

  const toggleMetric = (metric) => {
    setMetrics(prev => prev.includes(metric) ? prev.filter(m => m !== metric) : [...prev, metric])
  }

  return (
    <ThemeProvider theme={farmTheme}>
      <CssBaseline />
      <AppShell>
        <Box className="dashboard-content">
          {/* Page Header */}
          <Box sx={{
            background: 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 55%, #388e3c 100%)',
            borderRadius: 3, p: '28px 32px', mb: 3,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            position: 'relative', overflow: 'hidden'
          }}>
            <Box sx={{ position: 'absolute', width: 180, height: 180, borderRadius: '50%',
              background: 'rgba(255,255,255,0.05)', top: -50, right: -40, pointerEvents: 'none' }} />
            <Box>
              <Typography sx={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.7rem', fontWeight: 700,
                letterSpacing: 1.2, textTransform: 'uppercase', mb: 0.5 }}>
                BẢO CÁO & XUẤT DỮ LIỆU
              </Typography>
              <Typography sx={{ color: '#fff', fontSize: '1.5rem', fontWeight: 900, lineHeight: 1.2 }}>
                Report Builder
              </Typography>
              <Typography sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.82rem', mt: 0.5 }}>
                Tạo báo cáo đa chiều · Xuất CSV/Excel/PDF · Lập lịch tự động
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              <Button variant="contained" startIcon={<ScheduleIcon />}
                onClick={() => setScheduleOpen(true)}
                sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#fff', fontWeight: 700,
                  borderRadius: 2, textTransform: 'none', fontSize: '0.82rem',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.25)' } }}>
                Lập lịch
              </Button>
              <Button variant="contained" startIcon={<AddIcon />}
                onClick={() => setHistoryOpen(true)}
                sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#fff', fontWeight: 700,
                  borderRadius: 2, textTransform: 'none', fontSize: '0.82rem',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.25)' } }}>
                Lịch sử
              </Button>
            </Stack>
          </Box>

          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
            <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
              <Tab label="📋 Trình tạo đơn giản" icon={<ListIcon />} iconPosition="start" />
              <Tab label="🎨 Trình tạo tiên tiến (Widget)" icon={<BarChartIcon />} iconPosition="start" />
            </Tabs>
          </Box>

          {/* Tab 1: Simple Builder */}
          {tabValue === 0 && (
            <>
              {/* Build Form */}
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9', mb: 3 }}>
                <Box sx={{ px: 3, py: 2.5, display: 'flex', justifyContent: 'space-between',
                  alignItems: 'center', borderBottom: '1px solid #f0f4f0' }}>
                  <Typography variant="h6" fontWeight="800" color="primary.dark" sx={{ fontSize: '1rem' }}>
                    Tạo báo cáo mới
                  </Typography>
                  <Chip icon={<FilterIcon />} label="Bộ lọc" size="small"
                    sx={{ bgcolor: '#e8f5e9', color: '#1b5e20', fontWeight: 700 }} />
                </Box>

                <Box sx={{ p: 3 }}>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <TextField fullWidth size="small" label="Tên báo cáo *"
                        value={name} onChange={e => setName(e.target.value)} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Định dạng</InputLabel>
                        <Select value={format} onChange={e => setFormat(e.target.value)} label="Định dạng"
                          sx={{ borderRadius: 2, bgcolor: '#f9fafb' }}>
                          {REPORT_FORMATS.map(f => (
                            <MenuItem key={f.value} value={f.value}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {f.icon}
                                <Typography>{f.label}</Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField fullWidth size="small" label="Từ ngày" type="datetime-local"
                        value={dateFrom} onChange={e => setDateFrom(e.target.value)}
                        InputLabelProps={{ shrink: true }} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField fullWidth size="small" label="Đến ngày" type="datetime-local"
                        value={dateTo} onChange={e => setDateTo(e.target.value)}
                        InputLabelProps={{ shrink: true }} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2, bgcolor: '#f9fafb' }}>
                        <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                          Khu vực
                        </Typography>
                        <ZoneChips zones={zones} selectedIds={zoneIds} onToggle={toggleZone} />
                      </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2, bgcolor: '#f9fafb' }}>
                        <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                          Chỉ số
                        </Typography>
                        <MetricChips metrics={metrics} selected={metrics} onToggle={toggleMetric} />
                      </Paper>
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                        <Button variant="outlined" color="inherit"
                          onClick={() => { setName(''); setZoneIds([]); setMetrics(['temperature','humidity','light']); setDateFrom('2026-01-01T00:00'); setDateTo('2026-05-15T23:59'); }}>
                          Xóa form
                        </Button>
                        <Button variant="contained" startIcon={<PlayIcon />} onClick={handleGenerate}
                          sx={{ borderRadius: 2, fontWeight: 700, px: 3 }}>
                          Tạo báo cáo
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              </Card>

              {/* Quick Preview */}
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9' }}>
                <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #f0f4f0' }}>
                  <Typography variant="h6" fontWeight="800" color="primary.dark" sx={{ fontSize: '1rem' }}>
                    Xem trước
                  </Typography>
                </Box>
                <Box sx={{ p: 3 }}>
                  {name && dateFrom && dateTo ? (
                    <Box>
                      <Typography sx={{ fontSize: '0.88rem', mb: 1 }}>
                        <strong>{name}</strong> · {format.toUpperCase()} ·{' '}
                        {new Date(dateFrom).toLocaleDateString('vi-VN')} →{' '}
                        {new Date(dateTo).toLocaleDateString('vi-VN')}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
                        {zoneIds.length > 0 ? (
                          zoneIds.map(zid => {
                            const z = zones.find(z => z.id === zid)
                            return <Chip key={zid} label={z ? z.name : 'Zone ' + zid} size="small"
                              sx={{ bgcolor: '#e8f5e9', color: '#1b5e20', fontWeight: 600 }} />
                          })
                        ) : (
                          <Chip label="Tất cả khu vực" size="small"
                            sx={{ bgcolor: '#e8f5e9', color: '#1b5e20', fontWeight: 600 }} />
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {metrics.map(m => (
                          <Chip key={m} label={metricLabels[m]} size="small"
                            sx={{ bgcolor: '#fff3e0', color: '#e65100', fontWeight: 600 }} />
                        ))}
                      </Box>
                    </Box>
                  ) : (
                    <Typography sx={{ color: '#bdbdbd', textAlign: 'center', py: 3 }}>
                      Điền thông tin bên trên để xem trước báo cáo
                    </Typography>
                  )}
                </Box>
              </Card>
            </>
          )}

          {/* Tab 2: Widget Builder */}
          {tabValue === 1 && (
            <>
              {/* Widget Builder Header */}
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9', mb: 3, bgcolor: '#f9fafb' }}>
                <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #f0f4f0' }}>
                  <Typography variant="h6" fontWeight="800" color="primary.dark" sx={{ fontSize: '1rem', mb: 1.5 }}>
                    📦 Thêm Widget vào báo cáo
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                    Chọn widget dưới đây và cấu hình tùy chọn. Kéo để sắp xếp thứ tự.
                  </Typography>
                  <Grid container spacing={1}>
                    {WIDGET_TYPES.map(wt => (
                      <Grid item xs={12} sm={6} md={4} lg={2} key={wt.id}>
                        <Button
                          fullWidth
                          variant="outlined"
                          size="small"
                          startIcon={wt.icon}
                          onClick={() => addWidget(wt.id)}
                          sx={{
                            borderColor: wt.color,
                            color: wt.color,
                            fontWeight: 600,
                            textTransform: 'none',
                            fontSize: '0.75rem',
                            '&:hover': { bgcolor: wt.color + '10' }
                          }}
                        >
                          {wt.label}
                        </Button>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              </Card>

              {/* Basic Settings */}
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9', mb: 3 }}>
                <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #f0f4f0' }}>
                  <Typography variant="h6" fontWeight="800" color="primary.dark" sx={{ fontSize: '1rem' }}>
                    ⚙️ Cài đặt báo cáo
                  </Typography>
                </Box>
                <Box sx={{ p: 3 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={3}>
                      <TextField fullWidth size="small" label="Tên báo cáo" 
                        value={name} onChange={e => setName(e.target.value)} />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Định dạng</InputLabel>
                        <Select value={format} onChange={e => setFormat(e.target.value)} label="Định dạng"
                          sx={{ borderRadius: 2, bgcolor: '#f9fafb' }}>
                          {REPORT_FORMATS.map(f => (
                            <MenuItem key={f.value} value={f.value}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {f.icon}
                                <Typography>{f.label}</Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField fullWidth size="small" label="Từ ngày" type="datetime-local"
                        value={dateFrom} onChange={e => setDateFrom(e.target.value)}
                        InputLabelProps={{ shrink: true }} />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField fullWidth size="small" label="Đến ngày" type="datetime-local"
                        value={dateTo} onChange={e => setDateTo(e.target.value)}
                        InputLabelProps={{ shrink: true }} />
                    </Grid>
                  </Grid>
                </Box>
              </Card>

              {/* Widget Configuration */}
              <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9', mb: 3 }}>
                <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #f0f4f0' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" fontWeight="800" color="primary.dark" sx={{ fontSize: '1rem' }}>
                      🎨 Cấu hình Widget ({widgets.length})
                    </Typography>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={exportWidgetConfig}
                      disabled={widgets.length === 0}
                      sx={{ fontWeight: 600 }}
                    >
                      💾 Xuất cấu hình
                    </Button>
                  </Box>
                </Box>
                <Box sx={{ p: 3 }}>
                  {widgets.length === 0 ? (
                    <Typography sx={{ color: '#9e9e9e', textAlign: 'center', py: 4 }}>
                      Chưa có widget nào. Thêm widget từ bên trên để bắt đầu.
                    </Typography>
                  ) : (
                    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                      <SortableContext items={widgets.map(w => w.id)} strategy={verticalListSortingStrategy}>
                        {widgets.map(widget => (
                          <div key={widget.id}>
                            <WidgetSortable widget={{ id: widget.id, title: WIDGET_CONFIGS[widget.type].title }}>
                              <ReportWidget 
                                widget={widget}
                                onUpdate={updateWidget}
                                onRemove={removeWidget}
                                zones={zones}
                              />
                            </WidgetSortable>
                          </div>
                        ))}
                      </SortableContext>
                    </DndContext>
                  )}
                </Box>
              </Card>

              {/* Action Buttons */}
              {widgets.length > 0 && (
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mb: 3 }}>
                  <Button
                    variant="outlined"
                    onClick={() => setWidgets([])}
                    sx={{ borderRadius: 2, fontWeight: 700 }}
                  >
                    🗑️ Xóa tất cả widget
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<PreviewIcon />}
                    onClick={() => setPreviewOpen(true)}
                    sx={{ borderRadius: 2, fontWeight: 700 }}
                  >
                    👁️ Xem trước báo cáo
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={handleGenerate}
                    sx={{ borderRadius: 2, fontWeight: 700, px: 3 }}
                  >
                    ✨ Tạo báo cáo với widget
                  </Button>
                </Box>
              )}
              {/* ================= HIDDEN CAPTURE CONTAINER ================= */}
              {widgets.length > 0 && (
                <Box sx={{ position: 'fixed', top: '100vh', left: 0, width: '950px', zIndex: -1000, fontFamily: '"Segoe UI", Arial, sans-serif' }}>
                  {widgets.map(widget => (
                    <Box key={`hidden-${widget.id}`} id={`capture-widget-${widget.id}`} sx={{ bgcolor: '#ffffff', p: 3, mb: 2, pageBreakAfter: 'always' }}>
                      <PreviewWidgetRenderer 
                        widget={widget}
                        mockData={generateMockData()} 
                        onEdit={() => {}}
                        isCapture={true}
                      />
                    </Box>
                  ))}
                </Box>
              )}
              {/* ================= KẾT THÚC ĐOẠN RENDER NGẦM ================= */}
            </>
          )}
        </Box>

        {/* Preview Dialog */}
        <Dialog open={previewOpen} onClose={() => { setPreviewOpen(false); setPreviewEditingWidgetId(null); }}
          fullWidth maxWidth="md" PaperProps={{ sx: { maxHeight: '90vh' } }}>
          <DialogTitle fontWeight="bold" sx={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: 1 }}>
            <PreviewIcon /> Xem trước báo cáo
          </DialogTitle>
          <DialogContent dividers sx={{ overflowY: 'auto' }}>
            {previewEditingWidgetId ? (
              <Box>
                <Button
                  size="small"
                  startIcon={<CloseIcon />}
                  onClick={() => setPreviewEditingWidgetId(null)}
                  sx={{ mb: 2 }}
                >
                  Quay lại xem trước
                </Button>
                <Typography variant="h6" fontWeight={700} sx={{ mb: 2 }}>
                  Chỉnh sửa Widget
                </Typography>
                <Box>
                  {widgets.map(w => w.id === previewEditingWidgetId ? (
                    <Box key={w.id}>
                      <ReportWidget 
                        widget={w}
                        onUpdate={updateWidget}
                        onRemove={removeWidget}
                        zones={zones}
                      />
                    </Box>
                  ) : null)}
                </Box>
              </Box>
            ) : (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                  📊 Báo cáo: <strong>{name || 'Báo cáo không tên'}</strong> 
                  {dateFrom && dateTo && ` • ${new Date(dateFrom).toLocaleDateString('vi-VN')} → ${new Date(dateTo).toLocaleDateString('vi-VN')}`}
                </Typography>
                
                {widgets.length === 0 ? (
                  <Typography sx={{ textAlign: 'center', py: 4, color: '#9e9e9e' }}>
                    Chưa thêm widget nào
                  </Typography>
                ) : (
                  <Box>
                    {widgets.map(widget => (
                      <PreviewWidgetRenderer 
                        key={widget.id}
                        widget={widget}
                        mockData={generateMockData()}
                        onEdit={() => setPreviewEditingWidgetId(widget.id)}
                      />
                    ))}
                  </Box>
                )}
              </Box>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => { setPreviewOpen(false); setPreviewEditingWidgetId(null); }} color="inherit" size="small">
              Đóng
            </Button>
            <Button 
              variant="contained" 
              onClick={handleGenerate}
              disabled={widgets.length === 0}
              sx={{ borderRadius: 2, fontWeight: 700 }}
            >
              <DownloadIcon sx={{ mr: 0.5 }} /> Tạo báo cáo
            </Button>
          </DialogActions>
        </Dialog>

        {/* Report History Dialog */}
        <Dialog open={historyOpen} onClose={() => setHistoryOpen(false)}
          fullWidth maxWidth="md" PaperProps={{ sx: { maxHeight: '80vh' } }}>
          <DialogTitle fontWeight="bold" sx={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: 1 }}>
            <ReportIcon /> Lịch sử báo cáo
          </DialogTitle>
          <DialogContent dividers>
            {reports.length === 0 ? (
              <Box sx={{ py: 4, textAlign: 'center', color: 'text.secondary' }}>
                <ReportIcon sx={{ fontSize: 40, opacity: 0.3, mb: 1 }} />
                <Typography>Chưa có báo cáo nào</Typography>
              </Box>
            ) : (
              <ReportTable reports={reports} zones={zones}
                onDownload={handleDownload} onDelete={handleDeleteReport} />
            )}
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => setHistoryOpen(false)} color="inherit" size="small">Đóng</Button>
          </DialogActions>
        </Dialog>

        {/* Schedule Dialog */}
        <Dialog open={scheduleOpen} onClose={() => setScheduleOpen(false)} fullWidth maxWidth="sm">
          <DialogTitle fontWeight="bold" sx={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 1 }}>
            <ScheduleIcon /> Lập lịch báo cáo
          </DialogTitle>
          <DialogContent dividers>
            <Typography sx={{ fontSize: '0.82rem', color: '#9e9e9e', mb: 2 }}>
              Đặt lịch tự động tạo báo cáo theo biểu thức cron
            </Typography>
            <Grid container spacing={2} sx={{ mt: 0.5 }}>
              <Grid item xs={6}>
                <TextField fullWidth size="small" label="Giờ (0-23)" value={cronHour}
                  onChange={e => setCronHour(e.target.value)} helperText="* = mọi giờ" />
              </Grid>
              <Grid item xs={6}>
                <TextField fullWidth size="small" label="Phút (0-59)" value={cronMinute}
                  onChange={e => setCronMinute(e.target.value)} helperText="* = mọi phút" />
              </Grid>
              <Grid item xs={6}>
                <TextField fullWidth size="small" label="Ngày trong tháng" value={cronDayOfMonth}
                  onChange={e => setCronDayOfMonth(e.target.value)} helperText="1-31 hoặc *" />
              </Grid>
              <Grid item xs={6}>
                <TextField fullWidth size="small" label="Tháng (1-12)" value={cronMonth}
                  onChange={e => setCronMonth(e.target.value)} helperText="1-12 hoặc *" />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth size="small" label="Ngày trong tuần (0-6, 0=CN)" value={cronDayOfWeek}
                  onChange={e => setCronDayOfWeek(e.target.value)} helperText="0-6 hoặc *" />
              </Grid>
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }} />
                <Typography variant="caption">
                  Biểu thức: <strong>{cronMinute} {cronHour} {cronDayOfMonth} {cronMonth} {cronDayOfWeek}</strong>
                </Typography>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            <Button onClick={() => setScheduleOpen(false)} color="inherit" size="small">Hủy</Button>
            <Button onClick={handleSchedule} variant="contained" size="small" sx={{ borderRadius: 2, fontWeight: 700 }}>
              <ScheduleIcon sx={{ mr: 0.5 }} /> Đặt lịch
            </Button>
          </DialogActions>
        </Dialog>

        {/* Toast */}
        <Snackbar open={toast.open} autoHideDuration={3500}
          onClose={() => setToast({ ...toast, open: false })}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
          <Alert severity={toast.severity} variant="filled" sx={{ fontWeight: 700 }}>
            {toast.msg}
          </Alert>
        </Snackbar>
      </AppShell>
    </ThemeProvider>
  )
}
