import json
from collections import Counter

path = 'questions_meteorology.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

ids = [q.get('id') for q in data]
dup_ids = [item for item, count in Counter(ids).items() if count > 1]

errors = []
if dup_ids:
    errors.append(f"Duplicate IDs found: {dup_ids}")

for q in data:
    qid = q.get('id')
    opts = q.get('options')
    ca = q.get('correct_answer')
    if not isinstance(opts, list):
        errors.append(f"Question {qid}: 'options' is not a list")
    else:
        if not isinstance(ca, int):
            errors.append(f"Question {qid}: 'correct_answer' is not int: {ca}")
        else:
            if ca < 0 or ca >= len(opts):
                errors.append(f"Question {qid}: correct_answer index {ca} out of range (options len={len(opts)})")

print('Total questions:', len(data))
if errors:
    print('Errors detected:')
    for e in errors:
        print(' -', e)
else:
    print('No structural errors detected.')
