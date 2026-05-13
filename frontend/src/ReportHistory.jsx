import { useState, useEffect, useCallback } from 'react'
import { FormControl, InputLabel } from '@mui/material'
import axios from 'axios'
import {
  ThemeProvider, createTheme, CssBaseline,
  Box, Typography, Button, Card,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, IconButton, CircularProgress, Snackbar, Alert, Stack, Tooltip,
  Select, MenuItem, Paper, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  Report as ReportIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as PendingIcon,
  Error as ErrorIcon,
  CalendarMonth as CalendarIcon,
  FilterAlt as FilterIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon
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

const STATUS_MAP = {
  pending: { label: 'Đang chờ', color: 'default', icon: <PendingIcon fontSize="small" /> },
  processing: { label: 'Đang xử lý', color: 'warning', icon: <PendingIcon fontSize="small" /> },
  completed: { label: 'Hoàn thành', color: 'success', icon: <CheckCircleIcon fontSize="small" /> },
  failed: { label: 'Lỗi', color: 'error', icon: <ErrorIcon fontSize="small" /> },
  scheduled: { label: 'Đã lên lịch', color: 'info', icon: <CalendarIcon fontSize="small" /> },
}

const FORMAT_LABELS = { csv: 'CSV', xlsx: 'Excel', pdf: 'PDF' }

const metricLabels = { temperature: '🌡️', humidity: '💧', light: '☀️' }

function DetailRow({ label, value }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
      <Typography sx={{ fontSize: '0.82rem', color: '#757575', fontWeight: 600 }}>{label}</Typography>
      <Typography sx={{ fontSize: '0.82rem', color: '#212121', fontWeight: 600, textAlign: 'right', ml: 2 }}>{value}</Typography>
    </Box>
  )
}

export default function ReportHistory() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState({ open: false, msg: '', severity: 'success' })
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterFormat, setFilterFormat] = useState('all')
  const [detailOpen, setDetailOpen] = useState(false)
  const [detailReport, setDetailReport] = useState(null)

  const fetchReports = useCallback(async () => {
    try {
      const res = await axios.get(API + '/api/reports/')
      setReports(res.data)
    } catch {
      notify('Không thể tải danh sách báo cáo', 'error')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchReports() }, [fetchReports])

  const notify = (msg, severity) => setToast({ open: true, msg, severity: severity || 'success' })

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
      notify('Tải file thành công!')
    } catch {
      notify('Không thể tải file báo cáo', 'error')
    }
  }

  const handleDelete = async (reportId) => {
    if (!window.confirm('Xóa báo cáo này?')) return
    try {
      await axios.delete(API + '/api/reports/' + reportId)
      notify('Đã xóa báo cáo')
      fetchReports()
    } catch {
      notify('Không thể xóa báo cáo', 'error')
    }
  }

  const handleCancelSchedule = async (reportId) => {
    if (!window.confirm('Hủy báo cáo đã lên lịch này?')) return
    try {
      await axios.delete(API + '/api/reports/schedule/' + reportId)
      notify('Đã hủy báo cáo lịch')
      fetchReports()
    } catch {
      notify('Không thể hủy', 'error')
    }
  }

  const openDetail = (report) => {
    setDetailReport(report)
    setDetailOpen(true)
  }

  const filteredReports = reports.filter((r) => {
    if (filterStatus !== 'all' && r.status !== filterStatus) return false
    if (filterFormat !== 'all' && r.format !== filterFormat) return false
    return true
  })

  const stats = {
    total: reports.length,
    completed: reports.filter(r => r.status === 'completed').length,
    processing: reports.filter(r => r.status === 'processing').length,
    failed: reports.filter(r => r.status === 'failed').length,
    scheduled: reports.filter(r => r.status === 'scheduled').length,
  }

  return (
    <ThemeProvider theme={farmTheme}>
      <CssBaseline />
      <AppShell>
        <Box className="dashboard-content">
          {/* Page Header */}
          <Box sx={{
            background: 'linear-gradient(135deg, #0d3b4f 0%, #1565c0 55%, #1976d2 100%)',
            borderRadius: 3, p: '28px 32px', mb: 3,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            position: 'relative', overflow: 'hidden'
          }}>
            <Box sx={{ position: 'absolute', width: 200, height: 200, borderRadius: '50%',
              background: 'rgba(255,255,255,0.05)', top: -60, right: -50, pointerEvents: 'none' }} />
            <Box>
              <Typography sx={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.7rem', fontWeight: 700,
                letterSpacing: 1.2, textTransform: 'uppercase', mb: 0.5 }}>
                LỊCH SỬ BÁO CÁO
              </Typography>
              <Typography sx={{ color: '#fff', fontSize: '1.5rem', fontWeight: 900, lineHeight: 1.2 }}>
                Report History
              </Typography>
              <Typography sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.82rem', mt: 0.5 }}>
                Quản lý và tải về các báo cáo đã tạo · {stats.total} báo cáo
              </Typography>
            </Box>
            <Button variant="contained" startIcon={<RefreshIcon />}
              onClick={fetchReports}
              sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#fff', fontWeight: 700,
                borderRadius: 2, '&:hover': { bgcolor: 'rgba(255,255,255,0.25)' },
                textTransform: 'none', fontSize: '0.82rem' }}>
              Làm mới
            </Button>
          </Box>

          {/* Stats */}
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 2, mb: 3 }}>
            {[
              { label: 'Tổng cộng', value: stats.total, color: '#1565c0', bg: '#e3f2fd', Icon: ReportIcon },
              { label: 'Hoàn thành', value: stats.completed, color: '#2e7d32', bg: '#e8f5e9', Icon: CheckCircleIcon },
              { label: 'Đang xử lý', value: stats.processing, color: '#e65100', bg: '#fff3e0', Icon: PendingIcon },
              { label: 'Lỗi', value: stats.failed, color: '#d32f2f', bg: '#ffebee', Icon: ErrorIcon },
              { label: 'Lịch sử', value: stats.scheduled, color: '#0277bd', bg: '#e0f7fa', Icon: CalendarIcon },
            ].map((s) => (
              <Card key={s.label} elevation={0} sx={{ borderRadius: 16, border: '1px solid #e8f5e9', background: '#fff', textAlign: 'center', py: 2 }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                  <s.Icon sx={{ color: s.color, fontSize: 24 }} />
                  <Typography sx={{ fontSize: '1.5rem', fontWeight: 900, color: s.color }}>{s.value}</Typography>
                  <Typography sx={{ fontSize: '0.72rem', color: '#757575', fontWeight: 600 }}>{s.label}</Typography>
                </Box>
              </Card>
            ))}
          </Box>

          {/* Filters */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9', mb: 3 }}>
            <Box sx={{ px: 3, py: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <FilterIcon sx={{ color: '#1b5e20', fontSize: 20 }} />
              <Typography sx={{ fontWeight: 700, fontSize: '0.85rem', color: '#1b5e20' }}>Bộ lọc:</Typography>
              <FormControl size="small" sx={{ minWidth: 130 }}>
                <InputLabel>Trạng thái</InputLabel>
                <Select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} label="Trạng thái"
                  sx={{ borderRadius: 2, bgcolor: '#f9fafb' }}>
                  <MenuItem value="all">Tất cả</MenuItem>
                  {Object.entries(STATUS_MAP).map(([key, val]) => (
                    <MenuItem key={key} value={key}>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        {val.icon}
                        <Typography>{val.label}</Typography>
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Định dạng</InputLabel>
                <Select value={filterFormat} onChange={e => setFilterFormat(e.target.value)} label="Định dạng"
                  sx={{ borderRadius: 2, bgcolor: '#f9fafb' }}>
                  <MenuItem value="all">Tất cả</MenuItem>
                  {['csv', 'xlsx', 'pdf'].map(f => (
                    <MenuItem key={f} value={f}>{FORMAT_LABELS[f]}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Typography sx={{ fontSize: '0.78rem', color: '#9e9e9e' }}>
                {filteredReports.length} kết quả
              </Typography>
            </Box>
          </Card>

          {/* Table */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9', overflow: 'hidden' }}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                <CircularProgress color="primary" />
              </Box>
            ) : filteredReports.length === 0 ? (
              <Box sx={{ py: 6, textAlign: 'center' }}>
                <ReportIcon sx={{ fontSize: 48, color: '#c8e6c9', mb: 1 }} />
                <Typography fontWeight="bold" color="text.secondary">Chưa có báo cáo nào</Typography>
                <Typography sx={{ fontSize: '0.82rem', color: '#bdbdbd', mt: 1 }}>
                  Truy cập Report Builder để tạo báo cáo mới
                </Typography>
              </Box>
            ) : (
              <TableContainer sx={{ maxHeight: 550 }}>
                <Table stickyHeader size="small">
                  <TableHead>
                    <TableRow>
                      {['ID', 'Tên báo cáo', 'Định dạng', 'Trạng thái', 'Khu vực', 'Chỉ số', 'Ngày tạo', 'Hành động']
                        .map(h => (
                          <TableCell key={h} sx={{ fontWeight: 800, bgcolor: '#f1f8e9', color: '#1b5e20', fontSize: '0.75rem', py: 1, whiteSpace: 'nowrap' }}>
                            {h}
                          </TableCell>
                        ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredReports.map((r) => {
                      const st = STATUS_MAP[r.status] || STATUS_MAP.pending
                      const zoneList = r.zone_ids && r.zone_ids.length
                        ? r.zone_ids.map(zid => '#' + zid).join(', ')
                        : 'Tất cả'
                      const metricStr = (r.metrics || []).map(m => metricLabels[m] || m).join(' ')

                      return (
                        <TableRow key={r.id} hover sx={{ cursor: 'pointer' }}
                          onClick={() => openDetail(r)}>
                          <TableCell sx={{ fontSize: '0.78rem', fontWeight: 700, color: '#9e9e9e' }}>#{r.id}</TableCell>
                          <TableCell sx={{ fontSize: '0.82rem', fontWeight: 600 }}>
                            <Tooltip title={r.name}>
                              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'inline-block', maxWidth: 200 }}>
                                {r.name}
                              </span>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Chip label={FORMAT_LABELS[r.format] || r.format} size="small"
                              sx={{ fontWeight: 700, fontSize: '0.68rem' }} />
                          </TableCell>
                          <TableCell>
                            <Chip label={st.label} size="small" color={st.color} icon={st.icon}
                              sx={{ fontWeight: 700, fontSize: '0.68rem' }} />
                          </TableCell>
                          <TableCell sx={{ fontSize: '0.75rem', color: '#757575', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {zoneList}
                          </TableCell>
                          <TableCell sx={{ fontSize: '0.75rem' }}>{metricStr || 'Tất cả'}</TableCell>
                          <TableCell sx={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                            {new Date(r.created_at).toLocaleDateString('vi-VN') + ' ' + new Date(r.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" gap={0.3}>
                              {r.status === 'completed' && r.file_path && (
                                <Tooltip title="Tải xuống">
                                  <IconButton size="small" color="success" onClick={(e) => { e.stopPropagation(); handleDownload(r.id, r.format); }}>
                                    <DownloadIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                              )}
                              {r.status === 'scheduled' && (
                                <Tooltip title="Hủy lịch">
                                  <IconButton size="small" color="warning" onClick={(e) => { e.stopPropagation(); handleCancelSchedule(r.id); }}>
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                              )}
                              <Tooltip title="Xóa">
                                <IconButton size="small" color="error" onClick={(e) => { e.stopPropagation(); handleDelete(r.id); }}>
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
            )}
          </Card>
        </Box>

        {/* Detail Dialog */}
        <Dialog open={detailOpen} onClose={() => setDetailOpen(false)} fullWidth maxWidth="sm">
          <DialogTitle fontWeight="bold" sx={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 1 }}>
            <ReportIcon sx={{ mr: 1, color: '#1b5e20' }} /> Chi tiết báo cáo #{detailReport?.id}
          </DialogTitle>
          <DialogContent dividers>
            {detailReport && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <DetailRow label="Tên" value={detailReport.name} />
                <DetailRow label="Định dạng" value={FORMAT_LABELS[detailReport.format] || detailReport.format} />
                <DetailRow label="Trạng thái" value={
                  <Chip label={(STATUS_MAP[detailReport.status] || STATUS_MAP.pending).label}
                    size="small" color={(STATUS_MAP[detailReport.status] || STATUS_MAP.pending).color} />
                } />
                <DetailRow label="Khu vực" value={detailReport.zone_ids && detailReport.zone_ids.length
                  ? detailReport.zone_ids.map(zid => '#' + zid).join(', ') : 'Tất cả'} />
                <DetailRow label="Chỉ số" value={(detailReport.metrics || []).map(m => metricLabels[m] || m).join(', ') || 'Tất cả'} />
                <DetailRow label="Từ ngày" value={new Date(detailReport.date_from).toLocaleString('vi-VN')} />
                <DetailRow label="Đến ngày" value={new Date(detailReport.date_to).toLocaleString('vi-VN')} />
                <DetailRow label="Kích thước" value={detailReport.file_size ? (detailReport.file_size / 1024).toFixed(1) + ' KB' : '—'} />
                <DetailRow label="Ngày tạo" value={new Date(detailReport.created_at).toLocaleString('vi-VN')} />
                <DetailRow label="Hoàn thành lúc" value={detailReport.completed_at ? new Date(detailReport.completed_at).toLocaleString('vi-VN') : '—'} />
              </Box>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 2 }}>
            {detailReport && detailReport.status === 'completed' && detailReport.file_path && (
              <Button variant="contained" startIcon={<DownloadIcon />}
                onClick={() => { handleDownload(detailReport.id, detailReport.format); setDetailOpen(false); }}
                sx={{ borderRadius: 2, fontWeight: 700 }}>
                Tải xuống
              </Button>
            )}
            <Button onClick={() => setDetailOpen(false)} color="inherit" size="small">Đóng</Button>
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
