from config import config
from datetime import datetime

def _time(value):
    text=str(value).strip()
    if ":" not in text: raise ValueError("invalid time")
    pieces=text.split(":")
    if len(pieces)!=2 or not all(p.isdigit() for p in pieces): raise ValueError("invalid time")
    hour,minute=map(int,pieces)
    if minute>59 or hour>30: raise ValueError("invalid time")
    return hour*60+minute

def _normalise(value,mapping):
    text=str(value).strip()
    return mapping.get(text.lower(),text)

def _broadcast_day(day, minute):
    canonical=_normalise(day,config.WEEKDAY_MAPPING)
    if minute < config.BROADCAST_DAY_START_MINUTE:
        return config.WEEKDAYS[(config.WEEKDAYS.index(canonical)-1)%7]
    return canonical

def place_spot(spot, schedules):
    channel=_normalise(spot[config.CHANNEL_COLUMN],config.CHANNEL_MAPPING)
    system=_normalise(spot[config.SCHEDULING_SYSTEM_COLUMN],config.SCHEDULING_SYSTEM_MAPPING)
    minute=_time(spot[config.BREAK_TIME_COLUMN])
    if system in config.CALENDAR_CLOCK_SYSTEMS and minute < config.BROADCAST_DAY_START_MINUTE:
        broadcast_minute=minute+1440
    elif system in config.BROADCAST_CLOCK_SYSTEMS and minute < config.BROADCAST_DAY_START_MINUTE:
        raise ValueError("broadcast time before start")
    else: broadcast_minute=minute
    if broadcast_minute == config.BROADCAST_DAY_START_MINUTE:
        raise ValueError("spot at the start of the broadcast day cannot be placed")
    day=_broadcast_day(spot[config.TRANSMISSION_DAY_COLUMN],minute if system in config.CALENDAR_CLOCK_SYSTEMS else broadcast_minute)
    candidates=[r for r in schedules if _normalise(r[config.CHANNEL_COLUMN],config.CHANNEL_MAPPING)==channel
                and _normalise(r[config.TRANSMISSION_DAY_COLUMN],config.WEEKDAY_MAPPING)==day]
    if not candidates: raise ValueError("no schedule for spot")
    programmes=[]
    boundaries=[]
    for r in candidates:
        start=_time(r["start_time"]); end=_time(r["end_time"])
        if end < start: end += 1440
        if start < 360: start += 1440
        if start == broadcast_minute or end == broadcast_minute:
            boundaries.append((r, start, end))
        if start <= broadcast_minute < end: programmes=[r]; break
    if len(boundaries) >= 2:
        programmes=[boundaries[0][0], boundaries[1][0]]
    if not programmes:
        before=[r for r in candidates if (_time(r["end_time"]) if _time(r["end_time"])>=_time(r["start_time"]) else _time(r["end_time"])+1440) == broadcast_minute]
        after=[r for r in candidates if (_time(r["start_time"]) if _time(r["start_time"])>=360 else _time(r["start_time"])+1440) == broadcast_minute]
        if before and after: programmes=[before[0],after[0]]
    if not programmes: raise ValueError("spot is not in a programme or boundary break")
    position=config.BREAK_IN if len(programmes)==1 else config.BREAK_ADJACENT
    return {**spot,"broadcast_day":day,"break_time":f"{broadcast_minute//60:02d}:{broadcast_minute%60:02d}",
            "break_position":position,"programmes":programmes,"broadcast_minute":broadcast_minute}

def _flag(value): return str(value).strip().lower() in {"yes","y","true","1"}

def check_campaign_spots(placements, code):
    ordered=sorted(placements,key=lambda p:(p.get("broadcast_day",""),p.get("broadcast_minute",0),
                                             p.get("spot_reference","")))
    previous={}; counts={}
    results=[]
    for p in ordered:
        breaches=[]
        minute=p["broadcast_minute"]
        programmes=p["programmes"]
        if code.get("restricted_hours"):
            start=_time(code["restricted_hours"]["start"]); end=_time(code["restricted_hours"]["end"])
            restriction_minute = minute % config.MINUTES_PER_DAY
            restricted=(start <= restriction_minute < end) if start < end else (
                restriction_minute >= start or restriction_minute < end)
            exception=code.get("live_sport_exception")
            if restricted and exception and len(programmes)==1 and _flag(programmes[0].get("live_sport_flag")):
                # Centre break: enough margin from both edges of the live programme.
                ps=_time(programmes[0]["start_time"]); pe=_time(programmes[0]["end_time"])
                if minute-ps > exception["minutes_after_start"] and pe-minute > exception["minutes_before_end"]:
                    restricted=False
            if restricted: breaches.append(config.BREACH_WINDOW)
        if any(float(pgm.get(config.FORECAST_INDEX_COLUMN,0) or 0)>=code.get("index_threshold",float("inf"))
               for pgm in programmes): breaches.append(config.BREACH_INDEX)
        child=any(_flag(pgm.get(config.MADE_FOR_CHILDREN_FLAG_COLUMN)) for pgm in programmes)
        if child and (code.get("children_rule") == config.CHILDREN_IN_OR_ADJACENT
                      or (code.get("children_rule") == config.CHILDREN_IN_ONLY
                          and len(programmes) == 1)):
            breaches.append(config.BREACH_CHILDREN)
        key=(p[config.CHANNEL_COLUMN],p["broadcast_day"])
        counts[key]=counts.get(key,0)+1
        if counts[key]>code.get("daily_cap",float("inf")): breaches.append(config.BREACH_FREQUENCY)
        prev=previous.get(key)
        if prev is not None and minute-prev < code.get("separation_minutes",0):
            breaches.append(config.BREACH_SEPARATION)
        previous[key]=minute
        results.append({"spot_reference":p[config.SPOT_REFERENCE_COLUMN],"breach_codes":breaches,
                        "placement":p,"result":config.SPOT_RESULT_BREACHING if breaches else config.SPOT_RESULT_COMPLIANT})
    return sorted(results,key=lambda r:r["spot_reference"])

def summarise_spot_checks(results):
    compliant=[r for r in results if not r["breach_codes"]]
    breaches=[r for r in results if r["breach_codes"]]
    counts={code:sum(code in r["breach_codes"] for r in results) for code in config.BREACH_CODES}
    ordered=sorted(results,key=lambda r:(r["placement"].get("broadcast_day",""),
                                         r["placement"].get("broadcast_minute",0)))
    first=ordered[0]["placement"] if ordered else {}
    decisions=[config.DECISION_CLEAR,config.DECISION_REJECT] if not breaches else (
        [config.DECISION_REJECT] if not compliant else
        [config.DECISION_CLEAR_WITH_RESTRICTIONS,config.DECISION_REJECT])
    return {"spots_booked":len(results),"spots_compliant":len(compliant),"spots_breaching":len(breaches),
            "breaches_by_rule":counts,"decisions_open":decisions,
            "first_transmission":{"broadcast_day":first.get("broadcast_day"),
                                  "break_time":first.get("break_time")} if first else None}

def compute_clearance_outcome(decision, results):
    summary=summarise_spot_checks(results)
    if decision not in summary["decisions_open"]: raise ValueError("decision is not open")
    compliant=[r[config.SPOT_REFERENCE_COLUMN] for r in results if not r["breach_codes"]]
    breaching=[r[config.SPOT_REFERENCE_COLUMN] for r in results if r["breach_codes"]]
    if decision==config.DECISION_CLEAR: cleared,withdrawn=compliant+breaching,[]
    elif decision==config.DECISION_CLEAR_WITH_RESTRICTIONS: cleared,withdrawn=compliant,breaching
    else: cleared,withdrawn=[],compliant+breaching
    return {"spots_cleared":cleared,"spots_withdrawn":withdrawn,
            "spots_cleared_count":len(cleared),"spots_withdrawn_count":len(withdrawn)}