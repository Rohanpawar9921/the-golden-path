import re
from config import config
from knowledge.vector_index import read_document_chunks

def read_category_code(collection, category):
    if category not in config.CATEGORY_CODE_DOCUMENTS: raise ValueError("unknown category")
    document_name=config.CATEGORY_CODE_DOCUMENTS[category]
    text=" ".join(read_document_chunks(collection, document_name))
    restricted=re.findall(config.RESTRICTED_HOURS_PATTERN,text)
    if restricted and re.search(config.ANY_TIME_PATTERN,text) or not restricted and not re.search(config.ANY_TIME_PATTERN,text):
        raise ValueError("ambiguous hours")
    restricted_hours={"start":restricted[0][0],"end":restricted[0][1]} if restricted else None
    exceptions=re.findall(config.LIVE_SPORT_EXCEPTION_PATTERN,text)
    if len(set(exceptions))>1: raise ValueError("ambiguous exception")
    if not restricted and exceptions: raise ValueError("exception without restricted hours")
    live={"minutes_after_start":int(exceptions[0][0]),"minutes_before_end":int(exceptions[0][1])} if exceptions else None
    children=[name for name,pattern in config.CHILDREN_RULE_PATTERNS.items() if re.search(pattern,text)]
    if len(children)!=1: raise ValueError("ambiguous children rule")
    values={}
    for name,pattern in config.CODE_FIGURE_PATTERNS.items():
        found=set(re.findall(pattern,text))
        if len(found)!=1: raise ValueError("ambiguous code figure")
        values[name]=int(next(iter(found)))
    sentences={}
    for code,pattern in [(config.BREACH_WINDOW,config.RESTRICTED_HOURS_PATTERN),
                         (config.BREACH_INDEX,config.CODE_FIGURE_PATTERNS["index_threshold"]),
                         (config.BREACH_CHILDREN,config.CHILDREN_RULE_PATTERNS[children[0]]),
                         (config.BREACH_FREQUENCY,config.CODE_FIGURE_PATTERNS["daily_cap"]),
                         (config.BREACH_SEPARATION,config.CODE_FIGURE_PATTERNS["separation_minutes"])]:
        match=re.search(pattern,text); sentences[code]=match.group(0) if match else ""
    return {"document_name":document_name,"restricted_hours":restricted_hours,
            "live_sport_exception":live,"children_rule":children[0],"rule_sentences":sentences,**values}