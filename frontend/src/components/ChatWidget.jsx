import { useState, useEffect, useRef } from "react";
import { MessageCircle, Send, X, Hash, ChevronDown, Users } from "lucide-react";
import "./ChatWidget.css";
import { API_BASE } from "../config";

const API = API_BASE;
const POLL_MS = 3000;

const CHANNELS = [
  { id: "general", name: "General", icon: "💬" },
  { id: "dispatch", name: "Despacho", icon: "🚑" },
  { id: "medical", name: "Médico", icon: "🏥" },
];

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [channel, setChannel] = useState("general");
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [unread, setUnread] = useState(0);
  const [showChannels, setShowChannels] = useState(false);
  const scrollRef = useRef(null);
  const lastTsRef = useRef(null);
  const token = localStorage.getItem("token");
  const currentUser = (() => {
    try { return JSON.parse(atob(token.split(".")[1])).sub; } catch { return "operator"; }
  })();

  const hdrs = () => ({
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  });

  // Fetch messages
  const fetchMessages = async (ch = channel) => {
    try {
      const url = `${API}/api/chat/messages?channel=${ch}`;
      const res = await fetch(url, { headers: hdrs() });
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
        if (data.length > 0) {
          const latest = data[data.length - 1].ts;
          if (!open && lastTsRef.current && latest > lastTsRef.current) {
            setUnread((u) => u + data.filter((m) => m.ts > lastTsRef.current).length);
          }
          lastTsRef.current = latest;
        }
      }
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    if (!token) return;
    fetchMessages();
    const iv = setInterval(() => fetchMessages(), POLL_MS);
    return () => clearInterval(iv);
  }, [channel, token]);

  useEffect(() => {
    if (open) {
      setUnread(0);
      scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
    }
  }, [open, messages]);

  const sendMessage = async () => {
    const t = text.trim();
    if (!t) return;
    setText("");
    try {
      await fetch(`${API}/api/chat/messages`, {
        method: "POST",
        headers: hdrs(),
        body: JSON.stringify({ text: t, channel }),
      });
      fetchMessages();
    } catch {
      /* ignore */
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (ts) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  const ROLE_COLORS = {
    ADMIN: "#ef4444",
    OPERATOR: "#3b82f6",
    MEDICO: "#22c55e",
    PARAMEDIC: "#f59e0b",
  };

  const currentChannel = CHANNELS.find((c) => c.id === channel) || CHANNELS[0];

  return (
    <div className="chat-widget-wrapper">
      {/* Floating toggle button */}
      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)} title="Chat interno">
          <MessageCircle size={22} />
          {unread > 0 && <span className="chat-fab-badge">{unread > 9 ? "9+" : unread}</span>}
        </button>
      )}

      {/* Chat panel */}
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <div className="chat-header-left" onClick={() => setShowChannels((v) => !v)}>
              <span className="chat-ch-icon">{currentChannel.icon}</span>
              <span className="chat-ch-name">{currentChannel.name}</span>
              <ChevronDown size={14} />
            </div>
            <button className="chat-close" onClick={() => setOpen(false)}>
              <X size={16} />
            </button>
          </div>

          {showChannels && (
            <div className="chat-channels">
              {CHANNELS.map((ch) => (
                <button
                  key={ch.id}
                  className={`chat-ch-btn ${ch.id === channel ? "active" : ""}`}
                  onClick={() => {
                    setChannel(ch.id);
                    setShowChannels(false);
                    setMessages([]);
                  }}
                >
                  <span>{ch.icon}</span> <Hash size={12} /> {ch.name}
                </button>
              ))}
            </div>
          )}

          <div className="chat-messages" ref={scrollRef}>
            {messages.length === 0 && (
              <div className="chat-empty">
                <Users size={28} />
                <span>Sin mensajes en #{currentChannel.name}</span>
              </div>
            )}
            {messages.map((m) => {
              const isMe = m.user === currentUser;
              return (
                <div key={m.id} className={`chat-msg ${isMe ? "me" : "other"}`}>
                  {!isMe && (
                    <div className="chat-msg-user" style={{ color: ROLE_COLORS[m.role] || "#8b5cf6" }}>
                      {m.user}
                    </div>
                  )}
                  <div className="chat-msg-bubble">
                    <span className="chat-msg-text">{m.text}</span>
                    <span className="chat-msg-time">{formatTime(m.ts)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="chat-input-area">
            <input
              className="chat-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Mensaje a #${currentChannel.name}...`}
              maxLength={500}
            />
            <button className="chat-send" onClick={sendMessage} disabled={!text.trim()}>
              <Send size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
