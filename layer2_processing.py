"""
Layer 2: Processing — Constraint-Driven Chunking
Attention Buffer with limited capacity forces abstraction.
"""

from datetime import datetime
from typing import Optional


class ConceptChunk:
    """A unit in the attention buffer — either raw or compressed."""

    def __init__(self, concept: str, content: str, source: str, 
                 is_compressed: bool = False, raw_concepts: list[str] = None):
        self.concept = concept
        self.content = content
        self.source = source  # "episodic", "semantic", "conversation", "compression"
        self.is_compressed = is_compressed
        self.raw_concepts = raw_concepts or []
        self.added_at = datetime.now()
        self.access_count = 0
        self.last_accessed = self.added_at

    def access(self):
        self.access_count += 1
        self.last_accessed = datetime.now()

    def to_dict(self) -> dict:
        return {
            "concept": self.concept,
            "content": self.content[:80] + ("..." if len(self.content) > 80 else ""),
            "source": self.source,
            "compressed": self.is_compressed,
            "contains": self.raw_concepts if self.is_compressed else [],
            "accesses": self.access_count,
        }


class AttentionBuffer:
    """
    Limited-capacity buffer that forces chunking/compression.
    
    When buffer is full and new concept arrives:
    1. Model selects which concepts to keep (selective attention)
    2. Evicted concepts are compressed into a summary chunk
    
    This simulates the functional constraint of human working memory.
    """

    def __init__(self, capacity: int = 5):
        self.capacity = capacity
        self.buffer: list[ConceptChunk] = []
        self.compression_log: list[dict] = []  # History of compressions

    def add(self, concept: str, content: str, source: str = "conversation") -> dict:
        """
        Add a concept to the buffer.
        If buffer is full, triggers compression.
        Returns status report.
        """
        # Check if concept already in buffer
        for chunk in self.buffer:
            if concept.lower() in chunk.concept.lower() or chunk.concept.lower() in concept.lower():
                chunk.access()
                return {
                    "action": "refreshed",
                    "concept": concept,
                    "buffer_size": len(self.buffer),
                    "capacity": self.capacity,
                    "message": f"「{concept}」已在緩衝區中，刷新存取時間",
                }

        new_chunk = ConceptChunk(concept, content, source)

        if len(self.buffer) < self.capacity:
            self.buffer.append(new_chunk)
            return {
                "action": "added",
                "concept": concept,
                "buffer_size": len(self.buffer),
                "capacity": self.capacity,
                "message": f"「{concept}」加入緩衝區 [{len(self.buffer)}/{self.capacity}]",
            }
        else:
            # Buffer full — must compress
            return self._compress_and_add(new_chunk)

    def _compress_and_add(self, new_chunk: ConceptChunk) -> dict:
        """
        A+C hybrid strategy:
        C: Select which concepts to keep (selective attention)
        A: Compress evicted concepts into summary chunk
        """
        # Score each chunk: lower score = more likely to be evicted
        scored = []
        for chunk in self.buffer:
            score = (
                chunk.access_count * 2.0          # Frequency
                + (0 if chunk.is_compressed else 1.0)  # Prefer evicting compressed
                + (1.0 if chunk.source == "conversation" else 0.5)  # Recent convo matters more
            )
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0])

        # Evict the 2 lowest-scored chunks
        evicted = [s[1] for s in scored[:2]]
        kept = [s[1] for s in scored[2:]]

        # Compress evicted into one summary chunk
        evicted_names = [c.concept for c in evicted]
        compressed_content = " | ".join(
            f"{c.concept}: {c.content[:50]}" for c in evicted
        )
        compressed_chunk = ConceptChunk(
            concept=f"[壓縮] {' + '.join(evicted_names)}",
            content=f"（組塊化摘要）{compressed_content}",
            source="compression",
            is_compressed=True,
            raw_concepts=evicted_names,
        )

        # New buffer: kept + compressed + new
        self.buffer = kept + [compressed_chunk, new_chunk]

        # Log the compression event
        event = {
            "timestamp": datetime.now().isoformat(),
            "evicted": evicted_names,
            "compressed_into": compressed_chunk.concept,
            "new_concept": new_chunk.concept,
            "buffer_after": [c.concept for c in self.buffer],
        }
        self.compression_log.append(event)

        return {
            "action": "compressed",
            "concept": new_chunk.concept,
            "evicted": evicted_names,
            "compressed_into": compressed_chunk.concept,
            "buffer_size": len(self.buffer),
            "capacity": self.capacity,
            "message": (
                f"⚠️ 緩衝區已滿！\n"
                f"  淘汰：{', '.join(evicted_names)}\n"
                f"  壓縮為：{compressed_chunk.concept}\n"
                f"  新增：「{new_chunk.concept}」\n"
                f"  緩衝區 [{len(self.buffer)}/{self.capacity}]"
            ),
        }

    def get_state(self) -> list[dict]:
        """Return current buffer state for display."""
        return [chunk.to_dict() for chunk in self.buffer]

    def get_active_context(self) -> str:
        """Get all active concepts as a context string for LLM."""
        parts = []
        for chunk in self.buffer:
            chunk.access()
            parts.append(f"[{chunk.concept}] {chunk.content}")
        return "\n".join(parts)

    def get_compression_history(self) -> list[dict]:
        return self.compression_log


class PhonologicalLoop:
    """
    Simulates the phonological loop: new/unfamiliar concepts get
    'cycled' multiple times to reinforce them before long-term storage.
    """

    def __init__(self, cycle_threshold: int = 3):
        self.cycle_threshold = cycle_threshold
        self.cycling: dict[str, int] = {}  # concept -> cycle count

    def encounter(self, concept: str) -> dict:
        """Register an encounter with a concept."""
        key = concept.lower()
        if key not in self.cycling:
            self.cycling[key] = 1
            return {
                "concept": concept,
                "status": "new",
                "cycles": 1,
                "message": f"🔄 新概念偵測：「{concept}」開始循環激活 [1/{self.cycle_threshold}]",
            }
        else:
            self.cycling[key] += 1
            cycles = self.cycling[key]
            if cycles >= self.cycle_threshold:
                del self.cycling[key]
                return {
                    "concept": concept,
                    "status": "consolidated",
                    "cycles": cycles,
                    "message": f"✅ 「{concept}」循環激活完成 [{cycles}/{self.cycle_threshold}]，可轉入長期記憶",
                }
            else:
                return {
                    "concept": concept,
                    "status": "cycling",
                    "cycles": cycles,
                    "message": f"🔄 「{concept}」循環激活中 [{cycles}/{self.cycle_threshold}]",
                }

    def get_cycling_concepts(self) -> dict:
        return dict(self.cycling)
