"""
Layer 0: Representation — Neural-Symbolic Dual Representation
Confidence-Gated Arbitration between KG (symbolic) and LLM (neural)
"""

import json
from pathlib import Path
from typing import Optional

# Thresholds for arbitration
HIGH_CONFIDENCE = 0.85
LOW_CONFIDENCE = 0.50


class KnowledgeGraph:
    def __init__(self, kg_path: str):
        with open(kg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.triples = data["triples"]
        # Build index: subject -> list of triples
        self.index = {}
        for t in self.triples:
            key = t["subject"].lower()
            if key not in self.index:
                self.index[key] = []
            self.index[key].append(t)

    def query(self, concept: str, relation: str = None) -> list[dict]:
        """Query KG for triples matching concept (and optionally relation)."""
        concept_lower = concept.lower()
        results = []
        for key, triples in self.index.items():
            if concept_lower in key or key in concept_lower:
                for t in triples:
                    if relation is None or relation.lower() in t["relation"].lower():
                        results.append(t)
        # Also search in objects
        for t in self.triples:
            if concept_lower in t["object"].lower():
                if relation is None or relation.lower() in t["relation"].lower():
                    if t not in results:
                        results.append(t)
        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    def get_max_confidence(self, results: list[dict]) -> float:
        if not results:
            return 0.0
        return max(r["confidence"] for r in results)


class MockLLM:
    """Mock LLM that returns plausible but sometimes imprecise answers."""

    def generate(self, query: str) -> dict:
        """Returns a mock LLM response with content and a fake confidence."""
        # In real implementation, this calls an actual LLM API
        return {
            "content": f"[LLM 神經軌回應] 根據我的理解，關於「{query}」的資訊如下：這是一個需要綜合多方面知識來回答的問題。（此為 mock 回應，實際部署時接入真實 LLM）",
            "source": "neural_track",
            "confidence": 0.65,  # LLM self-reported confidence (notoriously uncalibrated)
        }


class ArbitrationLayer:
    """
    Confidence-Gated Arbitration between KG and LLM.
    
    Logic:
    - KG high confidence → use KG, suppress neural track
    - KG no record or low confidence → fall back to LLM, flag uncertainty
    - Conflict → report ambiguity upward
    """

    def __init__(self, kg: KnowledgeGraph, llm: MockLLM):
        self.kg = kg
        self.llm = llm

    def arbitrate(self, query: str, concepts: list[str] = None) -> dict:
        """
        Given a query, decide whether to use KG or LLM.
        Returns arbitration result with decision trace.
        """
        if concepts is None:
            # Simple extraction: split query into potential concept keywords
            concepts = self._extract_concepts(query)

        # Step 1: Query KG for all extracted concepts
        kg_results = []
        for concept in concepts:
            hits = self.kg.query(concept)
            kg_results.extend(hits)

        # Deduplicate
        seen = set()
        unique_results = []
        for r in kg_results:
            key = (r["subject"], r["relation"], r["object"])
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        kg_results = unique_results

        max_conf = self.kg.get_max_confidence(kg_results)

        # Step 2: Arbitration decision
        if max_conf >= HIGH_CONFIDENCE:
            decision = "kg_primary"
            explanation = f"KG 有高信心記錄 (max={max_conf:.2f})，採用符號軌"
            response = self._format_kg_response(kg_results, query)
        elif max_conf >= LOW_CONFIDENCE:
            # Partial coverage — use both
            llm_response = self.llm.generate(query)
            decision = "hybrid"
            explanation = f"KG 有部分記錄 (max={max_conf:.2f})，混合使用兩軌"
            response = self._format_hybrid_response(kg_results, llm_response, query)
        elif max_conf > 0:
            # Low confidence KG results exist
            llm_response = self.llm.generate(query)
            decision = "llm_primary_kg_ref"
            explanation = f"KG 信心不足 (max={max_conf:.2f})，以神經軌為主，KG 僅供參考"
            response = self._format_llm_with_ref(kg_results, llm_response, query)
        else:
            # No KG coverage at all
            llm_response = self.llm.generate(query)
            decision = "llm_fallback"
            explanation = "KG 無相關記錄，完全退回神經軌 ⚠️ 輸出不確定度較高"
            response = llm_response["content"]

        return {
            "decision": decision,
            "explanation": explanation,
            "response": response,
            "kg_hits": len(kg_results),
            "kg_max_confidence": max_conf,
            "concepts_searched": concepts,
            "trace": {
                "kg_results": kg_results[:5],  # Top 5 for display
            }
        }

    def _extract_concepts(self, query: str) -> list[str]:
        """Simple concept extraction from query. In production, use NER or LLM."""
        # Known concept keywords
        known = [t["subject"].lower() for t in self.kg.triples]
        known += [t["object"].lower() for t in self.kg.triples]
        known = list(set(known))

        query_lower = query.lower()
        found = []
        for concept in known:
            if concept in query_lower and len(concept) > 2:
                found.append(concept)

        if not found:
            # Fallback: use words longer than 3 chars
            words = query.replace("？", "").replace("?", "").replace("，", " ").replace("、", " ").split()
            found = [w for w in words if len(w) > 2][:5]

        return found

    def _format_kg_response(self, results: list[dict], query: str) -> str:
        lines = [f"[符號軌] 知識圖譜查詢結果："]
        for r in results[:5]:
            lines.append(f"  • {r['subject']} —[{r['relation']}]→ {r['object']} (信心度: {r['confidence']:.2f})")
        return "\n".join(lines)

    def _format_hybrid_response(self, kg_results: list[dict], llm_resp: dict, query: str) -> str:
        lines = [f"[混合模式] KG 提供部分事實，LLM 補充推論："]
        lines.append("  KG 事實：")
        for r in kg_results[:3]:
            lines.append(f"    • {r['subject']} —[{r['relation']}]→ {r['object']} (信心度: {r['confidence']:.2f})")
        lines.append(f"  LLM 補充：{llm_resp['content']}")
        return "\n".join(lines)

    def _format_llm_with_ref(self, kg_results: list[dict], llm_resp: dict, query: str) -> str:
        lines = [f"[神經軌為主] LLM 回應，KG 參考資料附後："]
        lines.append(f"  {llm_resp['content']}")
        lines.append("  KG 低信心參考：")
        for r in kg_results[:3]:
            lines.append(f"    • {r['subject']} —[{r['relation']}]→ {r['object']} (信心度: {r['confidence']:.2f})")
        return "\n".join(lines)
