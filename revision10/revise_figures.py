"""Reproduce three Experiment 1 panels with corrected labels and unchanged scores."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scores', type=Path, required=True)
parser.add_argument('--contrasts', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
with args.scores.open(encoding='utf-8-sig', newline='') as stream:
    rows = [{k: v == 'True' if v in ('True', 'False') else v for k, v in row.items()} for row in csv.DictReader(stream)]
with args.contrasts.open(encoding='utf-8-sig', newline='') as stream:
    contrasts = {(r['model'], r['condition'], r['parser']): r for r in csv.DictReader(stream)}
assert len(rows) == 1152 and len({r['job_id'] for r in rows}) == 1152
models = ['qwen-plus-2025-01-25', 'qwen3.5-plus-2026-02-15']
policies = ['task_only', 'boundary', 'evidence_binding']
conditions = ['clean', 'role_spoof', 'workflow_pretext', 'correction_claim']
model_labels = ['Qwen-Plus', 'Qwen3.5-Plus']
policy_labels = ['Task only', 'Boundary', 'Evidence binding']
condition_labels = ['Clean', 'Role spoofing', 'Workflow pretext', 'Correction claim']
plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
                     'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False,
                     'svg.fonttype': 'none', 'pdf.fonttype': 42})
args.output.mkdir(parents=True, exist_ok=True)
data = []

# Contract: distinguish accepted values from the composite schema-or-route rejection.
fig, axes = plt.subplots(1, 2, figsize=(7.09, 3.35), layout='constrained')
for ax, model, label in zip(axes, models, model_labels):
    left = np.zeros(3)
    for metric, color, legend in [('guard_correct', '#6F9D8C', 'Accepted, correct value'),
                                   ('guard_wrong_value', '#C78869', 'Accepted, wrong value'),
                                   ('guard_block', '#AEB6C0', 'Rejected: schema or route')]:
        values = []
        for policy in policies:
            rr = [r for r in rows if r['model'] == model and r['policy'] == policy and r['condition'] != 'clean']
            assert len(rr) == 144
            count = sum(r[metric] for r in rr)
            values.append(100 * count / 144)
            data.append({'figure': 'figure3_guard', 'model': model, 'policy': policy, 'condition': 'attacked',
                         'metric': metric, 'count': count, 'n': 144, 'difference': '', 'low': '', 'high': ''})
            if metric == 'guard_block':
                invalid = sum(not r['schema_valid'] for r in rr)
                unauthorized = sum(r['unauthorized_route'] for r in rr)
                assert invalid + unauthorized == count
                data.extend({'figure': 'figure3_guard', 'model': model, 'policy': policy, 'condition': 'attacked',
                             'metric': key, 'count': n, 'n': 144, 'difference': '', 'low': '', 'high': ''}
                            for key, n in [('rejected_schema_invalid', invalid), ('rejected_unauthorized_route', unauthorized)])
        ax.barh(range(3), values, left=left, color=color, label=legend, height=.58)
        for i, value in enumerate(values):
            if value >= 8:
                ax.text(left[i] + value / 2, i, f'{value:.1f}', ha='center', va='center', fontsize=7)
        left += values
    assert np.allclose(left, 100)
    ax.set_yticks(range(3), ['Task only', 'Boundary', 'Evidence\nbinding'], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel('All attacked trials (%); n = 144 per policy', fontsize=7)
    ax.set_title(label, loc='left', fontsize=9, weight='bold')
handles, legends = axes[0].get_legend_handles_labels()
fig.legend(handles, legends, loc='outside lower center', ncol=3, fontsize=7, frameon=False)
for ext in ['pdf', 'svg', 'png']:
    fig.savefig(args.output / ('figure3_guard.' + ext), dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)

# Contract: retain all frozen point estimates and task-level intervals.
fig, ax = plt.subplots(figsize=(7.09, 3.7), layout='constrained')
ys, tick_labels = [], []
for mi, model in enumerate(models):
    for ci, condition in enumerate(conditions):
        r = contrasts[model, condition, 'strict']
        difference, low, high = [float(r[k]) for k in ['difference', 'low', 'high']]
        aa = [r for r in rows if r['model'] == model and r['policy'] == 'evidence_binding' and r['condition'] == condition]
        bb = [r for r in rows if r['model'] == model and r['policy'] == 'boundary' and r['condition'] == condition]
        assert len(aa) == len(bb) == 48 and int(r['clusters']) == 24
        assert np.isclose(difference, np.mean([r['joint_correct'] for r in aa]) - np.mean([r['joint_correct'] for r in bb]))
        y = mi * 5 + ci
        ax.errorbar(100 * difference, y, xerr=[[100 * (difference - low)], [100 * (high - difference)]],
                    fmt='o', color=['#497999', '#9B705A'][mi], capsize=3, markersize=4)
        ys.append(y)
        tick_labels.append(model_labels[mi] + ' | ' + condition_labels[ci])
        data.append({'figure': 'figure4_effects', 'model': model, 'policy': 'binding_minus_boundary', 'condition': condition,
                     'metric': 'strict_joint_correct_contrast', 'count': '', 'n': 24,
                     'difference': difference, 'low': low, 'high': high})
ax.axvline(0, color='#B5BDC4', linewidth=.8)
ax.set_yticks(ys, tick_labels, fontsize=7)
ax.invert_yaxis()
ax.set_xlabel('Evidence binding minus boundary: joint correctness (percentage points)')
ax.set_title('Paired effects; task-level bootstrap 95% intervals', loc='left', fontsize=9, weight='bold')
for ext in ['pdf', 'svg', 'png']:
    fig.savefig(args.output / ('figure4_effects.' + ext), dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)

# Contract: the same strict/normalized counts, now with unambiguous endpoint labels.
fig, axes = plt.subplots(1, 2, figsize=(7.09, 3.85), layout='constrained')
for ax, metric, clean in [(axes[0], 'task_success', True), (axes[1], 'guard_wrong_value', False)]:
    ys, tick_labels = [], []
    for mi, model in enumerate(models):
        for pi, policy in enumerate(policies):
            rr = [r for r in rows if r['model'] == model and r['policy'] == policy and ((r['condition'] == 'clean') == clean)]
            n = 48 if clean else 144
            assert len(rr) == n
            strict = sum(r[metric] for r in rr)
            normalized = sum(r['normalized_' + metric] for r in rr)
            a, b, y = 100 * strict / n, 100 * normalized / n, mi * 4 + pi
            ax.plot([a, b], [y, y], color='#B6BEC6', linewidth=1.5)
            ax.plot(a, y, 'o', color='#497999', label='Strict' if y == 0 else None)
            ax.plot(b, y, 's', color='#B27B57', markerfacecolor='none', markersize=7, markeredgewidth=1.4,
                    label='Fence-normalized' if y == 0 else None)
            ys.append(y)
            tick_labels.append(model_labels[mi] + ' | ' + policy_labels[pi])
            data.extend({'figure': 'figure5_parser', 'model': model, 'policy': policy,
                         'condition': 'clean' if clean else 'attacked', 'metric': key, 'count': value,
                         'n': n, 'difference': '', 'low': '', 'high': ''}
                        for key, value in [(metric, strict), ('normalized_' + metric, normalized)])
    ax.set_yticks(ys, tick_labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlim(-3, 103)
    ax.set_title('Clean task success' if clean else 'Attacked: wrong value accepted', loc='left', fontsize=9, weight='bold')
    ax.set_xlabel('Responses (%)', fontsize=8)
axes[0].legend(loc='lower left', bbox_to_anchor=(0, -.32), ncol=2, fontsize=7, frameon=False)
for ext in ['pdf', 'svg', 'png']:
    fig.savefig(args.output / ('figure5_parser.' + ext), dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
with (args.output / 'figure_source_data.csv').open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(data[0]))
    writer.writeheader()
    writer.writerows(data)
print(json.dumps({'rows': len(rows), 'source_data_rows': len(data), 'figures': ['figure3_guard', 'figure4_effects', 'figure5_parser']}))
