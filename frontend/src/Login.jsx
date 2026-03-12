import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { 
  ThemeProvider, createTheme, CssBaseline, 
  Box, Typography, TextField, Button, Tabs, Tab, Alert, Paper
} from '@mui/material'
import AgricultureIcon from '@mui/icons-material/Agriculture'

const farmTheme = createTheme({
  palette: {
    primary: { main: '#2e7d32', light: '#4caf50', dark: '#1b5e20', contrastText: '#ffffff' },
    background: { default: '#f1f8e9', paper: '#ffffff' },
  },
  typography: { fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif' },
  shape: { borderRadius: 16 } // Bo góc form tròn trịa hơn một chút
})

export default function Login() {
  const navigate = useNavigate()
  const [tab, setTab] = useState(0)
  const [error, setError] = useState("")
  const [formData, setFormData] = useState({ username: '', password: '', name: '' })

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value })

  const handleRegister = async () => {
    try {
      await axios.post('http://localhost:8000/api/register', formData)
      alert("Đăng ký thành công! Vui lòng đăng nhập.")
      setTab(0)
      setError("")
      setFormData({ ...formData, password: '' })
    } catch (err) {
      setError(err.response?.data?.detail || "Lỗi đăng ký!")
    }
  }

  const handleLogin = async () => {
    try {
      const params = new URLSearchParams()
      params.append('username', formData.username)
      params.append('password', formData.password)
      const response = await axios.post('http://localhost:8000/api/login', params)
      localStorage.setItem('access_token', response.data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setError("Sai tên đăng nhập hoặc mật khẩu!")
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    tab === 0 ? handleLogin() : handleRegister()
  }

  return (
    <ThemeProvider theme={farmTheme}>
      <CssBaseline />
      
      {/* KHUNG NỀN TOÀN MÀN HÌNH */}
      <Box 
        sx={{ 
          display: 'flex', 
          height: '100vh', 
          width: '100vw', 
          alignItems: 'center',      // Ép nội dung vào giữa theo chiều dọc
          justifyContent: 'center',  // Ép nội dung vào giữa theo chiều ngang
          backgroundImage: 'url(https://images.unsplash.com/photo-1586771107445-d3ca888129ff?q=80&w=2072&auto=format&fit=crop)', // Ảnh cánh đồng xanh
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          position: 'relative',
          // Lớp phủ màu đen mờ giúp form màu trắng nổi bật lên
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0, right: 0, bottom: 0, left: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.45)', // Chỉnh độ mờ ở số 0.45
            zIndex: 0
          }
        }}
      >
        
        {/* THẺ ĐĂNG NHẬP (Lơ lửng ở giữa) */}
        <Paper 
          elevation={24} 
          sx={{ 
            p: { xs: 4, sm: 5 }, // Padding to hơn một chút
            width: '100%', 
            maxWidth: 450,       // Khóa độ rộng cực đại
            zIndex: 1,           // Nổi lên trên lớp nền đen mờ
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.95)', // Màu trắng hơi trong suốt nhẹ
            backdropFilter: 'blur(10px)' // Hiệu ứng kính mờ (Glassmorphism) cực trend
          }}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
            <Box sx={{ bgcolor: 'primary.main', p: 1.5, borderRadius: '50%', mb: 2, display: 'flex', boxShadow: 3 }}>
              <AgricultureIcon sx={{ fontSize: 40, color: '#ffffff' }} />
            </Box>
            <Typography component="h1" variant="h5" fontWeight="900" color="primary.dark" gutterBottom>
              SMART FARM
            </Typography>
            <Typography variant="body2" color="text.secondary" textAlign="center">
              Hệ thống Giám sát & Quản lý Nông nghiệp 
            </Typography>
          </Box>

          <Tabs 
            value={tab} 
            onChange={(e, newValue) => setTab(newValue)} 
            centered 
            indicatorColor="primary"
            textColor="primary"
            sx={{ width: '100%', mb: 3, borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="ĐĂNG NHẬP" sx={{ fontWeight: 'bold', fontSize: '0.95rem', width: '50%' }} />
            <Tab label="ĐĂNG KÝ" sx={{ fontWeight: 'bold', fontSize: '0.95rem', width: '50%' }} />
          </Tabs>

          {/* FORM NHẬP LIỆU */}
          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>}
            
            <TextField
              margin="dense" required fullWidth
              label="Tên đăng nhập" name="username" autoFocus
              value={formData.username} onChange={handleChange}
              sx={{ mb: 2 }}
            />
            
            {tab === 1 && (
              <TextField
                margin="dense" required fullWidth
                label="Họ và tên của bạn" name="name"
                value={formData.name} onChange={handleChange}
                sx={{ mb: 2 }}
              />
            )}

            <TextField
              margin="dense" required fullWidth
              name="password" label="Mật khẩu" type="password"
              value={formData.password} onChange={handleChange}
              sx={{ mb: 3 }}
            />

            <Button 
              type="submit" fullWidth variant="contained" size="large" 
              sx={{ 
                py: 1.5, 
                fontSize: '1rem', 
                fontWeight: 'bold', 
                boxShadow: 3,
                borderRadius: 2,
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 6, transition: 'all 0.2s' } 
              }}
            >
              {tab === 0 ? "ĐĂNG NHẬP HỆ THỐNG" : "TẠO TÀI KHOẢN MỚI"}
            </Button>
          </Box>
        </Paper>

      </Box>
    </ThemeProvider>
  )
}