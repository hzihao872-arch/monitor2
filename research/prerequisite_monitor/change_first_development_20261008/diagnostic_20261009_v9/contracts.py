"""Strict diagnostic contracts, with no output repairs or semantic relabeling."""
import json
TRI={'true','false','unknown'}
EFFECT={'beneficial','harmful','irrelevant','mixed','unknown'}

def keys(x,expected):
    if not isinstance(x,dict) or set(x)!=set(expected):raise ValueError('exact_keys:'+','.join(expected))
def short(x,n=160):
    if not isinstance(x,str) or len(x)>n:raise ValueError('string_length_or_type')
def seq(x,n):
    if not isinstance(x,list) or len(x)>n:raise ValueError('list_length_or_type')
def enum(x,choices):
    if not isinstance(x,str) or x not in choices:raise ValueError('enum')
def index(x,n,global_allowed=False):
    if type(x)!=int or not (-int(global_allowed)<=x<n):raise ValueError('index')
def final(x,n):
    keys(x,['state','impacts','net_effect','reversal','reason'])
    keys(x['state'],['goal_done','direct_ready','partial_preparation'])
    enum(x['state']['goal_done'],TRI)
    for k in ('direct_ready','partial_preparation'):enum(x['state'][k],TRI|{'not_applicable'})
    if x['state']['goal_done']=='true' and any(x['state'][k]!='not_applicable' for k in ('direct_ready','partial_preparation')):raise ValueError('completed_preparation_state')
    seq(x['impacts'],3)
    for i in x['impacts']:
        keys(i,['change','effect']);index(i['change'],n);enum(i['effect'],EFFECT)
    if len({i['change'] for i in x['impacts']})!=len(x['impacts']):raise ValueError('duplicate_impact')
    enum(x['net_effect'],EFFECT|{'unchanged'});enum(x['reversal'],TRI);short(x['reason'],240)

def validate(stage,raw,handles,change_count=0,test_count=0):
    obj=None
    try:
        obj=json.loads(raw)
        if stage=='V1':
            keys(obj,['context','changes','coverage']);short(obj['context'],240);seq(obj['changes'],3)
            for c in obj['changes']:
                keys(c,['b','a','object','before','after'])
                if c['b'] not in handles or c['a'] not in handles:raise ValueError('unknown_evidence')
                if handles[c['b']]['time_ms']>=handles[c['a']]['time_ms']:raise ValueError('nonchronological')
                for k in ('object','before','after'):short(c[k])
            enum(obj['coverage'],{'complete','overflow','occluded','no_observable_change'})
        elif stage=='DRAFT':
            keys(obj,['judgment','tests']);final(obj['judgment'],change_count);seq(obj['tests'],4)
            for t in obj['tests']:
                keys(t,['change','ref','predicate']);index(t['change'],change_count,True);short(t['predicate'])
                if t['ref'] not in handles:raise ValueError('unknown_evidence')
        elif stage=='VERIFY':
            keys(obj,['facts']);seq(obj['facts'],5)
            for f in obj['facts']:
                keys(f,['test','value','ref','statement']);index(f['test'],test_count);enum(f['value'],TRI);short(f['statement'],240)
                if f['ref'] not in handles:raise ValueError('unknown_evidence')
            if len({f['test'] for f in obj['facts']})!=len(obj['facts']):raise ValueError('duplicate_test')
        elif stage=='FINAL':final(obj,change_count)
        else:raise ValueError('unknown_stage')
        return {'valid':True,'errors':[],'payload':obj}
    except (ValueError,TypeError,KeyError) as e:
        return {'valid':False,'errors':[type(e).__name__+':'+str(e)],'payload':obj}
