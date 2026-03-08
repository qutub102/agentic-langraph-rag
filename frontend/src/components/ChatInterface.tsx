import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useState } from 'react';
import { ChatResponse } from '../types';
import { CitationList } from './CitationList';
import './ChatInterface.css';

interface ChatInterfaceProps {
  collectionName: string;
  onSubmit: (question: string, collectionName: string) => Promise<void>;
  response: ChatResponse | null;
  loading: boolean;
  error: Error | null;
}

export function ChatInterface({ collectionName, onSubmit, response, loading, error }: ChatInterfaceProps) {
  const [question, setQuestion] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading || !collectionName.trim()) {
      return;
    }
    await onSubmit(question.trim(), collectionName.trim());
    setQuestion('');
  };

  const getConfidenceColor = (confidence: string): string => {
    switch (confidence) {
      case 'HIGH':
        return '#28a745';
      case 'MEDIUM':
        return '#ffc107';
      case 'LOW':
        return '#dc3545';
      default:
        return '#6c757d';
    }
  };

  return (
    <div className="chat-interface">
      <h2>Ask a Question</h2>
      <form onSubmit={handleSubmit} className="chat-form">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Enter your question about the documents (max 1000 characters)..."
          maxLength={1000}
          rows={4}
          className="question-input"
          disabled={loading}
        />
        <div className="chat-controls">
          <div className="char-count">
            {question.length} / 1000
          </div>
          <button
            type="submit"
            disabled={!question.trim() || loading}
            className="send-button"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <p>{error.message}</p>
          <button
            onClick={() => onSubmit(question, collectionName)}
            className="retry-button"
          >
            Retry
          </button>
        </div>
      )}

      {loading && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>Processing your question...</p>
        </div>
      )}

      {response && !loading && (
        <div className="answer-panel">
          <div className="answer-header">
            <h3>Answer</h3>
            <span
              className="confidence-badge"
              style={{ backgroundColor: getConfidenceColor(response.confidence) }}
            >
              {response.confidence} Confidence
            </span>
          </div>
          <div className="answer-text">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {response.answer}
            </ReactMarkdown>
          </div>
          <CitationList citations={response.citations} />
        </div>
      )}

      {!response && !loading && !error && (
        <div className="empty-state">
          Ask a question about your uploaded documents to get started.
        </div>
      )}
    </div>
  );
}
