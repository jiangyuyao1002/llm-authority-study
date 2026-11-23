"""Verify stored strict/fence scores and first-object replay without model calls."""
import ast
import csv
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location('first_object', ROOT / 'revision6/first_object.py')
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    comparisons = 0
    records = []
    hashes = {}
    for experiment, raw_name, case_name, scores_name, script_name, names, normalized_name, scorer_name, id_key in [
        ('E1', 'data/responses.jsonl', 'data/cases.json', 'results/trial_scores.csv', 'analyze.py', ['parse', 'parse_normalized', 'evaluate'], 'parse_normalized', 'evaluate', 'case_id'),
        ('E2', 'validation/responses.jsonl', 'validation/cases.json', 'validation/results/trial_scores.csv', 'validation/analyze_validation.py', ['parse', 'normalized', 'number', 'score'], 'normalized', 'score', 'task_id')
    ]:
        tree = ast.parse((ROOT / script_name).read_text(encoding='utf-8'))
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        assert len(functions) == len(names)
        namespace = {'json': json, 're': re, 'Decimal': Decimal, 'InvalidOperation': InvalidOperation}
        exec(compile(ast.Module(body=functions, type_ignores=[]), script_name, 'exec'), namespace)
        cases = {(c[id_key], c['condition']): c for c in json.loads((ROOT / case_name).read_text(encoding='utf-8'))}
        scores = {r['job_id']: r for r in csv.DictReader((ROOT / scores_name).open(encoding='utf-8'))}
        raw = [json.loads(line) for line in (ROOT / raw_name).read_text(encoding='utf-8').splitlines()]
        assert len(raw) == len(scores) == len({r['job_id'] for r in raw})
        valid = {'strict': 0, 'normalized': 0, 'first_object': 0}
        for record in raw:
            text = record['response']['choices'][0]['message'].get('content') or ''
            case = cases[record[id_key], record['condition']]
            objects = {'strict': namespace['parse'](text), 'normalized': namespace[normalized_name](text),
                       'first_object': extractor.first_object(text, namespace['parse'])}
            assert objects['normalized'] == objects['first_object']
            for parser in ['strict', 'normalized']:
                current = namespace[scorer_name](objects[parser], case)
                for key, value in current.items():
                    column = key if experiment == 'E1' and parser == 'strict' else parser + '_' + key
                    assert (scores[record['job_id']][column] == 'True') == value, (record['job_id'], column)
                    comparisons += 1
            for parser, obj in objects.items():
                valid[parser] += obj is not None
        records.append({'experiment': experiment, 'responses': len(raw), 'valid': valid})
        for name in [raw_name, case_name, scores_name, script_name]:
            hashes[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    assert comparisons == 56016
    print(json.dumps({'boolean_score_fields_verified': comparisons, 'collections': records,
                      'all_first_objects_equal_fence_rule': True, 'input_sha256': hashes,
                      'model_calls': 0}, indent=2))


if __name__ == '__main__':
    main()
