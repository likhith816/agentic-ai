import React, { useState, useRef } from 'react';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';


const Icon = ({ name, size = 18, color = 'currentColor' }) => {
  const icons = {
    mic: <><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></>,
    upload: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>,
    file: <><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></>,
    sparkle: <><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z"/></>,
    check: <><polyline points="20 6 9 17 4 12"/></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
    alert: <><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
    wrench: <><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></>
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
};

const parseMarkdown = (text) => {
  if (!text) return '';
  const lines = text.split('\n');
  return lines.map((line, idx) => {
    let currentLine = line;
    const isBullet = currentLine.trim().startsWith('* ') || currentLine.trim().startsWith('- ');
    if (isBullet) {
      currentLine = currentLine.trim().substring(2);
    }
    const parts = [];
    let lastIndex = 0;
    const regex = /\*\*(.*?)\*\*/g;
    let match;
    while ((match = regex.exec(currentLine)) !== null) {
      const matchIndex = match.index;
      if (matchIndex > lastIndex) {
        parts.push(currentLine.substring(lastIndex, matchIndex));
      }
      parts.push(<strong key={matchIndex}>{match[1]}</strong>);
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < currentLine.length) {
      parts.push(currentLine.substring(lastIndex));
    }
    if (isBullet) {
      return (
        <li key={idx} style={{ marginLeft: '16px', listStyleType: 'disc', margin: '4px 0', fontSize: '13px', lineHeight: '1.4' }}>
          {parts.length > 0 ? parts : currentLine}
        </li>
      );
    }
    return (
      <p key={idx} style={{ margin: '6px 0', fontSize: '13px', lineHeight: '1.4' }}>
        {parts.length > 0 ? parts : currentLine}
      </p>
    );
  });
};

function App() {
  const [activeTab, setActiveTab] = useState('wizard'); // 'wizard' or 'dashboard'
  const [query, setQuery] = useState('');
  const [eqId, setEqId] = useState('');
  const [image, setImage] = useState(null);
  const [csv, setCsv] = useState(null);
  const [pdf, setPdf] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [agentStep, setAgentStep] = useState('');
  const [result, setResult] = useState(null);
  const [chatLog, setChatLog] = useState([]);

  // Dashboard states
  const [dashboardData, setDashboardData] = useState(null);
  const [predictionsData, setPredictionsData] = useState(null);
  const [overdueData, setOverdueData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  // Floating Guide Chatbot states
  const [guideOpen, setGuideOpen] = useState(false);
  const [guideQuery, setGuideQuery] = useState('');
  const [guideChatLog, setGuideChatLog] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your agentic-ai Guide. I can help you learn how to use this platform, explain our multi-agent diagnostics, or guide you on how to troubleshoot plant equipment. How can I assist you today?'
    }
  ]);
  const [guideLoading, setGuideLoading] = useState(false);
  const guideChatEndRef = useRef(null);

  const imgRef = useRef(null);
  const csvRef = useRef(null);
  const pdfRef = useRef(null);

  const fetchDashboardData = async () => {
    setDashboardLoading(true);
    try {
      const [summaryRes, predRes, overdueRes] = await Promise.all([
        axios.get(`${API}/summary`),
        axios.get(`${API}/predictions`),
        axios.get(`${API}/service-overdue`)
      ]);
      setDashboardData(summaryRes.data);
      setPredictionsData(predRes.data);
      setOverdueData(overdueRes.data);
    } catch (e) {
      console.error("Failed to fetch dashboard data", e);
    }
    setDashboardLoading(false);
  };

  const handleLaunch = async () => {
    if (!query && !image && !csv) return;
    setLoading(true);
    setResult(null);
    setAgentStep('Orchestrator Routing Inputs...');

    // Append user query to conversation logs
    const userMessage = { role: 'user', content: query || 'Analyze files.' };
    const updatedChatLog = [...chatLog, userMessage];
    setChatLog(updatedChatLog);

    try {
      const fd = new FormData();
      if (query) fd.append('query', query);
      else fd.append('query', 'Analyze provided files for diagnosis.');
      
      if (eqId) fd.append('equipment_id', eqId);
      if (image) fd.append('image', image);
      if (csv) fd.append('csv_file', csv);
      if (pdf) fd.append('documents', pdf);
      
      // Append JSON chat history for context-aware multi-turn conversational reasoning
      fd.append('chat_history', JSON.stringify(chatLog));

      // Simulate steps
      setTimeout(() => setAgentStep('Vision Agent analyzing image...'), 1000);
      setTimeout(() => setAgentStep('Anomaly Agent scanning sensor data...'), 2500);
      setTimeout(() => setAgentStep('RAG Agent searching SOPs...'), 4000);
      setTimeout(() => setAgentStep('Diagnostic Agent synthesizing...'), 5500);

      const res = await axios.post(`${API}/diagnose`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,   // 2 min timeout for long pipeline runs
      });
      
      setResult(res.data);

      // Append AI reply to conversation logs
      const aiReply = res.data.diagnosis?.fault_identified || res.data.report?.summary || 'No diagnosis available.';
      setChatLog(prev => [...prev, { role: 'assistant', content: aiReply }]);
      
      // Clear query box for follow-up dialog
      setQuery('');
    } catch (e) {
      const isNetworkErr = !e.response || e.code === 'ERR_NETWORK' || e.message === 'Network Error';
      const detail = isNetworkErr
        ? '🔴 Backend offline — the server is not responding. Please wait a moment and click Retry.'
        : (e.response?.data?.detail || e.message || 'Pipeline failed. Please try again.');
      setResult({ error: detail, canRetry: true });
    }
    
    setLoading(false);
  };


  const handleFeedback = async (outcome) => {
    if (!result) return;
    try {
      const fd = new FormData();
      fd.append('report_id', result.report?.report_id || 'UNKNOWN');
      fd.append('diagnosis_correct', outcome === 'RESOLVED');
      fd.append('outcome', outcome);
      fd.append('equipment_id', eqId || result.diagnosis?.equipment_id || 'Unknown ID');
      fd.append('actual_fault', outcome === 'RESOLVED' ? (result.diagnosis?.fault_identified || '') : 'Corrective maintenance required');
      fd.append('actual_steps_taken', 'Following corrective action steps outlined in database.');
      fd.append('engineer_notes', 'Feedback submitted from Web UI interface.');

      await axios.post(`${API}/feedback`, fd);
      alert(`Feedback "${outcome}" submitted successfully. Knowledge base FAISS index will be updated with this correction.`);
    } catch (e) {
      alert(`Failed to submit feedback: ${e.message}`);
    }
  };

  const clearChat = () => {
    setChatLog([]);
    setResult(null);
  };

  const handleGuideSend = async (customQuery = null) => {
    const textToSend = customQuery || guideQuery;
    if (!textToSend || !textToSend.trim()) return;

    const userMessage = { role: 'user', content: textToSend };
    const newChatLog = [...guideChatLog, userMessage];
    setGuideChatLog(newChatLog);
    setGuideQuery('');
    setGuideLoading(true);

    // Auto scroll to bottom
    setTimeout(() => {
      guideChatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);

    try {
      const res = await axios.post(`${API}/guide`, {
        query: textToSend,
        chat_history: guideChatLog
      });

      if (res.data && res.data.response) {
        setGuideChatLog(prev => [...prev, { role: 'assistant', content: res.data.response }]);
      } else {
        setGuideChatLog(prev => [...prev, { role: 'assistant', content: 'Sorry, I got an empty response.' }]);
      }
    } catch (e) {
      setGuideChatLog(prev => [...prev, { role: 'assistant', content: `Error: ${e.response?.data?.detail || e.message}` }]);
    }
    setGuideLoading(false);

    // Auto scroll to bottom
    setTimeout(() => {
      guideChatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  return (
    <div className="app-container">
      {/* HEADER */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">AA</div>
          <div>
            <h1>agentic-ai</h1>
            <span>Intelligent Maintenance Decision-Support Platform</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Tata Steel AI Hackathon 2026</div>
          <div style={{ background: 'var(--accent-glow)', border: '1px solid var(--border)', padding: '6px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, color: 'var(--accent)' }}>
            Status: Agents Online
          </div>
        </div>
      </header>

      {true ? (
        /* TROUBLESHOOTING WIZARD TAB */
        <div className="main-layout">
          {/* LEFT: INPUT WIZARD */}
          <div className="wizard-panel">
            <h2 style={{ fontSize: 18, marginBottom: 8 }}>Input Diagnosis Data</h2>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 24 }}>Provide logs, sensor data, or visual evidence to start the multi-agent pipeline.</p>

            <div className="section-title">1. Operational Inputs</div>
            <div className="input-group">
              <label>Equipment ID (Optional)</label>
              <input type="text" className="form-control" placeholder="e.g. BF-001" value={eqId} onChange={e => setEqId(e.target.value)} />
            </div>
            <div className="input-group">
              <label>{chatLog.length > 0 ? "Follow-up Query / Response" : "Engineer Query / Error Log"}</label>
              <textarea className="form-control" placeholder="Describe the issue, or paste error codes..." value={query} onChange={e => setQuery(e.target.value)} />
            </div>

            <div className="section-title">2. Condition Monitoring & Visual</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
              <input type="file" ref={imgRef} style={{ display: 'none' }} accept="image/*" onChange={e => setImage(e.target.files[0])} />
              <div className={`upload-btn ${image ? 'active' : ''}`} onClick={() => imgRef.current?.click()}>
                <Icon name="upload" size={16} /> {image ? 'Image Added' : 'Photo'}
              </div>

              <input type="file" ref={csvRef} style={{ display: 'none' }} accept=".csv" onChange={e => setCsv(e.target.files[0])} />
              <div className={`upload-btn ${csv ? 'active' : ''}`} onClick={() => csvRef.current?.click()}>
                <Icon name="file" size={16} /> {csv ? 'CSV Added' : 'Sensor Data'}
              </div>
            </div>

            <div className="section-title">3. Knowledge Context</div>
            <div className="input-group">
              <input type="file" ref={pdfRef} style={{ display: 'none' }} accept=".pdf,.txt" onChange={e => setPdf(e.target.files[0])} />
              <div className={`upload-btn ${pdf ? 'active' : ''}`} onClick={() => pdfRef.current?.click()}>
                <Icon name="file" size={16} /> {pdf ? 'Manual Added' : 'Upload Manual / SOP (PDF)'}
              </div>
            </div>

            <button className="launch-btn" onClick={handleLaunch} disabled={loading || (!query && !image && !csv)}>
              <Icon name="sparkle" size={18} />
              Launch Multi-Agent Pipeline
            </button>
            
            {chatLog.length > 0 && (
              <button className="btn-secondary" style={{ marginTop: 12, width: '100%', justifyContent: 'center' }} onClick={clearChat}>
                Reset Conversation Thread
              </button>
            )}
          </div>

          {/* RIGHT: OUTPUT RESULTS */}
          <div className="results-panel">
            {loading && (
              <div className="loading-overlay">
                <div className="spinner"></div>
                <div className="agent-status">{agentStep}</div>
              </div>
            )}

            {chatLog.length > 0 && (
              <div className="chat-log-container">
                <div className="section-title">💬 Chat Log & Conversational Context</div>
                <div className="chat-messages-box">
                  {chatLog.map((msg, idx) => (
                    <div key={idx} className={`chat-message ${msg.role}`}>
                      <div className="chat-sender">{msg.role === 'user' ? '👤 Maintenance Engineer' : '🧠 agentic-ai Assistant'}</div>
                      <div className="chat-body">{parseMarkdown(msg.content)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!result && !loading && chatLog.length === 0 && (
              <div className="empty-state">
                <Icon name="wrench" size={48} color="var(--border)" />
                <h2>Awaiting Input</h2>
                <p>Enter data on the left to generate explainable recommendations.</p>
              </div>
            )}

            {result && result.error && (
              <div className="result-card" style={{ borderColor: 'var(--critical-border)', marginTop: 16 }}>
                <h3 style={{ color: 'var(--critical)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Icon name="alert" /> Pipeline Error
                </h3>
                <p style={{ marginTop: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>{result.error}</p>
                {result.canRetry && (
                  <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(255,200,0,0.08)', borderRadius: 8, borderLeft: '3px solid var(--warning, #f59e0b)' }}>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
                      💡 <strong>Troubleshooting:</strong> The backend server may have restarted. Try again in a few seconds.
                    </p>
                    <button
                      className="launch-btn"
                      style={{ padding: '8px 20px', fontSize: 13 }}
                      onClick={() => { setResult(null); handleLaunch(); }}
                    >
                      ↺ Retry
                    </button>
                  </div>
                )}
              </div>
            )}


            {result && !result.error && (
              <div style={{ marginTop: 16 }}>
                <div className="result-card">
                  <div className="result-header">
                    <div>
                      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Diagnosis & Action Plan</h2>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Session: {result.session_id}</div>
                    </div>
                    <div className={`risk-badge ${(result.risk_level || 'LOW').toLowerCase()}`}>
                      RISK: {result.risk_level || 'UNKNOWN'}
                    </div>
                  </div>

                  <div className="grid-2">
                    <div className="data-box">
                      <h4><Icon name="sparkle" size={14} /> Probable Fault & Root Cause</h4>
                      <p style={{ fontSize: 14, color: 'var(--text-main)', lineHeight: 1.6 }}>
                        {result.diagnosis?.fault_identified || result.report?.summary || "No specific fault identified."}
                      </p>
                      {result.diagnosis?.root_cause && (
                        <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-muted)' }}>
                          <strong>Root Cause:</strong> {result.diagnosis.root_cause}
                        </div>
                      )}
                      {result.vision_output && result.vision_output.fault_detected && (
                        <div style={{ marginTop: 12, padding: 10, background: 'rgba(37, 99, 235, 0.05)', borderRadius: 6, fontSize: 12 }}>
                          <strong>Vision AI Detected:</strong> {result.vision_output.fault_type} on {result.vision_output.affected_component}
                        </div>
                      )}
                    </div>

                    <div className="data-box">
                      <h4><Icon name="alert" size={14} /> Sensor Anomaly & RUL</h4>
                      {result.anomaly_result ? (
                        <div>
                          <div style={{ fontSize: 24, fontWeight: 700, color: result.anomaly_result.rul_days < 7 ? 'var(--critical)' : 'var(--text-main)' }}>
                            {result.anomaly_result.rul_days} Days RUL
                          </div>
                          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                            {result.anomaly_result.anomaly_detected ? "⚠️ Critical sensor anomalies detected." : "✅ Sensor readings within normal ranges."}
                          </p>
                          {result.anomaly_result.anomalous_sensor && (
                            <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>
                              Outlier: {result.anomaly_result.anomalous_sensor} ({result.anomaly_result.current_value} vs {result.anomaly_result.normal_range})
                            </div>
                          )}
                        </div>
                      ) : (
                        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No sensor CSV provided for anomaly detection.</p>
                      )}
                    </div>
                  </div>

                  <div className="data-box" style={{ marginTop: 24 }}>
                    <h4><Icon name="wrench" size={14} /> Step-by-Step Maintenance Recommendation</h4>
                    {result.diagnosis?.repair_steps && result.diagnosis.repair_steps.length > 0 ? (
                      <ul className="step-list">
                        {result.diagnosis.repair_steps.map((step, idx) => (
                          <li key={idx}>{step}</li>
                        ))}
                      </ul>
                    ) : (
                      <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No specific repair steps generated. Refer to general SOP.</p>
                    )}
                  </div>

                  {result.diagnosis?.change_plan && result.diagnosis.change_plan.length > 0 && (
                    <div className="data-box" style={{ marginTop: 24 }}>
                      <h4><Icon name="wrench" size={14} /> Safe Components Change & Modification Plan</h4>
                      <ul className="step-list">
                        {result.diagnosis.change_plan.map((step, idx) => (
                          <li key={idx}>{step}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.diagnosis?.diagnosis_questions && result.diagnosis.diagnosis_questions.length > 0 && (
                    <div className="data-box" style={{ marginTop: 24, borderLeft: '3px solid var(--accent)' }}>
                      <h4><Icon name="sparkle" size={14} /> Diagnostic Follow-up Questions for Engineer</h4>
                      <ol style={{ paddingLeft: 20, margin: '12px 0 0 0', color: 'var(--text-main)', fontSize: 14 }}>
                        {result.diagnosis.diagnosis_questions.map((question, idx) => (
                          <li key={idx} style={{ marginBottom: 10, lineHeight: 1.6 }}>{question}</li>
                        ))}
                      </ol>
                    </div>
                  )}

                  <div className="feedback-section">
                    <div style={{ fontSize: 13, fontWeight: 600 }}>Did this solve the issue? (Submits to FAISS database learning loop)</div>
                    <div style={{ display: 'flex', gap: 12 }}>
                      <button className="btn-secondary" onClick={() => handleFeedback('RESOLVED')}>
                        <Icon name="check" size={14} color="var(--low)" /> Yes, Resolved
                      </button>
                      <button className="btn-secondary" onClick={() => handleFeedback('ESCALATED')}>
                        <Icon name="alert" size={14} color="var(--critical)" /> No, Correction Required
                      </button>
                    </div>
                  </div>
                </div>

                {/* REPORT DOWNLOAD */}
                {result.report && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 12 }}>
                    <a href={`${API}/report/${result.session_id}`} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                      <button className="btn-secondary" style={{ background: 'var(--accent)', color: 'white', border: 'none' }}>
                        <Icon name="download" size={16} /> Download Full PDF Report
                      </button>
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* PLANT HEALTH DASHBOARD TAB */
        <div className="dashboard-container">
          {dashboardLoading ? (
            <div className="empty-state">
              <div className="spinner"></div>
              <p style={{ marginTop: 16 }}>Aggregating plant KPIs & analytics...</p>
            </div>
          ) : (
            <div className="dashboard-content">
              {dashboardData && (
                <div style={{ padding: 24 }}>
                  <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Tata Steel Plant KPIs</h2>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>Overview of Jamshedpur Works facility status, logs database, and analytics.</p>
                  
                  <div className="metric-grid">
                    <div className="metric-card">
                      <div className="metric-header">
                        <h4>Total Monitored Units</h4>
                      </div>
                      <span className="metric-value">{dashboardData.total_equipment}</span>
                    </div>
                    <div className="metric-card">
                      <div className="metric-header">
                        <h4>Aggregate Sensor Records</h4>
                      </div>
                      <span className="metric-value">{dashboardData.total_sensor_readings?.toLocaleString()}</span>
                    </div>
                    <div className="metric-card">
                      <div className="metric-header">
                        <h4>Active Anomaly Flags</h4>
                      </div>
                      <span className="metric-value critical">{dashboardData.total_anomalies_detected}</span>
                    </div>
                    <div className="metric-card">
                      <div className="metric-header">
                        <h4>Plant Anomaly Rate</h4>
                      </div>
                      <span className="metric-value">{dashboardData.anomaly_rate}%</span>
                    </div>
                    <div className="metric-card">
                      <div className="metric-header">
                        <h4>Total Maintenance Logs</h4>
                      </div>
                      <span className="metric-value">{dashboardData.total_maintenance_logs} Logs</span>
                    </div>
                    <div className="metric-card">
                      <div className="metric-header">
                        <h4>Unplanned Downtime</h4>
                      </div>
                      <span className="metric-value high">{dashboardData.total_downtime_hours} hrs</span>
                    </div>
                  </div>
                </div>
              )}

              {predictionsData && predictionsData.predictions && (
                <div style={{ padding: '0 24px 24px 24px' }}>
                  <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Remaining Useful Life (RUL) & Equipment Alarms</h3>
                  <div className="dashboard-table-container">
                    <table className="dashboard-table">
                      <thead>
                        <tr>
                          <th>Equipment ID</th>
                          <th>Equipment Type</th>
                          <th>Status Risk</th>
                          <th>RUL (Days)</th>
                          <th>Failure Probability</th>
                          <th>Avg Temperature</th>
                          <th>Avg Vibration</th>
                          <th>Operational Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {predictionsData.predictions.map((p, idx) => (
                          <tr key={idx}>
                            <td style={{ fontWeight: 700 }}>{p.equipment_id}</td>
                            <td>{p.equipment_type}</td>
                            <td>
                              <span className={`risk-badge ${p.risk_level.toLowerCase()}`} style={{ display: 'inline-block', fontSize: 11, padding: '2px 8px' }}>
                                {p.risk_level}
                              </span>
                            </td>
                            <td style={{ fontWeight: 700, color: p.rul_days < 7 ? 'var(--critical)' : 'inherit' }}>
                              {p.rul_days} Days RUL
                            </td>
                            <td>{Math.round(p.failure_probability * 100)}%</td>
                            <td>{p.avg_temperature} °C</td>
                            <td>{p.avg_vibration} mm/s</td>
                            <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>{p.recommended_action}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {overdueData && overdueData.overdue && (
                <div style={{ padding: '0 24px 24px 24px' }}>
                  <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Service Overdue Alerts & Overhaul Schedules</h3>
                  <div className="dashboard-table-container">
                    <table className="dashboard-table">
                      <thead>
                        <tr>
                          <th>Equipment ID</th>
                          <th>Equipment Type</th>
                          <th>Last Service Date</th>
                          <th>Days Since Last Service</th>
                          <th>Service Interval</th>
                          <th>Overdue Days</th>
                          <th>Urgency Alert</th>
                        </tr>
                      </thead>
                      <tbody>
                        {overdueData.overdue.map((o, idx) => (
                          <tr key={idx}>
                            <td style={{ fontWeight: 700 }}>{o.equipment_id}</td>
                            <td>{o.equipment_type}</td>
                            <td>{o.last_service_date}</td>
                            <td>{o.days_since_service} Days</td>
                            <td>{o.service_interval_days} Days</td>
                            <td style={{ fontWeight: 700, color: o.is_overdue ? 'var(--high)' : 'var(--low)' }}>
                              {o.is_overdue ? `${o.overdue_by_days} Days` : 'OK'}
                            </td>
                            <td>
                              <span className={`risk-badge ${o.urgency.toLowerCase()}`} style={{ display: 'inline-block', fontSize: 11, padding: '2px 8px' }}>
                                {o.urgency}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* FLOATING GUIDE CHATBOT */}
      <div className={`floating-guide-container ${guideOpen ? 'open' : ''}`}>
        {guideOpen ? (
          <div className="guide-chat-window">
            <div className="guide-chat-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div className="guide-avatar">🧠</div>
                <div>
                  <h3 style={{ fontSize: 13, fontWeight: 700, margin: 0, color: 'white' }}>agentic-ai Guide Assistant</h3>
                  <span style={{ fontSize: 10, color: 'rgba(255, 255, 255, 0.85)' }}>Online | Support Agent</span>
                </div>
              </div>
              <button className="guide-close-btn" onClick={() => setGuideOpen(false)}>×</button>
            </div>
            
            <div className="guide-chat-body">
              {guideChatLog.map((msg, idx) => (
                <div key={idx} className={`guide-message ${msg.role}`}>
                  <div className="guide-message-content">
                    {parseMarkdown(msg.content)}
                  </div>
                </div>
              ))}
              {guideLoading && (
                <div className="guide-message assistant typing">
                  <div className="guide-message-content">
                    <span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
                  </div>
                </div>
              )}
              <div ref={guideChatEndRef} />
            </div>

            {/* Quick replies */}
            <div className="guide-quick-replies">
              <button onClick={() => handleGuideSend("Show me dashboard features")}>📊 Dashboard</button>
              <button onClick={() => handleGuideSend("How do I troubleshoot BF-001?")}>🔥 BF-001 Guide</button>
              <button onClick={() => handleGuideSend("How does feedback database loop work?")}>🔄 Feedback Loop</button>
            </div>

            <div className="guide-chat-footer">
              <input 
                type="text" 
                placeholder="Ask me how agentic-ai works..." 
                value={guideQuery}
                onChange={e => setGuideQuery(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleGuideSend(); }}
              />
              <button onClick={() => handleGuideSend()}>Send</button>
            </div>
          </div>
        ) : (
          <button className="guide-chat-bubble" onClick={() => setGuideOpen(true)}>
            <span style={{ fontSize: 20 }}>❓</span>
            <span className="guide-tooltip">Need Help?</span>
          </button>
        )}
      </div>
    </div>
  );
}

export default App;
