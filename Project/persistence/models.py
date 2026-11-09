from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String, Text, Boolean, Integer, JSON
from .database import Base
def now(): return datetime.now(timezone.utc)
class UserAccount(Base):
    __tablename__="users"; id=Column(Integer,primary_key=True); username=Column(String(80),unique=True,index=True,nullable=False); display_name=Column(String(200)); role=Column(String(80)); password_hash=Column(String(500)); password_salt=Column(String(100)); assigned_agencies=Column(JSON,default=list); session_token=Column(String(200)); created_at=Column(DateTime,default=now)
class Campaign(Base):
    __tablename__="campaigns"; id=Column(Integer,primary_key=True); campaign_reference=Column(String(40),unique=True,index=True,nullable=False); advertiser_name=Column(String(200)); agency_name=Column(String(200)); agency_code=Column(String(40)); status=Column(String(60),default="PENDING_DECISION"); created_at=Column(DateTime,default=now); updated_at=Column(DateTime,default=now,onupdate=now)
class Submission(Base):
    __tablename__="submissions"; id=Column(Integer,primary_key=True); campaign_reference=Column(String(40),index=True,nullable=False); submission_id=Column(String(80),unique=True); data=Column(JSON,default=dict)
class BookedSpot(Base):
    __tablename__="booked_spots"; id=Column(Integer,primary_key=True); spot_reference=Column(String(80),unique=True); campaign_reference=Column(String(40),index=True,nullable=False); data=Column(JSON,default=dict)
class CampaignNote(Base):
    __tablename__="campaign_notes"; id=Column(Integer,primary_key=True); note_id=Column(String(80),unique=True); campaign_reference=Column(String(40),index=True,nullable=False); data=Column(JSON,default=dict)
class ProgrammeSchedule(Base):
    __tablename__="programme_schedule"; id=Column(Integer,primary_key=True); schedule_entry_id=Column(String(80),unique=True); data=Column(JSON,default=dict)
class Assessment(Base):
    __tablename__="assessments";     id=Column(Integer,primary_key=True); assessment_id=Column(String(80),unique=True,index=True,nullable=False); campaign_reference=Column(String(40),index=True,nullable=False); started_by=Column(String(80),nullable=False); executive_request=Column(Text); status=Column(String(40),default="RUNNING"); decision=Column(String(80)); decision_reason=Column(Text); decided_by=Column(String(120)); decided_by_role=Column(String(80)); decided_at=Column(DateTime); result=Column(JSON,default=dict); created_at=Column(DateTime,default=now); updated_at=Column(DateTime,default=now,onupdate=now)
class AgentRun(Base):
    __tablename__="agent_runs"; id=Column(String(80),primary_key=True); run_id=Column(String(80),unique=True,index=True,nullable=False); assessment_id=Column(String(80),index=True); thread_id=Column(String(120),index=True); status=Column(String(40),default="RUNNING"); state=Column(JSON,default=dict); created_at=Column(DateTime,default=now); updated_at=Column(DateTime,default=now,onupdate=now)
class LLMCall(Base):
    __tablename__="llm_calls"; id=Column(Integer,primary_key=True); run_id=Column(String(80),index=True); agent_name=Column(String(100)); prompt=Column(Text); response=Column(Text); model=Column(String(100)); used_fallback=Column(Boolean,default=False); latency_milliseconds=Column(Integer,default=1); created_at=Column(DateTime,default=now)
class AuditEvent(Base):
    __tablename__="audit_events"; id=Column(Integer,primary_key=True); actor=Column(String(80)); action=Column(String(120)); campaign_reference=Column(String(40)); details=Column(JSON,default=dict); created_at=Column(DateTime,default=now)
class ChatTurn(Base):
    __tablename__="chat_turns"; id=Column(Integer,primary_key=True); username=Column(String(80),index=True); user_role=Column(String(80)); question_text=Column(Text); question_type=Column(String(80)); campaign_reference=Column(String(40)); answer_text=Column(Text); source_documents=Column(Text); closest_distance=Column(Integer,default=0); was_refused=Column(Boolean,default=False); created_at=Column(DateTime,default=now)
# Names used by the original service contract.
ClearanceAssessment = Assessment