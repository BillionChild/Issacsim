"""Report native Codex usage by user turn. No inferred per-file attribution."""
import argparse,csv,json
from pathlib import Path

def report(session,out):
    turns={};labels={};current='';label='';latest=None;seen=set();calls={}
    with session.open(encoding='utf-8') as f:
        for line in f:
            d=json.loads(line);p=d.get('payload',{});kind=d['type']
            if kind=='turn_context':current=p.get('turn_id',current)
            if kind=='response_item' and p.get('role')=='user':
                text=' '.join(c.get('text','') for c in p.get('content',[]))
                if '<environment_context>' not in text:
                    label=text.split('## My request:')[-1].strip().replace('\n',' ')[:180]
                    labels[current]=label
            if kind=='token_usage_record':
                key=p['turn_id'];labels.setdefault(key,label)
                turns[key]=(d['timestamp'],p['turn_token_usage'])
                latest=p.get('thread_token_usage')
                response=p.get('response_id')
                if response not in seen:
                    seen.add(response);calls[key]=calls.get(key,0)+1
    out.mkdir(parents=True,exist_ok=True)
    with (out/'token-usage-by-turn.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['turn_id','as_of_utc','request','responses','input','cached_input','uncached_input','output','total'])
        for key,(ts,u) in turns.items():
            w.writerow([key,ts,labels.get(key,''),calls.get(key,0),u['input_tokens'],u['cached_input_tokens'],u['input_tokens']-u['cached_input_tokens'],u['output_tokens'],u['total_tokens']])
    summary={'as_of_utc':ts,'native_thread_total':latest,'note':'Input includes cached input. Reasoning is included in output. Turn boundaries are measured; code/research/test subdivisions are not available. Current turn is incomplete.'}
    (out/'token-usage-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--session',type=Path,required=True);a.add_argument('--out',type=Path,default=Path('outputs'));args=a.parse_args();report(args.session,args.out)
