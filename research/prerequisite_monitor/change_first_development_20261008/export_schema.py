"""Export machine-readable JSON Schema matching the runtime exact-field contract."""
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments.prerequisite_probe.change_first_monitor.contracts import SPEC,ITEM_KEYS

ENUMS={
 ('V1','coverage'):['complete','overflow','occluded','no_observable_change'],
 ('V1','observation'):['observed','uncertain'],
 ('V1','status'):['closed_event','open_event'],
 ('L2','possible_effect'):['beneficial','harmful','irrelevant','unknown'],
 ('V3','at'):['before','after','current'],
 ('V3','value'):['true','false','unknown'],
 ('V3','exists'):['true','false','unknown'],
 ('V3','reason'):['occlusion','identity','geometry','stability','budget','out_of_prefix','not_observable'],
 ('L4','status'):['supported','refuted','unknown'],
 ('L4','impact'):['beneficial','harmful','irrelevant','mixed','unknown'],
 ('L4','basis'):['observed','inference'],
 ('L4','net_effect'):['beneficial','harmful','unchanged','mixed','unknown'],
 ('L4','reversal'):['true','false','unknown']}
LIST_FIELDS={'entity_ids','before_refs','after_refs','change_ids','test_ids','requested_refs',
             'evidence_refs','used_test_ids','fact_ids','reversed_event_ids'}


def scalar(stage,key):
    if (stage,key) in ENUMS:return {'type':'string','enum':ENUMS[(stage,key)]}
    return {'type':'string','maxLength':320}


def item_schema(stage,key):
    props={}
    for name in sorted(ITEM_KEYS[key]):
        props[name]={'type':'array','items':{'type':'string','maxLength':80},'maxItems':12} if name in LIST_FIELDS else scalar(stage,name)
    return {'type':'object','properties':props,'required':sorted(props),'additionalProperties':False}


def stage_schema(stage):
    props={}
    for key,typ in SPEC[stage].items():
        if isinstance(typ,tuple):
            if key=='unresolved':props[key]={'type':'array','maxItems':typ[1],'items':{'type':'string','maxLength':80}}
            else:props[key]={'type':'array','maxItems':typ[1],'items':item_schema(stage,key)}
        elif key=='state':
            props[key]={'type':'object','properties':{k:{'type':'string','enum':['true','false','unknown','not_applicable']}
              for k in ('goal_done','direct_ready','partial_preparation')},
              'required':['goal_done','direct_ready','partial_preparation'],'additionalProperties':False}
        elif key=='state_fact_ids':
            props[key]={'type':'object','properties':{k:{'type':'array','items':{'type':'string','maxLength':80}}
              for k in ('goal_done','direct_ready','partial_preparation')},
              'required':['goal_done','direct_ready','partial_preparation'],'additionalProperties':False}
        else:props[key]=scalar(stage,key)
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object',
            'properties':props,'required':sorted(props),'additionalProperties':False}


if __name__=='__main__':
    path=Path(__file__).resolve().parents[3]/'experiments/prerequisite_probe/change_first_monitor/protocol/stage_schemas.json'
    path.write_text(json.dumps({'version':'change-first-v1','schemas':{s:stage_schema(s) for s in SPEC}},indent=2),encoding='utf-8')
    print(path)
