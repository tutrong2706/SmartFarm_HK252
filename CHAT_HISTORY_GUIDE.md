# 💾 Chat History Feature Guide

## Overview

The SmartFarm AI Chatbot now includes a **comprehensive chat history management system** that allows you to:

✅ Save all chat conversations automatically  
✅ Organize chats into multiple sessions  
✅ Switch between previous conversations  
✅ Search chat history  
✅ Export conversations as JSON  
✅ Delete individual sessions or all history  
✅ View session metadata (timestamp, message count)  

---

## How It Works

### **Automatic Saving**
Every message sent and received is automatically saved to the browser's `localStorage`:

```
localStorage Key: chat_history_{userId}_{sessionId}
Format: JSON array of message objects with:
  - id: Unique message ID
  - role: 'user' | 'assistant' | 'system'
  - content: Message text
  - timestamp: ISO 8601 timestamp
```

### **Session Management**
Each chat session is tracked with metadata:

```json
{
  "id": "session_1234567890",
  "title": "Cuộc trò chuyện May 13, 2026",
  "createdAt": 1715592000000,
  "updatedAt": 1715592060000,
  "messageCount": 25
}
```

---

## Using Chat History

### **Access History Panel**

1. **Click the History Icon** 📋
   - Located at bottom-left corner (fixed position)
   - Blue button with clock icon
   - Shows list of all past conversations

2. **Left Drawer Opens**
   - Shows all sessions sorted by most recent first
   - Search bar to filter sessions
   - Session metadata (date, message count)

### **Switch Between Sessions**

```
1. Open History Panel (📋 icon)
2. Click on any session title
3. Chat window updates with that session's messages
4. Can continue conversation or view history
```

### **Create New Session**

```
1. Open History Panel (📋 icon)
2. Click "Cuộc trò chuyện mới" (New Conversation)
3. New empty session created
4. Chat window ready for new messages
```

### **Search Sessions**

```
1. Open History Panel (📋 icon)
2. Type in search field
3. Filters sessions by title or ID
4. Results update in real-time
```

### **Export Session**

```
1. Open History Panel (📋 icon)
2. Find session to export
3. Click Download icon (💾)
4. JSON file downloaded with:
   - Session metadata
   - All messages
   - Export timestamp
```

### **Delete Session**

```
1. Open History Panel (📋 icon)
2. Find session to delete
3. Click Delete icon (🗑️)
4. Confirm in dialog
5. Session removed (cannot undo)
```

### **Clear All Sessions**

```
1. Open History Panel (📋 icon)
2. If multiple sessions exist, see "Xóa tất cả" button
3. Click "Xóa tất cả" (Delete All)
4. Confirm in dialog
5. All sessions cleared
6. New default session created
```

---

## File Structure

### **New Files Created**

#### `frontend/src/hooks/useChatHistory.js` (260+ lines)
Custom React hook for chat history management:

```javascript
// Usage
const {
  sessions,           // Array of all sessions
  currentSessionId,   // Current session ID
  messages,           // Current session messages
  loading,            // Is request loading
  error,              // Error message if any
  isConnected,        // Is backend connected
  
  // Actions
  createSession,      // (sessionId, title) => create new
  loadSession,        // (sessionId) => load session
  addMessage,         // (text) => send message
  deleteSession,      // (sessionId) => delete
  clearAllSessions,   // () => delete all
  exportSession,      // (sessionId) => download JSON
  searchMessages,     // (query) => filter messages
  getStatistics,      // () => get stats
  checkConnection,    // () => verify backend
} = useChatHistory('default')
```

**Key Features:**
- Loads all sessions from localStorage on mount
- Persists messages automatically
- Saves session metadata (timestamps, message counts)
- Handles API calls with error catching
- Graceful degradation if backend disconnected

#### `frontend/src/components/ChatHistory.jsx` (250+ lines)
React component for history UI:

**Components Included:**
- `<Drawer>` - Left sidebar with session list
- `<TextField>` - Search sessions
- `<List>` - Session list with click handlers
- `<Dialog>` - Confirmation dialogs
- History icon button (floating)
- Export/delete action buttons
- Session metadata display

---

## Data Storage

### **localStorage Keys**

```javascript
// All sessions metadata
localStorage.getItem('sessions_default')
// Returns JSON array of session objects

// Messages for specific session
localStorage.getItem('chat_history_default_session_1234567890')
// Returns JSON array of message objects

// Example structure:
{
  "id": "msg_1234567890",
  "role": "user",
  "content": "Nên set nhiệt độ táo là bao nhiêu?",
  "timestamp": "2026-05-13T17:54:00.000Z"
}
```

### **Storage Limits**

⚠️ **Note**: localStorage has ~5-10MB limit per domain

**Approximate Capacity:**
- ~1000 messages per session (100KB)
- ~100 sessions max (depends on message count)
- Each message ≈ 100-500 bytes

**When Storage Full:**
- Cannot save new messages
- Error displayed in chat
- Export and delete to free space

---

## Integration with ChatBot Component

### **Updated ChatBot.jsx**

```jsx
import useChatHistory from '../hooks/useChatHistory'
import ChatHistory from './ChatHistory'

export default function ChatBot({ position = 'bottom-right' }) {
  const {
    sessions,
    currentSessionId,
    messages,
    loading,
    error,
    isConnected,
    addMessage,
    createSession,
    loadSession,
    deleteSession,
    exportSession,
    clearAllSessions,
  } = useChatHistory('default')

  // ... chat logic ...

  return (
    <>
      {/* Chat bubble and window */}
      {/* ... existing code ... */}

      {/* Chat History Panel */}
      <ChatHistory
        sessions={sessions}
        currentSessionId={currentSessionId}
        onLoadSession={loadSession}
        onCreateSession={createSession}
        onDeleteSession={deleteSession}
        onExportSession={exportSession}
        onClearAll={clearAllSessions}
      />
    </>
  )
}
```

---

## API Integration

### **Session Storage Strategy**

```
Browser Storage (localStorage)
├── Sessions Metadata
│   └── List of all session objects
├── Chat History #1
│   └── Messages for session 1
├── Chat History #2
│   └── Messages for session 2
└── Chat History #N
    └── Messages for session N

Backend (API)
└── Response saved to current session
    └── Persisted to localStorage
```

### **Message Flow**

```
User Input
    ↓
addMessage() Hook
    ├→ Add user message to state
    ├→ Save to localStorage
    ├→ Call chatClient.sendMessage()
    │   └→ API /api/chat endpoint
    ├→ Receive AI response
    ├→ Add AI message to state
    ├→ Save to localStorage
    └→ Update session metadata
```

---

## Exported JSON Format

When you export a session, you get a JSON file with this structure:

```json
{
  "session": {
    "id": "session_1234567890",
    "title": "Cuộc trò chuyện May 13, 2026",
    "createdAt": 1715592000000,
    "updatedAt": 1715592060000,
    "messageCount": 25
  },
  "messages": [
    {
      "id": "msg_1234567890",
      "role": "user",
      "content": "Xin chào",
      "timestamp": "2026-05-13T17:54:00.000Z"
    },
    {
      "id": "msg_1234567891",
      "role": "assistant",
      "content": "Xin chào! Tôi là trợ lý AI SmartFarm. Có gì tôi có thể giúp bạn?",
      "timestamp": "2026-05-13T17:54:05.000Z"
    }
    // ... more messages ...
  ],
  "exportedAt": "2026-05-13T17:55:00.000Z"
}
```

**Use Cases:**
- Backup important conversations
- Share conversation with team
- Archive for compliance
- Analyze conversation patterns

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message (in chat input) |
| `Shift+Enter` | New line in message |
| `Ctrl+H` | Open history (if implemented) |

---

## Troubleshooting

### **Problem: Chats not saving**

**Solution:**
1. Check browser storage not full:
   - Open DevTools → Application → localStorage
   - Check `sessions_default` and `chat_history_*` keys
2. Clear old sessions:
   - Open History panel
   - Delete unused sessions
   - Try again

### **Problem: Lost chat history**

**Prevention:**
- Export important conversations regularly
- Browser localStorage ≠ device sync
- Clearing browser cache deletes localStorage

**Recovery:**
- Check if JSON export files exist
- Contact system administrator
- Cannot recover deleted localStorage

### **Problem: Storage full error**

**Solution:**
1. Open History panel
2. Export old sessions (if needed)
3. Delete old sessions
4. Retry sending message

### **Problem: Session won't switch**

**Solution:**
1. Close and reopen history panel
2. Check browser console for errors
3. Refresh page
4. Check localStorage isn't corrupted

---

## Best Practices

### **Organizing Conversations**

1. **Use meaningful session titles**
   - Rename sessions about specific topics
   - Example: "Apple Cultivation Queries" instead of generic time-based name

2. **Regular exports**
   - Export important conversations weekly
   - Keep JSON files in secure location
   - Document which export is which

3. **Clean up periodically**
   - Delete irrelevant sessions
   - Maintain last 20-30 active sessions
   - Prevents storage bloat

### **Data Management**

```
Good Practices:
✅ Export before deleting
✅ Search to find old chats
✅ Use descriptive titles
✅ Regular cleanup

Avoid:
❌ Never force clear localStorage directly
❌ Don't delete without exporting
❌ Avoid duplicate session creation
❌ Don't store sensitive data expecting privacy
```

---

## Technical Implementation Details

### **useChatHistory Hook Features**

```javascript
// Session persistence
localStorage.setItem(`sessions_${userId}`, JSON.stringify(sessions))

// Message persistence per session
localStorage.setItem(
  `chat_history_${userId}_${sessionId}`,
  JSON.stringify(messages)
)

// Auto-update metadata when messages added
updateSessionMetadata(messages) → updates updatedAt and messageCount

// Search in current session
searchMessages(query) → filters by content

// Statistics
getStatistics() → returns totals and duration
```

### **Memory Optimization**

- Messages loaded on session switch (not all at once)
- Sessions list kept in state (typically < 100 items)
- Each session lazy-loads messages from localStorage
- Drawer can handle 1000+ sessions (with virtualization possible)

---

## Future Enhancements

Potential improvements (not yet implemented):

- [ ] Cloud sync across devices
- [ ] Elasticsearch integration for full-text search
- [ ] Database backend for unlimited storage
- [ ] Conversation tags/categories
- [ ] Pinned favorite conversations
- [ ] Share conversation links
- [ ] Conversation templates
- [ ] Analytics dashboard
- [ ] Bulk export/import
- [ ] Auto-archive old conversations

---

## Summary

The **Chat History system** provides:

| Feature | Benefit |
|---------|---------|
| Auto-save | Never lose a conversation |
| Multiple sessions | Organize by topic |
| Search | Find past conversations quickly |
| Export | Backup and share |
| Delete | Manage storage |
| Metadata | Track conversation info |
| Responsive UI | Easy to use |

**Quick Access:**
- Click 📋 icon (bottom-left) to open history
- All features accessible from one drawer panel
- Smooth integration with existing chatbot

---

**Status**: ✅ IMPLEMENTED & READY TO USE

Need help? Check the COMPLETE_AI_CHATBOT_GUIDE.md for system overview.
