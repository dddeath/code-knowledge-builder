#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'schemas'
FIXTURES = ROOT / 'fixtures'


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def is_type(value, kind):
    if kind == 'object': return isinstance(value, dict)
    if kind == 'array': return isinstance(value, list)
    if kind == 'string': return isinstance(value, str)
    if kind == 'integer': return isinstance(value, int) and not isinstance(value, bool)
    if kind == 'number': return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == 'boolean': return isinstance(value, bool)
    if kind == 'null': return value is None
    return False


def validate(schema, value, at='$'):
    errors=[]
    if 'allOf' in schema:
        for i, child in enumerate(schema['allOf']): errors += validate(child, value, f'{at}.allOf[{i}]')
    if 'oneOf' in schema:
        variants=[validate(child,value,at) for child in schema['oneOf']]
        if sum(not item for item in variants) != 1: errors.append(f'{at}: oneOf matched {sum(not item for item in variants)} variants')
        else: return errors
    if 'if' in schema and not validate(schema['if'], value, at):
        errors += validate(schema.get('then', {}), value, at)
    if 'const' in schema and value != schema['const']: errors.append(f'{at}: const mismatch')
    if 'enum' in schema and value not in schema['enum']: errors.append(f'{at}: enum mismatch')
    kind=schema.get('type')
    if kind and not is_type(value,kind): return errors+[f'{at}: expected {kind}, got {type(value).__name__}']
    if isinstance(value,dict):
        for name in schema.get('required',[]):
            if name not in value: errors.append(f'{at}: missing {name}')
        props=schema.get('properties',{})
        if schema.get('additionalProperties') is False:
            for name in value:
                if name not in props: errors.append(f'{at}: unknown {name}')
        for name,child in props.items():
            if name in value: errors += validate(child,value[name],f'{at}.{name}')
    if isinstance(value,list):
        if len(value) < schema.get('minItems',0): errors.append(f'{at}: too few items')
        if 'maxItems' in schema and len(value) > schema['maxItems']: errors.append(f'{at}: too many items')
        if schema.get('uniqueItems'):
            sig=[json.dumps(item,ensure_ascii=False,sort_keys=True) for item in value]
            if len(sig)!=len(set(sig)): errors.append(f'{at}: duplicate items')
        if 'items' in schema:
            for i,item in enumerate(value): errors += validate(schema['items'],item,f'{at}[{i}]')
    if isinstance(value,str):
        if len(value)<schema.get('minLength',0): errors.append(f'{at}: too short')
        if 'maxLength' in schema and len(value)>schema['maxLength']: errors.append(f'{at}: too long')
        if 'pattern' in schema and not re.search(schema['pattern'],value): errors.append(f'{at}: pattern mismatch')
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        if 'minimum' in schema and value<schema['minimum']: errors.append(f'{at}: below minimum')
        if 'maximum' in schema and value>schema['maximum']: errors.append(f'{at}: above maximum')
    return errors


def load(path): return json.loads(path.read_text(encoding='utf-8'))

def assert_valid(schema_name, instance_path):
    errors=validate(load(SCHEMAS/schema_name),load(instance_path))
    if errors: raise AssertionError(f'{instance_path}: {errors[:8]}')


def slug(text):
    text=text.strip().lower()
    text=re.sub(r'[^\w\u3400-\u9fff -]','',text)
    return re.sub(r'-+','-',re.sub(r'\s+','-',text)).strip('-')

# Parse all JSON/schema/Canvas.
json_files=sorted([*ROOT.rglob('*.json'),*ROOT.rglob('*.canvas')])
for path in json_files: load(path)
print(f'JSON_PARSE=passed files={len(json_files)}')

schema_files=sorted(SCHEMAS.glob('*.json'))
for path in schema_files:
    value=load(path)
    assert value.get('$schema')=='https://json-schema.org/draft/2020-12/schema'
    assert value.get('$id','').startswith('https://ckb.local/schemas/')
    assert '$ref' not in path.read_text(encoding='utf-8')
    def walk(v):
        if isinstance(v,dict):
            if v.get('type')=='object': assert v.get('additionalProperties') is False, path
            for item in v.values(): walk(item)
        elif isinstance(v,list):
            for item in v: walk(item)
    walk(value)
print(f'SCHEMA_SHAPE=passed schemas={len(schema_files)} draft=2020-12 external_refs=0')

mapping=[
 ('canvas-request.schema.json',FIXTURES/'success/canvas-request.json'),
 ('json-canvas-1.0-ckb-subset.schema.json',FIXTURES/'success/ckb-navigation.canvas'),
 ('canvas-success.schema.json',FIXTURES/'success/canvas-success.json'),
 ('canvas-validation-manifest.schema.json',FIXTURES/'success/ckb-navigation.canvas.validation.json'),
 ('canvas-rollback-manifest.schema.json',FIXTURES/'success/ckb-navigation.canvas.rollback.json'),
 ('benchmark-run.schema.json',FIXTURES/'benchmark/benchmark-run.json'),
 ('benchmark-session-result.schema.json',FIXTURES/'benchmark/benchmark-session-result.json'),
 ('benchmark-summary.schema.json',FIXTURES/'benchmark/benchmark-summary.json')]
for item in sorted((FIXTURES/'failure-results').glob('*.json')): mapping.append(('canvas-failure.schema.json',item))
for schema_name,path in mapping: assert_valid(schema_name,path)
print(f'FIXTURE_VALIDATION=passed instances={len(mapping)}')

# Unknown fields at every request object family must fail.
request_schema=load(SCHEMAS/'canvas-request.schema.json'); base=load(FIXTURES/'success/canvas-request.json')
mutations=[]
def add(path):
    x=copy.deepcopy(base); cur=x
    for part in path: cur=cur[part]
    cur['unknown_fixture_field']=1; mutations.append((path,x))
for path in [(),('ckb',),('ckb','frozen_evidence'),('ckb','frozen_evidence','human_files',0),('request',),('request','baseline'),('request','baseline','canvas'),('request','required_entries',0),('budget',)]: add(path)
for path,value in mutations:
    if not validate(request_schema,value): raise AssertionError(f'unknown field accepted at {path}')
print(f'NEGATIVE_UNKNOWN_FIELDS=passed cases={len(mutations)}')

reasons={'invalid_request','unsupported_record_schema','pack_record_mismatch','input_drift','snapshot_mismatch','source_outside_scope','target_exists','missing_backlink','missing_target','invalid_source_range','budget_exceeded','duplicate_id','dangling_edge','invalid_canvas','promotion_drift','rollback_drift','io_failure'}
actual={load(path)['reason'] for path in (FIXTURES/'failure-results').glob('*.json')}
assert actual==reasons
print(f'FAILURE_REASON_COVERAGE=passed reasons={len(actual)}')

# Hash and self-hash consistency.
request_bytes=(FIXTURES/'success/canvas-request.json').read_bytes(); canvas_bytes=(FIXTURES/'success/ckb-navigation.canvas').read_bytes(); val_bytes=(FIXTURES/'success/ckb-navigation.canvas.validation.json').read_bytes(); rb_bytes=(FIXTURES/'success/ckb-navigation.canvas.rollback.json').read_bytes()
success=load(FIXTURES/'success/canvas-success.json'); validation_manifest=load(FIXTURES/'success/ckb-navigation.canvas.validation.json'); rollback=load(FIXTURES/'success/ckb-navigation.canvas.rollback.json')
assert success['request_sha256']==digest(request_bytes)==validation_manifest['request_sha256']==rollback['request_sha256']
assert success['canvas']['sha256']==digest(canvas_bytes)==validation_manifest['canvas']['sha256']==rollback['generated']['canvas']['sha256']
assert success['validation_manifest']['sha256']==digest(val_bytes)==rollback['generated']['validation_manifest']['sha256']
assert success['rollback_manifest']['sha256']==digest(rb_bytes)
copy_rb=copy.deepcopy(rollback); expected=copy_rb['guard']['expected_manifest_content_sha256']; copy_rb['guard']['expected_manifest_content_sha256']='0'*64
assert digest(canonical(copy_rb))==expected
print(f'HASH_CONTRACT=passed request={digest(request_bytes)} canvas={digest(canvas_bytes)} rollback={digest(rb_bytes)}')

# Canonical sample and graph closure/stable IDs.
for path in [FIXTURES/'success/canvas-request.json',FIXTURES/'success/ckb-navigation.canvas',FIXTURES/'success/canvas-success.json',FIXTURES/'success/ckb-navigation.canvas.validation.json',FIXTURES/'success/ckb-navigation.canvas.rollback.json']:
    assert path.read_bytes()==canonical(load(path)), path
canvas=load(FIXTURES/'success/ckb-navigation.canvas'); ids={n['id'] for n in canvas['nodes']}; assert len(ids)==len(canvas['nodes'])
assert all(edge['fromNode'] in ids and edge['toNode'] in ids for edge in canvas['edges'])
assert len(canvas['nodes'])<=12 and len(canvas['edges'])<=16
for node in canvas['nodes']:
    assert not any(k in node for k in {'entity_id','document_id','score','score_breakdown','terms','retrieval_stats'})
print(f'CANVAS_STRUCTURE=passed nodes={len(canvas["nodes"])} edges={len(canvas["edges"])} dangling=0 canonical_files=5')

# Benchmark coverage: each condition sees all 12 tasks across sequences, every assignment has 6 unique tasks.
run=load(FIXTURES/'benchmark/benchmark-run.json'); tids=[t['task_id'] for t in run['tasks']]; assert len(tids)==len(set(tids))==12
for assignment in run['assignments']: assert len(assignment['task_order'])==len(set(assignment['task_order']))==6
for condition in ('markdown','canvas'):
    covered=set().union(*(set(a['task_order']) for a in run['assignments'] if a['condition']==condition))
    assert covered==set(tids)
assert run['conditions']['markdown']['evidence_set_sha256']==run['conditions']['canvas']['evidence_set_sha256']
print('BENCHMARK_CONTRACT=passed tasks=12 assignments=4 per_condition_coverage=12 evidence_equal=true')

# Local Markdown links and anchors.
links=0
for source in sorted(ROOT.glob('*.md')):
    text=source.read_text(encoding='utf-8')
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if re.match(r'^[a-z]+://',target): continue
        links+=1; target=unquote(target); file_part,sep,anchor=target.partition('#'); resolved=(source.parent/file_part).resolve()
        if not resolved.exists(): raise AssertionError(f'missing link {source}:{target}')
        if sep:
            if not resolved.is_file(): raise AssertionError(f'anchor on non-file {source}:{target}')
            headings=[]
            for line in resolved.read_text(encoding='utf-8').splitlines():
                m=re.match(r'^#{1,6}\s+(.+?)\s*$',line)
                if m: headings.append(slug(m.group(1)))
            if anchor not in headings: raise AssertionError(f'missing anchor {source}:{target}; have={headings[:8]}')
print(f'MARKDOWN_LINKS=passed links={links}')
print('DESIGN_VALIDATION=passed')
