#!/usr/bin/env python3
"""Build the generic ARM IOKit providers against the XNU compile records."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/arm-platforms'
OUT.mkdir(parents=True, exist_ok=True)
records = sorted((ROOT / 'build/xnu/ios-obj').glob('**/iokit/DEVELOPMENT/*.o.json'))
if not records:
    raise SystemExit('No XNU IOKit compile record; run the bootstrap kernel pass first')
record_path = next((p for p in records if p.name.lower().startswith('ioservice')), records[0])
record = json.loads(record_path.read_text().strip().rstrip(','))

def compile_driver(name):
    source = ROOT / 'drivers' / name / f'{name}.cpp'
    obj = OUT / f'{name}.o'
    args = list(record['arguments'])
    try:
        source_index = args.index(record['file'])
    except ValueError:
        source_index = next(i for i, value in enumerate(args) if str(value).endswith('.cpp'))
    args[source_index] = str(source)
    output_index = args.index('-o') + 1
    args[output_index] = str(obj)
    if not Path(args[0]).name.startswith('clang'):
        args = ['xcrun', '--sdk', 'iphoneos', 'clang++', *args[1:]]
    elif Path(args[0]).name == 'clang++':
        args[0] = shutil.which('clang++') or args[0]
    result = subprocess.run(args, cwd=record.get('directory', str(ROOT)), text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / f'{name}.log').write_text(result.stdout)
    if result.returncode:
        raise SystemExit(result.stdout[-8000:])
    archive = OUT / f'lib{name}.a'
    subprocess.run(['xcrun', '--sdk', 'iphoneos', 'ar', 'rcs', str(archive), str(obj)], check=True)
    return archive

archives = [compile_driver(name) for name in ('ArmCpu', 'ArmDTPlatform', 'ArmVirtPlatform')]
(OUT / 'build-report.json').write_text(json.dumps({
    'archives': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in archives},
}, indent=2) + '\n')
print('Built ARM platform archives: ' + ', '.join(p.name for p in archives))
