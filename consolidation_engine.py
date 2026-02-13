"""
Through-Axis: Consolidation-Pruning-Restructuring Engine
Drives system evolution across all layers.
"""

import math
from datetime import datetime, timedelta
from typing import Optional


class SaliencyScorer:
    """
    Multi-dimensional saliency scoring for episodic memories.
    
    saliency = w1*frequency + w2*recency + w3*user_signal + w4*novelty + w5*connection_density
    
    High score → consolidate to semantic store
    Low score → mark for pruning
    Middle → keep in episodic, await more signals
    """

    def __init__(self, weights: dict = None):
        self.weights = weights or {
            "frequency": 0.25,
            "recency": 0.20,
            "user_signal": 0.25,
            "novelty": 0.15,
            "connection_density": 0.15,
        }
        # Thresholds
        self.consolidation_threshold = 0.65
        self.pruning_threshold = 0.25

    def score(self, episode: dict, semantic_entries: list[dict], all_episodes: list[dict]) -> dict:
        """Score an episodic memory on all dimensions."""
        freq = self._frequency_score(episode)
        recency = self._recency_score(episode)
        user_sig = self._user_signal_score(episode)
        novelty = self._novelty_score(episode, semantic_entries)
        connections = self._connection_density_score(episode, all_episodes)

        total = (
            self.weights["frequency"] * freq
            + self.weights["recency"] * recency
            + self.weights["user_signal"] * user_sig
            + self.weights["novelty"] * novelty
            + self.weights["connection_density"] * connections
        )

        if total >= self.consolidation_threshold:
            action = "consolidate"
        elif total <= self.pruning_threshold:
            action = "prune"
        else:
            action = "retain"

        return {
            "episode_id": episode["id"],
            "total_score": round(total, 3),
            "dimensions": {
                "frequency": round(freq, 3),
                "recency": round(recency, 3),
                "user_signal": round(user_sig, 3),
                "novelty": round(novelty, 3),
                "connection_density": round(connections, 3),
            },
            "action": action,
            "thresholds": {
                "consolidation": self.consolidation_threshold,
                "pruning": self.pruning_threshold,
            }
        }

    def _frequency_score(self, episode: dict) -> float:
        """How often this memory has been retrieved. Normalized with log."""
        count = episode.get("retrieval_count", 0)
        return min(math.log1p(count) / math.log1p(15), 1.0)  # Saturates around 15

    def _recency_score(self, episode: dict) -> float:
        """Ebbinghaus-inspired decay: fast at first, then slow."""
        try:
            ts = datetime.fromisoformat(episode["timestamp"])
        except (ValueError, KeyError):
            return 0.5
        days_ago = (datetime.now() - ts).total_seconds() / 86400
        # Exponential decay with half-life of 30 days
        return math.exp(-0.693 * days_ago / 30)

    def _user_signal_score(self, episode: dict) -> float:
        """User-assigned importance + emotional valence."""
        importance = episode.get("user_importance", 3) / 5.0
        valence = abs(episode.get("emotional_valence", 0))  # Absolute value — strong emotion either way
        return 0.6 * importance + 0.4 * valence

    def _novelty_score(self, episode: dict, semantic_entries: list[dict]) -> float:
        """Is this information already covered in semantic store?"""
        ep_tags = set(t.lower() for t in episode.get("tags", []))
        if not ep_tags:
            return 0.5  # Unknown novelty

        # Check coverage in semantic store
        covered_tags = set()
        for entry in semantic_entries:
            entry_text = (entry.get("concept", "") + " " + entry.get("content", "")).lower()
            for tag in ep_tags:
                if tag in entry_text:
                    covered_tags.add(tag)

        coverage = len(covered_tags) / len(ep_tags) if ep_tags else 0
        return 1.0 - coverage  # Higher novelty = less coverage

    def _connection_density_score(self, episode: dict, all_episodes: list[dict]) -> float:
        """How connected is this episode to other episodes?"""
        ep_tags = set(t.lower() for t in episode.get("tags", []))
        if not ep_tags:
            return 0.0

        connections = 0
        for other in all_episodes:
            if other["id"] == episode["id"]:
                continue
            other_tags = set(t.lower() for t in other.get("tags", []))
            if ep_tags & other_tags:  # Any overlap
                connections += 1

        # Normalize: more than 4 connections is max
        return min(connections / 4.0, 1.0)


class ConsolidationEngine:
    """
    Orchestrates the consolidation-pruning-restructuring cycle.
    """

    def __init__(self, scorer: SaliencyScorer):
        self.scorer = scorer
        self.consolidation_history: list[dict] = []

    def run(self, episodic_store, semantic_store) -> dict:
        """
        Run one consolidation cycle:
        1. Score all episodic memories
        2. Consolidate high-scorers into semantic store
        3. Prune low-scorers
        4. Report what changed
        """
        scores = []
        for ep in episodic_store.episodes:
            score = self.scorer.score(ep, semantic_store.entries, episodic_store.episodes)
            scores.append(score)

        to_consolidate = [s for s in scores if s["action"] == "consolidate"]
        to_prune = [s for s in scores if s["action"] == "prune"]
        to_retain = [s for s in scores if s["action"] == "retain"]

        # Execute consolidation
        consolidated = []
        for item in to_consolidate:
            ep = next(e for e in episodic_store.episodes if e["id"] == item["episode_id"])
            # Check if already consolidated (check if this episode's content is already in semantic store)
            already = False
            for entry in semantic_store.entries:
                if ep["id"] in entry.get("source_episodes", []):
                    already = True
                    break
                # Also check content similarity (simple keyword overlap)
                ep_tags = set(t.lower() for t in ep.get("tags", []))
                entry_text = entry.get("content", "").lower()
                overlap = sum(1 for tag in ep_tags if tag in entry_text)
                if overlap >= 2:
                    already = True
                    break
            if not already:
                new_entry = semantic_store.add_entry(
                    concept=f"從「{ep['source'][:30]}」提煉的洞見",
                    content=self._extract_pattern(ep),
                    source_episodes=[ep["id"]],
                    confidence=item["total_score"],
                )
                consolidated.append({
                    "source_episode": ep["id"],
                    "new_semantic_entry": new_entry["id"],
                    "concept": new_entry["concept"],
                })

        # Execute pruning
        pruned_ids = [s["episode_id"] for s in to_prune]
        pruned_episodes = []
        remaining_episodes = []
        for ep in episodic_store.episodes:
            if ep["id"] in pruned_ids:
                pruned_episodes.append(ep["id"])
            else:
                remaining_episodes.append(ep)
        episodic_store.episodes = remaining_episodes

        # Log
        event = {
            "timestamp": datetime.now().isoformat(),
            "total_scored": len(scores),
            "consolidated": len(consolidated),
            "pruned": len(pruned_episodes),
            "retained": len(to_retain),
            "details": {
                "consolidated": consolidated,
                "pruned": pruned_episodes,
            }
        }
        self.consolidation_history.append(event)

        return event

    def _extract_pattern(self, episode: dict) -> str:
        """
        Extract a general pattern from an episode.
        In production, this would use an LLM to generalize.
        For now, we take the core content and frame it as a general insight.
        """
        content = episode.get("content", "")
        # Simple heuristic: take first 100 chars as the core insight
        if len(content) > 100:
            return f"（自動提煉）{content[:100]}..."
        return f"（自動提煉）{content}"

    def get_score_report(self, episodic_store, semantic_store) -> list[dict]:
        """Score all episodes without executing. For inspection."""
        scores = []
        for ep in episodic_store.episodes:
            score = self.scorer.score(ep, semantic_store.entries, episodic_store.episodes)
            score["source"] = ep.get("source", "unknown")[:40]
            scores.append(score)
        return sorted(scores, key=lambda x: x["total_score"], reverse=True)
