/**
 * AppShell — Layout dùng chung cho tất cả trang sau Login
 * Cấu trúc: AppBar (fixed, h=60px) + Sidebar (permanent, w=240px) + Main (fill remaining)
 */
import { useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemButton,
  ListItemIcon, ListItemText, Box, Button, Chip
} from '@mui/material'

import AgricultureIcon  from '@mui/icons-material/Agriculture'
import DashboardIcon    from '@mui/icons-material/Dashboard'
import SensorsIcon      from '@mui/icons-material/Sensors'
import GrassIcon        from '@mui/icons-material/Grass'
import SettingsIcon     from '@mui/icons-material/Settings'
import LogoutIcon       from '@mui/icons-material/Logout'
import './dashboard.css'

export const DRAWER_WIDTH = 240
export const APPBAR_HEIGHT = 60

const NAV_ITEMS = [
  { label: 'Tổng quan',          icon: <DashboardIcon fontSize="small" />, path: '/dashboard',           group: 'nav' },
  { label: 'Quản lý Thiết bị',   icon: <SensorsIcon   fontSize="small" />, path: '/device-management',   group: 'nav' },
  { label: 'Cấu hình Cây trồng', icon: <GrassIcon     fontSize="small" />, path: '/crop-settings',        group: 'nav' },
  { label: 'Cài đặt',            icon: <SettingsIcon  fontSize="small" />, path: '/settings',             group: 'sys' },
]

export default function AppShell({ children, wsStatus }) {
  const navigate  = useNavigate()
  const location  = useLocation()

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  const wsBadge = wsStatus ? {
    connected:  { label: 'Live',          color: 'success' },
    connecting: { label: 'Đang kết nối…', color: 'warning' },
    error:      { label: 'Lỗi kết nối',   color: 'error'   },
  }[wsStatus] : null

  return (
    <Box className="dashboard-root">
      {/* ── AppBar ── */}
      <AppBar position="fixed" elevation={0}
        sx={{ zIndex: (t) => t.zIndex.drawer + 1, bgcolor: '#1b5e20',
              borderBottom: '1px solid rgba(255,255,255,0.1)', height: APPBAR_HEIGHT }}>
        <Toolbar sx={{ minHeight: APPBAR_HEIGHT }}>
          <AgricultureIcon sx={{ mr: 1.5, fontSize: 26 }} />
          <Typography variant="h6" noWrap
            sx={{ flexGrow: 1, fontWeight: 800, letterSpacing: 0.5, fontSize: '1rem' }}>
            SmartFarm Admin
          </Typography>
          {wsBadge && (
            <Chip size="small" label={wsBadge.label} color={wsBadge.color}
              sx={{ mr: 2, fontWeight: 'bold', fontSize: '0.7rem', height: 24 }} />
          )}
          <Button color="inherit" onClick={handleLogout} startIcon={<LogoutIcon />}
            sx={{ fontWeight: 'bold', fontSize: '0.82rem' }}>
            Đăng xuất
          </Button>
        </Toolbar>
      </AppBar>

      {/* ── Sidebar ── */}
      <Drawer variant="permanent"
        sx={{ width: DRAWER_WIDTH, flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: 'border-box', border: 'none' } }}
        PaperProps={{ className: 'sidebar-paper' }}>

        <Toolbar sx={{ minHeight: APPBAR_HEIGHT }} />

        <Box className="sidebar-logo-area">
          <Typography sx={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.65rem', fontWeight: 800,
            letterSpacing: 1.5, textTransform: 'uppercase', mb: 0.5 }}>
            SmartFarm v1.0
          </Typography>
          <Typography sx={{ color: '#fff', fontSize: '0.82rem', fontWeight: 700 }}>
            Hệ thống nông trại thông minh
          </Typography>
        </Box>

        <Box sx={{ overflow: 'auto', mt: 2 }}>
          <Typography className="sidebar-nav-label">Điều hướng</Typography>
          <List dense disablePadding>
            {NAV_ITEMS.filter(i => i.group === 'nav').map((item) => {
              const active = location.pathname === item.path ||
                             (item.path !== '/dashboard' && location.pathname.startsWith(item.path))
              return (
                <ListItem disablePadding key={item.path}>
                  <ListItemButton
                    className={`sidebar-item${active ? ' sidebar-item-active' : ''}`}
                    onClick={() => navigate(item.path)}>
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.label}
                      primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: active ? 700 : 400 }} />
                  </ListItemButton>
                </ListItem>
              )
            })}
          </List>

          <Typography className="sidebar-nav-label" sx={{ mt: 1 }}>Hệ thống</Typography>
          <List dense disablePadding>
            {NAV_ITEMS.filter(i => i.group === 'sys').map((item) => {
              const active = location.pathname === item.path
              return (
                <ListItem disablePadding key={item.path}>
                  <ListItemButton
                    className={`sidebar-item${active ? ' sidebar-item-active' : ''}`}
                    onClick={() => navigate(item.path)}>
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.label}
                      primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: active ? 700 : 400 }} />
                  </ListItemButton>
                </ListItem>
              )
            })}
          </List>
        </Box>
      </Drawer>

      {/* ── Main Content ── */}
      <Box component="main" className="dashboard-main">
        {children}
      </Box>
    </Box>
  )
}
