from config import config
def answer_campaign_status(session, campaigns, user, campaign_reference):
    row = campaigns[campaigns[config.CAMPAIGN_REFERENCE_COLUMN] == campaign_reference]
    allowed = getattr(user, "assigned_agencies", None) or user.get("assigned_agencies", [])
    role = getattr(user, "role", None) or user.get("role")
    if not len(row) or (role == config.ROLE_LIAISON and str(row.iloc[0].get(config.AGENCY_CODE_COLUMN)) not in allowed):
        return config.CHAT_CAMPAIGN_NOT_FOUND_MESSAGE
    from persistence.models import Assessment
    record = session.query(Assessment).filter_by(campaign_reference=campaign_reference).order_by(Assessment.id.desc()).first()
    if not record:
        answer = config.CHAT_NOT_ASSESSED_TEMPLATE.format(campaign_reference=campaign_reference)
    elif record.decision:
        result = record.result or {}
        changed = record.updated_at or record.created_at
        answer = (config.CHAT_STATUS_TEMPLATE.format(
            campaign_reference=campaign_reference,
            status_phrase=config.CHAT_STATUS_PHRASES.get(record.status, "has been decided"),
            changed_at=changed.strftime(config.STATUS_CHANGE_TIME_FORMAT))
                  + " " + config.CHAT_DECIDED_TEMPLATE.format(
            decision=record.decision,
            spots_cleared=result.get("spots_cleared_count", 0),
            spots_withdrawn=result.get("spots_withdrawn_count", 0))
                  + " " + config.CHAT_DOCUMENTS_SENT.get(record.status, ""))
        if role == config.ROLE_EXECUTIVE:
            answer += (" Assessment " + record.assessment_id + " was opened by "
                       + str(record.started_by) + " and decided by "
                       + str(record.decided_by) + ". Reason: " + str(record.decision_reason)
                       + ". Issue: " + str(result.get("issue_category", ""))
                       + ". Cleared spots: " + ", ".join(result.get("spots_cleared", [])))
    else:
        changed = record.updated_at or record.created_at
        answer = config.CHAT_STATUS_TEMPLATE.format(
            campaign_reference=campaign_reference,
            status_phrase=config.CHAT_STATUS_PHRASES.get(record.status, "is under review"),
            changed_at=changed.strftime(config.STATUS_CHANGE_TIME_FORMAT))
    return answer