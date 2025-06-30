import React, { useState } from "react";
import GithubDropdown from "./components/GithubDropdown";
import ProgressBar from "./components/ProgressBar";
import TestResultTable from "./components/TestResultTable";
import { runTest, downloadGithubConfig, uploadGithubConfig } from "./api";
import { saveAs } from "file-saver";
import "./styles.css";

const GEOIP_OPTIONS = [
  { value: "ipinfo", label: "GeoIP (ipinfo.io)" },
  { value: "ip-api", label: "GeoIP (ip-api.com)" },
  { value: "whois", label: "WHOIS (lebih akurat, lambat)" }
];

export default function App() {
  const [githubFile, setGithubFile] = useState("");
  const [vpnLinks, setVpnLinks] = useState("");
  const [geoipMode, setGeoipMode] = useState("ipinfo");
  const [testing, setTesting] = useState(false);
  const [progress, setProgress] = useState({ progress: 0, total: 1 });
  const [testTable, setTestTable] = useState([]);
  const [configResult, setConfigResult] = useState(null);
  const [uploadMsg, setUploadMsg] = useState("");
  const [error, setError] = useState("");
  const [jsonTest, setJsonTest] = useState([]);

  const handleTest = async () => {
    setTesting(true);
    setUploadMsg("");
    setError("");
    setTestTable([]);
    setProgress({ progress: 0, total: 1 });

    try {
      const githubConfig = githubFile && githubFile !== "" ? githubFile : null;
      const lines = vpnLinks
        .split("\n")
        .map(l => l.trim())
        .filter(Boolean);
      const res = await runTest({
        links: lines,
        github_config: githubConfig,
        geoip_mode: geoipMode
      });
      setTestTable(res.test_table || []);
      setConfigResult(res.merged_config || null);
      setJsonTest(res.json_test || []);
      setProgress({ progress: res.test_table.length, total: res.test_table.length });
    } catch (e) {
      setError(
        e.response?.data?.detail?.toString() ||
        e.message ||
        "Gagal menjalankan test"
      );
    } finally {
      setTesting(false);
    }
  };

  const handleDownloadConfig = () => {
    if (!configResult) return;
    const blob = new Blob([JSON.stringify(configResult, null, 2)], { type: "application/json" });
    saveAs(blob, "merged-config.json");
  };

  const handleDownloadJson = () => {
    if (!jsonTest) return;
    const blob = new Blob([JSON.stringify(jsonTest, null, 2)], { type: "application/json" });
    saveAs(blob, "test-results.json");
  };

  const handleUploadGithub = async () => {
    if (!configResult) return;
    setUploadMsg("");
    try {
      const filename =
        (githubFile && githubFile !== "" ? githubFile : `merged-config-${Date.now()}.json`);
      const ok = await uploadGithubConfig(filename, configResult);
      if (ok) {
        setUploadMsg(`Berhasil upload ke GitHub: ${filename}`);
      } else {
        setUploadMsg("Gagal upload ke GitHub.");
      }
    } catch (e) {
      setUploadMsg("Gagal upload ke GitHub.");
    }
  };

  return (
    <div className="container">
      <div className="header">
        <span role="img" aria-label="shield" style={{ fontSize: 32, marginRight: 8 }}>🛡️</span>
        <span className="header-title">VPN Tester &amp; Auto Tag</span>
      </div>
      <div className="card">
        <GithubDropdown value={githubFile} onChange={opt => setGithubFile(opt.value)} />
        <div style={{ marginBottom: 12 }}>
          <label>Tambahkan link akun VPN baru (satu per baris):</label>
          <textarea
            className="textarea"
            value={vpnLinks}
            onChange={e => setVpnLinks(e.target.value)}
            rows={4}
            placeholder="Paste link VPN di sini..."
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <label>Mode Pengetesan:</label>
          <select
            value={geoipMode}
            onChange={e => setGeoipMode(e.target.value)}
            style={{ marginLeft: 8, padding: 4 }}
          >
            {GEOIP_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleTest}
          disabled={testing}
          style={{ width: "100%", marginBottom: 16 }}
        >
          {testing ? "Mengetes..." : "Test & Convert"}
        </button>
        {testing && <ProgressBar progress={progress.progress} total={progress.total} />}
        {error && <div className="error">{error}</div>}
        <TestResultTable data={testTable} />
        {uploadMsg && <div className="upload-msg">{uploadMsg}</div>}
        {testTable && testTable.length > 0 && (
          <div className="action-buttons">
            <button className="btn btn-success" onClick={handleDownloadConfig}>
              Download Config
            </button>
            <button className="btn btn-info" onClick={handleDownloadJson} style={{ marginLeft: 8 }}>
              Download JSON Hasil Test
            </button>
            <button className="btn btn-secondary" onClick={handleUploadGithub} style={{ marginLeft: 8 }}>
              Upload ke GitHub
            </button>
          </div>
        )}
      </div>
      <div className="footer">
        VPN Converter - by F4txhr
      </div>
    </div>
  );
}