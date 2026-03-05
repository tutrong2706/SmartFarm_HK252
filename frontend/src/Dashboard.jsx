import { useEffect, useState } from 'react'
import axios from 'axios'
import { 
  ThemeProvider, createTheme, CssBaseline, 
  AppBar, Toolbar, Typography, Container, 
  Grid, Card, CardContent, CircularProgress, Box, IconButton 
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import AgricultureIcon from '@mui/icons-material/Agriculture'

// 1. KHỞI TẠO THEME MÀU XANH NÔNG TRẠI (SMART FARM THEME)
const farmTheme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32', // Xanh lá đậm (Màu thanh Header và Nút bấm chính)
      light: '#4caf50', // Xanh lá sáng (Hiệu ứng hover)
      dark: '#1b5e20',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#8bc34a', // Xanh nõn chuối (Dùng cho các điểm nhấn)
    },
    background: {
      default: '#f1f8e9', // Màu nền tổng thể xanh nhạt mát mắt
      paper: '#ffffff',   // Màu nền của các thẻ (Card)
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h5: {
      fontWeight: 600,
    }
  },
  shape: {
    borderRadius: 12, // Bo góc các thẻ cho mềm mại
  }
})

function Dashboard() {
  const [zones, setZones] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchZones = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/zones/')
      setZones(response.data)
      setLoading(false)
    } catch (error) {
      console.error("Lỗi khi gọi API:", error)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchZones()
  }, [])

  return (
    // 2. BỌC TOÀN BỘ APP TRONG THEME MÀU XANH VÀ CSS BASELINE
    <ThemeProvider theme={farmTheme}>
      <CssBaseline /> {/* Reset CSS và áp dụng màu nền background.default */}

      {/* 3. THANH HEADER (APP BAR) */}
      <AppBar position="static" elevation={2}>
        <Toolbar>
          <IconButton size="large" edge="start" color="inherit" aria-label="menu" sx={{ mr: 2 }}>
            <MenuIcon />
          </IconButton>
          <AgricultureIcon sx={{ mr: 1, fontSize: 32 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            HỆ THỐNG NÔNG TRẠI THÔNG MINH
          </Typography>
        </Toolbar>
      </AppBar>

      {/* 4. KHU VỰC NỘI DUNG CHÍNH (MAIN CONTENT) */}
      <Box sx={{ py: 4 }}>
        <Container maxWidth="lg">
          <Typography variant="h4" gutterBottom color="primary.dark" sx={{ mb: 3 }}>
            Danh sách khu vực canh tác
          </Typography>

          {loading ? (
            <Grid container justifyContent="center" sx={{ mt: 5 }}>
              <CircularProgress color="primary" />
            </Grid>
          ) : (
            <Grid container spacing={3}>
              {zones.length === 0 ? (
                <Typography variant="body1" sx={{ mt: 5, mx: "auto", color: 'text.secondary' }}>
                  Chưa có khu vực nào. Hãy thêm từ Swagger UI!
                </Typography>
              ) : (
                zones.map((zone) => (
                  <Grid item xs={12} sm={6} md={4} key={zone.id}>
                    {/* THẺ HIỂN THỊ (CARD) MÀU XANH */}
                    <Card elevation={3} sx={{ 
                      height: '100%', 
                      borderTop: '4px solid #4caf50', // Đường viền xanh phía trên Card
                      transition: 'transform 0.2s', 
                      '&:hover': { transform: 'translateY(-5px)' } 
                    }}>
                      <CardContent>
                        <Typography variant="h5" color="primary.main" gutterBottom>
                          {zone.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ minHeight: '40px' }}>
                          {zone.description ? zone.description : "Chưa có mô tả chi tiết."}
                        </Typography>
                        <Box sx={{ mt: 2, p: 1, bgcolor: 'background.default', borderRadius: 1, textAlign: 'center' }}>
                          <Typography variant="caption" color="primary.dark" fontWeight="bold">
                            MÃ KHU VỰC: #{zone.id}
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))
              )}
            </Grid>
          )}
        </Container>
      </Box>
    </ThemeProvider>
  )
}

export default Dashboard