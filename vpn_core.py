import requests
import base64
import socket
import json
import re
from urllib.parse import urlparse, parse_qs, unquote
from config import GITHUB_REPO, GITHUB_BRANCH, GITHUB_TOKEN, GEOIP_API

def resolve_ip(host):
    try:
        return socket.gethostbyname(host)
    except Exception:
        return host

def is_alive(host, port=443):
    try:
        with socket.create_connection((host, int(port)), timeout=5):
            return True
    except Exception:
        return False

def geoip_ipinfo(ip):
    try:
        resp = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        data = resp.json()
        org = data.get('org','-')
        country = data.get('country','-')
        return org, country
    except Exception:
        return "-", "-"

def geoip_ipapi(ip):
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}?fields=country,countryCode,as,org", timeout=5)
        data = resp.json()
        org = data.get('as') or data.get('org') or '-'
        country = data.get('countryCode') or data.get('country') or '-'
        return org, country
    except Exception:
        return "-", "-"

def geoip_whois(ip):
    try:
        import whois
        import ipwhois
        w = ipwhois.IPWhois(ip)
        res = w.lookup_rdap()
        org = res.get('network', {}).get('name') or res.get('asn_description') or '-'
        country = res.get('network', {}).get('country') or '-'
        return org, country
    except Exception:
        return "-", "-"

def geoip_lookup(ip, mode="ipinfo"):
    if mode == "ipinfo":
        return geoip_ipinfo(ip)
    elif mode == "ip-api":
        return geoip_ipapi(ip)
    elif mode == "whois":
        return geoip_whois(ip)
    else:
        return geoip_ipinfo(ip)

def country_flag(country):
    if not country or len(country)!=2: return ""
    code = country.upper()
    return chr(0x1F1E6 + ord(code[0])-ord('A')) + chr(0x1F1E6 + ord(code[1])-ord('A'))

def extract_ip_port_from_path(path):
    m = re.search(r"/(\d+\.\d+\.\d+\.\d+)-(\d+)", path)
    if m:
        return m.group(1), int(m.group(2))
    return None, None

def get_host_to_test(server, ws_host):
    if ws_host:
        if ws_host.startswith(server + "."):
            return ws_host[len(server)+1:]
        return ws_host
    return server

def parse_ss(link):
    url = link.replace("ss://", "", 1)
    tag = ''
    if '#' in url:
        url, tag = url.split('#', 1)
        tag = unquote(tag)
    if '@' in url:
        base, rest = url.split('@', 1)
        base = unquote(base)
        try:
            decoded = base64.urlsafe_b64decode(base + '=' * (-len(base) % 4)).decode()
            method, password = decoded.split(':', 1)
        except Exception:
            method, password = base.split(':', 1)
        if '?' in rest:
            hostport, query = rest.split('?', 1)
        else:
            hostport, query = rest, ''
        if ':' in hostport:
            host, port = hostport.split(':', 1)
        else:
            host, port = hostport, ''
        query_params = parse_qs(query)
    else:
        if '?' in url:
            base, query = url.split('?', 1)
        else:
            base, query = url, ''
        base = unquote(base)
        try:
            decoded = base64.urlsafe_b64decode(base + '=' * (-len(base) % 4)).decode()
            if '@' in decoded:
                method_password, host_port = decoded.split('@', 1)
                method, password = method_password.split(':', 1)
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                else:
                    host, port = host_port, ''
            else:
                method, password = decoded.split(':', 1)
                host, port = '', ''
        except Exception:
            method = password = host = port = ''
        query_params = parse_qs(query)
        if not host and 'server' in query_params:
            host = query_params['server'][0]
        if not port and 'port' in query_params:
            port = query_params['port'][0]
    plugin = "v2ray-plugin"
    plugin_opts = []
    if query_params.get("type",[""])[0] == "ws":
        plugin_opts.append("mode=websocket")
    if "path" in query_params:
        plugin_opts.append(f"path={query_params['path'][0]}")
    if "host" in query_params:
        plugin_opts.append(f"host={query_params['host'][0]}")
    if "security" in query_params and query_params['security'][0] == "tls":
        plugin_opts.append("tls")
    if "sni" in query_params:
        plugin_opts.append(f"sni={query_params['sni'][0]}")
    if "encryption" in query_params:
        plugin_opts.append(f"encryption={query_params['encryption'][0]}")

    outbound = {
        "type": "shadowsocks",
        "tag": tag or host or "ss",
        "server": host,
        "server_port": int(port) if port else 443,
        "method": method,
        "password": password
    }
    if plugin_opts:
        outbound["plugin"] = plugin
        outbound["plugin_opts"] = ";".join(plugin_opts)
    outbound["_ss_ws_host"] = query_params['host'][0] if 'host' in query_params else ""
    outbound["_ss_path"] = query_params['path'][0] if 'path' in query_params else ""
    return outbound

def parse_vless(link):
    url = urlparse(link)
    params = parse_qs(url.query)
    net = params.get("type", ["ws"])[0]
    outbound = {
        "type": "vless",
        "tag": unquote(url.fragment) if url.fragment else url.hostname,
        "server": url.hostname,
        "server_port": int(url.port or 443),
        "uuid": url.username,
        "tls": {
            "enabled": params.get("security",["tls"])[0] == "tls",
            "server_name": params.get("sni", [url.hostname])[0],
            "insecure": params.get("allowInsecure",["false"])[0] == "true"
        },
        "transport": {}
    }
    if net == "ws":
        outbound["transport"] = {
            "type": "ws",
            "path": params.get("path", [""])[0],
            "headers": {"Host": params.get("host", [url.hostname])[0]}
        }
        outbound["_ws_host"] = params.get("host", [""])[0]
        outbound["_ws_path"] = params.get("path", [""])[0]
    else:
        outbound["_ws_host"] = ""
        outbound["_ws_path"] = ""
    return outbound

def parse_trojan(link):
    url = urlparse(link)
    params = parse_qs(url.query)
    outbound = {
        "type": "trojan",
        "tag": unquote(url.fragment) if url.fragment else url.hostname,
        "server": url.hostname,
        "server_port": int(url.port or 443),
        "password": url.username,
        "tls": {
            "enabled": params.get("security",["tls"])[0] == "tls",
            "server_name": params.get("sni", [url.hostname])[0],
            "insecure": params.get("allowInsecure",["false"])[0] == "true"
        },
        "transport": {}
    }
    net = params.get("type", ["ws"])[0]
    if net == "ws":
        outbound["transport"] = {
            "type": "ws",
            "path": params.get("path", [""])[0],
            "headers": {"Host": params.get("host", [url.hostname])[0]}
        }
        outbound["_ws_host"] = params.get("host", [""])[0]
        outbound["_ws_path"] = params.get("path", [""])[0]
    else:
        outbound["_ws_host"] = ""
        outbound["_ws_path"] = ""
    return outbound

def parse_link(link):
    if link.startswith('vless://'):
        return parse_vless(link)
    elif link.startswith('trojan://'):
        return parse_trojan(link)
    elif link.startswith('ss://'):
        return parse_ss(link)
    else:
        return None

def clean_outbound_fields(outbound):
    return {k: v for k, v in outbound.items() if not k.startswith("_")}

def github_headers():
    return {"Authorization": f"token {GITHUB_TOKEN}"}

def github_list_files():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/?ref={GITHUB_BRANCH}"
    r = requests.get(url, headers=github_headers())
    if r.status_code == 200:
        return [f["name"] for f in r.json() if f["type"] == "file"]
    return []

def github_download_file(filename):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}?ref={GITHUB_BRANCH}"
    r = requests.get(url, headers=github_headers())
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode()
        return content
    return None

def github_upload_file(filename, content, update=False):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    getr = requests.get(url, headers=github_headers())
    old_sha = getr.json()['sha'] if getr.status_code == 200 else None
    data = {
        "message": "Update via API",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": GITHUB_BRANCH
    }
    if update and old_sha:
        data["sha"] = old_sha
    r = requests.put(url, headers=github_headers(), data=json.dumps(data))
    return r.status_code in (200, 201)

def test_and_generate_tag(outbounds, geoip_mode="ipinfo"):
    result = []
    tag_count = {}
    table_rows = []
    for ob in outbounds:
        server = ob.get("server")
        port = ob.get("server_port", 443)
        ws_host = ob.get("_ss_ws_host") or ob.get("_ws_host") or ""
        host_to_test = get_host_to_test(server, ws_host)
        ip = resolve_ip(host_to_test)
        alive_host = is_alive(ip, port)
        path = ob.get("_ss_path") or ob.get("_ws_path") or ""
        ip_path, port_path = extract_ip_port_from_path(path) if path else (None, None)
        alive_path = False
        flag = org = country = ""
        tested_ip = ip
        if ip_path and port_path:
            alive_path = is_alive(ip_path, port_path)
            if alive_path:
                org, country = geoip_lookup(ip_path, geoip_mode)
                flag = country_flag(country)
                tested_ip = ip_path
        if not alive_path and alive_host:
            org, country = geoip_lookup(ip, geoip_mode)
            flag = country_flag(country)
        base_tag = (flag + " " + (org if org != "-" else country if country != "-" else tested_ip)).strip()
        tag_count.setdefault(base_tag, 0)
        tag_count[base_tag] += 1
        tag = f"{base_tag}{tag_count[base_tag]}"
        status = "ALIVE" if alive_host or alive_path else "DEAD"
        table_rows.append({
            "no": len(table_rows)+1, 
            "tag": tag, 
            "host": host_to_test, 
            "ip": tested_ip,
            "provider": org,
            "country": country,
            "status": status,
            "host_status": "ALIVE" if alive_host else "DEAD",
            "path_status": "ALIVE" if alive_path else "DEAD",
            "path_ip": ip_path or "-"
        })
        if alive_host or alive_path:
            ob["tag"] = tag
            result.append(ob)
    return result, table_rows

def merge_outbounds(template, parsed_outbounds, selector_tags):
    selectors = [ob for ob in template["outbounds"] if ob.get("tag") in selector_tags]
    tags = [ob["tag"] for ob in parsed_outbounds]
    for selector in selectors:
        util_tags = [t for t in selector.get("outbounds", []) if t not in selector_tags]
        selector["outbounds"] = tags + util_tags
    parsed_tags = set(tags)
    other_outbounds = [
        ob for ob in template["outbounds"] 
        if ob.get("tag") not in selector_tags and ob.get("tag") not in parsed_tags
    ]
    return selectors + [clean_outbound_fields(ob) for ob in parsed_outbounds] + other_outbounds

def get_config_template():
    with open("singbox-template.txt") as f:
        return json.load(f)
        
