// App.js - PROFESSIONAL POLISHED VERSION

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Container, Row, Col } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

// 🎨 Professional Styling
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
  }

  /* Hero Section */
  .hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }

  .hero-card {
    background: rgba(255, 255, 255, 0.98);
    border-radius: 24px;
    padding: 3rem;
    max-width: 650px;
    width: 100%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  }

  .hero-icon {
    font-size: 4rem;
    text-align: center;
    margin-bottom: 1.5rem;
    animation: float 3s ease-in-out infinite;
  }

  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
  }

  .hero-title {
    font-size: 2.5rem;
    font-weight: 700;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 1rem;
  }

  .hero-subtitle {
    color: #6c757d;
    font-size: 1.1rem;
    text-align: center;
    margin-bottom: 2.5rem;
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
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  .primary-btn {
    background: var(--primary-gradient);
    border: none;
    border-radius: 12px;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    font-weight: 600;
    color: white;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    margin-top: 1.5rem;
  }

  .primary-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
  }

  .primary-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .feature-list {
    text-align: center;
    margin-top: 2.5rem;
    font-size: 0.95rem;
    color: #6c757d;
  }

  .feature-list p {
    margin: 0.5rem 0;
  }

  /* Dashboard Styles */
  .dashboard-container {
    background: #f8f9fa;
    min-height: 100vh;
    padding: 2rem 0;
  }

  .dashboard-header {
    background: white;
    padding: 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  }

  .dashboard-title {
    margin: 0;
    color: #2c3e50;
    font-size: 1.8rem;
    font-weight: 700;
  }

  .dashboard-subtitle {
    margin: 0.5rem 0 0 0;
    color: #6c757d;
  }

  .btn-outline-primary {
    background: white;
    border: 2px solid #667eea;
    color: #667eea;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-outline-primary:hover {
    background: #667eea;
    color: white;
  }

  .btn-download {
    background: var(--primary-gradient);
    border: none;
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-download:hover {
    transform: translateY(-2px);
  }

  .score-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    margin-bottom: 2
	rem;
  }

    .score-circle {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1.5rem;
    font-size: 2.5rem;
    font-weight: bold;
    color: white;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  }

  .score-grade {
    color: #2c3e50;
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .score-url {
    color: #6c757d;
    font-size: 0.9rem;
    word-break: break-all;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-left: 4px solid;
    transition: transform 0.2s ease;
  }

  .stat-card:hover {
    transform: translateY(-4px);
  }

  .stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    line-height: 1;
  }

  .stat-label {
    color: #6c757d;
    margin-top: 0.5rem;
    font-size: 0.95rem;
  }

  .url-list {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    margin-bottom: 2rem;
  }

  .url-list-title {
    margin-bottom: 1.5rem;
    font-weight: 700;
    color: #2c3e50;
    font-size: 1.2rem;
  }

  .url-list-container {
    max-height: 600px;
    overflow-y: auto;
  }

  .url-item {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 2px solid transparent;
  }

  .url-item:hover {
    background: #f0f4ff !important;
  }

  .url-item.active {
    background: #f0f4ff;
    border-color: #667eea;
  }

  .url-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 0.5rem;
    word-break: break-word;
  }

  .url-meta {
    font-size: 0.85rem;
    color: #6c757d;
  }

  .content-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  }

  .tabs-container {
    border-bottom: 2px solid #e9ecef;
    margin-bottom: 1.5rem;
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .tab-button {
    padding: 0.75rem 1.5rem;
    border: none;
    background: transparent;
    border-bottom: 3px solid transparent;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
    color: #6c757d;
  }

  .tab-button:hover {
    color: #667eea;
  }

  .tab-button.active {
    color: #667eea;
    border-bottom-color: #667eea;
  }

  .table-container {
    max-height: 500px;
    overflow-y: auto;
  }

  .audit-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 0.5rem;
  }

  .audit-table thead tr {
    color: #6c757d;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .audit-table thead th {
    padding: 0.75rem;
    font-weight: 600;
    background: transparent;
    border: none;
  }

  .audit-table tbody tr {
    background: #f8f9fa;
    transition: all 0.2s ease;
  }

  .audit-table tbody tr:hover {
    background: #e9ecef;
    transform: scale(1.01);
  }

  .audit-table tbody td {
    padding: 1rem;
    border: none;
  }

  .audit-table tbody td:first-child {
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
  }

  .audit-table tbody td:last-child {
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
  }

  .sc-id-badge {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.85rem;
    display: inline-block;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #6c757d;
  }

  .empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .error-alert {
    background: #f8d7da;
    color: #721c24;
    padding: 1rem;
    border-radius: 8px;
    margin-top: 1rem;
    border: 1px solid #f5c6cb;
  }

  .spinner {
    animation: spin 1s linear infinite;
    display: inline-block;
    margin-right: 0.5rem;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

function App() {
  const [url, setUrl] = useState('');
  const [isCrawling, setIsCrawling] = useState(false);
  const [error, setError] = useState(null);
  const [allAuditResults, setAllAuditResults] = useState(null);
  const [selectedUrl, setSelectedUrl] = useState(null);
  const [activeTab, setActiveTab] = useState('Critical');

  // Initialize selected URL
  useEffect(() => {
    if (allAuditResults) {
      const allUrls = Object.keys(allAuditResults.results);
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
    const urlsToSend = url.split('\n').map(u => u.trim()).filter(u => u.length > 0);

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
        crawled_pages: Object.keys(resultsMap).length,
        results: resultsMap
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
      const report = allAuditResults.results[urlKey];
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

  // Get data
  const selectedReport = allAuditResults?.results[selectedUrl];
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
    const percentage = parseInt(String(score).match(/\d+/)?.[0] || '0');
    if (percentage >= 90) return '#28a745';
    if (percentage >= 70) return '#ffc107';
    return '#dc3545';
  };

  // HERO SCREEN
  if (!allAuditResults) {
    return (
      <>
        <style>{styles}</style>
        <div className="hero-section">
          <div className="hero-card">
            <div className="hero-icon">♿</div>
            <h1 className="hero-title">WCAG 2.2 Auditor</h1>
            <p className="hero-subtitle">
              AI-powered accessibility compliance checker. Identify WCAG 2.2 Level AA issues and get actionable fixes instantly.
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
              />
              <small style={{ color: '#6c757d', display: 'block', marginTop: '0.5rem' }}>
                💡 Enter one or multiple URLs, one per line
              </small>
            </div>

            {error && (
              <div className="error-alert">{error}</div>
            )}

            <button
              className="primary-btn"
              onClick={handleCrawl}
              disabled={isCrawling}
            >
              {isCrawling ? (
                <>
                  <span className="spinner">⏳</span>
                  Analyzing Accessibility...
                </>
              ) : (
                <>
                  <span style={{ marginRight: '0.5rem' }}>🚀</span>
                  Start Accessibility Audit
                </>
              )}
            </button>

            <div className="feature-list">
              <p>✓ WCAG 2.2 Level AA Compliance</p>
              <p>✓ AI-Powered Deep Analysis</p>
              <p>✓ Actionable Fix Recommendations</p>
              <p>✓ Multi-Page Crawling Support</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  // DASHBOARD VIEW
  return (
    <>
      <style>{styles}</style>
      <div className="dashboard-container">
        <Container fluid style={{ maxWidth: '1400px' }}>
          {/* Header */}
          <div className="dashboard-header">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h2 className="dashboard-title">Accessibility Audit Dashboard</h2>
                <p className="dashboard-subtitle">
                  {allAuditResults.crawled_pages} pages analyzed • WCAG 2.2 Level AA
                </p>
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button className="btn-outline-primary" onClick={handleBackToHome}>
                  ← New Scan
                </button>
                <button className="btn-download" onClick={handleDownloadReport}>
                  📥 Export CSV
                </button>
              </div>
            </div>
          </div>

          <Row>
            {/* Left Sidebar: URL List */}
            <Col md={4}>
              <div className="url-list">
                <h5 className="url-list-title">Scanned Pages ({allUrls.length})</h5>
                <div className="url-list-container">
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
                          background: isActive ? '#f0f4ff' : '#f8f9fa',
                          borderLeft: `4px solid ${isError ? '#dc3545' : getScoreColor(score)}`
                        }}
                      >
                        <div className="url-title">
                          {u.length > 50 ? `${u.substring(0, 47)}...` : u}
                        </div>
                        <div className="url-meta">
                          {isError ? (
                            <span style={{ color: '#dc3545' }}>⚠️ Audit Failed</span>
                          ) : (
                            <>
                              <span style={{ marginRight: '1rem' }}>🔴 {issuesCount} Issues</span>
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

            {/* Right Content: Report Details */}
            <Col md={8}>
              {selectedReport && summary ? (
                <>
                  {/* Score Card */}
                  <div className="score-card">
                    {/* New Audit Score Heading */}
                    <div className="score-heading">
                        AUDIT SCORE
                    </div>
                    <div
                      className="score-circle"
                      style={{
                        background: `linear-gradient(135deg, ${getScoreColor(summary.audit_score)} 0%, ${getScoreColor(summary.audit_score)}dd 100%)`
                      }}
                    >
                      {summary.audit_score}
                    </div>
                    <div className="score-grade">{summary.grade || 'N/A'}</div>
                    <div className="score-url">{summary.scanned_url}</div>
                  </div>

                  {/* Stats Grid */}
                  <div className="stats-grid">
                    <div className="stat-card" style={{ borderLeftColor: '#dc3545' }}>
                      <div className="stat-number" style={{ color: '#dc3545' }}>
                        {tabMapping['Critical'].length}
                      </div>
                      <div className="stat-label">Critical Issues</div>
                    </div>
                    <div className="stat-card" style={{ borderLeftColor: '#28a745' }}>
                      <div className="stat-number" style={{ color: '#28a745' }}>
                        {tabMapping['Passed'].length}
                      </div>
                      <div className="stat-label">Passed Checks</div>
                    </div>
                    <div className="stat-card" style={{ borderLeftColor: '#ffc107' }}>
                      <div className="stat-number" style={{ color: '#ffc107' }}>
                        {tabMapping['Manual'].length}
                      </div>
                      <div className="stat-label">Manual Review</div>
                    </div>
                    <div className="stat-card" style={{ borderLeftColor: '#6c757d' }}>
                      <div className="stat-number" style={{ color: '#6c757d' }}>
                        {tabMapping['Not Applicable'].length}
                      </div>
                      <div className="stat-label">Not Applicable</div>
                    </div>
                  </div>

                  {/* Tabs and Content */}
                  <div className="content-card">
                    <div className="tabs-container">
                      {Object.keys(tabMapping).map(key => (
                        <button
                          key={key}
                          onClick={() => setActiveTab(key)}
                          className={`tab-button ${activeTab === key ? 'active' : ''}`}
                        >
                          {key} ({tabMapping[key].length})
                        </button>
                      ))}
                    </div>

                    <div className="table-container">
                      {tabMapping[activeTab].length > 0 ? (
                        <table className="audit-table">
                          <thead>
                            <tr>
                              <th style={{ width: '15%' }}>SC ID</th>
                              <th style={{ width: activeTab === 'Critical' || activeTab === 'Manual' ? '45%' : '85%' }}>Description</th>
                              {(activeTab === 'Critical' || activeTab === 'Manual') && (
                                <th style={{ width: '40%' }}>Fix Recommendation</th>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {tabMapping[activeTab].map((item, index) => (
                              <tr key={index}>
                                <td>
                                  <span className="sc-id-badge">{item.sc_id || 'N/A'}</span>
                                </td>
                                <td style={{ color: '#2c3e50' }}>
                                  {item.description || 'N/A'}
                                </td>
                                {(activeTab === 'Critical' || activeTab === 'Manual') && (
                                  <td style={{ color: '#6c757d', fontSize: '0.9rem' }}>
                                    {item.fix_tip || 'N/A'}
                                  </td>
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
        </Container>
      </div>
    </>
  );
}

export default App;