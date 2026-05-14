/**
 * ChatHistory.jsx — Chat history panel for viewing and managing sessions
 * Features: Session list, search, export, delete, session switching
 */

import { useState } from 'react'
import {
  Box,
  Drawer,
  TextField,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Divider,
  Tooltip,
  Paper,
  Stack,
  InputAdornment,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import DownloadIcon from '@mui/icons-material/Download'
import SearchIcon from '@mui/icons-material/Search'
import AddIcon from '@mui/icons-material/Add'
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep'
import HistoryIcon from '@mui/icons-material/History'

export function ChatHistory({
  sessions,
  currentSessionId,
  onLoadSession,
  onCreateSession,
  onDeleteSession,
  onExportSession,
  onClearAll,
}) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [sessionToDelete, setSessionToDelete] = useState(null)
  const [clearAllConfirmOpen, setClearAllConfirmOpen] = useState(false)

  // Filter sessions by search query
  const filteredSessions = sessions.filter(
    (s) =>
      s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Format date
  const formatDate = (timestamp) => {
    const date = new Date(timestamp)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Hôm qua'
    } else {
      return date.toLocaleDateString('vi-VN')
    }
  }

  // Handle new session
  const handleNewSession = () => {
    const sessionId = `session_${Date.now()}`
    const title = `Cuộc trò chuyện ${new Date().toLocaleString('vi-VN')}`
    onCreateSession(sessionId, title)
    onLoadSession(sessionId)
    setOpen(false)
  }

  // Handle delete session
  const handleDeleteSession = (sessionId) => {
    setSessionToDelete(sessionId)
    setDeleteConfirmOpen(true)
  }

  const confirmDelete = () => {
    if (sessionToDelete) {
      onDeleteSession(sessionToDelete)
      setDeleteConfirmOpen(false)
      setSessionToDelete(null)
    }
  }

  // Handle clear all
  const handleClearAll = () => {
    setClearAllConfirmOpen(true)
  }

  const confirmClearAll = () => {
    onClearAll()
    setClearAllConfirmOpen(false)
    setOpen(false)
  }

  return (
    <>
      {/* History Drawer */}
      <Drawer
        anchor="left"
        open={open}
        onClose={() => setOpen(false)}
        PaperProps={{
          sx: {
            width: 350,
            backgroundColor: '#f5f5f5',
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          {/* Header */}
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
            <HistoryIcon sx={{ color: '#2196f3', fontSize: 24 }} />
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Lịch sử trò chuyện
            </Typography>
          </Stack>

          {/* New Session Button */}
          <Button
            fullWidth
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleNewSession}
            sx={{ mb: 2, backgroundColor: '#2196f3' }}
          >
            Cuộc trò chuyện mới
          </Button>

          <Divider sx={{ mb: 2 }} />

          {/* Search Field */}
          <TextField
            fullWidth
            placeholder="Tìm kiếm..."
            size="small"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: '#999' }} />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />

          {/* Sessions List */}
          <List sx={{ maxHeight: 'calc(100vh - 350px)', overflow: 'auto' }}>
            {filteredSessions.length > 0 ? (
              filteredSessions.map((session) => (
                <Paper
                  key={session.id}
                  sx={{
                    mb: 1,
                    backgroundColor:
                      currentSessionId === session.id ? '#e3f2fd' : '#fff',
                    border:
                      currentSessionId === session.id
                        ? '2px solid #2196f3'
                        : '1px solid #e0e0e0',
                  }}
                >
                  <ListItem
                    secondaryAction={
                      <Stack direction="row" spacing={0.5}>
                        <Tooltip title="Xuất">
                          <IconButton
                            edge="end"
                            size="small"
                            onClick={() => onExportSession(session.id)}
                            sx={{ color: '#4caf50' }}
                          >
                            <DownloadIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Xóa">
                          <IconButton
                            edge="end"
                            size="small"
                            onClick={() => handleDeleteSession(session.id)}
                            sx={{ color: '#f44336' }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    }
                    disablePadding
                  >
                    <ListItemButton
                      onClick={() => {
                        onLoadSession(session.id)
                        setOpen(false)
                      }}
                      sx={{ flexDirection: 'column', alignItems: 'flex-start', p: 1.5 }}
                    >
                      <ListItemText
                        primary={
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {session.title}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5 }}>
                            <Typography variant="caption" sx={{ color: '#666' }}>
                              {formatDate(session.updatedAt)} • {session.messageCount} tin nhắn
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                </Paper>
              ))
            ) : (
              <Typography variant="body2" color="textSecondary" align="center">
                {searchQuery ? 'Không tìm thấy phiên nào' : 'Chưa có phiên nào'}
              </Typography>
            )}
          </List>

          <Divider sx={{ my: 2 }} />

          {/* Clear All Button */}
          {sessions.length > 1 && (
            <Button
              fullWidth
              variant="outlined"
              color="error"
              startIcon={<DeleteSweepIcon />}
              onClick={handleClearAll}
              size="small"
            >
              Xóa tất cả
            </Button>
          )}
        </Box>
      </Drawer>

      {/* History Icon Button */}
      <Tooltip title="Lịch sử trò chuyện">
        <IconButton
          onClick={() => setOpen(true)}
          sx={{
            position: 'fixed',
            bottom: 30,
            left: 30,
            backgroundColor: '#2196f3',
            color: 'white',
            '&:hover': {
              backgroundColor: '#1976d2',
            },
            zIndex: 999,
          }}
        >
          <HistoryIcon />
        </IconButton>
      </Tooltip>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onClose={() => setDeleteConfirmOpen(false)}>
        <DialogTitle>Xóa phiên trò chuyện?</DialogTitle>
        <DialogContent>
          <Typography>
            Bạn có chắc chắn muốn xóa phiên này? Hành động này không thể hoàn tác.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Hủy</Button>
          <Button onClick={confirmDelete} variant="contained" color="error">
            Xóa
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clear All Confirmation Dialog */}
      <Dialog open={clearAllConfirmOpen} onClose={() => setClearAllConfirmOpen(false)}>
        <DialogTitle>Xóa tất cả phiên trò chuyện?</DialogTitle>
        <DialogContent>
          <Typography>
            Bạn có chắc chắn muốn xóa tất cả phiên trò chuyện? Hành động này không thể hoàn tác.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClearAllConfirmOpen(false)}>Hủy</Button>
          <Button onClick={confirmClearAll} variant="contained" color="error">
            Xóa tất cả
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default ChatHistory