import json
import math
import re
from collections import Counter
from pathlib import Path


_TOKEN_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "can",
    "could", "did", "do", "does", "for", "from", "had", "has", "have", "he", "her",
    "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "me",
    "might", "my", "of", "on", "or", "our", "ours", "she", "should", "that", "the",
    "their", "theirs", "them", "they", "this", "those", "to", "was", "we", "were",
    "what", "when", "where", "which", "who", "whom", "will", "with", "would", "you",
    "your", "yours",
}


def _tokens(text):
    return [token for token in re.findall(r"[a-z0-9]+", str(text).lower())
            if token not in _TOKEN_STOPWORDS]


class _Collection:
    def __init__(self, path, records): self.path, self.records = Path(path), records
    def count(self): return len(self.records)
    def get(self, include=None, where=None):
        records = [r for r in self.records if not where or all(r.get(k) == v for k,v in where.items())]
        return {"ids":[r["chunk_id"] for r in records], "documents":[r["chunk_text"] for r in records],
                "metadatas":[{"document_name":r["document_name"]} for r in records]}
    def query(self, query_texts, n_results=4, where=None, include=None):
        docs=[]; metas=[]; distances=[]; ids=[]
        corpus = self.records
        candidate_indexes = [index for index, record in enumerate(corpus)
                             if not where or all(record.get(k) == v for k, v in where.items())]
        document_tokens = []
        for record in corpus:
            title = re.sub(r"([a-z])([A-Z])", r"\1 \2",
                           Path(record["document_name"]).stem.replace("-", " "))
            document_tokens.append(_tokens(record["chunk_text"]) + _tokens(title))
        document_frequency = Counter()
        for words in document_tokens:
            document_frequency.update(set(words))
        count = max(1, len(corpus))
        average_length = sum(map(len, document_tokens)) / count or 1
        k1, b = 1.2, 0.75
        for query in query_texts:
            query_terms = set(_tokens(query))
            ranked=[]
            for index in candidate_indexes:
                r = corpus[index]
                words = document_tokens[index]
                frequencies = Counter(words)
                length_norm = k1 * (1 - b + b * len(words) / average_length)
                score = 0.0
                for term in query_terms:
                    frequency = frequencies.get(term, 0)
                    if not frequency:
                        continue
                    inverse_frequency = math.log1p(
                        (count - document_frequency[term] + 0.5)
                        / (document_frequency[term] + 0.5)
                    )
                    score += inverse_frequency * frequency * (k1 + 1) / (frequency + length_norm)
                # A bounded BM25 transform keeps the relevance value compatible
                # with CHAT_MAX_RELEVANCE_DISTANCE while ranking meaningful matches.
                distance = 1.0 / (1.0 + score)
                ranked.append((distance,r))
            ranked.sort(key=lambda x:(x[0],x[1]["chunk_id"]))
            docs.append([r["chunk_text"] for d,r in ranked[:n_results]])
            metas.append([{"document_name":r["document_name"]} for d,r in ranked[:n_results]])
            distances.append([d for d,r in ranked[:n_results]])
            ids.append([r["chunk_id"] for d,r in ranked[:n_results]])
        return {"ids":ids,"documents":docs,"metadatas":metas,"distances":distances}

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
    result=[]
    for question in questions:
        response=collection.query([question], n_results=config.CHAT_RETRIEVAL_RESULT_COUNT,
                                  include=["documents", "metadatas", "distances"])
        response_ids=(response.get("ids") or [[]])[0]
        filtered=[(chunk_id,text,meta,distance) for chunk_id,text,meta,distance in zip(
            response_ids or [None] * len(response["documents"][0]),
            response["documents"][0],response["metadatas"][0],response["distances"][0])
            if meta["document_name"] not in config.CHAT_EXCLUDED_DOCUMENTS]
        # Fetch additional passages when exclusions occupied the top results.
        if len(filtered) < config.CHAT_RETRIEVAL_RESULT_COUNT:
            all_response=collection.query([question], n_results=collection.count(),
                                          include=["documents", "metadatas", "distances"])
            all_ids=(all_response.get("ids") or [[]])[0]
            filtered=[(chunk_id,text,meta,distance) for chunk_id,text,meta,distance in zip(
                all_ids or [None] * len(all_response["documents"][0]),
                all_response["documents"][0],all_response["metadatas"][0],
                all_response["distances"][0])
                if meta["document_name"] not in config.CHAT_EXCLUDED_DOCUMENTS
            ][:config.CHAT_RETRIEVAL_RESULT_COUNT]
        result.append([{"chunk_id":chunk_id,"chunk_text":text,
                        "document_name":meta["document_name"],"distance":distance}
                       for chunk_id,text,meta,distance in filtered])
    return result

def read_document_chunks(collection, document_name):
    found=collection.get(where={"document_name":document_name})
    if not found["ids"]: raise ValueError("unknown document")
    return found["documents"]

def find_nearest_passage(collection, question, document_name):
    response=collection.query([question], n_results=1, where={"document_name":document_name})
    if not response["documents"][0]: raise ValueError("unknown document")
    return response["documents"][0][0]
