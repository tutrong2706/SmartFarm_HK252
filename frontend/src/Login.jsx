import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { 
  ThemeProvider, createTheme, CssBaseline, 
  Container, Box, Card, CardContent, Typography, 
  TextField, Button, Tabs, Tab, Alert
} from '@mui/material'
import AgricultureIcon from '@mui/icons-material/Agriculture'

// Tái sử dụng Theme màu xanh của Nông trại
const farmTheme = createTheme({
  palette: {
    primary: { main: '#2e7d32' },
    background: { default: '#f1f8e9' }
  },
  shape: { borderRadius: 12 }
})

export default function Login() {
  const navigate = useNavigate()
  const [tab, setTab] = useState(0) // 0: Đăng nhập, 1: Đăng ký
  const [error, setError] = useState("")
  
  // State lưu dữ liệu form
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    name: ''
  })

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  // Xử lý Đăng ký
  const handleRegister = async () => {
    try {
      await axios.post('http://localhost:8000/api/register', {
        username: formData.username,
        password: formData.password,
        name: formData.name
      })
      alert("Đăng ký thành công! Vui lòng đăng nhập.")
      setTab(0) // Chuyển về tab Đăng nhập
      setError("")
    } catch (err) {
      setError(err.response?.data?.detail || "Lỗi đăng ký!")
    }
  }

  // Xử lý Đăng nhập
  const handleLogin = async () => {
    try {
      // Vì FastAPI OAuth2 dùng Form Data nên phải bọc dữ liệu lại
      const params = new URLSearchParams()
      params.append('username', formData.username)
      params.append('password', formData.password)

      const response = await axios.post('http://localhost:8000/api/login', params)
      
      // Lưu token vào localStorage của trình duyệt
      localStorage.setItem('access_token', response.data.access_token)
      
      // Chuyển hướng thẳng vào trang Dashboard
      navigate('/dashboard')
    } catch (err) {
      setError("Sai tên đăng nhập hoặc mật khẩu!")
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (tab === 0) handleLogin()
    else handleRegister()
  }

  return (
    <ThemeProvider theme={farmTheme}>
      <CssBaseline />
      <Container maxWidth="sm" sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100vh' }}>
        <Card elevation={6} sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
            <AgricultureIcon sx={{ fontSize: 60, color: 'primary.main', mb: 1 }} />
            <Typography variant="h5" fontWeight="bold" color="primary.dark">
              SMART FARM
            </Typography>
          </Box>

          <Tabs value={tab} onChange={(e, newValue) => setTab(newValue)} centered sx={{ mb: 3 }}>
            <Tab label="Đăng nhập" />
            <Tab label="Đăng ký" />
          </Tabs>

          <CardContent>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            
            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth label="Tên đăng nhập" name="username"
                variant="outlined" margin="normal" required
                value={formData.username} onChange={handleChange}
              />
              
              {tab === 1 && (
                <TextField
                  fullWidth label="Họ và tên của bạn" name="name"
                  variant="outlined" margin="normal" required={tab === 1}
                  value={formData.name} onChange={handleChange}
                />
              )}

              <TextField
                fullWidth label="Mật khẩu" name="password" type="password"
                variant="outlined" margin="normal" required
                value={formData.password} onChange={handleChange}
              />

              <Button 
                type="submit" fullWidth variant="contained" 
                size="large" sx={{ mt: 3, py: 1.5, fontSize: '1.1rem' }}
              >
                {tab === 0 ? "ĐĂNG NHẬP" : "TẠO TÀI KHOẢN"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </Container>
    </ThemeProvider>
  )
}