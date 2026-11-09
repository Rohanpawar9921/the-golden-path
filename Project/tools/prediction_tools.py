import numpy as np
from config import config

def build_amendment_facts(model, schema, campaigns):
    from data_pipeline.feature_builder import build_feature_frame
    frame=build_feature_frame(campaigns.copy(),config.AMENDMENT_NUMERIC_FEATURES,
                              config.AMENDMENT_CATEGORICAL_FEATURES)[schema]
    scores=model.predict_proba(frame)[:,1]
    result=[]
    for ref,score in zip(campaigns[config.CAMPAIGN_REFERENCE_COLUMN],scores):
        score=round(float(score),config.AMENDMENT_SCORE_DECIMALS)
        band=(config.AMENDMENT_BAND_HIGH if score>=config.AMENDMENT_BAND_HIGH_THRESHOLD else
              config.AMENDMENT_BAND_MEDIUM if score>=config.AMENDMENT_BAND_MEDIUM_THRESHOLD else
              config.AMENDMENT_BAND_LOW)
        result.append({"campaign_reference":ref,"amendment_score":score,"amendment_band":band})
    return result

def build_exposure_forecasts(model,schema,airings):
    from data_pipeline.feature_builder import build_feature_frame, add_slot_minutes
    frame=build_feature_frame(add_slot_minutes(airings.copy()),config.EXPOSURE_NUMERIC_FEATURES,
                              config.EXPOSURE_CATEGORICAL_FEATURES)[schema]
    values=model.predict(frame)
    return [{"airing_id":ref,"exposure_forecast":round(float(value),config.EXPOSURE_DECIMALS)}
            for ref,value in zip(airings["airing_id"],values)]

def build_issue_facts(model, notes):
    readable=[n for n in notes if len(str(n.get("note_text","")).split())>=config.MINIMUM_NOTE_WORDS]
    short=len(notes)-len(readable)
    if not readable:
        raise ValueError("No readable notes are available for issue classification")
    probabilities=model.predict_proba([n["note_text"] for n in readable])
    labels=[str(model.classes_[i]) for i in probabilities.argmax(axis=1)]
    weighted={}
    confidence={}
    readings=[]
    for note,label,prob in zip(readable,labels,probabilities):
        if note["note_source"] not in config.NOTE_SOURCE_WEIGHTS:
            raise ValueError("Unknown note source has no configured vote weight")
        weight=config.NOTE_SOURCE_WEIGHTS[note["note_source"]]
        weighted[label]=weighted.get(label,0)+weight
        confidence[label]=confidence.get(label,0)+float(prob[list(model.classes_).index(label)])
        readings.append({"note_sequence":note["note_sequence"],"issue_category":label})
    winner=max(weighted,key=lambda k:(weighted[k],confidence.get(k,0)))
    return {"issue_category":winner,"weighted_votes":weighted,
            "weighted_agreement":round(weighted[winner]/sum(weighted.values()),config.NOTE_AGREEMENT_DECIMALS),
            "notes_read":len(readable),"notes_too_short_to_read":short,"note_readings":readings}