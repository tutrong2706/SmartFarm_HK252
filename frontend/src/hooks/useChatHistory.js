/**
 * useChatHistory.js — Enhanced hook for managing chat sessions and history
 * Features: Multiple sessions, session metadata, export, search
 */

import { useState, useCallback, useEffect } from 'react'
import chatClient from '../api/chatClient'

export function useChatHistory(userId = 'default') {
  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState('default')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isConnected, setIsConnected] = useState(false)

  // Load all sessions from localStorage on mount
  useEffect(() => {
    loadAllSessions()
    checkConnection()
  }, [userId])

  // Load all sessions from localStorage
  const loadAllSessions = useCallback(() => {
    try {
      const sessionList = localStorage.getItem(`sessions_${userId}`)
      if (sessionList) {
        const parsed = JSON.parse(sessionList)
        setSessions(parsed.sort((a, b) => b.createdAt - a.createdAt))
        // Load current session
        loadSession(currentSessionId)
      } else {
        // Create default session if none exist
        createSession('default', 'Cuộc trò chuyện mặc định')
      }
    } catch (e) {
      console.error('Failed to load sessions:', e)
      setError('Lỗi tải lịch sử')
    }
  }, [userId, currentSessionId])

  // Load a specific session
  const loadSession = useCallback((sessionId) => {
    try {
      const saved = localStorage.getItem(`chat_history_${userId}_${sessionId}`)
      if (saved) {
        const msgs = JSON.parse(saved)
        setMessages(msgs)
        setCurrentSessionId(sessionId)
      }
    } catch (e) {
      console.error('Failed to load session:', e)
      setError('Lỗi tải phiên')
    }
  }, [userId])

  // Create new session
  const createSession = useCallback((sessionId, title = '') => {
    try {
      const newSession = {
        id: sessionId,
        title: title || `Cuộc trò chuyện ${new Date().toLocaleString('vi-VN')}`,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        messageCount: 0,
      }

      const updated = [...sessions, newSession]
      localStorage.setItem(`sessions_${userId}`, JSON.stringify(updated))
      setSessions(updated)
      loadSession(sessionId)
      return newSession
    } catch (e) {
      console.error('Failed to create session:', e)
      setError('Lỗi tạo phiên')
      return null
    }
  }, [sessions, userId, loadSession])

  // Save message to current session
  const addMessage = useCallback(
    async (text, isUser = true) => {
      if (!text.trim()) return

      if (!isConnected) {
        setError('Không thể kết nối đến server')
        return
      }

      const newUserMessage = {
        id: `msg_${Date.now()}`,
        role: isUser ? 'user' : 'assistant',
        content: text,
        timestamp: new Date().toISOString(),
      }

      // Add user message
      const updatedMessages = [...messages, newUserMessage]
      setMessages(updatedMessages)
      saveMessagesToLocalStorage(updatedMessages)

      if (!isUser) return // If not user message, we're done

      // Call API for response
      setLoading(true)
      try {
        const response = await chatClient.sendMessage(text, currentSessionId)
        const aiMessage = {
          id: `msg_${Date.now()}_ai`,
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString(),
        }

        const finalMessages = [...updatedMessages, aiMessage]
        setMessages(finalMessages)
        saveMessagesToLocalStorage(finalMessages)
        updateSessionMetadata(finalMessages)
        setError(null)
      } catch (err) {
        const errorMessage = {
          id: `msg_${Date.now()}_error`,
          role: 'system',
          content: `❌ Lỗi: ${err.message}`,
          timestamp: new Date().toISOString(),
        }
        const errorMessages = [...updatedMessages, errorMessage]
        setMessages(errorMessages)
        saveMessagesToLocalStorage(errorMessages)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    },
    [messages, currentSessionId, isConnected]
  )

  // Save messages to localStorage
  const saveMessagesToLocalStorage = useCallback(
    (msgs) => {
      try {
        localStorage.setItem(
          `chat_history_${userId}_${currentSessionId}`,
          JSON.stringify(msgs)
        )
      } catch (e) {
        console.error('Failed to save messages:', e)
      }
    },
    [userId, currentSessionId]
  )

  // Update session metadata (timestamp, message count)
  const updateSessionMetadata = useCallback(
    (msgs) => {
      try {
        const updated = sessions.map((s) =>
          s.id === currentSessionId
            ? {
                ...s,
                updatedAt: Date.now(),
                messageCount: msgs.length,
              }
            : s
        )
        localStorage.setItem(`sessions_${userId}`, JSON.stringify(updated))
        setSessions(updated)
      } catch (e) {
        console.error('Failed to update session metadata:', e)
      }
    },
    [sessions, currentSessionId, userId]
  )

  // Delete a session
  const deleteSession = useCallback(
    (sessionId) => {
      try {
        const updated = sessions.filter((s) => s.id !== sessionId)
        localStorage.setItem(`sessions_${userId}`, JSON.stringify(updated))
        localStorage.removeItem(`chat_history_${userId}_${sessionId}`)
        setSessions(updated)

        // Switch to another session if current is deleted
        if (sessionId === currentSessionId && updated.length > 0) {
          loadSession(updated[0].id)
        }
      } catch (e) {
        console.error('Failed to delete session:', e)
        setError('Lỗi xóa phiên')
      }
    },
    [sessions, currentSessionId, userId, loadSession]
  )

  // Export session as JSON
  const exportSession = useCallback(
    (sessionId) => {
      try {
        const session = sessions.find((s) => s.id === sessionId)
        const msgs = JSON.parse(
          localStorage.getItem(`chat_history_${userId}_${sessionId}`) || '[]'
        )

        const data = {
          session,
          messages: msgs,
          exportedAt: new Date().toISOString(),
        }

        const dataStr = JSON.stringify(data, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `chat_${sessionId}_${Date.now()}.json`
        link.click()
        URL.revokeObjectURL(url)
      } catch (e) {
        console.error('Failed to export session:', e)
        setError('Lỗi xuất file')
      }
    },
    [sessions, userId]
  )

  // Clear all sessions
  const clearAllSessions = useCallback(() => {
    try {
      // Get all session IDs
      const sessionList = localStorage.getItem(`sessions_${userId}`)
      if (sessionList) {
        const parsed = JSON.parse(sessionList)
        // Remove all chat histories
        parsed.forEach((s) => {
          localStorage.removeItem(`chat_history_${userId}_${s.id}`)
        })
      }
      // Remove sessions list
      localStorage.removeItem(`sessions_${userId}`)
      setSessions([])
      setMessages([])
      setCurrentSessionId('default')
      createSession('default', 'Cuộc trò chuyện mặc định')
    } catch (e) {
      console.error('Failed to clear all sessions:', e)
      setError('Lỗi xóa tất cả')
    }
  }, [userId, createSession])

  // Check backend connection
  const checkConnection = useCallback(async () => {
    try {
      await chatClient.getHealth()
      setIsConnected(true)
      setError(null)
    } catch (err) {
      setIsConnected(false)
      setError('Không thể kết nối đến server')
    }
  }, [])

  // Search messages
  const searchMessages = useCallback(
    (query) => {
      const lowerQuery = query.toLowerCase()
      return messages.filter((msg) =>
        msg.content.toLowerCase().includes(lowerQuery)
      )
    },
    [messages]
  )

  // Get session statistics
  const getStatistics = useCallback(() => {
    return {
      totalSessions: sessions.length,
      totalMessages: messages.length,
      userMessages: messages.filter((m) => m.role === 'user').length,
      aiMessages: messages.filter((m) => m.role === 'assistant').length,
      currentSessionDuration: messages.length > 0
        ? new Date(messages[messages.length - 1].timestamp) -
          new Date(messages[0].timestamp)
        : 0,
    }
  }, [sessions, messages])

  return {
    // State
    sessions,
    currentSessionId,
    messages,
    loading,
    error,
    isConnected,

    // Actions
    createSession,
    loadSession,
    addMessage,
    deleteSession,
    clearAllSessions,
    exportSession,
    searchMessages,
    getStatistics,
    checkConnection,
  }
}

export default useChatHistory
