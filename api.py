from fastapi import FastAPI, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json

from vpn_core import (
    parse_link,
    test_and_generate_tag,
    merge_outbounds,
    get_config_template,
    github_list_files,
    github_download_file,
    github_upload_file,
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TestRequest(BaseModel):
    links: List[str]
    github_config: Optional[str] = None
    geoip_mode: Optional[str] = "ipinfo"

class TestResponse(BaseModel):
    test_table: list
    merged_config: dict
    json_test: list

@app.post("/test", response_model=TestResponse)
def test_config(req: TestRequest):
    template = get_config_template()
    selector_tags = ["Internet", "Best Latency", "Lock Region ID"]
    github_outbounds = []
    if req.github_config:
        # Download config dari github dan extract links
        cfg = github_download_file(req.github_config)
        if cfg:
            cfg = json.loads(cfg)
            for ob in cfg.get("outbounds", []):
                if ob.get("type") in ("shadowsocks", "trojan", "vless"):
                    # convert to link format for test ulang
                    # ... (bisa tambah fungsi outbound_to_link jika mau)
                    pass
    all_links = req.links # + github_links jika ingin combine
    outbounds = [parse_link(link) for link in all_links if link.strip()]
    outbounds = [x for x in outbounds if x]
    parsed, test_rows = test_and_generate_tag(outbounds, geoip_mode=req.geoip_mode)
    merged_outbounds = merge_outbounds(template, parsed, selector_tags)
    template["outbounds"] = merged_outbounds
    return TestResponse(
        test_table=test_rows,
        merged_config=template,
        json_test=test_rows
    )

@app.get("/github/files")
def github_files():
    return {"files": github_list_files()}

@app.get("/github/download")
def github_download(filename: str = Query(...)):
    content = github_download_file(filename)
    return {"content": content}

@app.post("/github/upload")
def github_upload(filename: str = Form(), content: str = Form()):
    ok = github_upload_file(filename, content, update=True)
    return {"ok": ok}