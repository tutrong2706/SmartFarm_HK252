import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './Login'
import Dashboard from './Dashboard'

// Component kiểm tra quyền truy cập (Người gác cổng)
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('access_token')
  // Nếu không có Token -> Đuổi về trang Đăng nhập
  if (!token) {
    return <Navigate to="/login" replace />
  }
  // Có Token -> Cho phép vào Dashboard
  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Đường dẫn mặc định đẩy về Login */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* Trang Đăng nhập */}
        <Route path="/login" element={<Login />} />
        
        {/* Trang Dashboard (Đã được bảo vệ) */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App