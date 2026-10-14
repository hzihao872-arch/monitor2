"""Bounded read-only HTTP collection; never execute downloaded content."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'fetch_manifest.json'
LIMIT = 2 * 1024 * 1024
TOTAL_LIMIT = 6 * 1024 * 1024

def fetch(name, url):
    records = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else []
    target = ROOT / name
    if target.exists():
        print(json.dumps({'name': name, 'status': 'reused'}, ensure_ascii=False))
        return
    row = {'name': name, 'url': url, 'retrieved_utc': datetime.now(timezone.utc).isoformat()}
    try:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Research-source-audit/1.0'}), timeout=20) as r:
                row['head_status'] = r.status
                row['content_length'] = r.headers.get('Content-Length')
        except Exception as e:
            row['head_error'] = str(e)
        if row.get('content_length') and int(row['content_length']) > LIMIT:
            raise ValueError('HEAD size exceeds per-file limit')
        used = sum(x.get('bytes', 0) for x in records)
        cap = min(LIMIT, TOTAL_LIMIT - used)
        if cap <= 0:
            raise ValueError('batch budget exhausted')
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Research-source-audit/1.0'}), timeout=30) as r:
            size = r.headers.get('Content-Length')
            if size and int(size) > cap:
                raise ValueError('GET headers exceed remaining budget')
            data = r.read(cap + 1)
            if len(data) > cap:
                raise ValueError('stream exceeds bounded read')
            row['resolved_url'] = r.url
            row['content_type'] = r.headers.get('Content-Type')
        target.write_bytes(data)
        row.update(status='saved', bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    except Exception as e:
        row.update(status='failed', error=str(e))
    records.append(row)
    MANIFEST.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(row, ensure_ascii=False))

if __name__ == '__main__':
    import sys
    fetch(sys.argv[1], sys.argv[2])
