"""
Summarization for SmartWrite AI.

Implements extractive TextRank: sentences become graph nodes, edges are
weighted by TF-IDF cosine similarity, and PageRank scores which
sentences are most "central" to the document. The top-scoring sentences
(in their original order) become the summary.

This is deliberately offline and dependency-light (scikit-learn +
networkx, both pure-Python/no-model-download) rather than a transformer
summarizer, which would need to pull a multi-hundred-MB model from
huggingface.co — not reachable from every network this app might run
on. Swap in `transformers.pipeline("summarization")` if you want
abstractive summaries and have model-download access.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


@dataclass
class SummaryResult:
    summary: str
    sentence_count: int
    original_sentence_count: int


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    sentences = _SENTENCE_SPLIT.split(text)
    return [s.strip() for s in sentences if len(s.split()) > 3]


def summarize(text: str, ratio: float = 0.3, min_sentences: int = 2, max_sentences: int = 10) -> SummaryResult:
    sentences = _split_sentences(text)
    n = len(sentences)

    if n <= min_sentences:
        return SummaryResult(summary=" ".join(sentences), sentence_count=n, original_sentence_count=n)

    target = max(min_sentences, min(max_sentences, round(n * ratio)))

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(sentences)
    similarity = (tfidf * tfidf.T).toarray()

    graph = nx.from_numpy_array(similarity)
    scores = nx.pagerank(graph, max_iter=200)

    ranked_idx = sorted(scores, key=scores.get, reverse=True)[:target]
    ranked_idx.sort()  # restore original reading order

    summary = " ".join(sentences[i] for i in ranked_idx)
    return SummaryResult(summary=summary, sentence_count=len(ranked_idx), original_sentence_count=n)
