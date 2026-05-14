# 🎨 Chat History Feature - Visual Guide

## Screen Layout

### **Main Chat Interface**

```
┌─────────────────────────────────────────────────────┐
│ SmartFarm Dashboard                          [User]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [Zones] [Devices] [Crop Settings] [...]           │
│                                                      │
│                                                      │
│     Main Content Area                               │
│                                                      │
│                                                      │
│                                                      │
│                                                      │
│          ┌──────────────────────┐                   │
│          │  SmartFarm AI        │                   │
│          │  [Messages...]       │                   │
│          │  [Input Field]       │ [Send]            │
│          └──────────────────────┘                   │
│                                                      │
│                                                      │
│    📋 History Icon (bottom-left)                   │
│    💬 Chat Bubble (bottom-right)                   │
└─────────────────────────────────────────────────────┘
```

---

## 1️⃣ Closed Chat Widget

```
┌─────────────────────────────────────┐
│                          💬          │  ← Floating bubble
│                                      │     Click to open
│                                      │
│   📋                                 │  ← History icon
│                                      │
└─────────────────────────────────────┘
```

**Appearance:**
- Green circle with chat icon (💬)
- Blue circle with history icon (📋)
- Fixed positions
- Always visible

---

## 2️⃣ Open Chat Window

```
┌─────────────────────────────────────┐
│ SmartFarm AI     [●Sẵn sàng]   ✕   │  Header
├─────────────────────────────────────┤
│  "Xin chào! Tôi là..."              │
│                                      │  Messages Area
│  User: "Nên set temp..."            │
│  AI: "Nhiệt độ tối ưu cho..."      │
│                                      │
│                                      │
│                                      │
├─────────────────────────────────────┤
│ [Input field...]              [→]   │  Input Area
└─────────────────────────────────────┘
     ↑                              ↑
     └── Typing area          Send button
```

---

## 3️⃣ History Panel - Closed State

```
┌─────────────────────────────────────┐
│    📋                                │  History icon
│  (Floating button)                   │
│                                      │
│    Click to open                     │
│                                      │
└─────────────────────────────────────┘
```

---

## 4️⃣ History Panel - Opened State

```
┌──────────────────────────────────────────────┬─────────────────────┐
│ SmartFarm Dashboard                          │ 📋 Lịch sử trò chuyện │
│                                              ├──────────────────────┤
│  Main Content                                │ [+ Cuộc trò chuyện mới]
│                                              │ [🔍 Tìm kiếm...]     │
│                                              │ ────────────────────  │
│                                              │                       │
│                                              │ ┌─────────────────┐   │
│                                              │ │ Cuộc trò chuyện │💾🗑│
│                                              │ │ May 13, 17:54   │   │
│                                              │ │ 25 tin nhắn     │   │
│                                              │ └─────────────────┘   │
│                                              │                       │
│                                              │ ┌─────────────────┐   │
│                                              │ │ Câu hỏi Rau cà │💾🗑│
│                                              │ │ chua            │   │
│                                              │ │ May 13, 15:20   │   │
│                                              │ │ 12 tin nhắn     │   │
│                                              │ └─────────────────┘   │
│                                              │                       │
│                                              │ ┌─────────────────┐   │
│                                              │ │ Config Sensor   │💾🗑│
│                                              │ │ May 12, 14:10   │   │
│                                              │ │ 8 tin nhắn      │   │
│                                              │ └─────────────────┘   │
│                                              │                       │
│                                              │ ────────────────────  │
│                                              │ [🗑️ Xóa tất cả]       │
│                                              │                       │
└──────────────────────────────────────────────┴─────────────────────┘
  ↑                                                 ↑
  Main dashboard content                     History panel (350px)
```

---

## 5️⃣ Workflow Examples

### **Workflow 1: Switch Between Conversations**

```
Step 1: User chatting about apples
  ┌────────────────┐
  │ Q: Nhiệt độ?   │
  │ A: 15-20°C...  │
  └────────────────┘

Step 2: Click 📋 icon
  ┌────────────────┐     ┌──────────────────┐
  │ Q: Nhiệt độ?   │     │ Cuộc 1: Táo ✓   │
  │ A: 15-20°C...  │────→│ Cuộc 2: Dưa     │
  └────────────────┘     │ Cuộc 3: Cà chua │
                         └──────────────────┘

Step 3: Click on "Cuộc 2: Dưa"
  ┌────────────────┐
  │ Q: Độ ẩm?      │
  │ A: 70-80%...   │
  └────────────────┘
  (Messages from Cucumber session loaded)
```

---

### **Workflow 2: Export Conversation**

```
Step 1: Open History (📋)
  ┌──────────────────┐
  │ Cuộc trò chuyện  │💾 ← Click here
  │ May 13, 17:54    │
  │ 25 tin nhắn      │
  └──────────────────┘

Step 2: JSON downloaded
  💻 Desktop/Downloads/
  └── chat_session_1715592000000.json

Step 3: File contains
  {
    "session": {...},
    "messages": [...],
    "exportedAt": "..."
  }
```

---

### **Workflow 3: Delete & Clean Up**

```
Option A: Delete One Session
  ┌──────────────────┐
  │ Old Session      │🗑️ ← Click delete
  │ May 01           │
  └──────────────────┘
  Dialog: "Xóa phiên?" [Cancel] [Xóa]

Option B: Delete All
  [🗑️ Xóa tất cả]  ← At bottom of panel
  Dialog: "Xóa tất cả?" [Cancel] [Xóa tất cả]
```

---

## 6️⃣ Session List - Color Coding

```
Current Session (Blue highlight):
┌─────────────────────────────┐
│ ██████████████████████████ │  ← Light blue background
│ Cuộc trò chuyện Hiện tại   │     Blue border (2px)
│ May 13, 17:54 • 25 messages│
└─────────────────────────────┘

Inactive Session (Gray):
┌─────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░ │  ← White background
│ Cuộc trò chuyện Khác       │     Light gray border
│ May 12, 14:20 • 12 messages│
└─────────────────────────────┘
```

---

## 7️⃣ Message Display Timeline

```
Timeline of a Session:

17:54:00 ┌─ User: "Xin chào"
         │
17:54:05 ├─ AI: "Xin chào! Tôi là..."
         │
17:54:15 ├─ User: "Nên set nhiệt độ táo?"
         │
17:54:22 ├─ AI: "Nhiệt độ tối ưu..."
         │
17:54:30 ├─ User: "Còn cà chua?"
         │
17:54:45 └─ AI: "Cà chua cần..."

localStorage: chat_history_default_session_12345
[
  {id: msg_1, role: "user", content: "...", timestamp: "17:54:00"},
  {id: msg_2, role: "assistant", content: "...", timestamp: "17:54:05"},
  ...
]
```

---

## 8️⃣ Storage Structure Diagram

```
┌─────────────────────────────────────────────────┐
│              Browser localStorage               │
├─────────────────────────────────────────────────┤
│                                                  │
│  KEY: sessions_default                         │
│  VALUE: [                                       │
│    {id: session_1, title: "...", ...},         │
│    {id: session_2, title: "...", ...},         │
│  ]                                              │
│                                                  │
│  KEY: chat_history_default_session_1           │
│  VALUE: [                                       │
│    {id: msg_1, role: "user", content: "..."},  │
│    {id: msg_2, role: "assistant", ...},        │
│  ]                                              │
│                                                  │
│  KEY: chat_history_default_session_2           │
│  VALUE: [                                       │
│    {id: msg_1, role: "user", content: "..."},  │
│    {id: msg_2, role: "assistant", ...},        │
│  ]                                              │
│                                                  │
└─────────────────────────────────────────────────┘
        ↑
    Auto-managed by useChatHistory hook
```

---

## 9️⃣ User Interaction Flow

```
                    ┌─────────────────┐
                    │  User Opens App │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Load Sessions  │
                    │  from Storage   │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼──────┐    ┌──────▼────────┐    ┌───▼──────┐
    │ Chat       │    │ History Panel │    │ Export   │
    │ Widget     │    │ (Click 📋)    │    │ (💾)    │
    │            │    │               │    │          │
    │ Send msg   │    │ Search        │    │ Download │
    │ (Enter)    │    │ Switch        │    │ JSON     │
    │            │    │ Delete        │    │          │
    │ Show msgs  │    │ Create new    │    │          │
    └──────┬─────┘    └───────────────┘    └──────────┘
           │
    ┌──────▼──────────────┐
    │ Save to localStorage│
    │ Update metadata     │
    └─────────────────────┘
```

---

## 🔟 Feature Comparison

### **Before vs After**

```
BEFORE Chat History:
┌──────────────────────────────────┐
│ Single Session Only              │
│ • Messages in one window         │
│ • Clear history = restart        │
│ • Can't switch conversations     │
│ • No search capability           │
│ • Can't backup chats             │
└──────────────────────────────────┘

AFTER Chat History:
┌──────────────────────────────────┐
│ Multiple Sessions                │
│ ✅ Many separate conversations  │
│ ✅ Clear individual sessions    │
│ ✅ Switch with 1 click          │
│ ✅ Search past messages         │
│ ✅ Export for backup            │
│ ✅ Session metadata             │
│ ✅ Beautiful history UI         │
└──────────────────────────────────┘
```

---

## Summary Visual

```
          Chat History Feature
               Overview
                 │
    ┌────────────┼────────────┐
    │            │            │
  Auto-save   Organize      Manage
    │            │            │
    ├─ Every     ├─ Multiple  ├─ Delete
    │  message   │  sessions  │  individual
    │            │            │
    ├─ To        ├─ By topic  ├─ Delete
    │  localStorage         all
    │            │            │
    └─ With      ├─ Switch    ├─ Export
       timestamp │  easily    │  to JSON
                 │            │
                 └─ Search    └─ See
                    messages     metadata
```

---

**Icon Meanings:**
- 💬 = Chat (open chatbot)
- 📋 = History (open panel)
- 🔍 = Search
- ➕ = Create new
- 💾 = Export/Download
- 🗑️ = Delete
- ✕ = Close

---

For step-by-step usage, see **CHAT_HISTORY_GUIDE.md**
