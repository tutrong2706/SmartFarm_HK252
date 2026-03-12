import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import {
  ThemeProvider, createTheme, CssBaseline,
  Box, Typography, Card, Button, Grid,
  MenuItem, Select, FormControl, Chip, Switch, Divider,
  IconButton, CircularProgress, Snackbar, Alert, Stack,
  Dialog, DialogTitle, DialogContent, DialogActions, Checkbox, ListItemText
} from '@mui/material'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend
} from 'recharts'

import AppShell from './AppShell'

import ArrowBackRoundedIcon        from '@mui/icons-material/ArrowBackRounded'
import DeviceThermostatRoundedIcon from '@mui/icons-material/DeviceThermostatRounded'
import WaterDropRoundedIcon        from '@mui/icons-material/WaterDropRounded'
import WbSunnyRoundedIcon          from '@mui/icons-material/WbSunnyRounded'
import GrassRoundedIcon            from '@mui/icons-material/GrassRounded'
import RouterIcon                  from '@mui/icons-material/Router'
import RefreshIcon                 from '@mui/icons-material/Refresh'
import PowerSettingsNewIcon        from '@mui/icons-material/PowerSettingsNew'
import AddCircleOutlineIcon        from '@mui/icons-material/AddCircleOutline'
import RemoveCircleOutlineIcon     from '@mui/icons-material/RemoveCircleOutline'
import WaterDropIcon               from '@mui/icons-material/WaterDrop'
import AirIcon                     from '@mui/icons-material/Air'
import LightbulbIcon               from '@mui/icons-material/Lightbulb'
import DesktopWindowsIcon          from '@mui/icons-material/DesktopWindows'
import SensorsIcon                 from '@mui/icons-material/Sensors'

const API = 'http://localhost:8000'
const MAX_HISTORY = 30   // số điểm giữ lại trên biểu đồ

const farmTheme = createTheme({
  palette: {
    primary: { main: '#2e7d32', light: '#4caf50', dark: '#1b5e20', contrastText: '#fff' },
    background: { default: '#f0f4f0', paper: '#ffffff' },
  },
  typography: { fontFamily: '"Be Vietnam Pro", "Plus Jakarta Sans", "Roboto", sans-serif' },
  shape: { borderRadius: 12 },
})

function DeviceIcon({ name = '', type = '' }) {
  const n = name.toLowerCase()
  const s = { fontSize: 20 }
  if (n.includes('pump') || n.includes('bơm'))   return <WaterDropIcon sx={s} />
  if (n.includes('fan')  || n.includes('quạt'))  return <AirIcon sx={s} />
  if (n.includes('led')  || n.includes('light')) return <LightbulbIcon sx={s} />
  if (n.includes('lcd')  || n.includes('screen'))return <DesktopWindowsIcon sx={s} />
  if (type === 'SENSOR')                          return <SensorsIcon sx={s} />
  return <RouterIcon sx={s} />
}

function relativeTime(isoString) {
  if (!isoString) return 'Chờ kết nối…'
  const diff = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  if (diff < 5)    return 'Vừa xong'
  if (diff < 60)   return `${diff} giây trước`
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`
  return `${Math.floor(diff / 3600)} giờ trước`
}

export default function ZoneDetail() {
  const { id }   = useParams()
  const navigate = useNavigate()

  // ── State ──────────────────────────────────────────────────────
  const [zone,        setZone]        = useState(null)
  const [crops,       setCrops]       = useState([])
  const [devices,     setDevices]     = useState([])       // devices IN zone
  const [allDevices,  setAllDevices]  = useState([])       // all devices (for picker)
  const [liveData,    setLiveData]    = useState({ temperature: '--', humidity: '--', light: '--' })
  const [chartData,   setChartData]   = useState([])       // history for chart
  const [loading,     setLoading]     = useState(true)
  const [wsStatus,    setWsStatus]    = useState('connecting')
  const [toast,       setToast]       = useState({ open: false, msg: '', severity: 'success' })
  const [savingCrop,  setSavingCrop]  = useState(false)
  const [pickerOpen,  setPickerOpen]  = useState(false)    // dialog thêm thiết bị
  const [pickerSel,   setPickerSel]   = useState([])       // selected in dialog
  const [assigning,   setAssigning]   = useState(false)
  const [relTimeStr,  setRelTimeStr]  = useState('Chờ kết nối…')
  const wsRef = useRef(null)

  const notify = (msg, severity = 'success') => setToast({ open: true, msg, severity })

  // ── Fetch ──────────────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [zoneRes, cropsRes, devicesRes, allDevRes] = await Promise.all([
        axios.get(`${API}/api/zones/${id}`),
        axios.get(`${API}/api/crop-settings/`),
        axios.get(`${API}/api/zones/${id}/devices`),
        axios.get(`${API}/api/devices/`),
      ])
      setZone(zoneRes.data)
      setCrops(cropsRes.data)
      setDevices(devicesRes.data)
      setAllDevices(allDevRes.data)
    } catch {
      notify('Không thể tải dữ liệu khu vực', 'error')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { fetchAll() }, [fetchAll])

  // ── Tick: re-compute relative time every second ───────────────
  useEffect(() => {
    const timer = setInterval(() => {
      setRelTimeStr(relativeTime(liveData.measured_at))
    }, 1000)
    return () => clearInterval(timer)
  }, [liveData.measured_at])

  // ── WebSocket live sensor + chart history ─────────────────────
  useEffect(() => {
    let retryTimer
    const connect = () => {
      const ws = new WebSocket(`ws://localhost:8000/ws/telemetry`)
      wsRef.current = ws
      ws.onopen  = () => setWsStatus('connected')
      ws.onerror = () => setWsStatus('error')
      ws.onclose = () => {
        setWsStatus('connecting')
        retryTimer = setTimeout(connect, 4000)
      }
      ws.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data)
          if (String(d.zone_id) !== String(id)) return
          setLiveData(d)
          // append to chart history
          const ts = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
          setChartData(prev => {
            const next = [...prev, {
              time: ts,
              temp:  d.temperature !== '--' ? parseFloat(d.temperature) : null,
              humid: d.humidity    !== '--' ? parseFloat(d.humidity)    : null,
              light: d.light       !== '--' ? parseFloat(d.light)       : null,
            }]
            return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next
          })
        } catch { /* ignore */ }
      }
    }
    connect()
    return () => { wsRef.current?.close(); clearTimeout(retryTimer) }
  }, [id])

  // ── Gán cây trồng ─────────────────────────────────────────────
  const handleCropChange = async (e) => {
    const cropId = e.target.value === '' ? null : Number(e.target.value)
    setSavingCrop(true)
    try {
      const res = await axios.patch(`${API}/api/zones/${id}`, { crop_setting_id: cropId })
      setZone(res.data)
      notify(cropId ? 'Đã gán cây trồng!' : 'Đã xoá cây trồng khỏi khu vực')
    } catch {
      notify('Không thể cập nhật cây trồng', 'error')
    } finally { setSavingCrop(false) }
  }

  // ── Bật / Tắt thiết bị ─────────────────────────────────────────
  const handleToggleDevice = async (device, newState) => {
    setDevices(prev => prev.map(d => d.id === device.id ? { ...d, is_active: newState } : d))
    try {
      await axios.patch(`${API}/api/devices/${device.id}/toggle`, { is_active: newState })
      notify(`${device.device_name} đã ${newState ? 'bật' : 'tắt'}`)
    } catch {
      setDevices(prev => prev.map(d => d.id === device.id ? { ...d, is_active: !newState } : d))
      notify('Không thể điều khiển thiết bị', 'error')
    }
  }

  // ── Thêm / gỡ thiết bị vào zone ───────────────────────────────
  const openPicker = () => {
    setPickerSel(devices.map(d => d.id))
    setPickerOpen(true)
  }

  const handleAssign = async () => {
    setAssigning(true)
    try {
      const currentIds = devices.map(d => d.id)
      const toAdd    = pickerSel.filter(id => !currentIds.includes(id))
      const toRemove = currentIds.filter(id => !pickerSel.includes(id))
      await Promise.all([
        ...toAdd.map(devId    => axios.post(`${API}/api/zones/${id}/devices/${devId}`)),
        ...toRemove.map(devId => axios.delete(`${API}/api/zones/${id}/devices/${devId}`)),
      ])
      await fetchAll()
      setPickerOpen(false)
      notify('Cập nhật danh sách thiết bị thành công!')
    } catch {
      notify('Có lỗi khi cập nhật thiết bị', 'error')
    } finally { setAssigning(false) }
  }

  // ── Computed ───────────────────────────────────────────────────
  const selectedCrop  = crops.find(c => c.id === zone?.crop_setting_id)
  const actuators     = devices.filter(d => d.device_type === 'ACTUATOR')
  const sensors       = devices.filter(d => d.device_type === 'SENSOR')
  const activeCount   = devices.filter(d => d.is_active).length

  const wsBadge = {
    connected:  { label: 'Live',       color: 'success' },
    connecting: { label: 'Kết nối…',   color: 'warning' },
    error:      { label: 'Lỗi WS',     color: 'error'   },
  }[wsStatus]

  const sensorCards = [
    { key: 'temperature', label: 'Nhiệt độ',    unit: '°C', Icon: DeviceThermostatRoundedIcon, color: '#e53935', bg: '#fff8f8', border: '#ffcdd2' },
    { key: 'humidity',    label: 'Độ ẩm',        unit: '%',  Icon: WaterDropRoundedIcon,        color: '#1e88e5', bg: '#f0f8ff', border: '#bbdefb' },
    { key: 'light',       label: 'Ánh sáng',     unit: ' lx',Icon: WbSunnyRoundedIcon,          color: '#f9a825', bg: '#fffde7', border: '#fff176' },
  ]

  if (loading) return (
    <ThemeProvider theme={farmTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress color="primary" />
      </Box>
    </ThemeProvider>
  )

  return (
    <ThemeProvider theme={farmTheme}>
      <CssBaseline />
      <AppShell wsStatus={wsStatus}>
        <Box className="dashboard-content">

          {/* ── Breadcrumb header ── */}
          <Box sx={{
            background: 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 60%, #388e3c 100%)',
            borderRadius: 3, p: '24px 32px', mb: 3,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            position: 'relative', overflow: 'hidden'
          }}>
            <Box sx={{ position: 'absolute', width: 180, height: 180, borderRadius: '50%',
              background: 'rgba(255,255,255,0.05)', top: -50, right: -40, pointerEvents: 'none' }} />
            <Stack direction="row" spacing={2} alignItems="center">
              <IconButton onClick={() => navigate('/dashboard')}
                sx={{ bgcolor: 'rgba(255,255,255,0.12)', color: '#fff',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.22)' } }}>
                <ArrowBackRoundedIcon />
              </IconButton>
              <Box>
                <Typography sx={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.7rem',
                  fontWeight: 700, letterSpacing: 1.2, textTransform: 'uppercase', mb: 0.3 }}>
                  Chi tiết khu vực #{id}
                </Typography>
                <Typography sx={{ color: '#fff', fontSize: '1.4rem', fontWeight: 900, lineHeight: 1.2 }}>
                  {zone?.name}
                </Typography>
                <Typography sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.8rem', mt: 0.3 }}>
                  {zone?.description || 'Giám sát & điều khiển thời gian thực'}
                </Typography>
              </Box>
            </Stack>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Chip size="small" label={wsBadge.label} color={wsBadge.color}
                sx={{ fontWeight: 700, fontSize: '0.72rem', height: 26 }} />
              <Button size="small" variant="contained"
                onClick={fetchAll} startIcon={<RefreshIcon />}
                sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#fff', fontWeight: 700,
                  borderRadius: 2, textTransform: 'none', '&:hover': { bgcolor: 'rgba(255,255,255,0.25)' } }}>
                Tải lại
              </Button>
            </Stack>
          </Box>

          {/* ═══ ROW 1: sensor live cards ═══ */}
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 3, mb: 3 }}>
            {sensorCards.map(({ key, label, unit, Icon, color, bg, border }) => {
              const raw = liveData[key]
              const val = raw !== '--' ? `${raw}${unit}` : '--'
              return (
                <Card key={key} elevation={0} sx={{ p: 3, bgcolor: bg,
                  border: `1px solid ${border}`, borderRadius: 3 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
                    <Typography sx={{ fontSize: '0.75rem', fontWeight: 700,
                      color: 'text.secondary', textTransform: 'uppercase', letterSpacing: 0.8 }}>
                      {label}
                    </Typography>
                    <Box sx={{ p: 0.8, borderRadius: 1.5, bgcolor: `${color}18` }}>
                      <Icon sx={{ color, fontSize: 20 }} />
                    </Box>
                  </Stack>
                  <Typography sx={{ fontSize: '2.2rem', fontWeight: 900, color, lineHeight: 1 }}>
                    {val}
                  </Typography>
                  <Stack direction="row" alignItems="center" spacing={0.8} mt={1}>
                    <Box sx={{
                      width: 7, height: 7, borderRadius: '50%',
                      bgcolor: wsStatus === 'connected' ? '#4caf50' : '#bdbdbd',
                      animation: wsStatus === 'connected' ? 'pulse-dot 1.5s infinite' : 'none'
                    }} />
                    <Typography sx={{ fontSize: '0.72rem', color: 'text.secondary' }}>
                      {relTimeStr}
                    </Typography>
                  </Stack>
                </Card>
              )
            })}
          </Box>

          {/* ═══ ROW 2: chart + crop config ═══ */}
          <Box sx={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 3, mb: 3 }}>

            {/* ── Biểu đồ lịch sử ── */}
            <Card elevation={0} sx={{ p: 3, borderRadius: 3, border: '1px solid #e8f5e9' }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                <Box>
                  <Typography fontWeight="800" color="primary.dark" sx={{ fontSize: '0.95rem' }}>
                    Biểu đồ thông số môi trường
                  </Typography>
                  <Typography sx={{ fontSize: '0.75rem', color: '#9e9e9e' }}>
                    {chartData.length} điểm gần nhất · cập nhật realtime
                  </Typography>
                </Box>
              </Stack>

              {chartData.length < 2 ? (
                <Box sx={{ height: 220, display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center', color: '#bdbdbd' }}>
                  <WbSunnyRoundedIcon sx={{ fontSize: 40, mb: 1, opacity: 0.4 }} />
                  <Typography sx={{ fontSize: '0.82rem' }}>
                    Đang chờ dữ liệu realtime từ WebSocket…
                  </Typography>
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#9e9e9e' }}
                      interval="preserveStartEnd" />
                    <YAxis tick={{ fontSize: 10, fill: '#9e9e9e' }} />
                    <Tooltip
                      contentStyle={{ fontSize: '0.78rem', borderRadius: 8, border: '1px solid #e0e0e0' }}
                      formatter={(v, name) => {
                        const map = { temp: ['°C', 'Nhiệt độ'], humid: ['%', 'Độ ẩm'], light: [' lx', 'Ánh sáng'] }
                        return v !== null ? [`${v}${map[name]?.[0] ?? ''}`, map[name]?.[1] ?? name] : ['--', name]
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '0.78rem', paddingTop: 8 }}
                      formatter={(v) => ({ temp: 'Nhiệt độ', humid: 'Độ ẩm', light: 'Ánh sáng' }[v] ?? v)} />
                    <Line type="monotone" dataKey="temp"  stroke="#e53935" strokeWidth={2} dot={false}
                      connectNulls activeDot={{ r: 4 }} />
                    <Line type="monotone" dataKey="humid" stroke="#1e88e5" strokeWidth={2} dot={false}
                      connectNulls activeDot={{ r: 4 }} />
                    <Line type="monotone" dataKey="light" stroke="#f9a825" strokeWidth={2} dot={false}
                      connectNulls activeDot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </Card>

            {/* ── Cấu hình cây trồng ── */}
            <Card elevation={0} sx={{ p: 3, borderRadius: 3, border: '1px solid #e8f5e9' }}>
              <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                <GrassRoundedIcon sx={{ color: '#4caf50', fontSize: 20 }} />
                <Typography fontWeight="800" color="primary.dark" sx={{ fontSize: '0.95rem' }}>
                  Cấu hình canh tác
                </Typography>
              </Stack>

              <Typography sx={{ fontSize: '0.72rem', fontWeight: 700, color: 'text.secondary',
                textTransform: 'uppercase', letterSpacing: 0.8, mb: 0.8 }}>
                Nông sản đang trồng
              </Typography>
              <FormControl fullWidth size="small" disabled={savingCrop} sx={{ mb: 2 }}>
                <Select value={zone?.crop_setting_id ?? ''}
                  onChange={handleCropChange} displayEmpty
                  sx={{ fontWeight: 700, borderRadius: 2, bgcolor: '#f9fafb' }}>
                  <MenuItem value=""><em>— Chưa thiết lập —</em></MenuItem>
                  {crops.map(c => (
                    <MenuItem key={c.id} value={c.id}>🌱 {c.crop_name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              {savingCrop && (
                <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                  <CircularProgress size={12} color="primary" />
                  <Typography variant="caption" color="text.secondary">Đang lưu…</Typography>
                </Stack>
              )}

              {selectedCrop ? (
                <Box sx={{ p: 2, bgcolor: '#f1f8e9', borderRadius: 2, border: '1px dashed #a5d6a7' }}>
                  <Typography fontWeight="800" color="primary.dark" sx={{ fontSize: '1rem', mb: 1.5 }}>
                    🌿 {selectedCrop.crop_name}
                  </Typography>
                  {[
                    { label: 'Nhiệt độ', val: `${selectedCrop.temp_min}°C – ${selectedCrop.temp_max}°C`, color: '#e53935' },
                    { label: 'Độ ẩm',    val: `${selectedCrop.humid_min}% – ${selectedCrop.humid_max}%`,   color: '#1e88e5' },
                  ].map(row => (
                    <Stack key={row.label} direction="row" justifyContent="space-between" alignItems="center" mb={0.8}>
                      <Typography sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>{row.label}</Typography>
                      <Typography sx={{ fontSize: '0.85rem', fontWeight: 800, color: row.color }}>{row.val}</Typography>
                    </Stack>
                  ))}
                  <Divider sx={{ my: 1 }} />
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography sx={{ fontSize: '0.8rem', color: 'text.secondary' }}>Tự động hóa</Typography>
                    <Chip size="small"
                      label={selectedCrop.auto_mode ? 'Đang bật' : 'Đang tắt'}
                      color={selectedCrop.auto_mode ? 'success' : 'default'}
                      sx={{ fontWeight: 700, fontSize: '0.72rem' }} />
                  </Stack>
                </Box>
              ) : (
                <Box sx={{ p: 2.5, bgcolor: '#fafafa', borderRadius: 2, border: '1px dashed #e0e0e0',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                  <GrassRoundedIcon sx={{ color: '#c8e6c9', fontSize: 36 }} />
                  <Typography sx={{ fontSize: '0.82rem', fontWeight: 700, color: 'text.secondary' }}>
                    Chưa gán cây trồng
                  </Typography>
                  <Typography sx={{ fontSize: '0.73rem', color: 'text.disabled', textAlign: 'center' }}>
                    Chọn nông sản để hiển thị ngưỡng canh tác
                  </Typography>
                </Box>
              )}
            </Card>
          </Box>

          {/* ═══ ROW 3: device control ═══ */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #e8f5e9', overflow: 'hidden' }}>
            <Box sx={{ px: 3, py: 2.5, display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', borderBottom: '1px solid #f0f4f0' }}>
              <Box>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <RouterIcon sx={{ color: '#2e7d32', fontSize: 20 }} />
                  <Typography fontWeight="800" color="primary.dark" sx={{ fontSize: '0.95rem' }}>
                    Điều khiển thiết bị
                  </Typography>
                  <Chip size="small" label={`${devices.length} thiết bị`}
                    sx={{ bgcolor: '#e8f5e9', color: '#1b5e20', fontWeight: 700, fontSize: '0.7rem', height: 22 }} />
                  <Chip size="small" label={`${activeCount} đang bật`}
                    color="success" variant="outlined"
                    sx={{ fontWeight: 700, fontSize: '0.7rem', height: 22 }} />
                </Stack>
                <Typography sx={{ fontSize: '0.75rem', color: '#9e9e9e', mt: 0.3 }}>
                  {sensors.length} cảm biến · {actuators.length} thiết bị chấp hành
                </Typography>
              </Box>
              <Button size="small" variant="outlined" color="primary"
                startIcon={<AddCircleOutlineIcon />}
                onClick={openPicker}
                sx={{ borderRadius: 2, fontWeight: 700, textTransform: 'none', fontSize: '0.8rem' }}>
                Quản lý thiết bị
              </Button>
            </Box>

            {devices.length === 0 ? (
              <Box sx={{ p: 5, textAlign: 'center' }}>
                <RouterIcon sx={{ fontSize: 44, color: '#c8e6c9', mb: 1 }} />
                <Typography fontWeight="700" color="text.secondary">Chưa có thiết bị trong khu vực</Typography>
                <Typography sx={{ fontSize: '0.8rem', color: '#bdbdbd', mb: 2 }}>
                  Nhấn "Quản lý thiết bị" để gán thiết bị vào đây.
                </Typography>
                <Button variant="outlined" size="small" onClick={openPicker}
                  startIcon={<AddCircleOutlineIcon />}
                  sx={{ borderRadius: 2, fontWeight: 700, textTransform: 'none' }}>
                  Thêm thiết bị
                </Button>
              </Box>
            ) : (
              <Box sx={{ p: 3 }}>
                {/* Actuators first */}
                {actuators.length > 0 && (
                  <>
                    <Typography sx={{ fontSize: '0.7rem', fontWeight: 800, color: '#1565c0',
                      letterSpacing: 1, textTransform: 'uppercase', mb: 1.5 }}>
                      Thiết bị chấp hành
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 2, mb: 2.5 }}>
                      {actuators.map(device => (
                        <Box key={device.id} sx={{
                          p: 2, borderRadius: 2, border: device.is_active ? '1px solid #a5d6a7' : '1px solid #e0e0e0',
                          bgcolor: device.is_active ? '#f1f8e9' : '#fafafa',
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          transition: 'all 0.2s', cursor: 'default'
                        }}>
                          <Stack direction="row" spacing={1.5} alignItems="center" sx={{ flex: 1, minWidth: 0 }}>
                            <Box sx={{
                              width: 36, height: 36, borderRadius: 2, display: 'flex',
                              alignItems: 'center', justifyContent: 'center',
                              bgcolor: device.is_active ? '#c8e6c9' : '#f3f4f6',
                              color:   device.is_active ? '#2e7d32' : '#9e9e9e',
                            }}>
                              <DeviceIcon name={device.device_name} type={device.device_type} />
                            </Box>
                            <Box sx={{ minWidth: 0 }}>
                              <Typography fontWeight="800" noWrap sx={{ fontSize: '0.85rem', color: '#1a1a2e' }}>
                                {device.device_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary" noWrap>
                                {device.pin || device.func || `ID #${device.id}`}
                              </Typography>
                            </Box>
                          </Stack>
                          <Stack alignItems="center" spacing={0.2} ml={1}>
                            <Switch checked={!!device.is_active} size="small" color="success"
                              onChange={(e) => handleToggleDevice(device, e.target.checked)} />
                            <Typography sx={{ fontSize: '0.65rem', fontWeight: 700,
                              color: device.is_active ? '#2e7d32' : '#9e9e9e' }}>
                              {device.is_active ? 'BẬT' : 'TẮT'}
                            </Typography>
                          </Stack>
                        </Box>
                      ))}
                    </Box>
                  </>
                )}

                {/* Sensors */}
                {sensors.length > 0 && (
                  <>
                    <Typography sx={{ fontSize: '0.7rem', fontWeight: 800, color: '#e65100',
                      letterSpacing: 1, textTransform: 'uppercase', mb: 1.5 }}>
                      Cảm biến
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 2 }}>
                      {sensors.map(device => (
                        <Box key={device.id} sx={{
                          p: 2, borderRadius: 2, border: '1px solid #ffe0b2',
                          bgcolor: '#fff8f2', display: 'flex', alignItems: 'center', gap: 1.5
                        }}>
                          <Box sx={{
                            width: 36, height: 36, borderRadius: 2, display: 'flex',
                            alignItems: 'center', justifyContent: 'center',
                            bgcolor: '#fff3e0', color: '#e65100',
                          }}>
                            <DeviceIcon name={device.device_name} type={device.device_type} />
                          </Box>
                          <Box sx={{ minWidth: 0 }}>
                            <Typography fontWeight="800" noWrap sx={{ fontSize: '0.85rem', color: '#1a1a2e' }}>
                              {device.device_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" noWrap>
                              {device.func || device.pin || `ID #${device.id}`}
                            </Typography>
                          </Box>
                          <Chip size="small" label="Đọc dữ liệu"
                            sx={{ ml: 'auto', fontSize: '0.65rem', bgcolor: '#fff3e0',
                              color: '#e65100', fontWeight: 700, border: '1px solid #ffcc80' }} />
                        </Box>
                      ))}
                    </Box>
                  </>
                )}
              </Box>
            )}
          </Card>

        </Box>
      </AppShell>

      {/* ═══ Dialog: chọn thiết bị ═══ */}
      <Dialog open={pickerOpen} onClose={() => setPickerOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontWeight: 800, fontSize: '1rem', pb: 1 }}>
          Quản lý thiết bị khu vực
          <Typography sx={{ fontSize: '0.78rem', color: '#9e9e9e', fontWeight: 400, mt: 0.3 }}>
            Chọn thiết bị muốn gán vào <strong>{zone?.name}</strong>
          </Typography>
        </DialogTitle>
        <DialogContent dividers sx={{ p: 0 }}>
          {allDevices.length === 0 ? (
            <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
              <RouterIcon sx={{ fontSize: 40, color: '#c8e6c9', mb: 1 }} />
              <Typography>Chưa có thiết bị nào trong hệ thống</Typography>
            </Box>
          ) : (
            allDevices.map(device => {
              const checked = pickerSel.includes(device.id)
              return (
                <Box key={device.id}
                  onClick={() => setPickerSel(prev =>
                    checked ? prev.filter(x => x !== device.id) : [...prev, device.id]
                  )}
                  sx={{
                    px: 2.5, py: 1.5, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 2,
                    borderBottom: '1px solid #f5f5f5',
                    bgcolor: checked ? '#f1f8e9' : 'white',
                    '&:hover': { bgcolor: checked ? '#e8f5e9' : '#fafafa' },
                    transition: 'background 0.15s'
                  }}>
                  <Checkbox checked={checked} color="success" size="small"
                    sx={{ p: 0 }} onChange={() => {}} />
                  <Box sx={{
                    width: 32, height: 32, borderRadius: 1.5, display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                    bgcolor: device.device_type === 'SENSOR' ? '#fff3e0' : '#e3f2fd',
                    color:   device.device_type === 'SENSOR' ? '#e65100' : '#1565c0',
                  }}>
                    <DeviceIcon name={device.device_name} type={device.device_type} />
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <Typography fontWeight="800" sx={{ fontSize: '0.88rem' }}>{device.device_name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {device.device_type} · {device.pin || device.func || `ID #${device.id}`}
                      {device.zone_id && device.zone_id !== Number(id) && (
                        <span style={{ color: '#e65100', marginLeft: 6 }}>· Khu {device.zone_id}</span>
                      )}
                    </Typography>
                  </Box>
                  <Chip size="small"
                    label={device.device_type === 'SENSOR' ? 'Cảm biến' : 'Chấp hành'}
                    sx={{
                      fontSize: '0.68rem', fontWeight: 700,
                      bgcolor: device.device_type === 'SENSOR' ? '#fff3e0' : '#e3f2fd',
                      color:   device.device_type === 'SENSOR' ? '#e65100' : '#1565c0',
                      border:  `1px solid ${device.device_type === 'SENSOR' ? '#ffcc80' : '#90caf9'}`,
                    }}
                  />
                </Box>
              )
            })
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Typography sx={{ flex: 1, fontSize: '0.78rem', color: '#9e9e9e' }}>
            {pickerSel.length} thiết bị được chọn
          </Typography>
          <Button onClick={() => setPickerOpen(false)} color="inherit" size="small">Hủy</Button>
          <Button onClick={handleAssign} variant="contained" size="small"
            disabled={assigning}
            sx={{ borderRadius: 2, fontWeight: 700, minWidth: 100 }}>
            {assigning ? <CircularProgress size={16} color="inherit" /> : 'Xác nhận'}
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
