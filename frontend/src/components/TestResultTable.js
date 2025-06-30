import React from "react";
import StatusDot from "./StatusDot";

function countryFlag(code) {
  if (!code || code.length !== 2) return "";
  const cc = code.toUpperCase();
  return String.fromCodePoint(
    0x1f1e6 + cc.charCodeAt(0) - 65,
    0x1f1e6 + cc.charCodeAt(1) - 65
  );
}

export default function TestResultTable({ data }) {
  if (!Array.isArray(data) || data.length === 0) return null;
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="modern-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Host</th>
            <th>IP</th>
            <th>Country</th>
            <th>Provider</th>
            <th>Latency</th>
            <th>Tag</th>
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={row.tag}>
              <td style={{ textAlign: "center" }}>
                <StatusDot alive={row.status === "ALIVE"} />
              </td>
              <td>{row.host}</td>
              <td>{row.ip}</td>
              <td style={{ textAlign: "center" }}>
                {countryFlag(row.country)} {row.country}
              </td>
              <td>{row.provider}</td>
              <td>
                {row.status === "ALIVE"
                  ? (row.latency || "-")
                  : "-"}
              </td>
              <td>{row.tag}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}