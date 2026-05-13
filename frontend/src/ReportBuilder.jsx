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
  TableHead, TableRow, IconButton, Tooltip, Divider, Stack
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
  FilterList as FilterIcon
} from '@mui/icons-material'

import AppShell from './AppShell'

const API = 'http://localhost:8000'

const farmTheme = createTheme({
  palette: {
    primary: { main: '#2e7d32', light: '#4caf50', dark: '#1b5e20', contrastText: '#ffffff' },
    background: { default: '#f0f4f0', paper: '#ffffff' },
  },
  typography: { fontFamily: '"Be Vietnam Pro", "Plus Jakarta Sans", "Inter", "Roboto", sans-serif' },
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
                      <Tooltip title="Tải xuống">
                        <IconButton size="small" color="success" onClick={() => onDownload(r.id, r.format)}>
                          <DownloadIcon fontSize="small" />
                        </IconButton>
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

  const [name, setName] = useState('')
  const [format, setFormat] = useState('csv')
  const [zoneIds, setZoneIds] = useState([])
  const [metrics, setMetrics] = useState(['temperature', 'humidity', 'light'])
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const [reports, setReports] = useState([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [scheduleOpen, setScheduleOpen] = useState(false)
  const [cronHour, setCronHour] = useState('0')
  const [cronMinute, setCronMinute] = useState('0')
  const [cronDayOfMonth, setCronDayOfMonth] = useState('*')
  const [cronMonth, setCronMonth] = useState('*')
  const [cronDayOfWeek, setCronDayOfWeek] = useState('*')

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
    try {
      await axios.post(API + '/api/reports/generate', {
        name, format, date_from: dateFrom, date_to: dateTo,
        zone_ids: zoneIds.length > 0 ? zoneIds : null,
        metrics: metrics.length > 0 ? metrics : null,
      })
      notify('Báo cáo đang được tạo...')
      setName('')
      fetchReports()
    } catch (err) {
      notify(err.response?.data?.detail || 'Có lỗi khi tạo báo cáo', 'error')
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
                      onClick={() => { setName(''); setZoneIds([]); setMetrics(['temperature','humidity','light']); setDateFrom(''); setDateTo(''); }}>
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
        </Box>

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
