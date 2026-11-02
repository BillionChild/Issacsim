"""Build a traceable portfolio snapshot from recorded runs; never starts a simulation."""
import argparse, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def summarize(rows):
    if not isinstance(rows,list) or not rows:raise ValueError('Expected a non-empty run list')
    seen=set();out=[]
    for row in rows:
        name=row['case']
        if name in seen:raise ValueError('Duplicate case: '+name)
        seen.add(name)
        checks=row.get('checks',[])
        errors=[];ids=[]
        for check in checks:
            error=float(check['seat_error_m'])*1000
            if not math.isfinite(error) or error<0:raise ValueError('Invalid seating error: '+name)
            errors.append(error);ids.append(check['engine'])
        e1=[errors[i] for i,e in enumerate(ids) if e=='E1']
        passed=(row.get('accepted') is True and row.get('finished') is True
                and not row.get('fault') and len(ids)==3 and set(ids)=={'E1','E2','E3'})
        out.append(dict(case=name,passed=passed,e1_mm=e1[0] if len(e1)==1 else None,
                        observations=row.get('observations'),fault=row.get('fault')))
    return out

def build(sources):
    lines=['# Engine Warehouse — recorded validation results','',
        'This report summarizes saved runs; generating it does not run Isaac Sim.',
        'Each case is a recorded trial, not a statistical success probability.',
        'Errors below are post-action seating position errors, not perception errors.',
        'Kinematic clamp only; no force/contact or real-machine validation.','']
    for path in sources:
        data=path.read_bytes();rows=summarize(json.loads(data));passed=sum(r['passed'] for r in rows)
        stamp=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()
        lines += [f'## {path.name}','',f'Source modified (UTC): {stamp}',
                  f'SHA-256: `{hashlib.sha256(data).hexdigest()}`','',
                  f'Complete recorded cases: **{passed}/{len(rows)}**.','',
                  '| Case | Complete + 3 seating checks | E1 seating error (mm) | Observations |',
                  '|---|---|---:|---:|']
        for r in rows:
            error='--' if r['e1_mm'] is None else f"{r['e1_mm']:.3f}"
            name=r['case'].replace('|','/')
            lines.append(f"| {name} | {'PASS' if r['passed'] else 'INCOMPLETE / FAIL'} | {error} | {r['observations']} |")
        valid=[r['e1_mm'] for r in rows if r['passed'] and r['e1_mm'] is not None]
        if valid:lines += ['',f'Maximum E1 seating error among complete cases: **{max(valid):.3f} mm**.']
        lines += ['','These sources are separate test batches; overlapping cases are not merged into a larger success rate.','']
    return '\n'.join(lines)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/portfolio-validation.md')
    parser.add_argument('--sources',nargs='+',type=Path,default=[ROOT/'outputs/warehouse-case-validation.json',ROOT/'outputs/correction-ui-validation.json'])
    args=parser.parse_args();report=build(args.sources)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(report,encoding='utf-8')
    print('Saved recorded-run report:',args.output)
