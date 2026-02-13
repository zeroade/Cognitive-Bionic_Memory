#!/usr/bin/env python3
"""
CBMA — Cognitive-Bionic Memory Architecture
Interactive CLI Demo

Commands:
  /help                  Show commands
  /alias <term> = <meaning>   Set temporary binding
  /aliases               Show active bindings
  /buffer                Show attention buffer state
  /buffer detail         Show buffer + compression history
  /search <query>        Search dual store (Layer 1)
  /kg <concept>          Query knowledge graph directly (Layer 0)
  /consolidate           Run consolidation cycle (Through-Axis)
  /scores                Show saliency scores for all episodes
  /episodes              List all episodic memories
  /semantics             List all semantic entries
  /status                Show full system status
  /quit                  Exit

Any other input is treated as a conversational query that
flows through all layers: L0 → L1 → L2 → L3.
"""

import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from layer0_representation import KnowledgeGraph, MockLLM, ArbitrationLayer
from layer1_storage import EpisodicStore, SemanticStore, TemporaryBinding, DualStore
from layer2_processing import AttentionBuffer, PhonologicalLoop
from layer3_output import CognitiveLoadMonitor, OutputRegulator
from consolidation_engine import SaliencyScorer, ConsolidationEngine

# ─── ANSI colors ───
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"


def colored(text, color):
    return f"{color}{text}{C.RESET}"


def header(text):
    width = 60
    print(colored(f"\n{'─' * width}", C.DIM))
    print(colored(f"  {text}", C.BOLD + C.CYAN))
    print(colored(f"{'─' * width}", C.DIM))


def subheader(text):
    print(colored(f"\n  ◆ {text}", C.BOLD + C.YELLOW))


def info(text):
    print(colored(f"  {text}", C.WHITE))


def dim(text):
    print(colored(f"  {text}", C.DIM))


def success(text):
    print(colored(f"  ✓ {text}", C.GREEN))


def warn(text):
    print(colored(f"  ⚠ {text}", C.YELLOW))


def error(text):
    print(colored(f"  ✗ {text}", C.RED))


class CBMA:
    """Main system that orchestrates all layers."""

    def __init__(self, data_dir: str):
        # Layer 0: Representation
        self.kg = KnowledgeGraph(os.path.join(data_dir, "knowledge_graph.json"))
        self.llm = MockLLM()
        self.arbitration = ArbitrationLayer(self.kg, self.llm)

        # Layer 1: Storage
        self.episodic = EpisodicStore(os.path.join(data_dir, "episodic_store.json"))
        self.semantic = SemanticStore(os.path.join(data_dir, "semantic_store.json"))
        self.binding = TemporaryBinding()
        self.dual_store = DualStore(self.episodic, self.semantic, self.binding)

        # Layer 2: Processing
        self.buffer = AttentionBuffer(capacity=5)
        self.phono_loop = PhonologicalLoop(cycle_threshold=3)

        # Layer 3: Output
        self.load_monitor = CognitiveLoadMonitor()
        self.regulator = OutputRegulator(self.load_monitor)

        # Through-Axis
        self.scorer = SaliencyScorer()
        self.consolidation = ConsolidationEngine(self.scorer)

        # Conversation state
        self.turn_count = 0

    def process_query(self, query: str):
        """Full pipeline: query flows through all layers."""
        self.turn_count += 1
        header(f"Query #{self.turn_count}: {query[:50]}{'...' if len(query) > 50 else ''}")

        # ── Layer 0: Arbitration ──
        subheader("Layer 0 — 表徵層：Confidence-Gated 仲裁")
        arb_result = self.arbitration.arbitrate(query)
        info(f"決策：{arb_result['decision']}")
        info(f"說明：{arb_result['explanation']}")
        if arb_result['kg_hits'] > 0:
            dim(f"KG 命中 {arb_result['kg_hits']} 條，最高信心 {arb_result['kg_max_confidence']:.2f}")
            for t in arb_result['trace']['kg_results'][:3]:
                dim(f"  {t['subject']} —[{t['relation']}]→ {t['object']} ({t['confidence']:.2f})")

        # ── Layer 1: Dual Store Search ──
        subheader("Layer 1 — 存儲層：雙存儲庫檢索")
        store_result = self.dual_store.search(query)
        info(f"策略：{store_result['strategy']}")
        info(f"說明：{store_result['explanation']}")
        if store_result['active_aliases']:
            dim(f"活躍別名：{store_result['active_aliases']}")

        if store_result['episodic_results']:
            dim(f"情節記憶命中 {len(store_result['episodic_results'])} 條：")
            for ep in store_result['episodic_results'][:2]:
                dim(f"  [{ep['id']}] {ep['source'][:40]} (相關度: {ep['_relevance']:.2f})")
        if store_result['semantic_results']:
            dim(f"語義記憶命中 {len(store_result['semantic_results'])} 條：")
            for sem in store_result['semantic_results'][:2]:
                dim(f"  [{sem['id']}] {sem['concept']} (相關度: {sem['_relevance']:.2f})")

        # ── Layer 2: Attention Buffer ──
        subheader("Layer 2 — 處理層：注意力緩衝區")
        # Extract key concepts: prefer KG-matched concepts, fall back to short terms
        concepts = arb_result.get("concepts_searched", [])
        # Filter out overly long concepts (likely full phrases, not concepts)
        concepts = [c for c in concepts if len(c) <= 20]
        if not concepts:
            # Fallback: extract short meaningful terms
            import re
            tokens = re.split(r'[\s，。？！、/]+', query)
            concepts = [t for t in tokens if 2 <= len(t) <= 15][:3]
        for concept in concepts[:3]:
            buf_result = self.buffer.add(concept, query, "conversation")
            info(buf_result["message"])

            # Phonological loop for new concepts
            loop_result = self.phono_loop.encounter(concept)
            if loop_result["status"] in ("new", "cycling"):
                dim(loop_result["message"])
            elif loop_result["status"] == "consolidated":
                success(loop_result["message"])

        # ── Layer 3: Output Regulation ──
        subheader("Layer 3 — 輸出層：認知負荷評估")
        # Build a mock response combining all results
        response_parts = []
        if arb_result['response']:
            response_parts.append(arb_result['response'])
        for ep in store_result['episodic_results'][:2]:
            response_parts.append(ep['content'][:100])
        for sem in store_result['semantic_results'][:1]:
            response_parts.append(sem['content'][:100])
        mock_response = "\n".join(response_parts) if response_parts else "（無相關資訊）"

        known = [c.concept for c in self.buffer.buffer]
        regulation = self.regulator.regulate(mock_response, known)
        info(regulation["assessment"]["message"])
        if regulation["was_regulated"]:
            warn("回應已進行認知負荷調節")

        # ── Final Output ──
        subheader("綜合回應")
        print()
        for line in regulation["regulated_response"].split("\n"):
            if line.strip():
                info(line)
        print()

    def cmd_alias(self, args: str):
        """Handle /alias command."""
        if "=" not in args:
            error("用法：/alias <term> = <meaning>")
            error("例如：/alias 瓶頸 = 工作記憶限制帶來的正面約束")
            return
        parts = args.split("=", 1)
        term = parts[0].strip()
        meaning = parts[1].strip()
        result = self.binding.add_alias(term, meaning)
        success(result)

    def cmd_aliases(self):
        """Show active aliases."""
        aliases = self.binding.get_aliases()
        if not aliases:
            info("目前沒有活躍的臨時綁定")
        else:
            header("活躍的臨時綁定")
            for term, meaning in aliases.items():
                info(f"「{term}」→「{meaning}」")

    def cmd_buffer(self, detail: bool = False):
        """Show buffer state."""
        header("注意力緩衝區狀態")
        state = self.buffer.get_state()
        if not state:
            info("緩衝區為空")
            return
        for i, chunk in enumerate(state):
            marker = "📦" if chunk["compressed"] else "💡"
            info(f"{marker} [{i+1}] {chunk['concept']}")
            dim(f"     {chunk['content']}")
            if chunk["compressed"] and chunk["contains"]:
                dim(f"     包含：{', '.join(chunk['contains'])}")
            dim(f"     來源：{chunk['source']} | 存取次數：{chunk['accesses']}")
        info(f"\n  容量：{len(state)}/{self.buffer.capacity}")

        cycling = self.phono_loop.get_cycling_concepts()
        if cycling:
            subheader("語音環路 — 循環激活中")
            for concept, count in cycling.items():
                dim(f"  🔄 {concept} [{count}/{self.phono_loop.cycle_threshold}]")

        if detail:
            history = self.buffer.get_compression_history()
            if history:
                subheader("壓縮歷史")
                for event in history:
                    dim(f"  {event['timestamp'][:19]}")
                    dim(f"    淘汰：{event['evicted']}")
                    dim(f"    壓縮為：{event['compressed_into']}")
                    dim(f"    新增：{event['new_concept']}")

    def cmd_kg(self, concept: str):
        """Query KG directly."""
        header(f"知識圖譜查詢：{concept}")
        results = self.kg.query(concept)
        if not results:
            info("無匹配記錄")
            return
        for r in results:
            conf_color = C.GREEN if r['confidence'] >= 0.85 else (C.YELLOW if r['confidence'] >= 0.5 else C.RED)
            conf_val = r['confidence']
            print(f"  {r['subject']} —[{r['relation']}]→ {r['object']}  {colored(f'{conf_val:.2f}', conf_color)}")

    def cmd_search(self, query: str):
        """Direct dual-store search."""
        header(f"雙存儲庫搜尋：{query}")
        result = self.dual_store.search(query)
        info(f"策略：{result['strategy']} — {result['explanation']}")
        if result['episodic_results']:
            subheader("情節記憶")
            for ep in result['episodic_results'][:5]:
                info(f"[{ep['id']}] {ep['source'][:50]}")
                dim(f"  {ep['content'][:80]}...")
        if result['semantic_results']:
            subheader("語義記憶")
            for sem in result['semantic_results'][:3]:
                info(f"[{sem['id']}] {sem['concept']}")
                dim(f"  {sem['content'][:80]}...")

    def cmd_consolidate(self):
        """Run consolidation cycle."""
        header("鞏固-遺忘-重組引擎 啟動")

        # First show scores
        scores = self.consolidation.get_score_report(self.episodic, self.semantic)
        subheader("顯著性評分")
        for s in scores:
            action_color = C.GREEN if s['action'] == 'consolidate' else (C.RED if s['action'] == 'prune' else C.YELLOW)
            action_marker = {"consolidate": "⬆ 鞏固", "prune": "⬇ 遺忘", "retain": "● 保留"}[s['action']]
            print(f"  {colored(action_marker, action_color)}  {s['episode_id']}  "
                  f"score={s['total_score']:.3f}  {s['source']}")
            dims = s['dimensions']
            dim(f"    freq={dims['frequency']:.2f} recency={dims['recency']:.2f} "
                f"user={dims['user_signal']:.2f} novelty={dims['novelty']:.2f} "
                f"connect={dims['connection_density']:.2f}")

        # Execute
        subheader("執行鞏固")
        result = self.consolidation.run(self.episodic, self.semantic)
        success(f"已評估 {result['total_scored']} 條情節記憶")
        if result['consolidated'] > 0:
            success(f"鞏固 {result['consolidated']} 條至語義記憶：")
            for c in result['details']['consolidated']:
                dim(f"  {c['source_episode']} → {c['new_semantic_entry']}: {c['concept']}")
        if result['pruned'] > 0:
            warn(f"遺忘 {result['pruned']} 條：{result['details']['pruned']}")
        if result['retained'] > 0:
            info(f"保留 {result['retained']} 條在情節存儲中")

    def cmd_scores(self):
        """Show saliency scores without executing."""
        header("顯著性評分（預覽，不執行）")
        scores = self.consolidation.get_score_report(self.episodic, self.semantic)
        for s in scores:
            action_color = C.GREEN if s['action'] == 'consolidate' else (C.RED if s['action'] == 'prune' else C.YELLOW)
            action_marker = {"consolidate": "⬆", "prune": "⬇", "retain": "●"}[s['action']]
            print(f"  {colored(action_marker, action_color)} {s['total_score']:.3f}  "
                  f"{s['episode_id']}  {s['source']}")

    def cmd_episodes(self):
        """List episodic store."""
        header(f"情節存儲庫（{len(self.episodic.episodes)} 條）")
        for ep in self.episodic.episodes:
            info(f"[{ep['id']}] {ep['timestamp'][:10]}  {ep['source'][:50]}")
            dim(f"  重要性: {ep.get('user_importance', '?')}/5  "
                f"檢索次數: {ep.get('retrieval_count', 0)}  "
                f"標籤: {', '.join(ep.get('tags', []))}")

    def cmd_semantics(self):
        """List semantic store."""
        header(f"語義存儲庫（{len(self.semantic.entries)} 條）")
        for entry in self.semantic.entries:
            info(f"[{entry['id']}] {entry['concept']}")
            dim(f"  {entry['content'][:80]}...")
            dim(f"  信心度: {entry.get('confidence', '?')}  來源: {entry.get('source_episodes', [])}")

    def cmd_status(self):
        """Full system status."""
        header("CBMA 系統狀態")
        subheader("Layer 0 — 知識圖譜")
        info(f"三元組數量：{len(self.kg.triples)}")

        subheader("Layer 1 — 雙存儲庫")
        info(f"情節記憶：{len(self.episodic.episodes)} 條")
        info(f"語義記憶：{len(self.semantic.entries)} 條")
        aliases = self.binding.get_aliases()
        info(f"臨時綁定：{len(aliases)} 條")
        if aliases:
            for t, m in aliases.items():
                dim(f"  「{t}」→「{m}」")

        subheader("Layer 2 — 注意力緩衝區")
        state = self.buffer.get_state()
        info(f"使用量：{len(state)}/{self.buffer.capacity}")
        for chunk in state:
            marker = "📦" if chunk["compressed"] else "💡"
            dim(f"  {marker} {chunk['concept']}")
        cycling = self.phono_loop.get_cycling_concepts()
        if cycling:
            info(f"循環激活中：{list(cycling.keys())}")

        subheader("Layer 3 — 輸出調節")
        info(f"密度閾值：{self.load_monitor.density_threshold}")
        info(f"新概念上限：{self.load_monitor.max_new_concepts}")

        subheader("貫穿軸 — 鞏固引擎")
        info(f"歷史鞏固次數：{len(self.consolidation.consolidation_history)}")
        info(f"對話輪次：{self.turn_count}")

    def cmd_help(self):
        header("CBMA 指令列表")
        commands = [
            ("/help", "顯示此說明"),
            ("/alias <term> = <meaning>", "設定臨時綁定（語義漂移追蹤）"),
            ("/aliases", "顯示所有活躍綁定"),
            ("/buffer", "顯示注意力緩衝區狀態"),
            ("/buffer detail", "顯示緩衝區 + 壓縮歷史"),
            ("/search <query>", "直接搜尋雙存儲庫"),
            ("/kg <concept>", "直接查詢知識圖譜"),
            ("/consolidate", "執行鞏固-遺忘-重組循環"),
            ("/scores", "預覽顯著性評分（不執行）"),
            ("/episodes", "列出所有情節記憶"),
            ("/semantics", "列出所有語義記憶"),
            ("/status", "顯示完整系統狀態"),
            ("/quit", "結束"),
            ("（其他任何輸入）", "作為查詢，流經全部四層處理"),
        ]
        for cmd, desc in commands:
            print(f"  {colored(cmd, C.CYAN):40s} {desc}")


def main():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    system = CBMA(data_dir)

    print(colored("""
╔══════════════════════════════════════════════════════════╗
║   CBMA — Cognitive-Bionic Memory Architecture           ║
║   認知仿生記憶架構 互動演示                                ║
╠══════════════════════════════════════════════════════════╣
║  四層架構 + 一軸                                         ║
║  L0 表徵 → L1 存儲 → L2 處理 → L3 輸出                  ║
║  貫穿軸：鞏固-遺忘-重組                                   ║
╠══════════════════════════════════════════════════════════╣
║  輸入 /help 查看指令   輸入任何問題開始互動                  ║
╚══════════════════════════════════════════════════════════╝
    """, C.CYAN))

    info(f"已載入 {len(system.kg.triples)} 條知識圖譜三元組")
    info(f"已載入 {len(system.episodic.episodes)} 條情節記憶")
    info(f"已載入 {len(system.semantic.entries)} 條語義記憶")
    print()

    while True:
        try:
            user_input = input(colored("CBMA > ", C.BOLD + C.GREEN)).strip()
        except (EOFError, KeyboardInterrupt):
            print(colored("\n\n  再見！", C.CYAN))
            break

        if not user_input:
            continue

        # Command routing
        lower = user_input.lower()

        if lower == "/quit" or lower == "/exit":
            print(colored("\n  再見！", C.CYAN))
            break
        elif lower == "/help":
            system.cmd_help()
        elif lower.startswith("/alias "):
            system.cmd_alias(user_input[7:])
        elif lower == "/aliases":
            system.cmd_aliases()
        elif lower == "/buffer detail":
            system.cmd_buffer(detail=True)
        elif lower == "/buffer":
            system.cmd_buffer()
        elif lower.startswith("/search "):
            system.cmd_search(user_input[8:])
        elif lower.startswith("/kg "):
            system.cmd_kg(user_input[4:])
        elif lower == "/consolidate":
            system.cmd_consolidate()
        elif lower == "/scores":
            system.cmd_scores()
        elif lower == "/episodes":
            system.cmd_episodes()
        elif lower == "/semantics":
            system.cmd_semantics()
        elif lower == "/status":
            system.cmd_status()
        else:
            # Treat as conversational query — full pipeline
            system.process_query(user_input)


if __name__ == "__main__":
    main()
