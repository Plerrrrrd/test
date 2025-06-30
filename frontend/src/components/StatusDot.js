import React from "react";

export default function StatusDot({ alive }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 14,
        height: 14,
        borderRadius: "50%",
        background: alive ? "#28c76f" : "#EA5455",
        margin: "auto"
      }}
    />
  );
}