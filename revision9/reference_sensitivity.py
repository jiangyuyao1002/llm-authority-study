"""Recompute a fixed post-hoc exclusion sensitivity without changing scores."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scores', type=Path, required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source_hash = hashlib.sha256(args.scores.read_bytes()).hexdigest()
    review = json.loads(args.review.read_text(encoding='utf-8'))
    plan = json.loads(args.plan.read_text(encoding='utf-8'))
    with args.scores.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1080 and len({r['job_id'] for r in rows}) == 1080
    all_tasks = sorted(r['task_id'] for r in review['findings'])
    excluded = set(plan['excluded_task_ids'])
    assert excluded == {r['task_id'] for r in review['findings'] if r['category'] == 'C'}
    assert len(all_tasks) == len(set(all_tasks)) == 24 and len(excluded) == 3
    keyed = {(r['task_id'], r['model'], r['policy'], r['condition']): r for r in rows}
    assert len(keyed) == 1080
    models = ['qwen-plus-2025-01-25', 'qwen3.5-plus-2026-02-15', 'deepseek-v3']
    results = []
    supported = sorted(r['task_id'] for r in review['findings'] if r['category'] == 'A')
    assert len(supported) == 15
    for subset, tasks in [('all_24', all_tasks), ('exclude_C_21', [t for t in all_tasks if t not in excluded]), ('supported_A_15', supported)]:
        for model in models:
            vectors = {}
            for policy in ['boundary', 'binding_a']:
                for scoring in ['strict', 'normalized']:
                    vectors[policy, scoring] = np.array([
                        keyed[t, model, policy, 'correction'][scoring + '_joint_correct'] == 'True'
                        for t in tasks], dtype=int)
            ds = vectors['binding_a', 'strict'] - vectors['boundary', 'strict']
            dn = vectors['binding_a', 'normalized'] - vectors['boundary', 'normalized']
            interaction = ds - dn
            rng = np.random.default_rng(117733)
            indices = rng.integers(0, len(tasks), (10000, len(tasks)))
            item = {'subset': subset, 'model': model, 'n': len(tasks)}
            for (policy, scoring), vector in vectors.items():
                item[scoring + '_' + policy + '_correct'] = int(vector.sum())
            for name, vector in [('delta_strict', ds), ('delta_normalized', dn), ('interaction', interaction)]:
                low, high = np.quantile(vector[indices].mean(axis=1) * 100, [0.025, 0.975])
                item[name + '_pp'] = float(vector.mean() * 100)
                item[name + '_low_pp'] = float(low)
                item[name + '_high_pp'] = float(high)
            item['clean_boundary_normalized_correct'] = sum(keyed[t, model, 'boundary', 'clean']['normalized_joint_correct'] == 'True' for t in tasks)
            results.append(item)
    full = {r['model']: r for r in results if r['subset'] == 'all_24'}
    assert np.isclose(full['deepseek-v3']['interaction_pp'], -100 * 10 / 24)
    assert np.isclose(full['qwen3.5-plus-2026-02-15']['interaction_pp'], -100 * 7 / 24)
    assert full['qwen-plus-2025-01-25']['interaction_pp'] == 0
    assert np.allclose([full['deepseek-v3']['interaction_low_pp'], full['deepseek-v3']['interaction_high_pp']], [-62.5, -100 * 5 / 24])
    assert hashlib.sha256(args.scores.read_bytes()).hexdigest() == source_hash
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / 'reference_sensitivity.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    output = {'plan': plan, 'scores_sha256': source_hash,
              'item_review_sha256': hashlib.sha256(args.review.read_bytes()).hexdigest(),
              'plan_sha256': hashlib.sha256(args.plan.read_bytes()).hexdigest(),
              'source_unchanged': True, 'results': results}
    (args.output / 'reference_sensitivity.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    transitions = []
    for model in models:
        for policy in ['boundary', 'binding_a']:
            baseline = [t for t in all_tasks if keyed[t, model, policy, 'clean']['normalized_joint_correct'] == 'True']
            failed = [t for t in baseline if keyed[t, model, policy, 'correction']['normalized_joint_correct'] != 'True']
            transitions.append({'model': model, 'policy': policy, 'all_tasks': len(all_tasks),
                                'clean_correct': len(baseline), 'clean_correct_then_correction_incorrect': len(failed),
                                'task_ids_clean_correct': '|'.join(baseline), 'task_ids_transition': '|'.join(failed)})
    with (args.output / 'clean_correction_transitions.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(transitions[0]))
        writer.writeheader()
        writer.writerows(transitions)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
