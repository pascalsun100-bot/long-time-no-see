#!/usr/bin/env python3
"""PowerContext 1.4.1 minimal smoke test, no third-party Python dependencies."""
import argparse, json, os, sys, urllib.request, urllib.error

BASE = os.environ.get('POWERCONTEXT_URL', 'http://127.0.0.1:8000').rstrip('/')
TOKEN = os.environ.get('POWERCONTEXT_TOKEN')
SCOPE = os.environ.get('POWERCONTEXT_SCOPE_ID')

def call(path, payload):
    if not TOKEN or TOKEN.startswith('REPLACE_'):
        raise RuntimeError('Set POWERCONTEXT_TOKEN in your environment')
    req = urllib.request.Request(BASE + path, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError('HTTP %s: %s' % (e.code, e.read().decode('utf-8','replace'))) from e

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('action',choices=['init','remember','query'])
    ap.add_argument('--scope',default=SCOPE)
    ap.add_argument('--query',default='玩家 学院 专业 主修 信息安全')
    args=ap.parse_args()
    if args.action=='init':
        data=call('/v1/scopes', {'title':'Long Time No See - Evaluation', 'summary':'Independent reproduction scope', 'idempotency_key':'long-time-no-see-evaluation-demo-001'})
        print(json.dumps(data,ensure_ascii=False,indent=2)); print('Set POWERCONTEXT_SCOPE_ID to the returned scope_id.');return
    if not args.scope or args.scope.startswith('REPLACE_'): raise RuntimeError('Set POWERCONTEXT_SCOPE_ID / --scope first')
    if args.action=='remember':
        data=call('/v1/memory/remember', {'scope_id': args.scope, 'kind': 'fact','text':'玩家目前就读于计算机学院，主修信息安全专业。','reason':'Evaluation demonstration: explicitly provided player background.'})
    else:
        data=call('/v1/context/prepare',{'scope_id':args.scope, 'query':args.query,'max_bytes':8000})
        if isinstance(data.get('content'),str):
            print('--- prepared content ---');print(data['content'])
    print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':
    try: main()
    except Exception as ex: print('ERROR:',ex,file=sys.stderr);sys.exit(1)
