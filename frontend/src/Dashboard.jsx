import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import './dashboard.css'
import {
  ThemeProvider, createTheme, CssBaseline,
  AppBar, Toolbar, Typography, Grid, Card, CardContent, CardActions,
  Box, Button, Dialog, DialogTitle, CircularProgress,
  DialogContent, DialogActions, TextField, Drawer, List,
  ListItem, ListItemButton, ListItemIcon, ListItemText, Divider
} from '@mui/material'
import { Stack, Chip } from '@mui/material'

import AgricultureIcon from '@mui/icons-material/Agriculture'
import AddIcon from '@mui/icons-material/Add'
import DashboardIcon from '@mui/icons-material/Dashboard'
import SensorsIcon from '@mui/icons-material/Sensors'
import SettingsIcon from '@mui/icons-material/Settings'
import LogoutIcon from '@mui/icons-material/Logout'
import GrassIcon from '@mui/icons-material/Grass'
import DeviceThermostatIcon from '@mui/icons-material/DeviceThermostat'
import WaterDropIcon from '@mui/icons-material/WaterDrop'
import WbSunnyIcon from '@mui/icons-material/WbSunny'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import LayersIcon from '@mui/icons-material/Layers'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import LocalFloristIcon from '@mui/icons-material/LocalFlorist'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'

const drawerWidth = 240

const farmTheme = createTheme({
  palette: {
    primary: { main: '#2e7d32', light: '#4caf50', dark: '#1b5e20', contrastText: '#ffffff' },
    background: { default: '#f0f4f0', paper: '#ffffff' },
  },
  typography: { fontFamily: '"Be Vietnam Pro", "Plus Jakarta Sans", "Roboto", sans-serif' },
  shape: { borderRadius: 12 },
})

const parseJwt = (token) => {
  try { return JSON.parse(atob(token.split('.')[1])) } catch { return null }
}

// Log data với severity
const LOG_DATA = (temp, humid) => [
  { msg: 'Nhiệt độ Vườn 1 vượt ngưỡng 35°C', time: 'Vừa xong', severity: 'error' },
  { msg: 'Máy bơm Vườn 2 đã bật tự động', time: '5 phút trước', severity: 'success' },
  { msg: `Cảm biến: ${temp}°C / ${humid}%`, time: 'Realtime', severity: 'info' },
  { msg: 'Độ ẩm đất Vườn 3 thấp dưới ngưỡng', time: '8 phút trước', severity: 'warn' },
  { msg: 'Admin đăng nhập hệ thống', time: '10 phút trước', severity: 'info' },
  { msg: 'Đèn LED Khu B tắt theo lịch', time: '15 phút trước', severity: 'success' },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [zones, setZones]             = useState([])
  const [loading, setLoading]         = useState(true)
  const [open, setOpen]               = useState(false)
  const [formData, setFormData]       = useState({ name: '', description: '' })
  const [sensorData, setSensorData]   = useState({ temperature: '--', humidity: '--', light: '--' })
  const [perZoneData, setPerZoneData] = useState({})   // zone_id → latest reading
  const [currentUser, setCurrentUser] = useState({ name: 'Đang tải...', role: '' })
  const [wsStatus, setWsStatus]       = useState('connecting')

  const plantedCount   = zones.filter(z => z.crop_setting_id).length
  const describedCount = zones.filter(z => z.description).length
  const emptyCount     = Math.max(zones.length - plantedCount, 0)

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { navigate('/login'); return }
    const payload = parseJwt(token)
    if (!payload) { handleLogout(); return }
    setCurrentUser({ name: payload.name || payload.sub || 'Người dùng', role: payload.role || 'USER' })
  }, [])

  const fetchZones = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/zones/')
      setZones(res.data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchZones() }, [])

  useEffect(() => {
    let ws, retryTimer
    const connect = () => {
      ws = new WebSocket('ws://localhost:8000/ws/telemetry')
      ws.onopen    = () => setWsStatus('connected')
      ws.onerror   = () => setWsStatus('error')
      ws.onclose   = () => { setWsStatus('connecting'); retryTimer = setTimeout(connect, 4000) }
      ws.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data)
          if (!d.zone_id) return
          // Lưu reading mới nhất per-zone
          setPerZoneData(prev => ({ ...prev, [d.zone_id]: d }))
          // Tính trung bình tất cả zones → setSensorData
          setPerZoneData(prev => {
            const updated = { ...prev, [d.zone_id]: d }
            const vals = Object.values(updated)
            const avg = (key) => {
              const arr = vals.map(v => v[key]).filter(v => v !== undefined && v !== '--' && !isNaN(Number(v)))
              return arr.length ? Math.round((arr.reduce((a, b) => a + Number(b), 0) / arr.length) * 10) / 10 : '--'
            }
            setSensorData({ temperature: avg('temperature'), humidity: avg('humidity'), light: avg('light'), _zones: updated })
            return updated
          })
        } catch { /* ignore */ }
      }
    }
    connect()
    return () => { ws?.close(); clearTimeout(retryTimer) }
  }, [])

  const handleClickOpen   = () => setOpen(true)
  const handleClose       = () => { setOpen(false); setFormData({ name: '', description: '' }) }
  const handleInputChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value })
  const handleSubmit      = async () => {
    if (!formData.name) return alert('Vui lòng nhập tên khu vực!')
    try {
      await axios.post('http://localhost:8000/api/zones/', { ...formData, crop_setting_id: null })
      handleClose(); setLoading(true); fetchZones()
    } catch { alert('Có lỗi xảy ra!') }
  }

  const wsBadge = {
    connected:  { label: 'Live', color: 'success' },
    connecting: { label: 'Đang kết nối…', color: 'warning' },
    error:      { label: 'Lỗi kết nối', color: 'error' },
  }[wsStatus]

  const stats = [
    { value: zones.length,   label: 'Tổng khu vực',     desc: 'đã thiết lập',         color: '#2e7d32', bg: '#e8f5e9', Icon: LayersIcon },
    { value: describedCount, label: 'Có mô tả',          desc: 'chuẩn hóa dữ liệu',   color: '#0277bd', bg: '#e3f2fd', Icon: CheckCircleOutlineIcon },
    { value: plantedCount,   label: 'Đang canh tác',     desc: 'khu vực có cây',       color: '#2e7d32', bg: '#f1f8e9', Icon: LocalFloristIcon },
    { value: emptyCount,     label: 'Bỏ trống',          desc: 'chưa gán cây trồng',   color: '#e65100', bg: '#fff3e0', Icon: WarningAmberIcon },
  ]

  return (
    <ThemeProvider theme={farmTheme}>
      <Box className="dashboard-root">
        <CssBaseline />

        {/* ── AppBar ── */}
        <AppBar position="fixed" elevation={0}
          sx={{ zIndex: (t) => t.zIndex.drawer + 1, bgcolor: '#1b5e20', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <Toolbar sx={{ minHeight: 60 }}>
            <AgricultureIcon sx={{ mr: 1.5, fontSize: 26 }} />
            <Typography variant="h6" noWrap sx={{ flexGrow: 1, fontWeight: 800, letterSpacing: 0.5, fontSize: '1rem' }}>
              SmartFarm Admin
            </Typography>
            <Chip size="small" label={wsBadge.label} color={wsBadge.color}
              sx={{ mr: 2, fontWeight: 'bold', fontSize: '0.7rem', height: 24 }} />
            <Button color="inherit" onClick={handleLogout} startIcon={<LogoutIcon />}
              sx={{ fontWeight: 'bold', fontSize: '0.82rem' }}>
              Đăng xuất
            </Button>
          </Toolbar>
        </AppBar>

        {/* ── Sidebar ── */}
        <Drawer variant="permanent"
          sx={{ width: drawerWidth, flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box', border: 'none' } }}
          PaperProps={{ className: 'sidebar-paper' }}
        >
          <Toolbar sx={{ minHeight: 60 }} />

          {/* Logo area */}
          <Box className="sidebar-logo-area">
            <Typography sx={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.65rem', fontWeight: 800, letterSpacing: 1.5, textTransform: 'uppercase', mb: 0.5 }}>
              SmartFarm v1.0
            </Typography>
            <Typography sx={{ color: '#fff', fontSize: '0.82rem', fontWeight: 700 }}>
              Hệ thống nông trại thông minh
            </Typography>
          </Box>

          <Box sx={{ overflow: 'auto', mt: 2 }}>
            <Typography className="sidebar-nav-label">Điều hướng</Typography>
            <List dense disablePadding>
              <ListItem disablePadding>
                <ListItemButton className="sidebar-item sidebar-item-active">
                  <ListItemIcon><DashboardIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Tổng quan" primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 700 }} />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton className="sidebar-item" onClick={() => navigate('/device-management')}>
                  <ListItemIcon><SensorsIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Quản lý Thiết bị" primaryTypographyProps={{ fontSize: '0.85rem' }} />
                </ListItemButton>
              </ListItem>
              <ListItem disablePadding>
                <ListItemButton className="sidebar-item" onClick={() => navigate('/crop-settings')}>
                  <ListItemIcon><GrassIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Cấu hình Cây trồng" primaryTypographyProps={{ fontSize: '0.85rem' }} />
                </ListItemButton>
              </ListItem>
            </List>

            <Typography className="sidebar-nav-label" sx={{ mt: 1 }}>Hệ thống</Typography>
            <List dense disablePadding>
              <ListItem disablePadding>
                <ListItemButton className="sidebar-item">
                  <ListItemIcon><SettingsIcon fontSize="small" /></ListItemIcon>
                  <ListItemText primary="Cài đặt" primaryTypographyProps={{ fontSize: '0.85rem' }} />
                </ListItemButton>
              </ListItem>
            </List>
          </Box>
        </Drawer>

        {/* ── Main ── */}
        <Box component="main" className="dashboard-main">
          <Box className="dashboard-content">

            {/* ── TOP ROW: Hero + Stats 2×2 ── */}
            <Box className="top-row">

              {/* Hero */}
              <Card className="hero-card" elevation={0}>
                <Box className="hero-card-inner">
                  <Box>
                    <Typography sx={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.7rem', fontWeight: 700, letterSpacing: 1.2, textTransform: 'uppercase', mb: 0.5 }}>
                      Bảng điều khiển
                    </Typography>
                    <Typography className="hero-greeting">
                      Xin chào,<br />{currentUser.name}! 👋
                    </Typography>
                    <Box className="hero-role-badge">
                      <AgricultureIcon sx={{ fontSize: 13 }} />
                      {currentUser.role === 'ADMIN' ? 'Quản trị viên' : 'Nông dân phụ trách'}
                    </Box>
                  </Box>
                  <Box className="hero-status-row">
                    <SensorsIcon sx={{ fontSize: 16, color: '#81c784' }} />
                    <Typography sx={{ fontSize: '0.8rem', fontWeight: 600, color: '#fff' }}>
                      IoT Gateway: hoạt động tốt
                    </Typography>
                    <Chip label={wsBadge.label} color={wsBadge.color} size="small"
                      sx={{ height: 20, fontSize: '0.65rem', fontWeight: 'bold', ml: 'auto' }} />
                  </Box>
                </Box>
                {/* Deco */}
                <Box className="hero-deco-circle" sx={{ width: 130, height: 130, top: -30, right: -30 }} />
                <Box className="hero-deco-circle" sx={{ width: 80, height: 80, bottom: 20, right: 60, opacity: 0.04 }} />
              </Card>

              {/* Stats 2×2 */}
              <Box className="stats-grid">
                {stats.map((s) => (
                  <Card key={s.label} className="stat-card" elevation={0}>
                    <Box className="stat-card-inner">
                      <Box className="stat-icon-box" sx={{ bgcolor: s.bg }}>
                        <s.Icon sx={{ color: s.color, fontSize: 22 }} />
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
            </Box>

            {/* ── MID ROW: ENV 6 + LOG 6 ── */}
            <Box className="mid-row">

              {/* ENV card */}
              <Card className="env-card" elevation={0}>
                <Box className="env-card-title-row">
                  <Typography variant="h6" fontWeight="800" color="primary.dark"
                    sx={{ display: 'flex', alignItems: 'center', gap: 1, fontSize: '0.95rem' }}>
                    <SensorsIcon sx={{ color: '#f44336', fontSize: 20 }} />
                    Môi trường — Live
                  </Typography>
                  <Button size="small" variant="outlined" color="primary"
                    onClick={() => navigate('/device-management')}
                    sx={{ textTransform: 'none', fontWeight: 700, borderRadius: 2, fontSize: '0.75rem', py: 0.4, px: 1.5 }}>
                    Quản lý thiết bị
                  </Button>
                </Box>
                <Typography className="env-card-sub">
                  {Object.keys(perZoneData).length > 0
                    ? `Trung bình ${Object.keys(perZoneData).length} khu vực · Realtime`
                    : 'Chờ dữ liệu cảm biến…'}
                </Typography>

                <Box className="sensor-metrics-row">
                  {/* Nhiệt độ */}
                  <Box className="sensor-metric sensor-metric-temp">
                    <DeviceThermostatIcon className="sensor-metric-icon sensor-metric-icon-temp" />
                    <Typography className="sensor-metric-value sensor-metric-value-temp">
                      {sensorData.temperature !== '--' ? `${sensorData.temperature}°` : '--'}
                    </Typography>
                    <Typography className="sensor-metric-label">Nhiệt độ</Typography>
                  </Box>
                  {/* Độ ẩm */}
                  <Box className="sensor-metric sensor-metric-humid">
                    <WaterDropIcon className="sensor-metric-icon sensor-metric-icon-humid" />
                    <Typography className="sensor-metric-value sensor-metric-value-humid">
                      {sensorData.humidity !== '--' ? `${sensorData.humidity}%` : '--'}
                    </Typography>
                    <Typography className="sensor-metric-label">Độ ẩm</Typography>
                  </Box>
                  {/* Ánh sáng */}
                  <Box className="sensor-metric sensor-metric-light">
                    <WbSunnyIcon className="sensor-metric-icon sensor-metric-icon-light" />
                    <Typography className="sensor-metric-value sensor-metric-value-light">
                      {sensorData.light !== '--' ? sensorData.light : '--'}
                    </Typography>
                    <Typography className="sensor-metric-label">Lux</Typography>
                  </Box>
                </Box>

                {/* Per-zone chips row */}
                {Object.keys(perZoneData).length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.7, px: 0.5, mt: 0.5, mb: 0.5 }}>
                    {Object.values(perZoneData).map((z) => (
                      <Chip
                        key={z.zone_id}
                        label={`${z.zone_name ?? `Zone #${z.zone_id}`}: ${z.temperature !== undefined ? `${z.temperature}° ` : ''}${z.humidity !== undefined ? `${z.humidity}%` : ''}`}
                        size="small"
                        color="primary"
                        variant="outlined"
                        onClick={() => navigate(`/zones/${z.zone_id}`)}
                        sx={{ height: 22, fontSize: '0.65rem', cursor: 'pointer', fontWeight: 600 }}
                      />
                    ))}
                  </Box>
                )}

                {/* Trend row */}
                <Box className="sensor-trend-row">
                  <Box className="trend-item">
                    <TrendingUpIcon sx={{ fontSize: 15 }} />
                    <Typography sx={{ fontSize: '0.72rem', fontWeight: 700 }}>Nhiệt độ tăng nhẹ</Typography>
                  </Box>
                  <Box className="trend-item trend-item-warn">
                    <TrendingDownIcon sx={{ fontSize: 15 }} />
                    <Typography sx={{ fontSize: '0.72rem', fontWeight: 700 }}>Độ ẩm giảm</Typography>
                  </Box>
                  <Box sx={{ ml: 'auto', display: 'flex', gap: 0.8 }}>
                    <Chip label={`${Object.keys(perZoneData).length || 0} zone hoạt động`} size="small" color="primary" sx={{ height: 20, fontSize: '0.65rem' }} />
                    <Chip label={`Trồng: ${plantedCount}`} size="small" variant="outlined" sx={{ height: 20, fontSize: '0.65rem' }} />
                  </Box>
                </Box>
              </Card>

              {/* LOG card */}
              <Card className="log-card" elevation={0}>
                <Box className="log-card-header">
                  <Typography variant="h6" fontWeight="800" color="primary.dark"
                    sx={{ display: 'flex', alignItems: 'center', gap: 1, fontSize: '0.95rem' }}>
                    <NotificationsActiveIcon sx={{ fontSize: 20, color: '#2e7d32' }} />
                    Nhật ký hệ thống
                  </Typography>
                  <Typography sx={{ fontSize: '0.73rem', color: '#bdbdbd', mt: 0.3 }}>
                    Hoạt động gần nhất
                  </Typography>
                </Box>
                <Box className="log-scroll-area">
                  {LOG_DATA(sensorData.temperature, sensorData.humidity).map((log, i) => (
                    <Box key={i} className="log-item">
                      <Box className={`log-dot log-dot-${log.severity}`} />
                      <Box>
                        <Typography className="log-item-msg">{log.msg}</Typography>
                        <Typography className="log-item-time">{log.time}</Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Card>
            </Box>

            {/* ── ZONES ── */}
            <Box className="zone-header-row">
              <Box>
                <Typography variant="h6" color="primary.dark" fontWeight="800" sx={{ fontSize: '1rem' }}>
                  Quản lý khu vực canh tác
                </Typography>
                <Typography sx={{ fontSize: '0.78rem', color: '#9e9e9e' }}>
                  {zones.length} khu vực · {plantedCount} đang trồng · {emptyCount} bỏ trống
                </Typography>
              </Box>
              {currentUser.role === 'ADMIN' && (
                <Button variant="contained" startIcon={<AddIcon />} onClick={handleClickOpen}
                  sx={{ borderRadius: 2, px: 2.5, py: 0.8, fontWeight: 'bold', fontSize: '0.82rem' }}>
                  Thêm khu vực
                </Button>
              )}
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                <CircularProgress color="primary" size={36} />
              </Box>
            ) : zones.length === 0 ? (
              <Card sx={{ p: 4, textAlign: 'center', borderRadius: 3, boxShadow: 'none', border: '2px dashed #c8e6c9' }}>
                <GrassIcon sx={{ fontSize: 40, color: '#c8e6c9', mb: 1 }} />
                <Typography color="text.secondary" fontWeight="bold">Chưa có khu vực nào</Typography>
                <Typography color="text.secondary" sx={{ fontSize: '0.82rem' }}>
                  Nhấn "Thêm khu vực" để bắt đầu!
                </Typography>
              </Card>
            ) : (
              <Grid container spacing={2}>
                {zones.map((zone) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={zone.id} sx={{ display: 'flex' }}>
                    <Card className="zone-card" elevation={0}>
                      <CardContent className="zone-card-body">
                        <Stack direction="row" spacing={0.8} sx={{ mb: 1 }}>
                          <Chip label={`#${zone.id}`} color="primary" size="small"
                            sx={{ fontWeight: 800, height: 20, fontSize: '0.68rem' }} />
                          <Chip
                            label={zone.crop_setting_id ? 'Đang trồng' : 'Bỏ trống'}
                            color={zone.crop_setting_id ? 'success' : 'default'}
                            size="small"
                            variant={zone.crop_setting_id ? 'filled' : 'outlined'}
                            sx={{ fontWeight: 700, height: 20, fontSize: '0.68rem' }}
                          />
                        </Stack>
                        <Typography className="zone-card-name">{zone.name}</Typography>
                        <Typography className="zone-card-desc">
                          {zone.description || 'Chưa có mô tả.'}
                        </Typography>
                        <Box className="zone-card-meta">
                          <Typography variant="caption" fontWeight="bold" color="text.secondary">
                            Crop: {zone.crop_setting_id ? `#${zone.crop_setting_id}` : '—'}
                          </Typography>
                          <Typography variant="caption" fontWeight="bold" color="text.secondary">
                            ID: #{zone.id}
                          </Typography>
                        </Box>
                      </CardContent>
                      <CardActions className="zone-card-footer">
                        <Button fullWidth variant="outlined" size="small" endIcon={<ArrowForwardIcon />}
                          sx={{ borderRadius: 2, fontWeight: 700, fontSize: '0.78rem', py: 0.7 }}
                          onClick={() => navigate(`/zones/${zone.id}`)}>
                          Quản lý khu vực
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}

          </Box>
        </Box>
      </Box>

      {/* ── Dialog ── */}
      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle fontWeight="bold" sx={{ fontSize: '1rem' }}>Thêm khu vực canh tác mới</DialogTitle>
        <DialogContent dividers>
          <TextField fullWidth label="Tên khu vực *" name="name" size="small"
            value={formData.name} onChange={handleInputChange} sx={{ mb: 2 }} />
          <TextField fullWidth label="Mô tả" name="description" multiline rows={3} size="small"
            value={formData.description} onChange={handleInputChange} />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleClose} color="inherit" size="small">Hủy</Button>
          <Button onClick={handleSubmit} variant="contained" size="small" sx={{ borderRadius: 2 }}>Lưu</Button>
        </DialogActions>
      </Dialog>

    </ThemeProvider>
  )
}