import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { checkHealth, sendChatMessage, getAnomalies, investigateAnomaly } from './services/api';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [healthStatus, setHealthStatus] = useState({ agent_ready: false, database_ready: false });
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load health status and anomalies on mount
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const health = await checkHealth();
        setHealthStatus(health);

        const anomalyData = await getAnomalies();
        setAnomalies(anomalyData.anomalies || []);
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    };

    loadInitialData();
  }, []);

  const handleSendMessage = async (messageText = null) => {
    const text = messageText || inputValue.trim();
    if (!text) return;

    // Add user message to UI
    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Send to API
      const response = await sendChatMessage(text, threadId);
      
      // Update thread ID if new
      if (!threadId) {
        setThreadId(response.thread_id);
      }

      // Add agent response to UI
      const agentMessage = {
        role: 'agent',
        content: response.response,
        timestamp: response.timestamp,
      };
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        role: 'agent',
        content: `Error: ${error.message || 'Failed to communicate with the agent'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInvestigateAnomaly = async (anomaly) => {
    setSelectedAnomaly(anomaly.anomaly_id);
    setIsLoading(true);

    // Add user message
    const userMessage = {
      role: 'user',
      content: `Investigate anomaly ${anomaly.anomaly_id}`,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await investigateAnomaly(anomaly.anomaly_id, threadId);
      
      if (!threadId) {
        setThreadId(response.thread_id);
      }

      const agentMessage = {
        role: 'agent',
        content: response.response,
        timestamp: response.timestamp,
      };
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error('Failed to investigate anomaly:', error);
      const errorMessage = {
        role: 'agent',
        content: `Error: ${error.message || 'Failed to investigate anomaly'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getSeverityClass = (severity) => {
    return `severity-${severity.toLowerCase()}`;
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🔍 Network Investigation Agent</h1>
        <p>AI-powered Root Cause Analysis for Network Anomalies</p>
        <div className="status-indicator">
          <span className={`status-dot ${healthStatus.agent_ready && healthStatus.database_ready ? '' : 'offline'}`}></span>
          <span>
            {healthStatus.agent_ready && healthStatus.database_ready
              ? 'Agent Online'
              : 'Agent Offline'}
          </span>
        </div>
      </header>

      <div className="main-content">
        {/* Sidebar with anomalies */}
        <aside className="sidebar">
          <h2>Detected Anomalies ({anomalies.length})</h2>
          <div className="anomaly-list">
            {anomalies.length === 0 ? (
              <div style={{ padding: '1rem', color: '#94a3b8', textAlign: 'center' }}>
                No anomalies found
              </div>
            ) : (
              anomalies.map((anomaly) => (
                <div
                  key={anomaly.anomaly_id}
                  className={`anomaly-card ${selectedAnomaly === anomaly.anomaly_id ? 'selected' : ''}`}
                  onClick={() => handleInvestigateAnomaly(anomaly)}
                >
                  <div className="anomaly-header">
                    <span className={`severity-badge ${getSeverityClass(anomaly.severity)}`}>
                      {anomaly.severity}
                    </span>
                    <span className="anomaly-date">{anomaly.date}</span>
                  </div>
                  <div className="anomaly-detector">{anomaly.detector}</div>
                  <div className="anomaly-hosts">
                    {anomaly.host_count} host{anomaly.host_count !== 1 ? 's' : ''}: {' '}
                    {anomaly.impacted_hosts.slice(0, 2).join(', ')}
                    {anomaly.impacted_hosts.length > 2 && '...'}
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Chat interface */}
        <main className="chat-container">
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="empty-state">
                <h2>👋 Welcome to the Network Investigation Agent</h2>
                <p>
                  I'm here to help you investigate network anomalies and perform root cause analysis.
                </p>
                <p>
                  You can click on any anomaly in the sidebar to start an investigation, or ask me questions directly.
                </p>
                <div className="suggestions">
                  <button
                    className="suggestion-button"
                    onClick={() => handleSendMessage('List all anomalies')}
                  >
                    📋 List all anomalies
                  </button>
                  <button
                    className="suggestion-button"
                    onClick={() => handleSendMessage('What types of anomalies have been detected?')}
                  >
                    🔍 What types of anomalies have been detected?
                  </button>
                  <button
                    className="suggestion-button"
                    onClick={() => handleSendMessage('Explain what a BGP session anomaly is')}
                  >
                    💡 Explain what a BGP session anomaly is
                  </button>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message, index) => (
                  <div key={index} className={`message ${message.role}`}>
                    <div className="message-avatar">
                      {message.role === 'user' ? 'U' : 'AI'}
                    </div>
                    <div className="message-content">
                      <div className="message-role">
                        {message.role === 'user' ? 'You' : 'Agent'}
                      </div>
                      <div className="message-text">
                        {message.role === 'agent' ? (
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        ) : (
                          message.content
                        )}
                      </div>
                      <div className="message-timestamp">
                        {formatTimestamp(message.timestamp)}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="thinking-indicator">
                    <div className="thinking-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span>Agent is investigating...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          <div className="input-container">
            <div className="input-wrapper">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about anomalies or request an investigation..."
                disabled={isLoading}
                rows={1}
              />
              <button
                className="send-button"
                onClick={() => handleSendMessage()}
                disabled={isLoading || !inputValue.trim()}
              >
                {isLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
