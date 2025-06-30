import React from "react";

export default function ProgressBar({ progress, total }) {
  const pct = total ? Math.floor((progress / total) * 100) : 0;
  return (
    <div style={{
      width: "100%",
      background: "#e9ecef",
      borderRadius: "8px",
      overflow: "hidden",
      margin: "8px 0"
    }}>
      <div style={{
        width: `${pct}%`,
        background: "#007bff",
        height: "20px",
        transition: "width 0.3s"
      }} />
    </div>
  );
}