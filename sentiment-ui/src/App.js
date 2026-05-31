import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL;

function App() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [seconds, setSeconds] = useState(0);
  const timerRef = useRef(null);

  const upload = async () => {
    if (!file) return;
    setError('');
    setResult(null);
    setSeconds(0);

    // Start timer
    timerRef.current = setInterval(() => {
      setSeconds(prev => prev + 1);
    }, 1000);

    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API}/jobs`, formData);
      setJobId(res.data.job_id);
      setStatus('queued');
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
      clearInterval(timerRef.current);
    }
  };

  useEffect(() => {
    if (!jobId || status === 'completed' || status === 'failed') return;
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API}/jobs/${jobId}`);
        setStatus(res.data.status);
        if (res.data.status === 'completed') {
          const resultRes = await axios.get(`${API}/jobs/${jobId}/result`);
          setResult(resultRes.data);
          clearInterval(timerRef.current);
        }
        if (res.data.status === 'failed') {
          setError(res.data.error);
          clearInterval(timerRef.current);
        }
      } catch (err) {
        setError('Failed to check status');
        clearInterval(timerRef.current);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [jobId, status]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  return (
    <div style={{padding: 20, maxWidth: 800, margin: 'auto', fontFamily: 'Arial'}}>
      <h1>Consumer Sentiment - AI Analyzer</h1>

      <input type="file" accept=".pdf" onChange={e => setFile(e.target.files[0])} />
      <button onClick={upload} disabled={!file} style={{marginLeft: 10}}>Analyze</button>

      {jobId &&!result &&!error && <p>Processing... {seconds}s</p>}

      {jobId && <p><b>Job ID:</b> {jobId}</p>}
      {status && <p><b>Status:</b> {status}</p>}
      {error && <p style={{color: 'red'}}><b>Error:</b> {error}</p>}

      {result && (
        <div style={{marginTop: 20, border: '1px solid #ccc', padding: 15}}>
          <h2>Results</h2>
          <p><b>Summary:</b> {result.summary}</p>
          <p><b>Overall Sentiment:</b> {result.overall_sentiment}</p>
          <h3>Themes:</h3>
          <ul>
            {result.themes.map((t, i) => (
              <li key={i}><b>{t.name}</b> - Evidence: {t.evidence_ids.join(', ')}</li>
            ))}
          </ul>
          <h3>Recommended Actions:</h3>
          <ul>{result.recommended_actions.map((a, i) => <li key={i}>{a}</li>)}</ul>
          {result.limitations && <p><b>Limitations:</b> {result.limitations}</p>}
        </div>
      )}
    </div>
  );
}

export default App;