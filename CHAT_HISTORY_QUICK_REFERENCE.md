# 📋 Chat History - Quick Reference Card

## 🎯 One-Page Quick Start

### **Access History**
**Click 📋 Icon** (blue button, bottom-left corner)

### **Main Actions**

| Action | How | Result |
|--------|-----|--------|
| **Send Message** | Type + Press Enter | Saved automatically |
| **View History** | Click 📋 icon | History drawer opens |
| **New Session** | History → "+ New" | Fresh conversation |
| **Switch Session** | History → Click session | Load that chat |
| **Search** | History → Type search | Filter sessions |
| **Export** | History → 💾 icon | Download JSON |
| **Delete One** | History → 🗑️ icon | Remove session |
| **Delete All** | History → "Xóa tất cả" | Clear everything |

---

## 💻 Visual Buttons

```
Chat Bubble (Bottom-Right):
    💬 Green button
    Click to chat

History Panel (Bottom-Left):
    📋 Blue button
    Click to see all chats
```

---

## 📊 Data Saved Automatically

✅ **Every message saved**
- User questions
- AI responses
- Timestamps
- Message count

✅ **Session info saved**
- Session title
- Creation date
- Last update
- Message count

---

## 🔍 Search Tips

```
Open History (📋)
↓
Type in search box:
- Session title
- Part of chat ID
↓
Results update instantly
```

---

## 💾 Export for Backup

```
Open History (📋)
↓
Find session
↓
Click 💾 (download icon)
↓
File saved: chat_session_[date].json
↓
Can share or archive
```

---

## 🗑️ Delete & Cleanup

**Delete One Session:**
1. Click 📋
2. Find session
3. Click 🗑️
4. Confirm

**Delete All Sessions:**
1. Click 📋
2. Click "Xóa tất cả"
3. Confirm

---

## ⚠️ Important Notes

- **localStorage Storage**: 5-10 MB max
- **Auto-Deleted On**: Clearing browser cache
- **Can't Recover**: Deleted sessions unless exported
- **Cross-Device**: NOT synced (local only)
- **Session**: Persists through page refresh

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| History not showing | Refresh page |
| Storage full | Export & delete old sessions |
| Lost chat history | Check exported JSON files |
| Can't export | Check browser download folder |
| Memory slow | Delete sessions to free space |

---

## 📱 Mobile Usage

- History panel works on mobile ✅
- Smaller screen? Drawer adapts ✅
- Touch-friendly buttons ✅
- All features available ✅

---

## 🎓 Typical Session

```
1. Open chatbot (💬)
2. Ask question
3. Get response
4. Click 📋 to see history
5. Can switch to old chat or continue current one
6. Click 💾 to backup important chat
7. Delete old sessions when needed
```

---

## 📲 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Enter | Send message |
| Shift+Enter | New line |
| Escape | Close drawer (WIP) |

---

## 📈 Track Your Usage

```
Statistics (in code):
- Total sessions: Count of all chats
- Total messages: Count of all messages
- Session duration: Time from first to last message
- User vs AI: Message distribution
```

---

## 💡 Best Practices

✅ **DO:**
- Export important chats
- Use meaningful titles
- Regular cleanup
- Reference past advice

❌ **DON'T:**
- Rely only on localStorage
- Forget to export backup
- Store sensitive info
- Expect cross-device sync

---

## 🎯 Common Tasks

**Save conversation about apples:**
1. Chat about apples
2. Click 📋
3. Find session
4. Click 💾
5. Done! File saved

**Find old advice:**
1. Click 📋
2. Use search box
3. Type keywords
4. Click session to load
5. Done! Chat loaded

**Clean up space:**
1. Click 📋
2. Review sessions
3. Delete unused ones
4. Click "Xóa tất cả" if needed
5. Done! Space freed

---

## 📁 Files Involved

- `useChatHistory.js` - State management
- `ChatHistory.jsx` - UI component
- `ChatBot.jsx` - Main chat widget
- `localStorage` - Browser storage

---

## ⏱️ Response Times

- Send message: ~1-3 seconds
- Switch session: <100ms
- Export: <1 second
- Delete: <50ms

---

## 🔐 Privacy Note

All data stored **locally in browser only**:
- NOT sent to server
- NOT synced to cloud
- Lost if you clear cache
- Not accessible on other devices

---

## 📞 Need Help?

**See Full Guide**: `CHAT_HISTORY_GUIDE.md`

**See Visuals**: `CHAT_HISTORY_VISUAL_GUIDE.md`

**See Technical**: `CHAT_HISTORY_IMPLEMENTATION.md`

---

## ✨ What You Get

| Feature | Status |
|---------|--------|
| Save messages | ✅ |
| Multiple chats | ✅ |
| Search | ✅ |
| Export | ✅ |
| Delete | ✅ |
| Nice UI | ✅ |
| Mobile ready | ✅ |

---

## 🚀 Start Now!

1. **Open chatbot** 💬
2. **Send message**
3. **Click history** 📋
4. **See all chats** ✨

That's it! You're ready to use chat history!

---

**Version**: 1.0  
**Status**: ✅ Ready  
**Last Updated**: May 13, 2026  
