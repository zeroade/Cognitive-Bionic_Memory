"""
Layer 1: Storage — Episodic-Semantic Dual Store + Temporary Binding
"""

import json
from datetime import datetime
from typing import Optional


class EpisodicStore:
    def __init__(self, data_path: str):
        with open(data_path, "r", encoding="utf-8") as f:
            self.episodes = json.load(f)

    def search(self, query: str, alias_map: dict = None) -> list[dict]:
        """Search episodes by keyword matching. Applies alias expansion."""
        query_terms = self._expand_query(query, alias_map)
        results = []
        for ep in self.episodes:
            score = self._relevance_score(ep, query_terms)
            if score > 0:
                results.append({**ep, "_relevance": score})
        return sorted(results, key=lambda x: x["_relevance"], reverse=True)

    def add_episode(self, content: str, source: str, tags: list[str], importance: int = 3) -> dict:
        """Add a new episodic memory from current conversation."""
        ep = {
            "id": f"ep_{len(self.episodes)+1:03d}",
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "content": content,
            "tags": tags,
            "user_importance": importance,
            "emotional_valence": 0.0,
            "retrieval_count": 0,
        }
        self.episodes.append(ep)
        return ep

    def increment_retrieval(self, episode_id: str):
        """Track retrieval frequency for saliency scoring."""
        for ep in self.episodes:
            if ep["id"] == episode_id:
                ep["retrieval_count"] = ep.get("retrieval_count", 0) + 1
                break

    def _expand_query(self, query: str, alias_map: dict = None) -> list[str]:
        """Expand query terms using alias map."""
        terms = query.lower().replace("？", "").replace("?", "").replace("，", " ").split()
        if alias_map:
            expanded = []
            for term in terms:
                expanded.append(term)
                if term in alias_map:
                    expanded.extend(alias_map[term].lower().split())
            terms = expanded
        return terms

    def _relevance_score(self, episode: dict, terms: list[str]) -> float:
        """Simple keyword relevance. In production, use embeddings."""
        text = (episode["content"] + " " + " ".join(episode.get("tags", []))).lower()
        hits = sum(1 for t in terms if t in text)
        return hits / max(len(terms), 1)


class SemanticStore:
    def __init__(self, data_path: str):
        with open(data_path, "r", encoding="utf-8") as f:
            self.entries = json.load(f)

    def search(self, query: str, alias_map: dict = None) -> list[dict]:
        """Search semantic entries by keyword matching."""
        terms = query.lower().replace("？", "").replace("?", "").replace("，", " ").split()
        if alias_map:
            expanded = []
            for term in terms:
                expanded.append(term)
                if term in alias_map:
                    expanded.extend(alias_map[term].lower().split())
            terms = expanded

        results = []
        for entry in self.entries:
            text = (entry["concept"] + " " + entry["content"]).lower()
            hits = sum(1 for t in terms if t in text)
            score = hits / max(len(terms), 1)
            if score > 0:
                results.append({**entry, "_relevance": score})
        return sorted(results, key=lambda x: x["_relevance"], reverse=True)

    def add_entry(self, concept: str, content: str, source_episodes: list[str], confidence: float) -> dict:
        """Add a new semantic entry (from consolidation or external source)."""
        entry = {
            "id": f"sem_{len(self.entries)+1:03d}",
            "concept": concept,
            "content": content,
            "source_episodes": source_episodes,
            "confidence": confidence,
            "last_updated": datetime.now().isoformat(),
        }
        self.entries.append(entry)
        return entry


class TemporaryBinding:
    """
    Session-scoped alias map for tracking semantic drift.
    Users can define aliases via /alias command.
    The system tracks all active bindings and uses them to expand queries.
    """

    def __init__(self):
        self.alias_map: dict[str, str] = {}  # term -> meaning

    def add_alias(self, term: str, meaning: str):
        """Register a temporary binding: term now means 'meaning' in this session."""
        self.alias_map[term.lower()] = meaning
        return f"臨時綁定已建立：「{term}」→「{meaning}」"

    def remove_alias(self, term: str) -> str:
        key = term.lower()
        if key in self.alias_map:
            del self.alias_map[key]
            return f"已移除「{term}」的臨時綁定"
        return f"未找到「{term}」的臨時綁定"

    def get_aliases(self) -> dict:
        return dict(self.alias_map)

    def expand_query(self, query: str) -> str:
        """Expand a query string using active aliases."""
        expanded = query
        for term, meaning in self.alias_map.items():
            if term in query.lower():
                expanded += f" {meaning}"
        return expanded


class DualStore:
    """
    Unified interface for the dual-store system.
    Implements bidirectional compensation:
    - When episodic info is insufficient → expand semantic search
    - When context is rich → use episodic context to narrow semantic search
    """

    def __init__(self, episodic: EpisodicStore, semantic: SemanticStore, binding: TemporaryBinding):
        self.episodic = episodic
        self.semantic = semantic
        self.binding = binding

    def search(self, query: str) -> dict:
        """
        Bidirectional search with compensation logic.
        Returns results from both stores with compensation info.
        """
        alias_map = self.binding.get_aliases()

        ep_results = self.episodic.search(query, alias_map)
        sem_results = self.semantic.search(query, alias_map)

        # Track retrieval counts
        for r in ep_results[:3]:
            self.episodic.increment_retrieval(r["id"])

        # Bidirectional compensation logic
        ep_sufficient = len(ep_results) >= 2 and ep_results[0].get("_relevance", 0) > 0.3
        sem_sufficient = len(sem_results) >= 1 and sem_results[0].get("_relevance", 0) > 0.3

        if ep_sufficient and sem_sufficient:
            strategy = "both_available"
            explanation = "情節與語義記憶皆有相關資料，交叉參照"
        elif ep_sufficient and not sem_sufficient:
            strategy = "episodic_primary"
            explanation = "語義記憶不足，以情節記憶為主（具體經驗優先）"
        elif not ep_sufficient and sem_sufficient:
            strategy = "semantic_compensation"
            explanation = "情節記憶不足，語義記憶補償（通用知識補位）"
        else:
            strategy = "insufficient"
            explanation = "兩者皆不足，可能需要外部知識或 LLM 直接回應"

        return {
            "strategy": strategy,
            "explanation": explanation,
            "episodic_results": ep_results[:5],
            "semantic_results": sem_results[:3],
            "active_aliases": alias_map,
        }
