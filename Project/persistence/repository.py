"""Small repository facade keeping API code independent of SQLAlchemy details."""
import csv, uuid
import secrets
from pathlib import Path
from sqlalchemy import select
from .models import *
try:
    from access.password_security import hash_password, verify_password, create_session_token
    from config import config
except ImportError:
    from Project.access.password_security import hash_password, verify_password, create_session_token
    from Project.config import config

class Repository:
    def __init__(self, db): self.db=db
    def _add(self, obj): self.db.add(obj); self.db.commit(); self.db.refresh(obj); return obj
    def get_user(self, username): return self.db.scalar(select(UserAccount).where(UserAccount.username==username))
    def authenticate(self, username, password):
        user=self.get_user(username)
        if not user or not verify_password(password,user.password_hash): return None
        user.session_token=create_session_token(); self.db.commit(); return user
    def get_by_token(self, token):
        return self.db.scalar(select(UserAccount).where(UserAccount.session_token==token))
    def seed_users(self):
        for item in config.SEED_USER_ACCOUNTS:
            if not self.get_user(item["username"]):
                encoded = hash_password(item["password"])
                self._add(UserAccount(username=item["username"],display_name=item["display_name"],role=item["role"],assigned_agencies=item.get("assigned_agencies",[]),password_hash=encoded,password_salt=encoded.split("$")[1]))
    def campaign(self, reference): return self.db.scalar(select(Campaign).where(Campaign.campaign_reference==reference))
    def list_campaigns(self, status=None):
        q=select(Campaign).order_by(Campaign.created_at)
        if status: q=q.where(Campaign.status==status)
        return list(self.db.scalars(q))
    def create_assessment(self, reference, started_by, executive_request=""):
        assessment=Assessment(assessment_id=config.ASSESSMENT_ID_PREFIX+uuid.uuid4().hex[:config.IDENTIFIER_HEX_LENGTH].upper(),campaign_reference=reference,started_by=started_by,executive_request=executive_request)
        return self._add(assessment)
    def assessment(self, assessment_id): return self.db.scalar(select(Assessment).where(Assessment.assessment_id==assessment_id))
    def record_llm_call(self, **kwargs): return self._add(LLMCall(**kwargs))
    def audit(self, **kwargs): return self._add(AuditEvent(**kwargs))
    def import_csv(self, directory=None):
        root=Path(directory or Path(__file__).resolve().parents[1])
        def rows(name): 
            with open(root/"data"/"input"/name,newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))
        for row in rows("open_campaigns.csv"):
            ref=row["campaign_reference"]
            if not self.campaign(ref): self._add(Campaign(campaign_reference=ref,advertiser_name=row.get("advertiser_name"),agency_name=row.get("agency_name"),agency_code=row.get("agency_code")))
            if not self.db.scalar(select(Submission).where(Submission.submission_id==row.get("submission_id"))): self._add(Submission(campaign_reference=ref,submission_id=row.get("submission_id"),data=row))
        for row in rows("booked_spots.csv"):
            if not self.db.scalar(select(BookedSpot).where(BookedSpot.spot_reference==row.get("spot_reference"))): self._add(BookedSpot(campaign_reference=row["campaign_reference"],spot_reference=row.get("spot_reference"),data=row))
        for row in rows("open_campaign_notes.csv"):
            if not self.db.scalar(select(CampaignNote).where(CampaignNote.note_id==row.get("note_id"))): self._add(CampaignNote(campaign_reference=row["campaign_reference"],note_id=row.get("note_id"),data=row))
        return len(self.list_campaigns())

def insert_chat_turn(session, values):
    turn = ChatTurn(**{k: v for k, v in values.items() if hasattr(ChatTurn, k)})
    session.add(turn); session.commit(); session.refresh(turn); return turn

def fetch_assessment_records(session, campaign_reference=None):
    q = select(Assessment)
    if campaign_reference is not None:
        q = q.where(campaign_reference if not isinstance(campaign_reference, str)
                    else Assessment.campaign_reference == campaign_reference)
    return list(session.scalars(q.order_by(Assessment.created_at.desc())))

def fetch_user_account(session, criterion):
    """Return a legacy dict-shaped account for service/audit callers."""
    user = session.query(UserAccount).filter(criterion).first()
    if user is None:
        return None
    salt = user.password_salt
    if not salt and user.password_hash and "$" in user.password_hash:
        salt = user.password_hash.split("$")[1]
    return {"id": user.id, "username": user.username, "display_name": user.display_name,
            "role": user.role, "password_hash": user.password_hash, "password_salt": salt,
            "assigned_agencies": user.assigned_agencies or [], "session_token": user.session_token}