import axios from "axios";
const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

export const getGithubFiles = async () => {
  const res = await axios.get(`${API}/github/files`);
  return res.data.files || [];
};

export const downloadGithubConfig = async (filename) => {
  const res = await axios.get(`${API}/github/download`, { params: { filename } });
  return res.data.content || "";
};

export const uploadGithubConfig = async (filename, config) => {
  const res = await axios.post(`${API}/github/upload`, new URLSearchParams({
    filename,
    content: typeof config === "string" ? config : JSON.stringify(config, null, 2)
  }));
  return res.data.ok;
};

export const runTest = async ({
  links,
  github_config,
  geoip_mode
}) => {
  const res = await axios.post(`${API}/test`, {
    links,
    github_config,
    geoip_mode
  });
  return res.data;
};