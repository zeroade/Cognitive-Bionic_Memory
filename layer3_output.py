"""
Layer 3: Output Regulation — Cognitive Load-Aware Generation
"""


class CognitiveLoadMonitor:
    """
    Estimates cognitive load of a response and suggests restructuring
    if information density is too high.
    
    Metrics:
    - new_concept_count: concepts not in current buffer
    - sentence_count: total sentences
    - density: new concepts per sentence
    """

    def __init__(self, density_threshold: float = 0.5, max_new_concepts: int = 4):
        self.density_threshold = density_threshold
        self.max_new_concepts = max_new_concepts

    def assess(self, response_text: str, known_concepts: list[str]) -> dict:
        """
        Assess cognitive load of a response.
        Returns load assessment and scaffolding suggestions.
        """
        sentences = self._split_sentences(response_text)
        sentence_count = len(sentences)

        # Count concepts that are new (not in known_concepts)
        words = set(response_text.lower().replace("，", " ").replace("。", " ").split())
        known_lower = {c.lower() for c in known_concepts}
        # Simple heuristic: words longer than 3 chars that aren't known
        potential_new = [w for w in words if len(w) > 3 and w not in known_lower]
        new_concept_count = len(potential_new)

        density = new_concept_count / max(sentence_count, 1)

        overloaded = density > self.density_threshold or new_concept_count > self.max_new_concepts

        result = {
            "sentence_count": sentence_count,
            "new_concept_count": new_concept_count,
            "density": round(density, 2),
            "overloaded": overloaded,
            "threshold": self.density_threshold,
        }

        if overloaded:
            result["suggestion"] = self._suggest_scaffolding(response_text, new_concept_count, sentence_count)
            result["message"] = (
                f"⚠️ 認知負荷警告：資訊密度 {density:.2f} 超過閾值 {self.density_threshold}\n"
                f"  新概念數：{new_concept_count}（上限 {self.max_new_concepts}）\n"
                f"  建議：{result['suggestion']['strategy']}"
            )
        else:
            result["message"] = f"✓ 認知負荷正常：密度 {density:.2f}，新概念 {new_concept_count}"

        return result

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences (supports Chinese and English)."""
        import re
        sentences = re.split(r'[。！？.!?\n]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _suggest_scaffolding(self, text: str, new_concepts: int, sentences: int) -> dict:
        """Suggest how to restructure the response."""
        if new_concepts > 6:
            return {
                "strategy": "分段呈現",
                "detail": "新概念過多，建議拆分為 2-3 個段落，每段引入 2-3 個新概念",
                "recommended_segments": (new_concepts + 2) // 3,
            }
        elif new_concepts > 4:
            return {
                "strategy": "插入類比",
                "detail": "建議為核心新概念提供類比或例子，降低理解門檻",
                "recommended_analogies": new_concepts - 3,
            }
        else:
            return {
                "strategy": "添加摘要節點",
                "detail": "在回應結尾添加一句話摘要，幫助鞏固理解",
                "recommended_summary_length": "1-2 sentences",
            }


class OutputRegulator:
    """
    Wraps the cognitive load monitor and applies scaffolding to outputs.
    """

    def __init__(self, monitor: CognitiveLoadMonitor):
        self.monitor = monitor

    def regulate(self, response_text: str, known_concepts: list[str]) -> dict:
        """
        Assess and potentially restructure a response.
        Returns the (possibly modified) response and assessment.
        """
        assessment = self.monitor.assess(response_text, known_concepts)

        if assessment["overloaded"]:
            # In production, we'd actually restructure the text via LLM
            # For the prototype, we annotate the response with scaffolding markers
            regulated_response = self._apply_scaffolding(response_text, assessment)
        else:
            regulated_response = response_text

        return {
            "original_response": response_text,
            "regulated_response": regulated_response,
            "assessment": assessment,
            "was_regulated": assessment["overloaded"],
        }

    def _apply_scaffolding(self, text: str, assessment: dict) -> str:
        """Apply scaffolding markers to the text."""
        suggestion = assessment.get("suggestion", {})
        strategy = suggestion.get("strategy", "")

        if strategy == "分段呈現":
            segments = suggestion.get("recommended_segments", 2)
            sentences = self.monitor._split_sentences(text)
            chunk_size = max(len(sentences) // segments, 1)
            parts = []
            for i in range(0, len(sentences), chunk_size):
                chunk = "。".join(sentences[i:i+chunk_size]) + "。"
                parts.append(chunk)
            return "\n\n---\n\n".join(parts)

        elif strategy == "插入類比":
            return text + "\n\n💡 [建議此處插入類比以降低認知負荷]"

        elif strategy == "添加摘要節點":
            return text + "\n\n📌 [建議在此添加一句話摘要]"

        return text
