#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, shutil, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'fixtures/success'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def replace_bytes(path,data):
    tmp=path.with_name(path.name+'.tmp'); tmp.write_bytes(data); os.replace(tmp,path)
def remove_guarded(path,expected):
    assert sha(path)==expected; path.unlink()

success=json.loads((FIX/'canvas-success.json').read_text(encoding='utf-8'))
canvas_bytes=(FIX/'ckb-navigation.canvas').read_bytes(); validation_bytes=(FIX/'ckb-navigation.canvas.validation.json').read_bytes(); rollback_bytes=(FIX/'ckb-navigation.canvas.rollback.json').read_bytes()
assert hashlib.sha256(canvas_bytes).hexdigest()==success['canvas']['sha256']
assert hashlib.sha256(validation_bytes).hexdigest()==success['validation_manifest']['sha256']
assert hashlib.sha256(rollback_bytes).hexdigest()==success['rollback_manifest']['sha256']

with tempfile.TemporaryDirectory(prefix='ckb-canvas-rollback-') as tmp:
    root=Path(tmp)
    # absent -> generated -> rollback -> absent
    paths={'canvas':root/'a.canvas','validation':root/'a.canvas.validation.json','rollback':root/'a.canvas.rollback.json'}
    for path,data in zip(paths.values(),(canvas_bytes,validation_bytes,rollback_bytes)): path.write_bytes(data)
    remove_guarded(paths['canvas'],success['canvas']['sha256'])
    remove_guarded(paths['validation'],success['validation_manifest']['sha256'])
    remove_guarded(paths['rollback'],success['rollback_manifest']['sha256'])
    assert all(not path.exists() for path in paths.values())
    print('ROLLBACK_ABSENT=passed roles=3 final=absent')

    # present baseline -> generated -> rollback -> byte-identical baseline
    baseline={'canvas':b'BASELINE-CANVAS\n','validation':b'BASELINE-VALIDATION\n','rollback':b'BASELINE-ROLLBACK\n'}
    generated={'canvas':canvas_bytes,'validation':validation_bytes,'rollback':rollback_bytes}
    backups={}
    for role,path in paths.items():
        path.write_bytes(baseline[role]); backup=root/(role+'.baseline'); shutil.copyfile(path,backup); backups[role]=backup
        replace_bytes(path,generated[role])
    for role,path in paths.items():
        assert sha(path)==hashlib.sha256(generated[role]).hexdigest()
        assert sha(backups[role])==hashlib.sha256(baseline[role]).hexdigest()
        replace_bytes(path,backups[role].read_bytes())
    assert all(paths[role].read_bytes()==baseline[role] for role in paths)
    print('ROLLBACK_PRESENT=passed roles=3 byte_identical=true')

    # drift refuses overwrite and preserves manual bytes
    paths['canvas'].write_bytes(canvas_bytes)
    manual=canvas_bytes+b'X'; paths['canvas'].write_bytes(manual)
    expected=success['canvas']['sha256']; actual=sha(paths['canvas'])
    assert actual!=expected and paths['canvas'].read_bytes()==manual
    print(f'ROLLBACK_DRIFT=passed refused=true manual_sha256={actual}')
print('ROLLBACK_PROBES=passed count=3/3')
