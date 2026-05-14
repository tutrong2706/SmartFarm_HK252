/**
 * chatClient.js — API client for SmartFarm AI Chatbot
 * Handles all communication with backend chat endpoints
 */

const API_BASE_URL = 'http://localhost:8000'

export const chatClient = {
  /**
   * Send a chat message to the backend
   * @param {string} message - User message
   * @param {string} sessionId - Session ID (optional, defaults to 'default')
   * @returns {Promise<{response: string, sessionId: string, timestamp: string}>}
   */
  async sendMessage(message, sessionId = 'default') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return {
        response: data.response,
        sessionId: data.session_id,
        timestamp: data.timestamp,
      }
    } catch (error) {
      console.error('Chat API error:', error)
      throw error
    }
  },

  /**
   * Get chat health status
   * @returns {Promise<{status: string}>}
   */
  async getHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/health`)
      return await response.json()
    } catch (error) {
      console.error('Health check error:', error)
      throw error
    }
  },

  /**
   * Clear chat history for a session
   * @param {string} sessionId - Session ID to clear
   * @returns {Promise<{success: boolean}>}
   */
  async clearHistory(sessionId = 'default') {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/chat/history/${sessionId}`,
        { method: 'DELETE' }
      )
      return await response.json()
    } catch (error) {
      console.error('Clear history error:', error)
      throw error
    }
  },

  /**
   * Query database directly with explanation
   * @param {string} question - SQL query question
   * @param {boolean} includeExplanation - Include AI explanation
   * @returns {Promise<{success: boolean, queryResult: string, aiExplanation: string}>}
   */
  async queryDatabase(question, includeExplanation = true) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          include_ai_explanation: includeExplanation,
        }),
      })
      return await response.json()
    } catch (error) {
      console.error('Query error:', error)
      throw error
    }
  },

  /**
   * Get database schema
   * @returns {Promise<{schema: string}>}
   */
  async getSchema() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/query/schema`)
      return await response.json()
    } catch (error) {
      console.error('Schema error:', error)
      throw error
    }
  },

  /**
   * Retrieve relevant documents from RAG system
   * @param {string} query - Search query
   * @param {number} k - Number of documents to retrieve
   * @returns {Promise<{success: boolean, documents: Array}>}
   */
  async retrieveDocuments(query, k = 3) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/retrieve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, k }),
      })
      return await response.json()
    } catch (error) {
      console.error('RAG retrieval error:', error)
      throw error
    }
  },

  /**
   * Check RAG system status
   * @returns {Promise<{status: string, documentCount: number}>}
   */
  async ragStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/status`)
      return await response.json()
    } catch (error) {
      console.error('RAG status error:', error)
      throw error
    }
  },
}

export default chatClient
