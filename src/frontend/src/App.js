// App.js - Modified per your requests (Header, Footer, revised texts, compact score card, chatbot minimize)
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Container, Row, Col } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

// 🎨 Professional Styling (modified)
const styles = `
  :root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --info-color: #17a2b8;
    --secondary-color: #6c757d;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    background: #f8f9fa;
    margin: 0;
    padding: 0;
  }

  /* Header & Footer */
  .app-header {
    background: white;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    border-bottom: 1px solid #eef1f6;
    box-shadow: 0 1px 6px rgba(0,0,0,0.03);
  }
  .brand {
    display:flex;
    align-items:center;
    gap:0.75rem;
  }
  .brand-symbol { font-size: 1.6rem; }
  .brand-title { font-size: 1.15rem; font-weight:700; color:#2c3e50; }
  .brand-sub { font-size:0.85rem; color:var(--secondary-color); }

  .app-footer {
    background: white;
    padding: 1rem 1.5rem;
    margin-top: 2rem;
    border-top: 1px solid #eef1f6;
    display:flex;
    gap:1rem;
    align-items:flex-start;
    justify-content:space-between;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  }
  .footer-left { display:flex; gap:0.75rem; align-items:center; }
  .footer-text { color: #6c757d; max-width: 900px; font-size:0.95rem; line-height:1.4; }

  /* Hero Section */
  .hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: calc(100vh - 80px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }

  .hero-card {
    background: rgba(255, 255, 255, 0.98);
    border-radius: 24px;
    padding: 3rem;
    max-width: 760px;
    width: 100%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
  }

  .hero-icon {
    font-size: 3rem;
    text-align: center;
    margin-bottom: 1rem;
  }

  .hero-title {
    font-size: 2rem;
    font-weight: 700;
    color: #2c3e50;
    text-align: center;
    margin-bottom: 0.25rem;
  }

  .hero-subtitle {
    color: #6c757d;
    font-size: 1rem;
    text-align: center;
    margin-bottom: 1.75rem;
    line-height: 1.6;
  }

  .input-box {
    border-radius: 12px;
    border: 2px solid #e9ecef;
    padding: 1rem;
    font-size: 1rem;
    transition: all 0.3s ease;
    width: 100%;
    resize: vertical;
  }

  .input-box:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.08);
  }

  .primary-btn {
    background: var(--primary-gradient);
    border: none;
    border-radius: 12px;
    padding: 0.95rem 1.25rem;
    font-size: 1rem;
    font-weight: 600;
    color: white;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    margin-top: 1rem;
  }

  .primary-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.28);
  }

  .feature-list {
    text-align: center;
    margin-top: 1.5rem;
    font-size: 0.95rem;
    color: #6c757d;
  }

  .feature-list p { margin: 0.35rem 0; }

  /* Dashboard Styles */
  .dashboard-container {
    background: #f8f9fa;
    min-height: calc(100vh - 110px);
    padding: 2rem 0 1rem;
  }

  .dashboard-header {
    background: white;
    padding: 1.25rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.25rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  }

  .dashboard-title { margin: 0; color: #2c3e50; font-size: 1.2rem; font-weight: 700; }
  .dashboard-subtitle { margin: 0.25rem 0 0 0; color: #6c757d; font-size: 0.95rem; }

  .btn-outline-primary, .btn-download {
    padding: 0.55rem 1rem;
    border-radius: 8px;
    font-weight: 600;
    cursor:pointer;
    border: none;
  }
  .btn-outline-primary {
    background: white;
    border: 2px solid #667eea;
    color: #667eea;
  }
  .btn-download {
    background: var(--primary-gradient);
    color: white;
  }

  .score-card {
    background: white;
    border-radius: 12px;
    padding: 1rem;
    display:flex;
    align-items:center;
    gap:1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
  }

  .score-circle {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    font-weight: bold;
    color: white;
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    flex: 0 0 110px;
  }

  .score-summary {
    display:flex;
    flex-direction:column;
    gap:0.25rem;
  }
  .score-grade { color: #2c3e50; font-weight:700; font-size:1.05rem; }
  .score-url { color:#6c757d; font-size:0.9rem; word-break:break-all; }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .stat-card {
    background: white;
    border-radius: 8px;
    padding: 0.9rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border-left: 4px solid;
    text-align:center;
  }
  .stat-number { font-size:1.25rem; font-weight:800; }
  .stat-label { color: #6c757d; font-size:0.9rem; margin-top:0.25rem; }

  .url-list { background: white; border-radius: 12px; padding: 1rem; box-shadow: 0 2px 12px rgba(0,0,0,0.04); }
  .url-list-title { margin-bottom: 0.6rem; font-weight:700; color:#2c3e50; font-size:1rem; }

  .url-item { padding: 0.7rem; border-radius: 8px; margin-bottom: 0.5rem; cursor:pointer; transition: all 0.15s ease; border: 1px solid transparent; }
  .url-item.active { border-color:#e6e9ff; background:#fbfdff; }

  .content-card { background: white; border-radius: 12px; padding: 1rem; box-shadow: 0 2px 12px rgba(0,0,0,0.04); }

  .tabs-container { border-bottom: 1px solid #eef1f6; margin-bottom: 0.75rem; display:flex; gap:0.5rem; flex-wrap:wrap; padding:0.5rem 0; }
  .tab-button { background:transparent; border:none; cursor:pointer; padding:0.5rem 0.9rem; border-bottom: 3px solid transparent; font-weight:700; color:#6c757d; }
  .tab-button.active { color:#667eea; border-bottom-color:#667eea; }

  .audit-table { width: 100%; border-collapse: collapse; }
  .audit-table thead th { text-align:left; padding:0.5rem; color:#6c757d; font-size:0.85rem; text-transform:uppercase; }
  .audit-table tbody tr { background:#fbfbfb; }
  .audit-table tbody td { padding:0.85rem; vertical-align:top; }

  .sc-id-badge { background: linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; padding:0.25rem 0.6rem; border-radius:6px; font-weight:700; font-size:0.85rem; }

  .empty-state { text-align:center; padding:2rem; color:#6c757d; }

  /* Chatbot */
  .chat-minimized {
    position: fixed;
    right: 20px;
    bottom: 20px;
    z-index: 9999;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.55rem 0.9rem;
    border-radius: 999px;
    box-shadow: 0 8px 30px rgba(102,126,234,0.3);
    cursor:pointer;
    display:flex;
    align-items:center;
    gap:0.6rem;
    font-weight:700;
  }

  .chat-full {
    position: fixed;
    right: 20px;
    bottom: 20px;
    width: 400px;
    height: 600px;
    z-index: 9999;
    border-radius: 12px;
    overflow: hidden;
  }

  .error-alert { background:#f8d7da; color:#721c24; padding:0.8rem; border-radius:8px; margin-top:0.75rem; border:1px solid #f5c6cb; }

  @keyframes bounce { 0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)} }
`;

/* ---------------- Header & Footer Components ---------------- */
function Header({ small }) {
  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-symbol">♿</div>
        <div>
          <div className="brand-title">ADA Accessibility Checker</div>
          <div className="brand-sub">WCAG 2.1 &amp; 2.2 Auditor</div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <div style={{ color: '#6c757d', fontSize: 14 }}>Demo • Accessibility-first</div>
        <button className="btn-outline-primary" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>Home</button>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-left">
        <div style={{ fontSize: '1.4rem' }}>♿</div>
        <div>
          <div style={{ fontWeight: 700, color: '#2c3e50' }}>ADA Accessibility Checker</div>
          <div className="footer-text">
            A comprehensive platform for testing and ensuring ADA compliance across web applications. Built with accessibility-first principles and automated testing capabilities.
          </div>
        </div>
      </div>
      <div style={{ color: '#6c757d', fontSize: 13 }}>
        © {new Date().getFullYear()} Accessibility Lab — Built for the hackathon
      </div>
    </footer>
  );
}

/* ---------------- Chatbot Component (minimize feature) ---------------- */
function AccessibilityChatbot({ onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! Ask me about your accessibility scan results.\n\nExamples:\n• Which pages have the most critical issues?\n• What are the top 3 violations?\n• Give me a summary\n• What are the accessibility scores?"
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [minimized, setMinimized] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:3001/chat', { question: input });
      const aiMessage = { role: 'assistant', content: response.data.answer || 'No answer' };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = { role: 'assistant', content: `Error: ${error.response?.data?.error || error.message}` };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  if (minimized) {
    return (
      <div className="chat-minimized" onClick={() => setMinimized(false)} role="button" aria-label="Open accessibility assistant">
        💬 Accessibility Assistant
      </div>
    );
  }

  return (
    <div className="chat-full" aria-live="polite">
      <div style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'white',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 10px 40px rgba(0,0,0,0.25)'
      }}>
        <div style={{
          padding: '0.9rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
          color: 'white'
        }}>
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', fontWeight: 700 }}>
            <span style={{ fontSize: 18 }}>🤖</span>
            Accessibility Assistant
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button
              onClick={() => setMinimized(true)}
              style={{ background: 'transparent', border: 'none', color: 'white', fontSize: 16, cursor: 'pointer' }}
              aria-label="Minimize chat"
            >
              _
            </button>
            <button
              onClick={onClose}
              style={{ background: 'transparent', border: 'none', color: 'white', fontSize: 20, cursor: 'pointer' }}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0.9rem', display:'flex', flexDirection:'column', gap: '0.6rem' }}>
          {messages.map((m, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{
                maxWidth: '78%',
                padding: '0.65rem 0.9rem',
                borderRadius: 10,
                background: m.role === 'user' ? 'linear-gradient(135deg,#667eea 0%,#764ba2 100%)' : '#f3f5f7',
                color: m.role === 'user' ? 'white' : '#2c3e50',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                fontSize: 14
              }}>
                {m.content}
              </div>
            </div>
          ))}
          {loading && <div style={{ color:'#6c757d', fontSize:13 }}>Thinking...</div>}
        </div>

        <div style={{ padding: '0.75rem', borderTop: '1px solid #eef1f6', display:'flex', gap:'0.5rem' }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your scan..."
            style={{ flex: 1, padding: '0.6rem', borderRadius: 8, border: '1px solid #eef1f6', outline:'none' }}
            aria-label="Ask about your scan"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{ padding: '0.6rem 0.9rem', borderRadius: 8, border: 'none', background: 'linear-gradient(135deg,#667eea 0%,#764ba2 100%)', color: 'white', fontWeight:700 }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------------- Main App ---------------- */
function App() {
  const [url, setUrl] = useState('');
  const [isCrawling, setIsCrawling] = useState(false);
  const [error, setError] = useState(null);
  const [allAuditResults, setAllAuditResults] = useState(null);
  const [selectedUrl, setSelectedUrl] = useState(null);
  const [activeTab, setActiveTab] = useState('Critical');
  const [showChatbot, setShowChatbot] = useState(false);

  useEffect(() => {
    if (allAuditResults) {
      const allUrls = Object.keys(allAuditResults.results || {});
      const firstUrl = allUrls.find(u => !allAuditResults.results[u].error) || allUrls[0];
      if (firstUrl) setSelectedUrl(firstUrl);
      setActiveTab('Critical');
    }
  }, [allAuditResults]);

  const handleBackToHome = useCallback(() => {
    setAllAuditResults(null);
    setUrl('');
    setError(null);
    setSelectedUrl(null);
    setActiveTab('Critical');
  }, []);

  const handleCrawl = async () => {
    const urlsToSend = url.split('\n').map(u => u.trim()).filter(Boolean);
    if (urlsToSend.length === 0) {
      setError("Please enter at least one URL to start the audit.");
      return;
    }

    setError(null);
    setIsCrawling(true);
    setAllAuditResults(null);
    setSelectedUrl(null);

    try {
      const response = await axios.post('http://localhost:3001/audit', { url });
      const resultsMap = response.data;
      const structuredResults = {
        crawled_pages: Object.keys(resultsMap || {}).length,
        results: resultsMap || {}
      };
      setAllAuditResults(structuredResults);
    } catch (err) {
      setError(err.response?.data?.error || `Failed to connect: ${err.message}`);
    } finally {
      setIsCrawling(false);
    }
  };

  const handleDownloadReport = () => {
    if (!allAuditResults) return;

    let csvContent = "URL,SC ID,Status,Description,Fix Tip\n";

    const processResults = (arr, status, currentUrl) => {
      arr.forEach(item => {
        const scId = String(item.sc_id || 'N/A').replace(/"/g, '""');
        const description = String(item.description || 'N/A').replace(/"/g, '""');
        const fixTip = String(item.fix_tip || 'N/A').replace(/"/g, '""');
        csvContent += `"${currentUrl}","${scId}","${status}","${description}","${fixTip}"\n`;
      });
    };

    for (const urlKey in allAuditResults.results) {
      const report = allAuditResults.results[urlKey] || {};
      if (report.automatic_results) processResults(report.automatic_results, 'CRITICAL', urlKey);
      if (report.passed_checks) processResults(report.passed_checks, 'PASSED', urlKey);
      if (report.manual_audits_required) processResults(report.manual_audits_required, 'MANUAL', urlKey);
      if (report.not_applicable) processResults(report.not_applicable, 'NOT APPLICABLE', urlKey);
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const fileUrl = URL.createObjectURL(blob);
    link.setAttribute("href", fileUrl);
    link.setAttribute("download", "wcag_audit_report.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const selectedReport = allAuditResults?.results?.[selectedUrl];
  const summary = selectedReport?.summary;
  const allUrls = allAuditResults?.results ? Object.keys(allAuditResults.results) : [];

  const tabMapping = {
    'Critical': selectedReport?.automatic_results || [],
    'Passed': selectedReport?.passed_checks || [],
    'Manual': selectedReport?.manual_audits_required || [],
    'Not Applicable': selectedReport?.not_applicable || []
  };

  const getScoreColor = (score) => {
    if (!score || score === 'N/A' || score === 'Error') return '#6c757d';
    const percentage = parseInt(String(score).match(/\d+/)?.[0] || '0', 10);
    if (percentage >= 90) return '#28a745';
    if (percentage >= 70) return '#ffc107';
    return '#dc3545';
  };

  // HERO (Home) VIEW
  if (!allAuditResults) {
    return (
      <>
        <style>{styles}</style>
        <Header />
        <div className="hero-section">
          <div className="hero-card" role="main" aria-labelledby="hero-heading">
            <div className="hero-icon">♿</div>
            <h1 id="hero-heading" className="hero-title">ADA Accessibility Checker</h1>
            <div style={{ textAlign: 'center', marginBottom: '0.5rem', color:'#5e6b8a', fontWeight:600 }}>WCAG 2.1 &amp; 2.2 Auditor</div>
            <p className="hero-subtitle">
              Automated accessibility scanner that finds common issues like missing alt text, low color contrast, and inaccessible navigation — and gives clear, prioritized remediation guidance so teams can fix problems quickly.
            </p>

            <div>
              <label style={{ color: '#495057', fontWeight: '600', marginBottom: '0.5rem', display: 'block' }}>
                Enter URL(s) to Scan
              </label>
              <textarea
                className="input-box"
                placeholder="https://example.com&#10;https://example.com/about&#10;https://example.com/contact"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isCrawling}
                rows={5}
                aria-label="URLs to scan"
              />
              <small style={{ color: '#6c757d', display: 'block', marginTop: '0.5rem' }}>
                💡 Enter one or multiple URLs, one per line
              </small>
            </div>

            {error && <div className="error-alert" role="alert">{error}</div>}

            <button
              className="primary-btn"
              onClick={handleCrawl}
              disabled={isCrawling}
              aria-busy={isCrawling}
            >
              {isCrawling ? (
                <>
                  <span style={{ marginRight: 8 }}>⏳</span>
                  Analyzing Accessibility...
                </>
              ) : (
                <>Start Accessibility Audit</>
              )}
            </button>

            <div className="feature-list" aria-hidden="false">
              <p>✓ Comprehensive accessibility coverage</p>
              <p>✓ Automated deep analysis</p>
              <p>✓ Clear, actionable remediation</p>
              <p>✓ Multi-page crawling & reporting</p>
            </div>
          </div>
        </div>
        <Container fluid style={{ maxWidth: 1200, marginTop: '1rem' }}>
          <Footer />
        </Container>
      </>
    );
  }

  // DASHBOARD VIEW
  return (
    <>
      <style>{styles}</style>
      <Header />
      <div className="dashboard-container">
        <Container fluid style={{ maxWidth: 1400 }}>
          <div className="dashboard-header">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div>
                <h2 className="dashboard-title">Accessibility Audit Dashboard</h2>
                <p className="dashboard-subtitle">{allAuditResults.crawled_pages} pages analyzed • Accessibility summary</p>
              </div>
              <div style={{ display: 'flex', gap: '0.6rem' }}>
                <button className="btn-outline-primary" onClick={handleBackToHome}>← New Scan</button>
                <button className="btn-download" onClick={handleDownloadReport}>📥 Export CSV</button>
              </div>
            </div>
          </div>

          <Row>
            <Col md={4}>
              <div className="url-list">
                <h5 className="url-list-title">Scanned Pages ({allUrls.length})</h5>
                <div style={{ maxHeight: 520, overflowY: 'auto', paddingRight: 6 }}>
                  {allUrls.map((u) => {
                    const urlReport = allAuditResults.results?.[u] || {};
                    const isError = !!urlReport.error;
                    const issuesCount = urlReport.summary?.critical_count ?? 0;
                    const score = urlReport.summary?.audit_score || 'N/A';
                    const isActive = u === selectedUrl;

                    return (
                      <div
                        key={u}
                        onClick={() => setSelectedUrl(u)}
                        className={`url-item ${isActive ? 'active' : ''}`}
                        style={{
                          borderLeft: `4px solid ${isError ? '#dc3545' : getScoreColor(score)}`,
                          marginBottom: 8
                        }}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => e.key === 'Enter' && setSelectedUrl(u)}
                        aria-pressed={isActive}
                      >
                        <div style={{ fontWeight: 700, color: '#2c3e50', marginBottom: 4 }}>
                          {u.length > 60 ? `${u.substring(0, 57)}...` : u}
                        </div>
                        <div style={{ color: '#6c757d', fontSize: 13 }}>
                          {isError ? <span style={{ color: '#dc3545' }}>⚠️ Audit Failed</span> : (
                            <>
                              <span style={{ marginRight: 8 }}>🔴 {issuesCount} Issues</span>
                              <span>Score: {score}</span>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </Col>

            <Col md={8}>
              {selectedReport && summary ? (
                <>
                  <div className="score-card" role="region" aria-label="Audit score">
                    <div
                      className="score-circle"
                      style={{
                        background: `linear-gradient(135deg, ${getScoreColor(summary.audit_score)} 0%, ${getScoreColor(summary.audit_score)}cc 100%)`
                      }}
                    >
                      {summary.audit_score}
                    </div>
                    <div className="score-summary">
                      <div style={{ display:'flex', alignItems:'center', gap:'0.6rem', flexWrap:'wrap' }}>
                        <div className="score-grade">{summary.grade || 'Needs Improvement'}</div>
                        <div style={{ color:'#6c757d', fontSize:13 }}>{summary.scanned_url}</div>
                      </div>
                      <div style={{ color:'#6c757d', fontSize:13 }}>
                        AUDIT SCORE • {summary.audit_score} • {summary.grade || 'Needs Improvement'}
                      </div>
                    </div>
                  </div>

                  <div className="stats-grid" role="list">
                    <div className="stat-card" style={{ borderLeftColor: '#dc3545' }} role="listitem">
                      <div className="stat-number" style={{ color: '#dc3545' }}>{tabMapping['Critical'].length}</div>
                      <div className="stat-label">Critical Issues</div>
                    </div>
                    <div className="stat-card" style={{ borderLeftColor: '#28a745' }}>
                      <div className="stat-number" style={{ color: '#28a745' }}>{tabMapping['Passed'].length}</div>
                      <div className="stat-label">Passed Checks</div>
                    </div>
                    <div className="stat-card" style={{ borderLeftColor: '#ffc107' }}>
                      <div className="stat-number" style={{ color: '#ffc107' }}>{tabMapping['Manual'].length}</div>
                      <div className="stat-label">Manual Review</div>
                    </div>
                    <div className="stat-card" style={{ borderLeftColor: '#6c757d' }}>
                      <div className="stat-number" style={{ color: '#6c757d' }}>{tabMapping['Not Applicable'].length}</div>
                      <div className="stat-label">Not Applicable</div>
                    </div>
                  </div>

                  <div className="content-card">
                    <div className="tabs-container" role="tablist" aria-label="Audit tabs">
                      {Object.keys(tabMapping).map(key => (
                        <button
                          key={key}
                          onClick={() => setActiveTab(key)}
                          className={`tab-button ${activeTab === key ? 'active' : ''}`}
                          role="tab"
                          aria-selected={activeTab === key}
                        >
                          {key} ({tabMapping[key].length})
                        </button>
                      ))}
                    </div>

                    <div style={{ maxHeight: 420, overflowY: 'auto' }}>
                      {tabMapping[activeTab].length > 0 ? (
                        <table className="audit-table" aria-live="polite">
                          <thead>
                            <tr>
                              <th style={{ width: '18%' }}>SC ID</th>
                              <th style={{ width: activeTab === 'Critical' || activeTab === 'Manual' ? '47%' : '82%' }}>Description</th>
                              {(activeTab === 'Critical' || activeTab === 'Manual') && <th style={{ width: '35%' }}>Fix Recommendation</th>}
                            </tr>
                          </thead>
                          <tbody>
                            {tabMapping[activeTab].map((item, index) => (
                              <tr key={index}>
                                <td>
                                  <span className="sc-id-badge">{item.sc_id || 'N/A'}</span>
                                </td>
                                <td style={{ color: '#2c3e50' }}>{item.description || 'N/A'}</td>
                                {(activeTab === 'Critical' || activeTab === 'Manual') && (
                                  <td style={{ color: '#6c757d' }}>{item.fix_tip || 'N/A'}</td>
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <div className="empty-state">
                          <div className="empty-state-icon">✓</div>
                          <h5 style={{ color: '#2c3e50', marginBottom: '0.5rem' }}>All Clear!</h5>
                          <p>No {activeTab.toLowerCase()} checks found for this page</p>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <div className="content-card empty-state">
                  <div className="empty-state-icon">📊</div>
                  <h4 style={{ color: '#2c3e50', marginBottom: '0.5rem' }}>Select a Page</h4>
                  <p>Choose a URL from the left panel to view its detailed audit report</p>
                </div>
              )}
            </Col>
          </Row>

          <div style={{ marginTop: 16 }}>
            <Footer />
          </div>
        </Container>

        {/* Chat controls */}
        {!showChatbot && (
          <button
            onClick={() => setShowChatbot(true)}
            title="Open assistant"
            style={{
              position: 'fixed',
              bottom: 20,
              right: 20,
              width: 60,
              height: 60,
              borderRadius: '50%',
              background: 'linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
              border: 'none',
              color: 'white',
              fontSize: 22,
              cursor: 'pointer',
              zIndex: 9998,
              boxShadow: '0 8px 30px rgba(102,126,234,0.28)'
            }}
            aria-label="Open accessibility assistant"
          >
            💬
          </button>
        )}

        {showChatbot && <AccessibilityChatbot onClose={() => setShowChatbot(false)} />}

      </div>
    </>
  );
}

export default App;
