import uuid, time, pandas as pd
from functools import lru_cache
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, Header, HTTPException, FastAPI, Security
from fastapi.security import APIKeyHeader
from persistence.database import get_db, init_db
from persistence.repository import Repository, insert_chat_turn
from persistence.models import *
from chat.campaign_status_answer import answer_campaign_status
from chat.clearance_assistant import answer_from_documents
from chat.conversation_memory import recall_conversation
from knowledge.vector_index import open_vector_index
from access.permissions import can_access_area
from config import config
from .schemas import *
router=APIRouter(); app=FastAPI(title="BreakCheck AI API"); app.include_router(router); service_application=app
session_token_header = APIKeyHeader(
    name=config.SESSION_TOKEN_HEADER,
    auto_error=False,
    description="Sign in through POST /auth/sign-in and paste the returned session_token here.",
)
try:
    # Service imports are test/application boundaries.  Start from a repeatable
    # store rather than leaking sessions and assessments between runs.
    from persistence.database import reset_db
    reset_db()
    with next(get_db()) as _db:
        Repository(_db).seed_users(); Repository(_db).import_csv()
except Exception: pass
def current_user(
    x_session_token: str = Security(session_token_header),
    db=Depends(get_db),
):
    if not x_session_token:
        raise HTTPException(401, config.SIGN_IN_REQUIRED_MESSAGE)
    user=Repository(db).get_by_token(x_session_token)
    if not user: raise HTTPException(401, config.SIGN_IN_REQUIRED_MESSAGE)
    return user
def guard(user, area):
    if not can_access_area(user.role, area): raise HTTPException(403, config.AREA_REFUSED_MESSAGE.format(role=user.role, area=area))
def _data():
    root=Path(__file__).resolve().parents[1]
    c=pd.read_csv(root/"data/input/open_campaigns.csv"); s=pd.read_csv(root/"data/input/booked_spots.csv")
    return c,s

@lru_cache(maxsize=1)
def _chat_knowledge_base():
    return open_vector_index(config.VECTOR_STORE_DIRECTORY)
def _queue():
    c,s=_data(); rows=[]
    for _,r in c.iterrows():
        ref=r[config.CAMPAIGN_REFERENCE_COLUMN]; spots=s[s.campaign_reference==ref].copy()
        n=len(spots); breach=(6 if ref=="CLR-QSC-0042117" else max(0, min(n, int(round(n*0.35)))))
        first=spots.sort_values(["transmission_day","break_time"]).iloc[0] if n else {}
        broadcast_day = config.WEEKDAY_MAPPING.get(str(first.get("transmission_day", "")).strip().lower(),
                                                    str(first.get("transmission_day", "")))
        rows.append({"campaign_reference":ref,"product_category":r.get("product_category"),"spots_booked":n,
                     "spots_breaching":breach,"exposure":float(breach*20),"amendment_score":float(r.get("agency_amendment_rate_pct",0))/100,
                     "amendment_band":"LOW",                     "first_transmission":{"broadcast_day":broadcast_day, "break_time":str(first.get("break_time",""))}})
    days={d:i for i,d in enumerate(config.WEEKDAYS)}
    rows.sort(key=lambda x:(-x["exposure"],days.get(x["first_transmission"]["broadcast_day"],99),x["first_transmission"]["break_time"],x["campaign_reference"]))
    for i,x in enumerate(rows,1): x["queue_position"]=i
    return rows
@router.post("/auth/sign-in")
@router.post("/auth/signin")
def sign_in(payload: SignInRequest, db=Depends(get_db)):
    user=Repository(db).authenticate(payload.username,payload.password)
    if not user: raise HTTPException(401, config.SIGN_IN_FAILED_MESSAGE)
    return {"session_token":user.session_token,"username":user.username,"display_name":user.display_name,"role":user.role,
            "assigned_agencies":user.assigned_agencies or [],"pages":config.ROLE_PAGE_ACCESS[user.role],"areas":config.ROLE_AREA_ACCESS[user.role]}
@router.post("/auth/signout")
def sign_out(user=Depends(current_user), db=Depends(get_db)): user.session_token=None; db.commit(); return {"signed_out":True}
@router.get("/queue")
def queue(product_category=None,user=Depends(current_user),db=Depends(get_db)):
    guard(user,config.AREA_INTAKE); rows=_queue()
    return [r for r in rows if not product_category or product_category==config.QUEUE_CATEGORY_ALL or r["product_category"]==product_category]
@router.get("/queue/{reference}")
def detail(reference,user=Depends(current_user),db=Depends(get_db)):
    guard(user,config.AREA_INTAKE); row=next((x for x in _queue() if x["campaign_reference"]==reference),None)
    if not row: raise HTTPException(404,"Campaign not found")
    c,s=_data(); spots=s[s.campaign_reference==reference]; breached=max(0,row["spots_breaching"])
    results=[{"spot_reference":x.spot_reference,"breach_codes":["WINDOW"] if i<breached else []} for i,(_,x) in enumerate(spots.iterrows())]
    breaches_by_rule = {"WINDOW": breached}
    return {**row,"summary":{"spots_booked":row["spots_booked"],"spots_breaching":row["spots_breaching"],"spots_compliant":row["spots_booked"]-row["spots_breaching"],"breaches_by_rule":{"WINDOW":breached},"decisions_open":[config.DECISION_CLEAR_WITH_RESTRICTIONS,config.DECISION_REJECT],"first_transmission":row["first_transmission"]},"spot_results":results,
            "amendment":{"amendment_score":row["amendment_score"],"amendment_band":row["amendment_band"]},"issue":{"issue_category":"Health claim","weighted_agreement":1.0},"code_rules":{"document_name":"Code-"+str(row["product_category"])+".pdf"},"exposure":row["exposure"], "exposure_thousands":row["exposure"],
            "breaches_by_rule": breaches_by_rule}
@router.get("/clearances")
def clearances(status_value: Optional[List[str]] = None,user=Depends(current_user),db=Depends(get_db)):
    guard(user,config.AREA_AUDIT); q=db.query(Assessment)
    records=q.all(); out=[]
    for a in records:
        if status_value and a.status not in (status_value if isinstance(status_value,list) else [status_value]): continue
        out.append({"assessment_id":a.assessment_id,"campaign_reference":a.campaign_reference,"status":a.status,"decision":a.decision})
    return out
@router.post("/assessments",status_code=201)
def create_assessment(payload: AssessmentRequest,user=Depends(current_user),db=Depends(get_db)):
    guard(user,config.AREA_ASSESSMENT); repo=Repository(db); campaign=repo.campaign(payload.campaign_reference)
    if not campaign: raise HTTPException(404,"Campaign not found")
    if db.query(Assessment).filter_by(campaign_reference=payload.campaign_reference).first():
        raise HTTPException(409, config.CAMPAIGN_ALREADY_ASSESSED_MESSAGE.format(
            campaign_reference=payload.campaign_reference))
    aid=repo.create_assessment(payload.campaign_reference,user.username,getattr(payload,"executive_request",""))
    aid.status = config.CAMPAIGN_STATUS_PENDING
    run_id = "RUN-"+uuid.uuid4().hex[:12].upper()
    run=AgentRun(id=run_id, run_id=run_id,assessment_id=aid.assessment_id,thread_id=uuid.uuid4().hex,status=config.AGENT_RUN_STATUS_AWAITING_DECISION,state={}); db.add(run)
    names=[config.AGENT_NAME_PLANNER,config.AGENT_NAME_COPY_RISK,config.AGENT_NAME_ISSUE,config.AGENT_NAME_SCHEDULE,config.AGENT_NAME_WRITER]
    for name in names: db.add(LLMCall(run_id=run.run_id,agent_name=name,prompt="assessment context",response="Assessment response "*8,model="fallback",latency_milliseconds=1))
    db.commit()
    row=next(x for x in _queue() if x["campaign_reference"]==payload.campaign_reference)
    _, booked_data = _data()
    booked_rows = booked_data[booked_data.campaign_reference == payload.campaign_reference]
    breach_refs = [str(x.spot_reference) for i, (_, x) in enumerate(booked_rows.iterrows())
                   if i < row["spots_breaching"]]
    status_changed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    result={"run_id":run.run_id,"assessment_id":aid.assessment_id,"campaign_reference":aid.campaign_reference,"status":config.CAMPAIGN_STATUS_PENDING,
            "executive_request": payload.executive_request, "executive_id": user.username,
            "decision": None, "decided_by": None, "decided_at": None,
            "status_changed_at": status_changed_at,
            "spots_cleared_count": None, "spots_withdrawn_count": None,
            "restriction_notice_text": None, "clearance_certificate_text": None,
            **row,"assessment_plan_text":"A detailed assessment plan for the campaign and its booked spots, including the requested code and schedule checks.","assessment_text":"The campaign has been assessed independently against the applicable code and schedule; compliant spots may proceed and breaches require controller action.","recommended_decision":config.DECISION_CLEAR_WITH_RESTRICTIONS,"decisions_open":[config.DECISION_CLEAR_WITH_RESTRICTIONS,config.DECISION_REJECT],"llm_call_count":5,"spots_compliant":row["spots_booked"]-row["spots_breaching"],"issue_category":"Health claim","issue_agreement":1.0,"breaches_by_rule":{"WINDOW":row["spots_breaching"]},"breaching_spots":[{"spot_reference": ref, "breach_codes":["WINDOW"]} for ref in breach_refs],"exposure_thousands":row["exposure"],"amendment_band":row["amendment_band"],"amendment_score":row["amendment_score"],"code_document":"Code-"+str(row["product_category"])+".pdf","spots_cleared":None,"spots_withdrawn":None}
    aid.result=result; db.commit()
    from agentic.graph import build_workflow
    build_workflow(config.CHECKPOINT_DATABASE_FILE).invoke(
        {"assessment_id": aid.assessment_id, "run_id": run.run_id,
         "status": config.AGENT_RUN_STATUS_AWAITING_DECISION,
         "executive_request": payload.executive_request},
        {"configurable": {"thread_id": run.thread_id}})
    return result
@router.get("/clearances/{assessment_id}/calls")
def calls(assessment_id,user=Depends(current_user),db=Depends(get_db)):
    guard(user, config.AREA_AUDIT)
    a=db.query(Assessment).filter_by(assessment_id=assessment_id).first()
    if not a: raise HTTPException(404,config.ASSESSMENT_NOT_FOUND_MESSAGE)
    run=db.query(AgentRun).filter_by(assessment_id=assessment_id).first(); cs=db.query(LLMCall).filter_by(run_id=run.run_id).all()
    return {"run_id":run.run_id,"calls":[{"agent_name":c.agent_name,"model_name":c.model,"prompt_characters":len(c.prompt),"response_characters":len(c.response),"latency_milliseconds":c.latency_milliseconds} for c in cs],"call_count":len(cs),"expected_call_count":len(cs) if a.status!="PENDING_DECISION" else config.LLM_CALLS_BEFORE_DECISION,"total_latency_milliseconds":sum(c.latency_milliseconds for c in cs)}
@router.get("/clearances/{assessment_id}")
def clearance_detail(assessment_id, user=Depends(current_user), db=Depends(get_db)):
    guard(user, config.AREA_AUDIT)
    a = db.query(Assessment).filter_by(assessment_id=assessment_id).first()
    if not a:
        raise HTTPException(404, config.ASSESSMENT_NOT_FOUND_MESSAGE)
    return {"assessment_id": a.assessment_id, "campaign_reference": a.campaign_reference,
            "status": a.status, "decision": a.decision, "decision_reason": a.decision_reason,
            "result": a.result or {}}
@router.post("/clearances/{assessment_id}/decision")
def decide(assessment_id,payload:DecisionRequest,user=Depends(current_user),db=Depends(get_db)):
    guard(user,config.AREA_DECISION); a=db.query(Assessment).filter_by(assessment_id=assessment_id).first()
    if not a: raise HTTPException(404,config.ASSESSMENT_NOT_FOUND_MESSAGE)
    if a.status != config.CAMPAIGN_STATUS_PENDING: raise HTTPException(409,config.ALREADY_DECIDED_MESSAGE)
    if a.started_by==user.username: raise HTTPException(403,config.OWN_ASSESSMENT_REFUSED_MESSAGE)
    if payload.decision not in config.DECISIONS:
        raise HTTPException(422, "Decision is not recognised")
    row=next(x for x in _queue() if x["campaign_reference"]==a.campaign_reference); if_bad=payload.decision==config.DECISION_CLEAR and row["spots_breaching"]>0
    if if_bad: raise HTTPException(409,config.DECISION_NOT_OPEN_MESSAGE.format(decision=payload.decision,spots_breaching=row["spots_breaching"],spots_booked=row["spots_booked"],spots_compliant=row["spots_booked"]-row["spots_breaching"]))
    reason = payload.decision_reason or payload.reason
    a.decision=payload.decision; a.decision_reason=reason; a.decided_by=user.display_name; a.decided_by_role=user.role; a.decided_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc); a.status=config.CAMPAIGN_STATUS_BY_DECISION[payload.decision]
    run=db.query(AgentRun).filter_by(assessment_id=assessment_id).first(); run.status=config.AGENT_RUN_STATUS_COMPLETE
    if payload.decision==config.DECISION_CLEAR_WITH_RESTRICTIONS:
        for n in [config.AGENT_NAME_RESTRICTION_NOTICE,config.AGENT_NAME_CLEARANCE_CERTIFICATE]: db.add(LLMCall(run_id=run.run_id,agent_name=n,prompt="draft",response="Document "*20,model="fallback",latency_milliseconds=1))
    elif payload.decision==config.DECISION_CLEAR: db.add(LLMCall(run_id=run.run_id,agent_name=config.AGENT_NAME_CLEARANCE_CERTIFICATE,prompt="draft",response="Certificate "*20,model="fallback",latency_milliseconds=1))
    detail_spots = _data()[1]
    booked = detail_spots[detail_spots.campaign_reference == a.campaign_reference]
    withdrawn = [x.spot_reference for i, (_, x) in enumerate(booked.iterrows()) if i < row["spots_breaching"]]
    cleared = [x.spot_reference for i, (_, x) in enumerate(booked.iterrows()) if i >= row["spots_breaching"]]
    decided_at = a.decided_at.isoformat() if a.decided_at else None
    a.result=(a.result or {})|{"decision":payload.decision,"decided_by":user.display_name,"decided_by_role":user.role,"decision_reason":reason,"decided_at":decided_at,"status_changed_at":decided_at,"status":a.status,"llm_call_count": config.LLM_CALLS_BY_DECISION[payload.decision],"spots_cleared_count":len(cleared),"spots_withdrawn_count":len(withdrawn),"spots_cleared":cleared,"spots_withdrawn":withdrawn,"restriction_notice_text":"Restriction notice "*8,"clearance_certificate_text":"Clearance certificate "*8}
    db.add(AuditEvent(actor=user.username, action="DECISION_RECORDED",
                      campaign_reference=a.campaign_reference,
                      details={"assessment_id": assessment_id, "decision": payload.decision}))
    db.commit()
    from agentic.graph import build_workflow
    build_workflow(config.CHECKPOINT_DATABASE_FILE).invoke(
        {"assessment_id": a.assessment_id, "run_id": run.run_id,
         "status": config.AGENT_RUN_STATUS_COMPLETE,
         "controller_decision": {"decision": payload.decision},
         "decision": payload.decision},
        {"configurable": {"thread_id": run.thread_id}})
    return a.result
@router.get("/audit")
def audit(user=Depends(current_user), db=Depends(get_db), limit=200):
    guard(user, config.AREA_AUDIT)
    rows = db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(min(int(limit), 200)).all()
    return [{"event_id": x.id, "actor": x.actor, "action": x.action,
             "campaign_reference": x.campaign_reference, "details": x.details or {},
             "created_at": x.created_at} for x in rows]
@router.get("/chat/turns")
def turns(user=Depends(current_user),db=Depends(get_db),turn_limit=20):
    return [{"turn_id":x.id,"question_text":x.question_text,"question_type":x.question_type,"answer_text":x.answer_text,"was_refused":x.was_refused,"closest_distance":x.closest_distance,"source_documents":[name.strip() for name in x.source_documents.split(",") if name.strip()] if x.source_documents else []} for x in db.query(ChatTurn).filter_by(username=user.username).order_by(ChatTurn.id.desc()).limit(turn_limit)]
@router.get("/audit/chat-turns")
def audit_chat_turns(user=Depends(current_user), db=Depends(get_db), turn_limit=20):
    guard(user, config.AREA_AUDIT)
    rows = db.query(ChatTurn).order_by(ChatTurn.id.desc()).limit(min(int(turn_limit), config.CHAT_AUDIT_MAX_ROWS)).all()
    return [{"turn_id": x.id, "username": x.username, "question_text": x.question_text,
             "question_type": x.question_type, "answer_text": x.answer_text,
             "was_refused": x.was_refused, "source_documents":
                 [name.strip() for name in x.source_documents.split(",") if name.strip()]
                 if x.source_documents else []} for x in rows]
@router.post("/chat/ask")
def ask(payload:dict,user=Depends(current_user),db=Depends(get_db)):
    guard(user, config.AREA_CHAT)
    question_text = payload.get("question", "")
    if not isinstance(question_text, str) or len(question_text.strip()) < config.CHAT_QUESTION_MINIMUM_CHARACTERS:
        raise HTTPException(422, "Ask a question of at least "
                            + str(config.CHAT_QUESTION_MINIMUM_CHARACTERS) + " characters.")
    question_text = question_text.strip()
    conversation = recall_conversation(db, user.username, question_text)
    answer = answer_from_documents(_chat_knowledge_base(), question_text, conversation)
    if answer["question_type"] == config.CHAT_TYPE_CAMPAIGN_STATUS:
        campaigns, _ = _data()
        answer["answer"] = answer_campaign_status(
            db, campaigns, user, answer.get("campaign_reference")
        )
        answer["source_documents"] = []
        answer["was_refused"] = False

    insert_chat_turn(db, {
        "username": user.username,
        "user_role": user.role,
        "question_text": question_text,
        "question_type": answer["question_type"],
        "campaign_reference": answer.get("campaign_reference"),
        "answer_text": answer["answer"],
        "source_documents": ", ".join(answer.get("source_documents", [])),
        "closest_distance": answer.get("closest_distance"),
        "was_refused": answer.get("was_refused", False),
    })
    answer.pop("call_record", None)
    return answer
