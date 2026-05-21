import React, { useState, useRef, useEffect } from 'react';
import api from '../lib/api';
import {
  Send, Bot, User, Loader2, MessageSquare,
  AlertCircle, Sparkles, Trash2
} from 'lucide-react';
import styles from './ChatbotPage.module.css';

const SUGGESTIONS = [
  'How many cheques have been processed?',
  'What is the total amount across all cheques?',
  'Which payee has the highest amount?',
  'Show me all IFSC codes found.',
  'What is the average cheque amount?',
];

export default function ChatbotPage() {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      text: "Hello! I'm your financial document assistant. I can answer questions about your processed cheque data. What would you like to know?",
      ts: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef();
  const inputRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput('');
    setError('');

    setMessages(prev => [...prev, { role: 'user', text: msg, ts: new Date() }]);
    setLoading(true);

    try {
      const res = await api.post('/chat', { message: msg });
      setMessages(prev => [...prev, { role: 'bot', text: res.data.reply, ts: new Date() }]);
    } catch (err) {
      const errMsg = err.response?.data?.error || 'Failed to get a response.';
      setError(errMsg);
      setMessages(prev => [...prev, { role: 'bot', text: `Sorry, I couldn't process that. ${errMsg}`, ts: new Date(), isError: true }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const clearChat = () => {
    setMessages([{
      role: 'bot',
      text: "Chat cleared. How can I help you with your financial documents?",
      ts: new Date(),
    }]);
    setError('');
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>AI Chatbot</h1>
          <p className={styles.subtitle}>Ask questions about your extracted cheque data</p>
        </div>
        <button className={styles.clearBtn} onClick={clearChat}>
          <Trash2 size={14} /> Clear chat
        </button>
      </div>

      <div className={styles.chatLayout}>
        {/* Suggestions */}
        <div className={styles.suggestions}>
          <div className={styles.suggestionsHeader}>
            <Sparkles size={14} style={{ color: 'var(--indigo)' }} />
            <span>Suggested questions</span>
          </div>
          <div className={styles.suggestionList}>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className={styles.suggestionChip}
                onClick={() => send(s)}
                disabled={loading}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Chat window */}
        <div className={styles.chatWrap}>
          <div className={styles.messages}>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`${styles.msgRow} ${msg.role === 'user' ? styles.msgRowUser : styles.msgRowBot}`}
              >
                <div className={`${styles.avatar} ${msg.role === 'user' ? styles.avatarUser : styles.avatarBot}`}>
                  {msg.role === 'user' ? <User size={15} /> : <Bot size={15} />}
                </div>
                <div className={styles.msgBubbleWrap}>
                  <div className={`${styles.bubble} ${msg.role === 'user' ? styles.bubbleUser : styles.bubbleBot} ${msg.isError ? styles.bubbleError : ''}`}>
                    {msg.text}
                  </div>
                  <div className={styles.msgTime}>{formatTime(msg.ts)}</div>
                </div>
              </div>
            ))}

            {loading && (
              <div className={`${styles.msgRow} ${styles.msgRowBot}`}>
                <div className={`${styles.avatar} ${styles.avatarBot}`}>
                  <Bot size={15} />
                </div>
                <div className={styles.typingIndicator}>
                  <span /><span /><span />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className={styles.inputBar}>
            <div className={styles.inputWrap}>
              <MessageSquare size={16} className={styles.inputIcon} />
              <input
                ref={inputRef}
                className={styles.input}
                placeholder="Ask about your cheque data..."
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
                disabled={loading}
              />
            </div>
            <button
              className={styles.sendBtn}
              onClick={() => send()}
              disabled={!input.trim() || loading}
            >
              {loading ? <Loader2 size={16} className={styles.spin} /> : <Send size={16} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
