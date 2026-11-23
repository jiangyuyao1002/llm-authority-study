"""Collect the frozen additive jobs using an environment-provided credential."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--key-env', default='STUDY_API_KEY')
    args = parser.parse_args()
    protocol = json.loads((ROOT / 'protocol.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT / 'protocol.json').read_bytes()).hexdigest() == (ROOT / 'protocol.sha256').read_text().strip()
    for name, digest in protocol['frozen_files_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    jobs = [json.loads(s) for s in (ROOT / 'jobs.jsonl').read_text(encoding='utf-8').splitlines()]
    for job in jobs:
        encoded = json.dumps(job['payload'], ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        assert hashlib.sha256(encoded).hexdigest() == job['request_sha256']
    completed = [json.loads(s) for s in (ROOT / 'responses.jsonl').read_text(encoding='utf-8').splitlines()] if (ROOT / 'responses.jsonl').exists() else []
    attempts = [json.loads(s) for s in (ROOT / 'http_attempts.jsonl').read_text(encoding='utf-8').splitlines()] if (ROOT / 'http_attempts.jsonl').exists() else []
    done = {r['job_id'] for r in completed}
    assert len(done) == len(completed)
    todo = [j for j in jobs if j['job_id'] not in done]
    if args.limit:
        todo = todo[:args.limit]
    print(json.dumps({'complete_before': len(done), 'planned': len(jobs), 'scheduled': len(todo), 'live_calls': args.run}), flush=True)
    if not args.run:
        return
    credential = os.environ.get(args.key_env)
    if not credential:
        raise SystemExit('Configured credential variable is unavailable; no requests sent.')
    state = {'last_start': 0.0, 'attempts': len(attempts), 'tokens': sum(r.get('response', {}).get('usage', {}).get('total_tokens', 0) for r in attempts), 'completed': len(done)}
    lock = threading.Lock()
    rate = threading.Lock()
    halted = threading.Event()
    config = protocol['collection']

    def append(name, record):
        with lock:
            with (ROOT / name).open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + '\n')

    def call(job):
        encoded = json.dumps(job['payload'], ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        for attempt in range(config['transport_attempts_per_job']):
            with rate:
                if halted.is_set():
                    return
                time.sleep(max(0, config['global_min_interval_seconds'] - (time.monotonic() - state['last_start'])))
                state['last_start'] = time.monotonic()
                with lock:
                    if halted.is_set() or state['tokens'] >= config['reported_token_limit'] or state['attempts'] >= config['max_http_attempts']:
                        halted.set()
                        return
                    state['attempts'] += 1
            record = {k: job[k] for k in ['job_id', 'task_id', 'condition', 'model', 'policy', 'repeat', 'request_sha256']}
            record.update(started_at_utc=datetime.now(timezone.utc).isoformat(), attempt=attempt + 1)
            request = urllib.request.Request(protocol['api_base'] + '/chat/completions', data=encoded, headers={'Authorization': 'Bearer ' + credential, 'Content-Type': 'application/json'})
            started = time.monotonic()
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    body = json.load(response)
            except urllib.error.HTTPError as error:
                record.update(status='http_error', http_status=error.code)
                # Do not persist server error bodies, which can echo request credentials.
                append('http_attempts.jsonl', record)
                if error.code in [401, 402, 403] or error.code not in [429, 500, 502, 503, 504]:
                    halted.set()
                    return
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as error:
                record.update(status='transport_error', error_type=type(error).__name__)
                append('http_attempts.jsonl', record)
            else:
                if 'choices' not in body or not body['choices']:
                    record.update(status='invalid_api_envelope')
                    append('http_attempts.jsonl', record)
                    halted.set()
                    return
                record.update(status='completed' if body.get('model') == job['model'] else 'model_mismatch', response=body, elapsed_seconds=time.monotonic() - started)
                with lock:
                    state['tokens'] += body.get('usage', {}).get('total_tokens', 0)
                append('http_attempts.jsonl', record)
                if record['status'] == 'completed':
                    append('responses.jsonl', record)
                    with lock:
                        state['completed'] += 1
                        if state['completed'] % 12 == 0:
                            print(json.dumps({'completed': state['completed'], 'http_attempts': state['attempts'], 'reported_tokens': state['tokens']}), flush=True)
                else:
                    halted.set()
                return
            if attempt < config['transport_attempts_per_job'] - 1:
                time.sleep([5, 12][attempt])

    with concurrent.futures.ThreadPoolExecutor(max_workers=config['workers']) as executor:
        list(executor.map(call, todo))
    print(json.dumps({'finished': True, 'completed': state['completed'], 'planned': len(jobs), 'http_attempts': state['attempts'], 'reported_tokens': state['tokens'], 'halted': halted.is_set()}), flush=True)
    if state['completed'] != len(jobs):
        raise SystemExit('Collection incomplete; retained responses are resumable.')


if __name__ == '__main__':
    main()
