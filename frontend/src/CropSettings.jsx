import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  ThemeProvider, createTheme, CssBaseline,
  Box, Typography, Button, Card,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Grid, Chip, IconButton, Switch, Stack,
  CircularProgress, Snackbar, Alert
} from '@mui/material'

import AppShell             from './AppShell'
import GrassIcon            from '@mui/icons-material/Grass'
import AddIcon              from '@mui/icons-material/Add'
import EditIcon             from '@mui/icons-material/Edit'
import DeleteIcon           from '@mui/icons-material/Delete'
import DeviceThermostatIcon from '@mui/icons-material/DeviceThermostat'
import WaterDropIcon        from '@mui/icons-material/WaterDrop'
import AutoModeIcon         from '@mui/icons-material/AutoMode'
import LocalFloristIcon     from '@mui/icons-material/LocalFlorist'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import WarningAmberIcon     from '@mui/icons-material/WarningAmber'

const API = 'http://localhost:8000'

const farmTheme = createTheme({
  palette: {
    primary: { main: '#2e7d32', light: '#4caf50', dark: '#1b5e20', contrastText: '#fff' },
    background: { default: '#f0f4f0', paper: '#ffffff' },
  },
  typography: { fontFamily: '"Be Vietnam Pro", "Plus Jakarta Sans", "Roboto", sans-serif' },
  shape: { borderRadius: 12 },
})

const EMPTY_FORM = {
  crop_name: '', temp_min: '', temp_max: '',
  humid_min: '', humid_max: '', auto_mode: true
}

export default function CropSettings() {
  const [crops,    setCrops]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [open,     setOpen]     = useState(false)
  const [editId,   setEditId]   = useState(null)
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [saving,   setSaving]   = useState(false)
  const [toast,    setToast]    = useState({ open: false, msg: '', severity: 'success' })

  const notify = (msg, severity = 'success') => setToast({ open: true, msg, severity })

  // ── Fetch ──────────────────────────────────────────────────────
  const fetchCrops = async () => {
    try {
      const res = await axios.get(`${API}/api/crop-settings/`)
      setCrops(res.data)
    } catch {
      notify('Không thể tải danh sách cây trồng', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchCrops() }, [])

  // ── Form helpers ───────────────────────────────────────────────
  const handleChange = (e) =>
    setFormData({ ...formData, [e.target.name]: e.target.value })

  const openAdd = () => { setEditId(null); setFormData(EMPTY_FORM); setOpen(true) }

  const openEdit = (crop) => {
    setEditId(crop.id)
    setFormData({
      crop_name: crop.crop_name,
      temp_min:  crop.temp_min,
      temp_max:  crop.temp_max,
      humid_min: crop.humid_min,
      humid_max: crop.humid_max,
      auto_mode: crop.auto_mode,
    })
    setOpen(true)
  }

  const handleClose = () => { setOpen(false); setFormData(EMPTY_FORM); setEditId(null) }

  // ── Save (Add / Edit) ──────────────────────────────────────────
  const handleSave = async () => {
    if (!formData.crop_name) return notify('Vui lòng nhập tên nông sản!', 'warning')
    setSaving(true)
    try {
      const payload = {
        ...formData,
        temp_min:  parseFloat(formData.temp_min),
        temp_max:  parseFloat(formData.temp_max),
        humid_min: parseFloat(formData.humid_min),
        humid_max: parseFloat(formData.humid_max),
      }
      if (editId) {
        await axios.put(`${API}/api/crop-settings/${editId}`, payload)
        notify('Đã cập nhật cấu hình!')
      } else {
        await axios.post(`${API}/api/crop-settings/`, payload)
        notify('Đã thêm cây trồng mới!')
      }
      handleClose()
      fetchCrops()
    } catch {
      notify('Có lỗi xảy ra khi lưu', 'error')
    } finally {
      setSaving(false)
    }
  }

  // ── Delete ─────────────────────────────────────────────────────
  const handleDelete = async (id) => {
    if (!window.confirm('Xoá cấu hình này?')) return
    try {
      await axios.delete(`${API}/api/crop-settings/${id}`)
      notify('Đã xoá cấu hình')
      fetchCrops()
    } catch {
      notify('Không thể xoá', 'error')
    }
  }

  // ── Toggle auto_mode ───────────────────────────────────────────
  const handleToggleAuto = async (crop) => {
    try {
      await axios.put(`${API}/api/crop-settings/${crop.id}`, {
        ...crop, auto_mode: !crop.auto_mode
      })
      setCrops(prev => prev.map(c => c.id === crop.id ? { ...c, auto_mode: !c.auto_mode } : c))
    } catch {
      notify('Không thể cập nhật chế độ tự động', 'error')
    }
  }

  const autoCount   = crops.filter(c => c.auto_mode).length
  const manualCount = crops.length - autoCount

  const stats = [
    { value: crops.length, label: 'Tổng giống',      desc: 'đang cấu hình',         color: '#2e7d32', bg: '#e8f5e9', Icon: LocalFloristIcon },
    { value: autoCount,    label: 'Bật tự động',      desc: 'chăm sóc tự động',      color: '#0277bd', bg: '#e3f2fd', Icon: CheckCircleOutlineIcon },
    { value: manualCount,  label: 'Chế độ thủ công',  desc: 'cần giám sát thêm',     color: '#e65100', bg: '#fff3e0', Icon: WarningAmberIcon },
  ]

  return (
    <ThemeProvider theme={farmTheme}>
      <CssBaseline />
      <AppShell>
        <Box className="dashboard-content">

          {/* ── Page Header ── */}
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
                Tủ cấu hình giống
              </Typography>
              <Typography sx={{ color: '#fff', fontSize: '1.5rem', fontWeight: 900, lineHeight: 1.2 }}>
                Cấu hình cây trồng
              </Typography>
              <Typography sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.82rem', mt: 0.5 }}>
                Thiết lập ngưỡng sinh thái & chế độ tự động cho từng giống
              </Typography>
            </Box>
            <Stack direction="row" spacing={1.5}>
              <Button variant="contained"
                sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#fff', fontWeight: 700,
                  borderRadius: 2, '&:hover': { bgcolor: 'rgba(255,255,255,0.25)' },
                  textTransform: 'none', fontSize: '0.82rem' }}
                startIcon={<AutoModeIcon />}>
                Kích hoạt Auto Mode
              </Button>
              <Button variant="contained"
                onClick={openAdd}
                sx={{ bgcolor: '#fff', color: '#1b5e20', fontWeight: 700,
                  borderRadius: 2, '&:hover': { bgcolor: '#f1f8e9' },
                  textTransform: 'none', fontSize: '0.82rem' }}
                startIcon={<AddIcon />}>
                Thêm giống cây
              </Button>
            </Stack>
          </Box>

          {/* ── Stats row ── */}
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 3, mb: 3 }}>
            {stats.map((s) => (
              <Card key={s.label} className="stat-card" elevation={0}>
                <Box className="stat-card-inner">
                  <Box className="stat-icon-box" sx={{ bgcolor: s.bg }}>
                    <s.Icon sx={{ color: s.color, fontSize: 24 }} />
                  </Box>
                  <Box className="stat-text">
                    <Typography className="stat-value" color={s.color}>{s.value}</Typography>
                    <Typography className="stat-label">{s.label}</Typography>
                    <Typography className="stat-desc">{s.desc}</Typography>
                  </Box>
                </Box>
              </Card>
            ))}
          </Box>

          {/* ── Table card ── */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9', overflow: 'hidden' }}>
            <Box sx={{ px: 3, py: 2.5, display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', borderBottom: '1px solid #f0f4f0' }}>
              <Box>
                <Typography variant="h6" fontWeight="800" color="primary.dark" sx={{ fontSize: '1rem' }}>
                  Danh sách cấu hình
                </Typography>
                <Typography sx={{ fontSize: '0.78rem', color: '#9e9e9e' }}>
                  {crops.length} giống · {autoCount} tự động · {manualCount} thủ công
                </Typography>
              </Box>
              <Button variant="outlined" color="primary" startIcon={<AddIcon />}
                onClick={openAdd}
                sx={{ borderRadius: 2, fontWeight: 700, textTransform: 'none', fontSize: '0.82rem' }}>
                Thêm cấu hình
              </Button>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                <CircularProgress color="primary" size={36} />
              </Box>
            ) : crops.length === 0 ? (
              <Box sx={{ p: 6, textAlign: 'center' }}>
                <GrassIcon sx={{ fontSize: 48, color: '#c8e6c9', mb: 1 }} />
                <Typography fontWeight="bold" color="text.secondary">Chưa có cấu hình</Typography>
                <Typography sx={{ fontSize: '0.82rem', color: '#bdbdbd', mb: 2 }}>
                  Nhấn "Thêm giống cây" để bắt đầu.
                </Typography>
                <Button variant="contained" startIcon={<AddIcon />} onClick={openAdd}
                  sx={{ borderRadius: 2, fontWeight: 700 }}>
                  Thêm giống cây
                </Button>
              </Box>
            ) : (
              <TableContainer sx={{ maxHeight: 520 }}>
                <Table stickyHeader sx={{ minWidth: 900 }}>
                  <TableHead>
                    <TableRow>
                      {['ID', 'Tên nông sản', 'Ngưỡng Nhiệt độ (°C)', 'Ngưỡng Độ ẩm (%)', 'Tự động', 'Thao tác'].map(h => (
                        <TableCell key={h}
                          sx={{ fontWeight: 800, bgcolor: '#f1f8e9', color: '#1b5e20',
                            fontSize: '0.78rem', py: 1.5, whiteSpace: 'nowrap' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {crops.map((crop) => (
                      <TableRow key={crop.id}
                        sx={{ '&:hover': { bgcolor: '#f9fbe7' }, transition: 'background 0.15s' }}>
                        <TableCell sx={{ color: '#9e9e9e', fontWeight: 700, fontSize: '0.8rem' }}>
                          #{crop.id}
                        </TableCell>
                        <TableCell>
                          <Stack spacing={0.2}>
                            <Typography fontWeight="800" color="primary.dark" sx={{ fontSize: '0.88rem' }}>
                              {crop.crop_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Profile #{crop.id}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            icon={<DeviceThermostatIcon fontSize="small" />}
                            label={`${crop.temp_min} – ${crop.temp_max}°C`}
                            sx={{ bgcolor: '#fff3e0', color: '#e65100', fontWeight: 700,
                              border: '1px solid #ffcc80', fontSize: '0.78rem' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip
                            icon={<WaterDropIcon fontSize="small" />}
                            label={`${crop.humid_min} – ${crop.humid_max}%`}
                            sx={{ bgcolor: '#e3f2fd', color: '#1565c0', fontWeight: 700,
                              border: '1px solid #90caf9', fontSize: '0.78rem' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Switch
                            checked={crop.auto_mode}
                            onChange={() => handleToggleAuto(crop)}
                            color="success" size="small"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton size="small" color="primary" onClick={() => openEdit(crop)}>
                            <EditIcon fontSize="small" />
                          </IconButton>
                          <IconButton size="small" color="error" onClick={() => handleDelete(crop.id)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Card>

        </Box>
      </AppShell>

      {/* ── Dialog thêm / sửa ── */}
      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle fontWeight="bold" sx={{ fontSize: '1rem' }}>
          {editId ? 'Chỉnh sửa cấu hình' : 'Thêm cấu hình giống mới'}
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2} sx={{ mt: 0.2 }}>
            <Grid item xs={12}>
              <TextField fullWidth size="small" label="Tên nông sản *"
                name="crop_name" value={formData.crop_name} onChange={handleChange} />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth size="small" label="Nhiệt độ min (°C)"
                name="temp_min" value={formData.temp_min} onChange={handleChange} type="number" />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth size="small" label="Nhiệt độ max (°C)"
                name="temp_max" value={formData.temp_max} onChange={handleChange} type="number" />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth size="small" label="Độ ẩm min (%)"
                name="humid_min" value={formData.humid_min} onChange={handleChange} type="number" />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth size="small" label="Độ ẩm max (%)"
                name="humid_max" value={formData.humid_max} onChange={handleChange} type="number" />
            </Grid>
            <Grid item xs={12}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <Switch checked={formData.auto_mode} color="success"
                  onChange={(e) => setFormData({ ...formData, auto_mode: e.target.checked })} />
                <Typography sx={{ fontSize: '0.88rem', fontWeight: 600 }}>
                  Bật chế độ tự động tưới / điều khiển
                </Typography>
              </Stack>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleClose} color="inherit" size="small">Hủy</Button>
          <Button onClick={handleSave} variant="contained" size="small"
            disabled={saving} sx={{ borderRadius: 2, fontWeight: 700 }}>
            {saving ? <CircularProgress size={18} color="inherit" /> : 'Lưu cấu hình'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Toast ── */}
      <Snackbar open={toast.open} autoHideDuration={3000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert severity={toast.severity} variant="filled" sx={{ fontWeight: 700 }}>
          {toast.msg}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  )
}
