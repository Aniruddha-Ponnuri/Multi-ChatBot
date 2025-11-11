import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader, ThumbsUp, ThumbsDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Sidebar from './components/Sidebar';
import apiService from './services/api';
import './Chatbot.css';

const Chatbot = () => {
  const [question, setQuestion] = useState('');
  const [conversation, setConversation] = useState([]);
  const [summarizedHistory, setSummarizedHistory] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [feedbackGiven, setFeedbackGiven] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loadingSessions, setLoadingSessions] = useState(false);

  const chatContainerRef = useRef(null);
  const lastMessageRef = useRef(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Auto scroll to the last message
  useEffect(() => {
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation]);

  const loadSessions = async () => {
    try {
      setLoadingSessions(true);
      const sessions = await apiService.getAllSessions();
      setSessions(sessions);
    } catch (error) {
      console.error('Error loading sessions:', error.message);
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      setLoading(true);
      const data = await apiService.getSession(sessionId);
      
      setCurrentSessionId(sessionId);
      setConversation(data.messages || []);
      setSummarizedHistory('');
      setFeedbackGiven({});
    } catch (error) {
      console.error('Error loading session:', error.message);
      alert('Failed to load session: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setCurrentSessionId(newSessionId);
    setConversation([]);
    setSummarizedHistory('');
    setFeedbackGiven({});
  };

  const deleteSession = async (sessionId, event) => {
    // Handle case where event is not provided (called from Sidebar)
    if (event && event.stopPropagation) {
      event.stopPropagation();
    }
    
    if (!window.confirm('Are you sure you want to delete this chat?')) {
      return;
    }

    try {
      await apiService.deleteSession(sessionId);
      
      if (sessionId === currentSessionId) {
        startNewChat();
      }
      
      loadSessions();
    } catch (error) {
      console.error('Error deleting session:', error.message);
      alert('Failed to delete session: ' + error.message);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      alert('Please enter a question.');
      return;
    }
    
    // Create session ID if this is a new chat
    const sessionId = currentSessionId || `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    if (!currentSessionId) {
      setCurrentSessionId(sessionId);
    }

    const userQuestion = question;
    
    try {
      setLoading(true);
      const newConversation = [...conversation, { role: 'user', content: userQuestion }];
      setConversation(newConversation);
      setQuestion('');

      const data = await apiService.askQuestion(userQuestion, summarizedHistory, false, sessionId);

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        question: userQuestion,
        rlUsed: data.rl_used || false,
        timestamp: Date.now(),
      };

      setConversation([...newConversation, assistantMessage]);
      setSummarizedHistory(data.summarized_history);
      
      if (data.session) {
        loadSessions();
      }
    } catch (error) {
      console.error('Error asking question:', error.message);
      alert('Failed to get response: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (messageIndex, rating) => {
    const message = conversation[messageIndex];
    
    if (!message || message.role !== 'assistant') {
      console.error('Invalid message for feedback');
      return;
    }

    try {
      await apiService.submitFeedback(
        message.question,
        message.content,
        rating,
        currentSessionId
      );

      setFeedbackGiven(prev => ({
        ...prev,
        [messageIndex]: rating,
      }));

      console.log(`Feedback submitted: ${rating === 1 ? 'Positive' : 'Negative'}`);
    } catch (error) {
      console.error('Error submitting feedback:', error.message);
      alert('Failed to submit feedback: ' + error.message);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleAskQuestion();
    }
  };

  return (
    <div className="chat-app">
      {/* Sidebar Component */}
      <Sidebar
        isOpen={sidebarOpen}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onNewChat={startNewChat}
        onSelectSession={loadSession}
        onDeleteSession={deleteSession}
        loading={loadingSessions}
      />

      {/* Main Chat Area */}
      <div className="chat-main">
        <div className="chat-container">
          {/* Header */}
          <div className="chat-header">
            <div className="header-content">
              <button 
                className="sidebar-toggle"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                ☰
              </button>
              <h2>Financial Chatbot</h2>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="chat-messages" ref={chatContainerRef}>
            {conversation.length === 0 ? (
              <div className="empty-state">
                <h3>Welcome to Financial Chatbot</h3>
                <p>Start a conversation by asking a question about finance or stocks</p>
              </div>
            ) : (
              conversation.map((msg, index) => (
                <div
                  key={index}
                  className={`message-wrapper ${msg.role === 'user' ? 'user-message' : 'bot-message'}`}
                  ref={index === conversation.length - 1 ? lastMessageRef : null}
                >
                  <div
                    className={msg.role === 'user' ? 'user-bubble' : 'bot-bubble'}
                    data-sender={msg.role === 'user' ? 'You' : 'Bot'}
                  >
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown
                        rehypePlugins={[rehypeRaw]}
                        components={{
                          code({node, inline, className, children, ...props}) {
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                              <SyntaxHighlighter
                                style={vscDarkPlus}
                                language={match[1]}
                                PreTag="div"
                                {...props}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            );
                          }
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      <div>{msg.content}</div>
                    )}
                    
                    {/* Feedback Buttons */}
                    {msg.role === 'assistant' && (
                      <div className="feedback-buttons">
                        <button
                          className={`feedback-btn ${feedbackGiven[index] === 1 ? 'active-positive' : ''}`}
                          onClick={() => handleFeedback(index, 1)}
                          disabled={feedbackGiven[index] !== undefined}
                          title="Good response"
                        >
                          <ThumbsUp size={16} />
                        </button>
                        <button
                          className={`feedback-btn ${feedbackGiven[index] === 0 ? 'active-negative' : ''}`}
                          onClick={() => handleFeedback(index, 0)}
                          disabled={feedbackGiven[index] !== undefined}
                          title="Poor response"
                        >
                          <ThumbsDown size={16} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="footer">
            <textarea
              placeholder="Ask a question..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="message-input"
              disabled={loading}
              onKeyDown={handleKeyDown}
              rows="1"
            />

            <button 
              onClick={handleAskQuestion}
              disabled={loading}
              className={`ask-button ${loading ? 'disabled' : ''}`}
            >
              {loading ? <Loader className="loader-spin" /> : <Send />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
