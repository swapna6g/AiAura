import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Container, Form, Button, Alert, Card, ListGroup, Tabs, Tab, Spinner, Table } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

// --- Helper Functions and Components ---

// AuditItem component: Standardize on item.description
const AuditItem = ({ item, index, showFixTip, isManual }) => { 
    
    // Ensure all fields are safe strings and include sc_id
    const scId = String(item.sc_id || 'N/A');
    const description = String(item.description || 'N/A'); 
    const fixTip = String(item.fix_tip || 'N/A'); 
    
    const columns = [
        <td key={`col-num-${index}`}>{index + 1}</td>,
        <td key={`col-scid-${index}`}>{scId}</td>, // Added SC ID column for clarity
        <td key={`col-desc-${index}`}>{description}</td>,
        showFixTip && <td key={`col-fix-${index}`}>{fixTip}</td>,
    ].filter(Boolean);

    return <tr key={`row-${index}`}>{columns}</tr>;
};

// --- Main Dashboard Component (App) ---
function App() {
    const [url, setUrl] = useState('');
    const [isCrawling, setIsCrawling] = useState(false);
    const [error, setError] = useState(null);
    const [allAuditResults, setAllAuditResults] = useState(null); 
    const [selectedUrl, setSelectedUrl] = useState(null);
    const [activeTab, setActiveTab] = useState('Critical');
    
    // 💡 STATE for dynamic config
    const [maxPagesToScan, setMaxPagesToScan] = useState(20); // Default value

    // 1. Initial URL Selection Logic
    useEffect(() => {
        if (allAuditResults) {
            const allUrls = Object.keys(allAuditResults.results);
            const firstUrl = allUrls.find(u => !allAuditResults.results[u].error) || allUrls[0];
            if (firstUrl) {
                setSelectedUrl(firstUrl);
            }
            setActiveTab('Critical');
        }
    }, [allAuditResults]);

    // 2. Dynamic Configuration Fetching
    useEffect(() => {
        const fetchConfig = async () => {
            try {
                // Fetching from the new /config endpoint
                const response = await axios.get('http://localhost:3001/config');
                const settings = response.data.AUDIT_SETTINGS;
                if (settings && settings.MAX_PAGES_TO_SCAN) {
                    // 💡 FIX 1: Dynamically update maxPagesToScan
                    setMaxPagesToScan(settings.MAX_PAGES_TO_SCAN);
                    console.log(`[Config] Max pages set to: ${settings.MAX_PAGES_TO_SCAN}`);
                }
            } catch (err) {
                // Log 404 error but continue with default (20)
                console.error("Failed to fetch configuration (Check for 404 on /config). Using default max pages.", err);
            }
        };
        fetchConfig();
    }, []); 
    
    // 3. 💡 FIX 2: Handler to fully reset the session state
    const handleBackToHome = useCallback(() => {
        setAllAuditResults(null); // Resets the results view (goes back to input screen)
        setUrl('');               // Clears the text area input
        setError(null);           // Clears any previous errors
        setSelectedUrl(null);
        setActiveTab('Critical');
    }, []);


    const handleCrawl = async () => {
        const urlsToSend = url
            .split('\n')
            .map(u => u.trim())
            .filter(u => u.length > 0);

        if (urlsToSend.length === 0) { 
            setError("Please enter a URL(s) to start the audit.");
            return;
        }
        
        // Enforce maxPagesToScan limit
        if (urlsToSend.length > maxPagesToScan) {
            setError(`You entered ${urlsToSend.length} URLs, but the maximum allowed is ${maxPagesToScan}. Please reduce the list.`);
            return;
        }
        
        setError(null);
        setIsCrawling(true);
        setAllAuditResults(null);
        setSelectedUrl(null);

        try {
            // Sending the entire multi-line string in the 'url' property for the backend to parse
            const response = await axios.post('http://localhost:3001/audit', { url }); 
            
            const resultsMap = response.data;
            const auditedCount = Object.keys(resultsMap).length;

            const structuredResults = {
                crawled_pages: auditedCount, 
                results: resultsMap 
            };
            
            setAllAuditResults(structuredResults);
            
            console.log('Audit Results Received:', structuredResults);
            
        } catch (err) {
            const errorMessage = err.response?.data?.error || `Failed to connect to the audit API or an unknown error occurred. Error: ${err.message}`;
            setError(errorMessage);
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
                
                // Escape quotes within the CSV fields
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
        if (link.download !== undefined) {
            const fileUrl = URL.createObjectURL(blob);
            link.setAttribute("href", fileUrl);
            link.setAttribute("download", "accessibility_audit_report.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };
    
    // DATA MAPPING
    const selectedReport = allAuditResults?.results[selectedUrl];
    
    // Handle error case for selected report
    if (selectedReport && selectedReport.error && !selectedReport.summary) {
        // Ensure summary object exists for display even on error
        selectedReport.summary = { scanned_url: selectedUrl, audit_score: 'Error', critical_count: 0, manual_count: 0, passed_count: 0, error: selectedReport.error };
    }
    
    const summary = selectedReport?.summary; 
    const allUrls = allAuditResults?.results ? Object.keys(allAuditResults.results) : [];

    const tabMapping = {
        'Critical': selectedReport?.automatic_results || [],
        'Passed': selectedReport?.passed_checks || [],
        'Manual': selectedReport?.manual_audits_required || [],
        'Not Applicable': selectedReport?.not_applicable || [],
    };
    
    const getScoreVariant = (score) => {
        if (score === 'N/A' || score === 'Error' || !score) return 'secondary';
        // Handle combined score format like "75.0% (Good)"
        const scoreMatch = String(score).match(/^(\d+\.?\d*)/);
        const percentage = scoreMatch ? parseInt(scoreMatch[1], 10) : 0;
        
        if (percentage >= 90) return 'success';
        if (percentage >= 70) return 'warning';
        return 'danger';
    };


    // --- RENDER LOGIC: The UI Structure ---
    if (!allAuditResults) {
        return (
            <Container className="my-5">
                <Card>
                    <Card.Body>
                        <Card.Title as="h1" className="text-center mb-4">🤖 AI-Powered WCAG 2.2 Auditor</Card.Title>
                        <Form>
                            <Form.Group className="mb-3">
                                <Form.Label>Enter URL(s) to Scan</Form.Label>
                                <Form.Control
                                    type="url"
                                    placeholder="Enter one URL per line"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    disabled={isCrawling}
                                    as="textarea"
                                    rows={4}
                                />
                                <Form.Text className="text-muted">
                                    Enter one or multiple URLs, one per line.
                                </Form.Text>
                            </Form.Group>
                            
                            {error && <Alert variant="danger">{error}</Alert>}
                            
                            <Button
                                variant="primary"
                                onClick={handleCrawl}
                                disabled={isCrawling}
                                className="w-100"
                            >
                                {isCrawling ? (
                                    <>
                                        <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" className="me-2" />
                                        Auditing Multiple Pages...
                                    </>
                                ) : (
                                    'Start New Scan'
                                )}
                            </Button>
                        </Form>
                    </Card.Body>
                </Card>
            </Container>
        );
    }
    
    // Case B: Results Display Page
    return (
        <Container fluid className="my-5"> 
            <h1 className="text-center mb-4">✅ Multi-Page Audit Dashboard</h1>
            
            <div className='d-flex justify-content-between mb-3'>
                {/* 💡 FIX 3: Updated button text and uses the full reset handler */}
                <Button variant="secondary" onClick={handleBackToHome}>
                    ← Welcome to Home Page
                </Button>
                <Button variant="success" onClick={handleDownloadReport} disabled={!allAuditResults}>
                    Download Full CSV Report
                </Button>
            </div>
            
            <Alert variant="success" className="text-center">
                Audit Complete! **{allAuditResults.crawled_pages || 0}** pages were successfully audited.
            </Alert>
            
            <div className="d-flex">
                {/* Left Panel: List of Crawled URLs */}
                <Card style={{ width: '30%', marginRight: '1rem', minWidth: '300px' }}>
                    <Card.Header as="h5">Audited Pages ({allUrls.length})</Card.Header>
                    <ListGroup variant="flush" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
                        {allUrls.map((u) => {
                            const urlReport = allAuditResults.results?.[u] || {};
                            const isError = !!urlReport.error;
                            const issuesCount = urlReport.summary?.critical_count ?? urlReport.automatic_results?.length ?? 0;
                            const score = urlReport.summary?.audit_score || 'N/A'; 
                            
                            return (
                                <ListGroup.Item
                                    key={u}
                                    action
                                    onClick={() => setSelectedUrl(u)}
                                    active={u === selectedUrl}
                                    title={u}
                                    variant={isError ? 'danger' : ''}
                                >
                                    {u.length > 50 ? `${u.substring(0, 47)}...` : u}
                                    {isError ? (
                                        <div className='text-danger'>**Audit Failed**</div>
                                    ) : (
                                        <small>Critical Issues: {issuesCount} | Score: {score}</small>
                                    )}
                                </ListGroup.Item>
                            );
                        })}
                    </ListGroup>
                </Card>

                {/* Right Panel: Selected Page Dashboard */}
                <div style={{ flex: 1 }}>
                    {selectedReport && summary ? (
                        <>
                            {selectedReport.error ? (
                                <Alert variant="danger" className="text-center">
                                    <h3>Audit Failed: {selectedReport.summary.error || 'Check logs for details.'}</h3>
                                    <p className='mb-0'>URL: {summary.scanned_url}</p>
                                </Alert>
                            ) : (
                                <Alert variant={getScoreVariant(summary.audit_score)} className="text-center">
                                    <h3>Audit Score: {summary.audit_score || 'N/A'}</h3>
                                    <p className='mb-0'>Auditing: {summary.scanned_url}</p>
                                </Alert>
                            )}
                            
                            <div className="d-flex justify-content-around mb-4">
                                <Card bg="danger" text="white" className="p-3 text-center w-25">
                                    <h4>Critical Issues</h4>
                                    <h2>{tabMapping['Critical'].length}</h2> 
                                </Card>
                                <Card bg="success" text="white" className="p-3 text-center w-25">
                                    <h4>Passed Audits</h4>
                                    <h2>{tabMapping['Passed'].length}</h2>
                                </Card>
                                <Card bg="warning" text="dark" className="p-3 text-center w-25">
                                    <h4>Required Manual</h4>
                                    <h2>{tabMapping['Manual'].length}</h2>
                                </Card>
                                <Card bg="secondary" text="white" className="p-3 text-center w-25">
                                    <h4>Not Applicable</h4>
                                    <h2>{tabMapping['Not Applicable'].length}</h2>
                                </Card>
                            </div>
                            
                            <Card>
                                <Tabs
                                    activeKey={activeTab}
                                    onSelect={(k) => setActiveTab(k)}
                                    className="mb-3"
                                    fill
                                >
                                    {Object.keys(tabMapping).map(key => {
                                        const items = tabMapping[key];
                                        
                                        let headers = ['No.', 'SC ID', 'Description']; // Added SC ID to header
                                       // let headers = ['No.',  'Description']; // Added SC ID to header
                                        let showFixTip = false;
                                        
                                        if (key === 'Critical' || key === 'Manual') {
                                            showFixTip = true;
                                            headers.push('Fix Tip');
                                        }

                                        
                                        return (
                                            <Tab 
                                                key={key} 
                                                eventKey={key} 
                                                title={`${key} (${items.length})`}
                                            >
                                                <div style={{ maxHeight: '50vh', overflowY: 'auto' }}>
                                                    {items.length > 0 ? (
                                                        <Table striped bordered hover size="sm">
                                                            <thead>
                                                                <tr>
                                                                    {headers.map(h => (
                                                                        <th key={h} style={{ width: (h === 'Description') ? '60%' : '15%' }}>{h}</th>
                                                                    ))}
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                {items.map((item, index) => (
                                                                    <AuditItem 
                                                                        key={index} 
                                                                        item={item} 
                                                                        index={index}
                                                                        showFixTip={showFixTip}
                                                                        isManual={key === 'Manual'} 
                                                                    />
                                                                ))}
                                                            </tbody>
                                                        </Table>
                                                    ) : (
                                                        <Alert variant="info" className="text-center">
                                                            No {key.toLowerCase()} checks reported for this category on the selected page.
                                                        </Alert>
                                                    )}
                                                </div>
                                            </Tab>
                                        );
                                    })}
                                </Tabs>
                            </Card>
                        </>
                    ) : (
                        <Alert variant="secondary" className="text-center">
                            Select a URL from the left panel to view the detailed audit report.
                        </Alert>
                    )}
                </div>
            </div>
        </Container> 
    );
}

export default App;