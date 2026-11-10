"""Answer campaign questions from the clearance record and enforce agency ownership."""

from __future__ import annotations

from datetime import datetime

from config import config
from persistence.models import Assessment


def _user_value(user, name, default=None):
    if isinstance(user, dict):
        return user.get(name, default)
    return getattr(user, name, default)


def _changed_at(record, result):
    value = result.get("status_changed_at")
    if not value:
        value = record.decided_at or record.updated_at or record.created_at
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    return value.strftime(config.STATUS_CHANGE_TIME_FORMAT) if value else "at an unknown time"


def _campaign_facts(campaigns, campaign_reference):
    row = campaigns[campaigns[config.CAMPAIGN_REFERENCE_COLUMN].astype(str)
                    == str(campaign_reference)]
    return row.iloc[0].to_dict() if len(row) else {}


def _desk_details(record, result, campaign):
    """Summarize details the internal desk may see, never sent to a liaison."""
    def value(*names, default="not recorded"):
        for name in names:
            found = result.get(name)
            if found is not None and found != "":
                return found
            found = campaign.get(name)
            if found is not None and found != "":
                return found
        return default

    breach_counts = result.get("breaches_by_rule") or {}
    breach_text = ", ".join(f"{code}: {breach_counts.get(code, 0)}"
                             for code in config.BREACH_CODES)
    spots = result.get("breaching_spots") or []
    if spots:
        breach_spot_text = "; ".join(
            f"{spot.get('spot_reference', 'unknown spot')} "
            f"({', '.join(spot.get('breach_codes') or []) or 'breach recorded'}"
            + (f"; programmes {', '.join(map(str, spot.get('programmes', [])))}"
               if spot.get("programmes") else "")
            + (f"; under-18 indexes {', '.join(map(str, spot.get('under18_indexes', [])))}"
               if spot.get("under18_indexes") else "")
            + ")"
            for spot in spots
        )
    else:
        breach_spot_text = "none recorded"

    first_transmission = result.get("first_transmission") or {}
    if isinstance(first_transmission, dict):
        first_text = " ".join(str(first_transmission.get(key))
                               for key in ("broadcast_day", "break_time")
                               if first_transmission.get(key)) or "not recorded"
    else:
        first_text = str(first_transmission or "not recorded")

    decisions_open = result.get("decisions_open") or []
    issue_agreement = value("issue_agreement", "weighted_agreement")
    details = (
        f"Assessment {record.assessment_id} was opened by {record.started_by}. "
        f"Copy: {value(config.COPY_TITLE_COLUMN)}; clock number: {value(config.CLOCK_NUMBER_COLUMN)}; "
        f"agency: {value(config.AGENCY_NAME_COLUMN)} ({value(config.AGENCY_CODE_COLUMN)}); "
        f"category: {value(config.PRODUCT_CATEGORY_COLUMN)}; code: "
        f"{value('code_document', 'code_document_name')}. "
        f"Amendment score: {value('amendment_score')}; band: {value('amendment_band')}. "
        f"Issue: {value('issue_category')} (agreement {issue_agreement}). "
        f"Spots: {value('spots_booked')} booked, {value('spots_breaching')} breaching, "
        f"{value('spots_compliant')} compliant. Breaches by rule: {breach_text}. "
        f"Breaching spots: {breach_spot_text}. First transmission: {first_text}. "
        f"Exposure: {value('exposure', 'exposure_thousands')}. "
        f"Decisions open: {', '.join(map(str, decisions_open)) or 'not recorded'}. "
        f"Recommendation: {value('recommended_decision')}."
    )
    if record.decision:
        details += (
            f" Decided by {record.decided_by} ({record.decided_by_role or 'role not recorded'})."
            f" Reason: {record.decision_reason or 'not recorded'}."
            f" Cleared spots: {', '.join(map(str, result.get('spots_cleared') or [])) or 'none'}."
            f" Withdrawn spots: {', '.join(map(str, result.get('spots_withdrawn') or [])) or 'none'}."
        )
    return details


def answer_campaign_status(session, open_campaigns, signed_in_user, campaign_reference):
    """Return a record-backed answer without disclosing another agency's campaign."""
    if not campaign_reference:
        return config.CHAT_CAMPAIGN_NOT_FOUND_MESSAGE

    campaign = _campaign_facts(open_campaigns, campaign_reference)
    role = _user_value(signed_in_user, "role")
    allowed_agencies = _user_value(signed_in_user, "assigned_agencies", []) or []
    agency_code = str(campaign.get(config.AGENCY_CODE_COLUMN, ""))
    if not campaign or (role == config.ROLE_LIAISON and agency_code not in allowed_agencies):
        return config.CHAT_CAMPAIGN_NOT_FOUND_MESSAGE

    record = (session.query(Assessment)
              .filter_by(campaign_reference=campaign_reference)
              .order_by(Assessment.id.desc()).first())
    if not record:
        return config.CHAT_NOT_ASSESSED_TEMPLATE.format(campaign_reference=campaign_reference)

    result = record.result or {}
    status_line = config.CHAT_STATUS_TEMPLATE.format(
        campaign_reference=campaign_reference,
        status_phrase=config.CHAT_STATUS_PHRASES.get(record.status, "is under review"),
        changed_at=_changed_at(record, result),
    )
    if role not in config.CHAT_RECORD_ROLES:
        if not record.decision:
            return status_line
        return " ".join([
            status_line,
            config.CHAT_DECIDED_TEMPLATE.format(
                decision=record.decision,
                spots_cleared=result.get("spots_cleared_count", 0),
                spots_withdrawn=result.get("spots_withdrawn_count", 0),
            ),
            config.CHAT_DOCUMENTS_SENT.get(record.status, ""),
        ]).strip()

    detail = _desk_details(record, result, campaign)
    if not record.decision:
        return status_line + " " + detail

    return " ".join([
        status_line,
        detail,
        config.CHAT_DECIDED_TEMPLATE.format(
            decision=record.decision,
            spots_cleared=result.get("spots_cleared_count", 0),
            spots_withdrawn=result.get("spots_withdrawn_count", 0),
        ),
        config.CHAT_DOCUMENTS_SENT.get(record.status, ""),
    ]).strip()
