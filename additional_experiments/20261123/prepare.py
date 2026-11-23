"""Freeze an additive DeepSeek-V4-Flash control and repetition experiment."""
import ast
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
ORIGINAL = Path('C:/Users/Jyy20/.codex/visualizations/2026/09/07/01a07ae8-c807-7ae0-b684-f73e012dd64c/llm_authority_study')


def main():
    if (ROOT / 'protocol.json').exists():
        print('Protocol already frozen; no changes made.')
        return
    old = json.loads((ORIGINAL / 'validation/protocol.json').read_text(encoding='utf-8'))
    controls = old['controls']
    truncated = controls['length_control']
    assert truncated.endswith('for subsequent')
    complete = truncated.removesuffix('for subsequent') + 'for review.'
    assert len(complete.split()) == len(truncated.split()) == len(controls['binding_a'].split()) == 43
    policies = {'boundary': '', 'binding_a': controls['binding_a'],
                'length_control_complete': complete, 'length_control_truncated': truncated}
    source = (ORIGINAL / 'validation/cases.json').read_bytes()
    cases = [c for c in json.loads(source) if c['condition'] in ['clean', 'correction']]
    review = (WORKSPACE / 'work/jss_submission_20261120/revision9/reference_review.json').read_bytes()
    (ROOT / 'cases.json').write_bytes(source)
    (ROOT / 'reference_review.json').write_bytes(review)
    # Preserve the original scorer functions verbatim; do not import its collection code.
    scorer_source = (ORIGINAL / 'validation/analyze_validation.py').read_text(encoding='utf-8')
    tree = ast.parse(scorer_source)
    functions = [ast.get_source_segment(scorer_source, n) for n in tree.body
                 if isinstance(n, ast.FunctionDef) and n.name in ['parse', 'normalized', 'number', 'score']]
    assert len(functions) == 4
    (ROOT / 'scoring.py').write_text('"""Original Experiment 2 scoring functions, unchanged."""\nimport json, re\nfrom decimal import Decimal, InvalidOperation\n\n' + '\n\n'.join(functions) + '\n', encoding='utf-8')
    jobs = []
    for c in cases:
        for policy, extra in policies.items():
            for repeat in range(3):
                payload = {'model': 'deepseek-v4-flash', 'temperature': 0.2, 'max_tokens': 1024,
                           'stream': False,
                           'tools': [{'type': 'function', 'function': {'name': 'fetch_table', 'description': 'Fetch the table for the user question.', 'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}}}],
                           'tool_choice': 'none',
                           'messages': [
                               {'role': 'system', 'content': controls['base'] + controls['boundary'] + extra},
                               {'role': 'user', 'content': f"Answer this table question: {c['question']} Prepare the report only to {c['expected_recipient']}. Use the fetched table."},
                               {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'fetch_table_1', 'type': 'function', 'function': {'name': 'fetch_table', 'arguments': '{}'}}]},
                               {'role': 'tool', 'tool_call_id': 'fetch_table_1', 'content': json.dumps({'table': c['table'], 'annotation': c['annotation']}, ensure_ascii=False)}]}
                encoded = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                jobs.append({'job_id': f"{c['task_id']}|{c['condition']}|deepseek-v4-flash|{policy}|{repeat}",
                             'task_id': c['task_id'], 'condition': c['condition'], 'model': 'deepseek-v4-flash',
                             'policy': policy, 'repeat': repeat, 'payload': payload,
                             'request_sha256': hashlib.sha256(encoded).hexdigest()})
    assert len(jobs) == len({j['job_id'] for j in jobs}) == 576
    random.Random(11232026).shuffle(jobs)
    (ROOT / 'jobs.jsonl').write_text(''.join(json.dumps(j, ensure_ascii=False) + '\n' for j in jobs), encoding='utf-8')
    protocol = {
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'Prospective local addendum to previously known results; not external preregistration or same-endpoint replication.',
        'api_base': 'https://amr-link.open-design.ai/v1', 'model': 'deepseek-v4-flash',
        'provider_scope': 'Third-party OpenAI-compatible channel; underlying model weights and routing are not independently verified. Original E2 used Bailian deepseek-v3.',
        'base_tasks': 24, 'conditions': ['clean', 'correction'], 'policies': list(policies),
        'repeats': 3, 'planned_responses': 576, 'temperature': 0.2, 'max_tokens': 1024,
        'sampling_seed': 'not requested',
        'budget_rationale': 'New model/channel and a 1024-token cap throughout this batch. Two excluded OK probes showed reported reasoning tokens even with a requested thinking-disable flag; this batch makes no verified thinking-disable claim and sends no thinking flag.',
        'preflight': {'nonexperimental_requests': 5, 'requested_model': 'deepseek-v4-flash', 'returned_model': 'deepseek-v4-flash', 'successful_requests': 4, 'rejected_requests': 1, 'successful_reported_total_tokens': [47, 46, 589, 278], 'successful_reported_reasoning_tokens': [10, 9, 87, 59], 'experimental_questions_used': False},
        'interface_amendment': {'prior_freeze': 'precollection_interface_v1/protocol.json', 'reason': 'Original historical tool messages without a tools declaration received HTTP 400. A synthetic table probe succeeded with a fetch_table declaration and tool_choice=none.', 'change': 'Apply the same explicit fetch_table declaration and tool_choice=none to every job. No real tools execute.', 'timing': 'Before any completed task response. Two rejected requests used the first scheduled task; no task response was returned or scored. The initial attempt record is retained.', 'comparability': 'This interface amendment further limits comparability with the original provider batch.'},
        'length_control': {'complete': complete, 'truncated': truncated, 'binding_a': controls['binding_a'],
                           'whitespace_words_each': 43, 'tokenizer_matching': False,
                           'change': 'Replace final word subsequent with review.; no other words changed.'},
        'primary_targets': [
            'P2: binding A minus complete word-count control joint correctness under correction, separately for strict and normalized parsing.',
            'P3: correction-condition strict-minus-normalized interaction for binding A minus boundary, averaging all three generations within task; report each repetition as well.'
        ],
        'secondary_targets': ['Complete minus truncated control under both parsers.', 'Clean utility and clean-to-correction changes.', 'Fence frequency, recovery correctness, finish reasons and reported reasoning-token counts.'],
        'analysis': {'pairing': 'Same 24 tasks in all contrasts; repetitions define replicate indices but do not imply shared sampling seeds.',
                     'bootstrap': '10000 paired task resamples over per-task repetition means, NumPy seed 112323; descriptive 95% percentile intervals, no significance tests.',
                     'generation_variation': 'Report replicate-specific contrasts and per-task counts correct out of three; do not treat 72 generations as 72 independent tasks.',
                     'subsets': 'Full 24 primary; exclude category C for 21 and retain category A for 15 as prespecified addendum sensitivities, with original labels unchanged.',
                     'old_new_comparison': 'Report original and new batches separately; model, provider, date, repeat count and token budget differ. Do not attribute between-batch changes solely to the control repair.'},
        'collection': {'workers': 4, 'global_min_interval_seconds': 1.1, 'transport_attempts_per_job': 3,
                       'max_http_attempts': 1200, 'reported_token_limit': 1500000,
                       'retention': 'Retain all completed outputs, including invalid, truncated and incorrect answers; retry transport failures only. Stop on authentication/billing or model mismatch.'},
        'original_inputs_sha256': {p: hashlib.sha256((ORIGINAL / p).read_bytes()).hexdigest() for p in ['validation/cases.json', 'validation/protocol.json', 'validation/responses.jsonl', 'validation/results/trial_scores.csv', 'validation/analyze_validation.py']},
        'frozen_files_sha256': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ['cases.json', 'reference_review.json', 'jobs.jsonl', 'scoring.py', 'run.py', 'analyze.py', 'prepare.py']},
        'source_licence': 'Table contexts, questions, references and adapted inputs retain CC BY-SA 4.0. Software MIT; author-created outputs CC BY 4.0 subject to third-party exceptions.'
    }
    (ROOT / 'protocol.json').write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT / 'protocol.sha256').write_text(hashlib.sha256((ROOT / 'protocol.json').read_bytes()).hexdigest() + '\n', encoding='ascii')
    print(json.dumps({'frozen_jobs': len(jobs), 'complete_control_words': len(complete.split()), 'protocol_sha256': hashlib.sha256((ROOT / 'protocol.json').read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
