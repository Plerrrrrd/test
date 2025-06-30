import React, { useEffect, useState } from "react";
import Select from "react-select";
import { getGithubFiles } from "../api";

export default function GithubDropdown({ value, onChange }) {
  const [options, setOptions] = useState([]);
  useEffect(() => {
    getGithubFiles().then(files => {
      setOptions([
        { value: "", label: "(Buat config baru)" },
        ...files.map(f => ({ value: f, label: f }))
      ]);
    });
  }, []);
  return (
    <div style={{ marginBottom: 12 }}>
      <label>Pilih file config dari GitHub:</label>
      <Select
        value={options.find(o => o.value === value) || options[0]}
        onChange={onChange}
        options={options}
        isSearchable
        styles={{
          container: base => ({ ...base, marginTop: 4 }),
          menu: base => ({ ...base, zIndex: 9999 })
        }}
      />
    </div>
  );
}