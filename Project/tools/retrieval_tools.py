from config import config
from knowledge.vector_index import find_nearest_passage

def _read(collection, subject, mapping, question):
    document=mapping.get(subject)
    if not document: raise ValueError(f"unknown subject: {subject}")
    return find_nearest_passage(collection, question, document)

def read_executive_checks(collection, issue):
    return _read(collection, issue, config.GUIDE_DOCUMENT_BY_ISSUE, config.EXECUTIVE_CHECKS_QUESTION)

def read_rebooking_steps(collection, issue):
    return _read(collection, issue, config.CATEGORY_CODE_DOCUMENTS, config.REBOOKING_QUESTION)

def read_standing_restrictions(collection, category):
    return _read(collection, category, config.CATEGORY_CODE_DOCUMENTS,
                 config.STANDING_RESTRICTIONS_QUESTION)