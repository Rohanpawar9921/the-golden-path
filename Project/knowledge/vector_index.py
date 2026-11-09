import json
import re
from pathlib import Path

class _Collection:
    def __init__(self, path, records): self.path, self.records = Path(path), records
    def count(self): return len(self.records)
    def get(self, include=None, where=None):
        records = [r for r in self.records if not where or all(r.get(k) == v for k,v in where.items())]
        return {"ids":[r["chunk_id"] for r in records], "documents":[r["chunk_text"] for r in records],
                "metadatas":[{"document_name":r["document_name"]} for r in records]}
    def query(self, query_texts, n_results=4, where=None, include=None):
        docs=[]; metas=[]; distances=[]
        for query in query_texts:
            q=set(re.findall(r"\w+", query.lower()))
            ranked=[]
            duplicate_names = {}
            for r in self.records:
                duplicate_names.setdefault(r["chunk_text"], set()).add(r["document_name"])
            for r in self.records:
                if where and any(r.get(k)!=v for k,v in where.items()): continue
                words=set(re.findall(r"\w+", r["chunk_text"].lower()))
                distance = 1-len(q&words)/max(1,len(q|words))
                # Identical boilerplate occurs in several codes.  Prefer the
                # first document's copy and let the other code contribute its
                # next-best, category-specific passage.
                duplicates = duplicate_names.get(r["chunk_text"], set())
                if len(duplicates) > 1 and r["document_name"] != min(duplicates):
                    distance += 0.1
                ranked.append((distance,r))
            ranked.sort(key=lambda x:(x[0],x[1]["chunk_id"]))
            docs.append([r["chunk_text"] for d,r in ranked[:n_results]])
            metas.append([{"document_name":r["document_name"]} for d,r in ranked[:n_results]])
            distances.append([d for d,r in ranked[:n_results]])
        return {"documents":docs,"metadatas":metas,"distances":distances}

def build_vector_index(chunk_records, directory):
    path=Path(directory); path.mkdir(parents=True, exist_ok=True)
    records=list(chunk_records)
    if len({r["chunk_id"] for r in records}) != len(records): raise ValueError("duplicate chunk ids")
    (path/"records.json").write_text(json.dumps(records), encoding="utf-8")
    return len(records)

def open_vector_index(directory):
    path=Path(directory); file=path/"records.json"
    if not file.exists():
        # The application entry point is intentionally tiny; lazily creating the
        # configured store keeps first-use behaviour deterministic.
        from config import config
        from knowledge.pdf_extraction import extract_text_from_directory
        from knowledge.chunk_splitting import split_documents_into_sections, build_chunk_records
        docs=extract_text_from_directory(config.DOCS_DIRECTORY)
        build_vector_index(build_chunk_records(split_documents_into_sections(docs)), directory)
    return _Collection(path, json.loads(file.read_text(encoding="utf-8")))

def search_documents(collection, questions):
    from config import config
    ids={r["chunk_text"]:r["chunk_id"] for r in collection.records}
    result=[]
    for question in questions:
        response=collection.query([question], n_results=config.CHAT_RETRIEVAL_RESULT_COUNT)
        filtered=[(text,meta,distance) for text,meta,distance in zip(response["documents"][0],
                         response["metadatas"][0],response["distances"][0])
                  if meta["document_name"] not in config.CHAT_EXCLUDED_DOCUMENTS]
        # Fetch additional passages when exclusions occupied the top results.
        if len(filtered) < config.CHAT_RETRIEVAL_RESULT_COUNT:
            all_response=collection.query([question], n_results=collection.count())
            filtered=[(text,meta,distance) for text,meta,distance in zip(
                all_response["documents"][0],all_response["metadatas"][0],all_response["distances"][0])
                if meta["document_name"] not in config.CHAT_EXCLUDED_DOCUMENTS][:config.CHAT_RETRIEVAL_RESULT_COUNT]
        result.append([{"chunk_id":ids[text],"chunk_text":text,"document_name":meta["document_name"],
                        "distance":distance} for text,meta,distance in filtered])
    return result

def read_document_chunks(collection, document_name):
    found=collection.get(where={"document_name":document_name})
    if not found["ids"]: raise ValueError("unknown document")
    return found["documents"]

def find_nearest_passage(collection, question, document_name):
    response=collection.query([question], n_results=1, where={"document_name":document_name})
    if not response["documents"][0]: raise ValueError("unknown document")
    return response["documents"][0][0]