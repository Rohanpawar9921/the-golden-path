import re
from config import config

def _records(frame, reference):
    if reference not in set(frame[config.CAMPAIGN_REFERENCE_COLUMN].astype(str)):
        raise ValueError(config.CAMPAIGN_NOT_IN_QUEUE_MESSAGE.format(campaign_reference=reference))
    return frame[frame[config.CAMPAIGN_REFERENCE_COLUMN].astype(str) == reference]

def fetch_campaign_notes(notes, campaign_reference):
    rows=_records(notes,campaign_reference).copy()
    if rows[config.NOTE_SEQUENCE_COLUMN].duplicated().any(): raise ValueError("duplicate note sequence")
    rows["_sort"]=rows[config.NOTE_SEQUENCE_COLUMN].map(lambda x:int(str(x).strip()) if str(x).strip().isdigit() else 10**9)
    if (rows["_sort"]>=10**9).any(): raise ValueError("invalid note sequence")
    if rows["note_text"].fillna("").astype(str).str.strip().eq("").any():
        raise ValueError("note text is blank")
    rows=rows.sort_values("_sort")
    return [{k: row[k] for k in rows.columns if k != "_sort"} for _,row in rows.iterrows()]

def fetch_campaign_profile(campaigns, campaign_reference):
    rows=_records(campaigns,campaign_reference)
    if len(rows)!=1: raise ValueError("campaign profile is not unique")
    return rows.iloc[0].to_dict()

def _number(value):
    text=str(value).strip()
    match=re.fullmatch(r"(\d+)(?:\"|s| sec)?",text)
    if match:return int(match.group(1))
    match=re.fullmatch(r"(\d+):([0-5]\d)",text)
    if match:return int(match.group(1))*60+int(match.group(2))
    match=re.fullmatch(r"(\d{2}):([0-5]\d):([0-5]\d)",text)
    if match:return int(match.group(1))*3600+int(match.group(2))*60+int(match.group(3))
    raise ValueError("invalid spot length")

def _clock_length(clock):
    match=re.fullmatch(config.CLOCK_NUMBER_PATTERN,str(clock).strip())
    if not match: raise ValueError("invalid clock number")
    seconds=int(match.group(1))
    if seconds not in config.STANDARD_SPOT_LENGTHS: raise ValueError("non-standard spot length")
    return seconds

def fetch_campaign_spots(spots, campaign_reference):
    rows=_records(spots,campaign_reference)
    result=[]
    for _,row in rows.iterrows():
        record=row.to_dict(); record[config.SPOT_LENGTH_COLUMN]=_clock_length(record[config.CLOCK_NUMBER_COLUMN])
        record["_written_length"]=_number(record.get(config.SPOT_LENGTH_COLUMN,record.get("spot_length_seconds","30")))
        result.append(record)
    return result

def fetch_campaign_schedules(schedule, spots):
    wanted={str(s[config.CHANNEL_COLUMN]) for s in spots}
    return [row.to_dict() for _,row in schedule.iterrows()
            if str(row[config.CHANNEL_COLUMN]) in wanted or
            config.CHANNEL_MAPPING.get(str(row[config.CHANNEL_COLUMN]).lower(),str(row[config.CHANNEL_COLUMN])) in
            {config.CHANNEL_MAPPING.get(x.lower(),x) for x in wanted}]