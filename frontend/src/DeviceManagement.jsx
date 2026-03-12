import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  ThemeProvider, createTheme, CssBaseline,
  Box, Typography, Button, Card,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Switch, Stack, CircularProgress, Snackbar, Alert
} from '@mui/material'

import AppShell         from './AppShell'
import RouterIcon       from '@mui/icons-material/Router'
import SensorsIcon      from '@mui/icons-material/Sensors'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import WifiIcon         from '@mui/icons-material/Wifi'
import WifiOffIcon      from '@mui/icons-material/WifiOff'
import WaterDropIcon    from '@mui/icons-material/WaterDrop'
import AirIcon          from '@mui/icons-material/Air'
import WbSunnyIcon      from '@mui/icons-material/WbSunny'
import LightbulbIcon    from '@mui/icons-material/Lightbulb'
import DesktopWindowsIcon from '@mui/icons-material/DesktopWindows'
import GrassIcon        from '@mui/icons-material/Grass'

const API = 'http://localhost:8000'

const farmTheme = createTheme({
  palette: {
    primary: { main: '#2e7d32', light: '#4caf50', dark: '#1b5e20', contrastText: '#fff' },
    background: { default: '#f0f4f0', paper: '#ffffff' },
  },
  typography: { fontFamily: '"Be Vietnam Pro", "Plus Jakarta Sans", "Roboto", sans-serif' },
  shape: { borderRadius: 12 },
})

// Map device name → icon
function DeviceIcon({ name, type }) {
  const n = (name || '').toLowerCase()
  const iconProps = { fontSize: 'small' }
  if (n.includes('pump') || n.includes('bơm')) return <WaterDropIcon {...iconProps} />
  if (n.includes('fan') || n.includes('quạt')) return <AirIcon {...iconProps} />
  if (n.includes('light') || n.includes('led')) return <LightbulbIcon {...iconProps} />
  if (n.includes('lcd') || n.includes('screen')) return <DesktopWindowsIcon {...iconProps} />
  if (n.includes('soil') || n.includes('đất')) return <GrassIcon {...iconProps} />
  if (n.includes('ánh') || n.includes('solar')) return <WbSunnyIcon {...iconProps} />
  if (type === 'SENSOR') return <SensorsIcon {...iconProps} />
  return <RouterIcon {...iconProps} />
}

export default function DeviceManagement() {
  const [devices,  setDevices]  = useState([])
  const [loading,  setLoading]  = useState(true)
  const [toast,    setToast]    = useState({ open: false, msg: '', severity: 'success' })

  const notify = (msg, severity = 'success') => setToast({ open: true, msg, severity })

  // ── Fetch devices ──────────────────────────────────────────────
  const fetchDevices = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API}/api/devices/`)
      setDevices(res.data)
    } catch {
      // fallback static data if API not ready
      setDevices([
        { id: 1, device_name: 'DHT20',        device_type: 'SENSOR',   pin: 'I2C (SDA, SCL)',    status: 'ONLINE',  is_active: true  },
        { id: 2, device_name: 'Soil Moisture', device_type: 'SENSOR',   pin: 'GPIO 2 (Analog)',   status: 'ONLINE',  is_active: true  },
        { id: 3, device_name: 'Light Sensor',  device_type: 'SENSOR',   pin: 'GPIO 3 (Analog)',   status: 'ONLINE',  is_active: true  },
        { id: 4, device_name: 'LCD 16x2',      device_type: 'ACTUATOR', pin: 'I2C (0x27)',        status: 'ONLINE',  is_active: true  },
        { id: 5, device_name: 'Pump 1',        device_type: 'ACTUATOR', pin: 'GPIO 8 (Digital)',  status: 'ONLINE',  is_active: false },
        { id: 6, device_name: 'Pump 2',        device_type: 'ACTUATOR', pin: 'GPIO 9 (Digital)',  status: 'ONLINE',  is_active: false },
        { id: 7, device_name: 'Fan',           device_type: 'ACTUATOR', pin: 'GPIO 1 (PWM)',      status: 'ONLINE',  is_active: true  },
        { id: 8, device_name: 'NeoPixel LED',  device_type: 'ACTUATOR', pin: 'GPIO 6 (WS2812B)', status: 'OFFLINE', is_active: false },
      ])
      notify('Không kết nối được API — đang dùng dữ liệu tĩnh', 'warning')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDevices() }, [])

  // ── Toggle actuator ────────────────────────────────────────────
  const handleToggle = async (device) => {
    if (device.device_type !== 'ACTUATOR' || device.status !== 'ONLINE') return
    const newState = !device.is_active
    setDevices(prev => prev.map(d => d.id === device.id ? { ...d, is_active: newState } : d))
    try {
      await axios.patch(`${API}/api/devices/${device.id}/toggle`, { is_active: newState })
      notify(`${device.device_name} đã được ${newState ? 'bật' : 'tắt'}`)
    } catch {
      setDevices(prev => prev.map(d => d.id === device.id ? { ...d, is_active: !newState } : d))
      notify('Không thể thay đổi trạng thái thiết bị', 'error')
    }
  }

  // ── Stats ──────────────────────────────────────────────────────
  const sensorCount   = devices.filter(d => d.device_type === 'SENSOR').length
  const actuatorCount = devices.filter(d => d.device_type === 'ACTUATOR').length
  const onlineCount   = devices.filter(d => d.status === 'ONLINE').length
  const activeCount   = devices.filter(d => d.is_active).length

  const stats = [
    { value: devices.length, label: 'Tổng thiết bị',       desc: 'đã đăng ký',               color: '#2e7d32', bg: '#e8f5e9', Icon: RouterIcon },
    { value: sensorCount,    label: 'Cảm biến',             desc: 'đọc dữ liệu môi trường',   color: '#e65100', bg: '#fff3e0', Icon: SensorsIcon },
    { value: actuatorCount,  label: 'Thiết bị chấp hành',   desc: 'điều khiển tự động',        color: '#0277bd', bg: '#e3f2fd', Icon: PowerSettingsNewIcon },
    { value: onlineCount,    label: 'Đang kết nối',         desc: `${devices.length - onlineCount} mất tín hiệu`, color: '#00695c', bg: '#e0f2f1', Icon: WifiIcon },
  ]

  return (
    <ThemeProvider theme={farmTheme}>
      <CssBaseline />
      <AppShell>
        <Box className="dashboard-content">

          {/* ── Page Header ── */}
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
                Hạ tầng IoT
              </Typography>
              <Typography sx={{ color: '#fff', fontSize: '1.5rem', fontWeight: 900, lineHeight: 1.2 }}>
                Quản lý Thiết bị
              </Typography>
              <Typography sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.82rem', mt: 0.5 }}>
                Sơ đồ kết nối Gateway ESP32/Microbit · {onlineCount}/{devices.length} online · {activeCount} đang hoạt động
              </Typography>
            </Box>
            <Button variant="contained"
              onClick={fetchDevices}
              sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#fff', fontWeight: 700,
                borderRadius: 2, '&:hover': { bgcolor: 'rgba(255,255,255,0.25)' },
                textTransform: 'none', fontSize: '0.82rem' }}
              startIcon={<WifiIcon />}>
              Làm mới
            </Button>
          </Box>

          {/* ── Stats row ── */}
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 3, mb: 3 }}>
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

          {/* ── Device Table ── */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e3f2fd', overflow: 'hidden' }}>
            <Box sx={{ px: 3, py: 2.5, display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', borderBottom: '1px solid #f0f4f0' }}>
              <Box>
                <Typography variant="h6" fontWeight="800" color="#1565c0" sx={{ fontSize: '1rem' }}>
                  Danh sách thiết bị
                </Typography>
                <Typography sx={{ fontSize: '0.78rem', color: '#9e9e9e' }}>
                  {sensorCount} cảm biến · {actuatorCount} thiết bị chấp hành
                </Typography>
              </Box>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
                <CircularProgress color="primary" size={36} />
              </Box>
            ) : (
              <TableContainer sx={{ maxHeight: 520 }}>
                <Table stickyHeader sx={{ minWidth: 900 }}>
                  <TableHead>
                    <TableRow>
                      {['Thiết bị', 'Cổng giao tiếp', 'Phân loại', 'Khu vực', 'Kết nối', 'Điều khiển'].map(h => (
                        <TableCell key={h}
                          sx={{ fontWeight: 800, bgcolor: '#e3f2fd', color: '#1565c0',
                            fontSize: '0.78rem', py: 1.5, whiteSpace: 'nowrap' }}>
                          {h}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {devices.map((device) => (
                      <TableRow key={device.id}
                        sx={{ '&:hover': { bgcolor: '#f8fbff' }, transition: 'background 0.15s' }}>

                        {/* Thiết bị */}
                        <TableCell>
                          <Stack direction="row" spacing={1.5} alignItems="center">
                            <Box sx={{
                              width: 34, height: 34, borderRadius: 2, display: 'flex',
                              alignItems: 'center', justifyContent: 'center',
                              bgcolor: device.device_type === 'SENSOR' ? '#fff3e0' : '#e3f2fd',
                              color:   device.device_type === 'SENSOR' ? '#e65100'  : '#1565c0',
                            }}>
                              <DeviceIcon name={device.device_name} type={device.device_type} />
                            </Box>
                            <Box>
                              <Typography fontWeight="800" sx={{ fontSize: '0.88rem', color: '#1a1a2e' }}>
                                {device.device_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">ID #{device.id}</Typography>
                            </Box>
                          </Stack>
                        </TableCell>

                        {/* Pin */}
                        <TableCell>
                          <Chip label={device.pin || '—'}
                            size="small"
                            sx={{ bgcolor: '#f5f5f5', fontFamily: 'monospace',
                              fontWeight: 700, fontSize: '0.75rem', border: '1px solid #e0e0e0' }} />
                        </TableCell>

                        {/* Phân loại */}
                        <TableCell>
                          <Chip
                            label={device.device_type === 'SENSOR' ? 'Input (Đọc)' : 'Output (Điều khiển)'}
                            size="small" variant="outlined"
                            sx={{
                              color:       device.device_type === 'SENSOR' ? '#e65100' : '#1565c0',
                              borderColor: device.device_type === 'SENSOR' ? '#e65100' : '#1565c0',
                              fontWeight: 700, fontSize: '0.75rem'
                            }}
                          />
                        </TableCell>

                        {/* Zone */}
                        <TableCell>
                          <Typography sx={{ fontSize: '0.82rem', color: '#9e9e9e' }}>
                            {device.zone_id ? `Khu ${device.zone_id}` : '—'}
                          </Typography>
                        </TableCell>

                        {/* Status */}
                        <TableCell>
                          {device.status === 'ONLINE' ? (
                            <Chip icon={<WifiIcon fontSize="small" />}
                              label="Online" size="small" color="success"
                              sx={{ fontWeight: 700, fontSize: '0.75rem' }} />
                          ) : (
                            <Chip icon={<WifiOffIcon fontSize="small" />}
                              label="Offline" size="small"
                              sx={{ bgcolor: '#9e9e9e', color: '#fff', fontWeight: 700, fontSize: '0.75rem' }} />
                          )}
                        </TableCell>

                        {/* Control */}
                        <TableCell>
                          {device.device_type === 'SENSOR' ? (
                            <Typography sx={{ fontSize: '0.82rem', color: '#9e9e9e', fontStyle: 'italic' }}>
                              Đọc dữ liệu
                            </Typography>
                          ) : (
                            <Switch
                              checked={!!device.is_active}
                              onChange={() => handleToggle(device)}
                              disabled={device.status !== 'ONLINE'}
                              color="primary" size="small"
                            />
                          )}
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

      {/* ── Toast ── */}
      <Snackbar open={toast.open} autoHideDuration={3500}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert severity={toast.severity} variant="filled" sx={{ fontWeight: 700 }}>
          {toast.msg}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  )
}
