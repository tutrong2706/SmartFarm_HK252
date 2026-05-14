/**
 * ChatBot.jsx — AI Assistant floating widget for SmartFarm HK252
 * Integrates ChatHistory component with real API calls
 */

import { useState, useRef, useEffect } from 'react'
import {
  Box,
  Card,
  CardHeader,
  CardContent,
  CardActions,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Paper,
  Stack,
  Collapse,
  Zoom,
  Tooltip,
} from '@mui/material'
import ChatIcon from '@mui/icons-material/Chat'
import CloseIcon from '@mui/icons-material/Close'
import SendIcon from '@mui/icons-material/Send'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import HistoryIcon from '@mui/icons-material/History'
import ReactMarkdown from 'react-markdown'
import { ChatHistory } from './ChatHistory'
import remarkGfm from 'remark-gfm'
import { chatClient } from '../api/chatClient'

const API_URL = 'http://localhost:8000/api'

export function ChatBot({ position = 'bottom-right' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [currentSession, setCurrentSession] = useState({
    id: `session_${Date.now()}`,
    title: 'Cuộc trò chuyện mới',
    messages: [],
  })
  const [sessions, setSessions] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  // ... (Giữ nguyên phần logic Session và Effects của bạn, tôi chỉ tập trung vào JSX) ...
  // Tự động load sessions khi component mount
  useEffect(() => {
    loadSessions()
  }, [])

  // Cuộn xuống tin nhắn mới nhất
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [currentSession.messages])

  // Tải danh sách session từ localStorage
  const loadSessions = async () => {
    try {
      const saved = localStorage.getItem(`sessions_${currentSession.id}`)
      if (saved) {
        const sessionsList = JSON.parse(saved)
        setSessions(sessionsList)
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
      setError('Lỗi tải lịch sử')
    }
  }

  // Load một session cụ thể từ localStorage
  const loadSessionDetails = async (sessionId) => {
    if (sessionId === currentSession.id) return

    try {
      setIsLoading(true)
      const saved = localStorage.getItem(`chat_history_${currentSession.id}_${sessionId}`)
      if (saved) {
        const sessionData = JSON.parse(saved)
        setCurrentSession(sessionData)
      } else {
        // Create empty session if not found
        const newSession = {
          id: sessionId,
          title: sessions.find(s => s.id === sessionId)?.title || 'Session Details',
          messages: []
        }
        setCurrentSession(newSession)
      }
      setError(null)
    } catch (error) {
      console.error('Failed to load session details:', error)
      setError('Lỗi tải phiên')
    } finally {
      setIsLoading(false)
    }
  }

  // Tạo session mới
  const createNewSession = (sessionId, title) => {
    const newSession = { id: sessionId, title: title, messages: [] }
    setCurrentSession(newSession)
    // Add to list if not present
    setSessions(prev => [{ id: sessionId, title: title, updatedAt: Date.now(), messageCount: 0 }, ...prev])
  }

  // Xóa session
  const deleteSession = async (sessionId) => {
    // ... (Giữ nguyên logic xóa)
    try {
      // Simulate API call to delete
      setSessions(prev => prev.filter(s => s.id !== sessionId))
      // If deleted current, switch to first available or new
      if (sessionId === currentSession.id) {
        if (sessions.length > 1) {
          const nextSession = sessions.filter(s => s.id !== sessionId)[0]
          loadSessionDetails(nextSession.id)
        } else {
          const newId = `session_${Date.now()}`
          createNewSession(newId, 'Cuộc trò chuyện mới')
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  // Gửi tin nhắn với API thực
  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return

    const userMessage = { type: 'user', text: message, timestamp: Date.now() }
    
    // Thêm tin nhắn user vào session
    setCurrentSession(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage]
    }))
    
    const userInput = message
    setMessage('')
    setIsLoading(true)
    setError(null)

    try {
      // Gọi API đến Backend sử dụng chatClient
      const response = await chatClient.sendMessage(userInput, currentSession.id)
      
      const botResponse = { 
        type: 'bot', 
        text: response.response, 
        timestamp: Date.now() 
      }
      
      setCurrentSession(prev => ({
        ...prev,
        messages: [...prev.messages, botResponse]
      }))

      // Lưu vào localStorage
      const updatedSession = {
        ...currentSession,
        messages: [...currentSession.messages, userMessage, botResponse]
      }
      localStorage.setItem(
        `chat_history_${currentSession.id}_${currentSession.id}`,
        JSON.stringify(updatedSession)
      )

    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage = { 
        type: 'bot', 
        text: `❌ Lỗi: ${error.message}. Vui lòng kiểm tra backend có chạy không.`, 
        timestamp: Date.now() 
      }
      setCurrentSession(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage]
      }))
      setError('Không thể kết nối đến server')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleChat = () => setIsOpen(!isOpen)
  const toggleHistory = () => setHistoryOpen(!historyOpen)

  // Position styles
  const positionStyles = {
    'bottom-right': { bottom: 20, right: 20 },
    'bottom-left': { bottom: 20, left: 20 },
  }

  return (
    <>
      <Collapse in={isOpen}>
        <Card
          sx={{
            position: 'fixed',
            ...positionStyles[position],
            // ✅ SỬA LỖI 2: Tăng kích thước KHUNG CHAT TO HƠN
            // Rộng từ 350px -> 450px, Cao từ 500px -> 650px
            width: 450, 
            height: 650, 
            display: 'flex',
            flexDirection: 'column',
            boxShadow: 6,
            borderRadius: 3,
            overflow: 'hidden',
            zIndex: 1000,
          }}
        >
          {/* Header */}
          <CardHeader
            avatar={
              <Avatar sx={{ bgcolor: '#2196f3' }}>
                <SmartToyIcon />
              </Avatar>
            }
            title={
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                Trợ lý SmartFarm AI
              </Typography>
            }
            subheader={
              <Typography variant="caption" color="textSecondary">
                Online
              </Typography>
            }
            action={
              <Stack direction="row" spacing={0.5}>
                <Tooltip title="Lịch sử">
                  <IconButton size="small" onClick={toggleHistory}>
                    <HistoryIcon fontSize="small" sx={{ color: historyOpen ? '#2196f3' : 'inherit' }} />
                  </IconButton>
                </Tooltip>
                <IconButton size="small" onClick={toggleChat}>
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Stack>
            }
            sx={{ p: 2, borderBottom: '1px solid #e0e0e0', backgroundColor: '#fafafa' }}
          />

          {/* Messages Area */}
          <CardContent
            sx={{
              flexGrow: 1,
              overflowY: 'auto',
              p: 2,
              backgroundColor: '#f9f9f9',
              display: 'flex',
              flexDirection: 'column',
              gap: 1.5,
              // Error message styling
              '& .error-message': { color: '#d32f2f', fontWeight: 'bold' },
            }}
          >
            {error && (
              <Paper sx={{ p: 2, backgroundColor: '#ffebee', border: '1px solid #f44336', borderRadius: 2, mb: 1 }}>
                <Typography variant="body2" sx={{ color: '#d32f2f' }}>
                  {error}
                </Typography>
              </Paper>
            )}
            
            {currentSession.messages.length === 0 && !error && (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, color: '#999', textAlign: 'center' }}>
                <SmartToyIcon sx={{ fontSize: 48, mb: 2, opacity: 0.3 }} />
                <Typography variant="body2">
                  Xin chào! Tôi là trợ lý AI của SmartFarm
                  <br />
                  Hỏi tôi về: canh tác, IoT, bệnh cây...
                </Typography>
              </Box>
            )}
              {/* ĐÃ SỬA: Thêm vòng lặp map để render tin nhắn */}
            {currentSession.messages.map((msg, index) => (
              <Box
                key={index}
                sx={{
                  alignSelf: msg.type === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                }}
              >
                <Stack direction="row" spacing={1} alignItems="flex-start" justifyContent={msg.type === 'user' ? 'flex-end' : 'flex-start'}>
                  {msg.type === 'bot' && <Avatar sx={{ width: 28, height: 28, mt: 0.5, bgcolor: '#e3f2fd', color: '#2196f3' }}><SmartToyIcon fontSize="small" /></Avatar>}
                  
                  <Paper
                    elevation={0}
                    sx={{
                      p: '10px 16px',
                      borderRadius: msg.type === 'user' ? '18px 18px 0 18px' : '0 18px 18px 18px',
                      backgroundColor: msg.type === 'user' ? '#2196f3' : '#fff',
                      color: msg.type === 'user' ? 'white' : '#333',
                      border: msg.type === 'user' ? 'none' : '1px solid #e0e0e0',
                      whiteSpace: 'pre-wrap',
                      // Styles cho Markdown rendering
                      '& strong': { fontWeight: 'bold', color: msg.type === 'user' ? 'inherit' : '#1565c0' },
                      '& em': { fontStyle: 'italic' },
                      '& code': { 
                        backgroundColor: msg.type === 'user' ? 'rgba(255,255,255,0.2)' : '#f5f5f5',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontFamily: 'monospace',
                        fontSize: '0.9em'
                      },
                      '& pre': { 
                        backgroundColor: msg.type === 'user' ? 'rgba(255,255,255,0.1)' : '#f5f5f5',
                        padding: '10px',
                        borderRadius: '4px',
                        overflow: 'auto',
                        '& code': {
                          backgroundColor: 'transparent',
                          padding: 0
                        }
                      },
                      '& ul, & ol': { paddingLeft: '20px', marginBottom: '8px' },
                      '& li': { marginBottom: '4px' },
                      '& a': { color: msg.type === 'user' ? 'inherit' : '#2196f3', textDecoration: 'underline' },
                      '& table': { borderCollapse: 'collapse', marginTop: '8px', marginBottom: '8px' },
                      '& th, & td': { border: '1px solid #ccc', padding: '8px', textAlign: 'left' },
                      '& blockquote': { 
                        borderLeft: '4px solid #2196f3',
                        paddingLeft: '12px',
                        marginLeft: 0,
                        opacity: 0.8
                      },
                      '& p': { margin: '4px 0' }
                    }}
                  >
                    {msg.type === 'bot' ? (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.text}
                        </ReactMarkdown>
                    ) : (
                        <Typography variant="body2">{msg.text}</Typography>
                    )}
                    <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.7, textAlign: 'right', fontSize: '0.65rem' }}>
                      {new Date(msg.timestamp).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                  </Paper>
                </Stack>
              </Box>
            ))}

            {isLoading && (
              <Box sx={{ alignSelf: 'flex-start', maxWidth: '80%', ml: 4.5 }}>
                <Paper elevation={0} sx={{ p: '10px 16px', borderRadius: '0 18px 18px 18px', backgroundColor: '#e0e0e0', color: '#555' }}>
                  <Typography variant="body2">Đang suy nghĩ...</Typography>
                </Paper>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </CardContent>

          {/* Input Area */}
          <CardActions sx={{ p: 1.5, borderTop: '1px solid #e0e0e0', backgroundColor: '#fff' }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Hỏi AI về nông trại..."
              size="small"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              disabled={isLoading}
              InputProps={{
                sx: { borderRadius: 4 },
                endAdornment: (
                  <IconButton size="small" onClick={handleSendMessage} disabled={!message.trim() || isLoading} color="primary">
                    <SendIcon fontSize="small" />
                  </IconButton>
                ),
              }}
            />
          </CardActions>
        </Card>
      </Collapse>

      {/* Floating Toggle Button */}
      <Zoom in={true}>
        <Tooltip title={isOpen ? "Đóng chat" : "Trợ lý AI"}>
          <IconButton
            onClick={toggleChat}
            sx={{
              position: 'fixed',
              ...positionStyles[position],
              backgroundColor: '#2196f3',
              color: 'white',
              // ✅ SỬA LỖI 1: Tăng kích thước ICON (Nút bấm) TO HƠN
              // Mặc định là 56x56, tăng lên 70x70
              width: 70, 
              height: 70, 
              '&:hover': {
                backgroundColor: '#1976d2',
              },
              boxShadow: 3,
              zIndex: 1000,
            }}
          >
            {/* ✅ SỬA LỖI 1: Tăng kích thước ICON CHAT TO HƠN */}
            <ChatIcon sx={{ fontSize: 35 }} />
          </IconButton>
        </Tooltip>
      </Zoom>
      
      {/* History Side Panel */}
      <ChatHistory 
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        sessions={sessions}
        currentSessionId={currentSession.id}
        onLoadSession={loadSessionDetails}
        onCreateSession={createNewSession}
        onDeleteSession={deleteSession}
      />
    </>
  )
}

export default ChatBot