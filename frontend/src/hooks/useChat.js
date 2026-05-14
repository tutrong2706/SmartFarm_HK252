/**
 * useChat.js — Custom hook for chat state management
 * Manages messages, loading state, and API interactions
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import chatClient from '../api/chatClient'

export function useChat(sessionId = 'default') {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const messagesEndRef = useRef(null)

  // Load messages from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(`chat_history_${sessionId}`)
    if (saved) {
      try {
        setMessages(JSON.parse(saved))
      } catch (e) {
        console.error('Failed to load saved messages:', e)
      }
    }
    // Check backend health
    checkConnection()
  }, [sessionId])

  // Auto-scroll to latest message
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Check if backend is available
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

  // Send a message
  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim()) return
      if (!isConnected) {
        setError('Không thể kết nối đến server')
        return
      }

      // Add user message immediately
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, userMessage])
      setLoading(true)
      setError(null)

      try {
        // Get AI response
        const result = await chatClient.sendMessage(text, sessionId)

        // Add AI response
        const aiMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: result.response,
          timestamp: result.timestamp,
        }

        setMessages((prev) => {
          const updated = [...prev, aiMessage]
          // Save to localStorage
          localStorage.setItem(`chat_history_${sessionId}`, JSON.stringify(updated))
          return updated
        })
      } catch (err) {
        setError(err.message || 'Đã xảy ra lỗi')
        // Keep user message but add error
        const errorMessage = {
          id: Date.now() + 1,
          role: 'system',
          content: `Lỗi: ${err.message || 'Không thể nhận phản hồi'}`,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setLoading(false)
      }
    },
    [sessionId, isConnected]
  )

  // Clear conversation
  const clearMessages = useCallback(async () => {
    try {
      await chatClient.clearHistory(sessionId)
      setMessages([])
      localStorage.removeItem(`chat_history_${sessionId}`)
      setError(null)
    } catch (err) {
      setError('Không thể xóa lịch sử')
    }
  }, [sessionId])

  return {
    messages,
    loading,
    error,
    isConnected,
    sendMessage,
    clearMessages,
    messagesEndRef,
    checkConnection,
  }
}

export default useChat
