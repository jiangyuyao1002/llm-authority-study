"""Analyze the additive batch without pooling it with original generations."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scoring import normalized, parse, score

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()
    protocol = json.loads((ROOT / 'protocol.json').read_text(encoding='utf-8'))
    for name, digest in protocol['frozen_files_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    cases = {(c['task_id'], c['condition']): c for c in json.loads((ROOT / 'cases.json').read_text(encoding='utf-8'))}
    jobs = {j['job_id']: j for j in map(json.loads, (ROOT / 'jobs.jsonl').read_text(encoding='utf-8').splitlines())}
    raw = [json.loads(s) for s in (ROOT / 'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(raw) == len({r['job_id'] for r in raw})
    if not args.partial:
        assert len(raw) == len(jobs) == 576
    rows = []
    for record in raw:
        assert record['job_id'] in jobs
        assert record['request_sha256'] == jobs[record['job_id']]['request_sha256']
        assert record['response']['model'] == record['model']
        assert protocol['frozen_at_utc'] < record['started_at_utc']
        case = cases[record['task_id'], record['condition']]
        choice = record['response']['choices'][0]
        content = choice['message'].get('content')
        strict, norm = parse(content), normalized(content)
        row = {k: record[k] for k in ['job_id', 'task_id', 'condition', 'model', 'policy', 'repeat']}
        row.update({prefix + k: v for prefix, obj in [('strict_', strict), ('normalized_', norm)] for k, v in score(obj, case).items()})
        usage = record['response'].get('usage', {})
        row.update(fence_recovered=strict is None and norm is not None, finish_reason=choice.get('finish_reason'),
                   prompt_tokens=usage.get('prompt_tokens', 0), completion_tokens=usage.get('completion_tokens', 0),
                   reasoning_tokens=usage.get('completion_tokens_details', {}).get('reasoning_tokens', 0))
        assert row['strict_joint_correct'] <= row['normalized_joint_correct']
        rows.append(row)
    result = ROOT / 'results'
    result.mkdir(exist_ok=True)

    def write_csv(name, records):
        with (result / name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)

    write_csv('trial_scores.csv', rows)
    counts = []
    for condition in protocol['conditions']:
        for policy in protocol['policies']:
            cell = [r for r in rows if (r['condition'], r['policy']) == (condition, policy)]
            counts.append({'condition': condition, 'policy': policy, 'n': len(cell),
                           **{k: sum(int(r[k]) for r in cell) for k in ['strict_joint_correct', 'normalized_joint_correct', 'fence_recovered']},
                           'length_finishes': sum(r['finish_reason'] == 'length' for r in cell),
                           'reasoning_tokens': sum(r['reasoning_tokens'] for r in cell)})
    write_csv('condition_counts.csv', counts)
    audit = {'completed': len(rows), 'planned': len(jobs), 'complete': len(rows) == len(jobs),
             'request_hashes_verified': True, 'protocol_before_all_task_requests': True,
             'model': protocol['model'], 'api_base': protocol['api_base'],
             'finish_reasons': dict(Counter(r['finish_reason'] for r in rows)),
             'prompt_tokens': sum(r['prompt_tokens'] for r in rows), 'completion_tokens': sum(r['completion_tokens'] for r in rows),
             'reasoning_tokens': sum(r['reasoning_tokens'] for r in rows), 'old_responses_pooled': False}
    if len(rows) == len(jobs):
        key = {(r['task_id'], r['condition'], r['policy'], r['repeat']): r for r in rows}
        review = json.loads((ROOT / 'reference_review.json').read_text(encoding='utf-8'))['findings']
        subsets = [('all_24', sorted(r['task_id'] for r in review)),
                   ('exclude_C_21', sorted(r['task_id'] for r in review if r['category'] != 'C')),
                   ('only_A_15', sorted(r['task_id'] for r in review if r['category'] == 'A'))]
        contrasts, distributions = [], []
        for subset, tasks in subsets:
            for condition in protocol['conditions']:
                for rep in ['mean_of_3', 0, 1, 2]:
                    vectors = {}
                    for policy in protocol['policies']:
                        for mode in ['strict', 'normalized']:
                            vectors[policy, mode] = np.array([np.mean([key[t, condition, policy, r][mode + '_joint_correct'] for r in (range(3) if rep == 'mean_of_3' else [rep])]) for t in tasks])
                    metrics = []
                    for a, b in [('binding_a', 'boundary'), ('binding_a', 'length_control_complete'), ('length_control_complete', 'length_control_truncated')]:
                        for mode in ['strict', 'normalized']:
                            metrics.append((f'{a} - {b}', mode, vectors[a, mode] - vectors[b, mode]))
                    metrics.append(('binding_a - boundary', 'interaction', (vectors['binding_a', 'strict'] - vectors['boundary', 'strict']) - (vectors['binding_a', 'normalized'] - vectors['boundary', 'normalized'])))
                    rng = np.random.default_rng(112323)
                    indices = rng.integers(0, len(tasks), (10000, len(tasks)))
                    for contrast, mode, vector in metrics:
                        lo, hi = np.quantile(vector[indices].mean(axis=1) * 100, [.025, .975])
                        contrasts.append({'subset': subset, 'condition': condition, 'repetition': rep, 'contrast': contrast, 'parser': mode,
                                          'tasks': len(tasks), 'difference_pp': float(vector.mean() * 100), 'low_pp': float(lo), 'high_pp': float(hi)})
            for condition in protocol['conditions']:
                for policy in protocol['policies']:
                    for t in tasks:
                        distributions.append({'subset': subset, 'condition': condition, 'policy': policy, 'task_id': t,
                                              **{mode + '_correct_out_of_3': sum(key[t, condition, policy, r][mode + '_joint_correct'] for r in range(3)) for mode in ['strict', 'normalized']}})
        write_csv('paired_contrasts.csv', contrasts)
        write_csv('per_task_repetition_counts.csv', distributions)
        (result / 'paired_contrasts.json').write_text(json.dumps(contrasts, indent=2) + '\n', encoding='utf-8')
    (result / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
