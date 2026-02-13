# CBMA — Cognitive-Bionic Memory Architecture
# 認知仿生記憶架構 互動原型

## 快速開始

```bash
cd cbma
python3 main.py
```

無外部依賴，純 Python 3.10+。

## 架構

```
cbma/
├── main.py                  # CLI 入口，整合所有層
├── layer0_representation.py # Layer 0: KG + Confidence-Gated 仲裁
├── layer1_storage.py        # Layer 1: 情節-語義雙存儲 + 臨時綁定
├── layer2_processing.py     # Layer 2: 注意力緩衝區 + 語音環路
├── layer3_output.py         # Layer 3: 認知負荷監測 + 輸出調節
├── consolidation_engine.py  # 貫穿軸: 鞏固-遺忘-重組引擎
└── data/
    ├── knowledge_graph.json # 40 條 AI 領域三元組（帶信心分數）
    ├── episodic_store.json  # 7 條虛構閱讀筆記
    └── semantic_store.json  # 4 條已鞏固的語義條目
```

## 指令

| 指令 | 說明 |
|------|------|
| `/help` | 顯示指令列表 |
| `/alias <term> = <meaning>` | 設定臨時綁定（語義漂移追蹤） |
| `/aliases` | 顯示所有活躍綁定 |
| `/buffer` | 顯示注意力緩衝區狀態 |
| `/buffer detail` | 緩衝區 + 壓縮歷史 |
| `/search <query>` | 直接搜尋雙存儲庫 |
| `/kg <concept>` | 直接查詢知識圖譜 |
| `/consolidate` | 執行鞏固-遺忘-重組循環 |
| `/scores` | 預覽顯著性評分 |
| `/episodes` | 列出情節記憶 |
| `/semantics` | 列出語義記憶 |
| `/status` | 完整系統狀態 |
| （任何其他輸入） | 作為查詢流經四層處理 |

## 演示流程建議

1. `/status` — 看系統初始狀態
2. 問一個 KG 能回答的問題：`RAG 是什麼？` → 觀察 Layer 0 走符號軌
3. 問一個 KG 不能回答的問題：`AI 會做夢嗎？` → 觀察退回神經軌
4. `/alias 瓶頸 = 工作記憶限制帶來的正面約束` → 建立臨時綁定
5. `瓶頸在 AI 設計中有什麼啟發？` → 觀察 Layer 1 如何用別名擴展檢索
6. 連續問 6+ 個不同主題 → 觀察 Layer 2 緩衝區壓縮行為
7. `/consolidate` → 觀察顯著性評分和鞏固/遺忘決策

## 已知限制（原型階段）

- **LLM 為 mock**：神經軌回應是假的，接入真實 API 後替換 `MockLLM` 類即可
- **概念提取粗糙**：中文斷詞用簡單分割，生產環境應接入 jieba 或 LLM NER
- **檢索用關鍵字匹配**：生產環境應換成 embedding + 向量搜尋
- **組塊壓縮是拼接**：生產環境應用 LLM 做真正的摘要壓縮
- **認知負荷估算是啟發式**：需要更精細的新概念偵測（目前用詞長度代替）

## 下一步

- [ ] 接入真實 LLM API（MockLLM → Anthropic/OpenAI）
- [ ] 接入 jieba 做中文概念提取
- [ ] 用 embedding + FAISS/Chroma 替換關鍵字檢索
- [ ] 替換真實閱讀筆記數據
- [ ] 加入 Web UI（視覺化緩衝區和 KG）


## AI-Friendly Project Summary (for LLMs / Agents)

**Project Name:** Cognitive-Bionic Memory Architecture (CBMA)  
**Core Thesis (one sentence):** AI memory should emulate human cognitive constraints (limited working memory, selective consolidation, active forgetting, context-dependent binding) as functional enablers of abstraction, generalization, and lifelong adaptation — not obstacles to bypass with brute-force scaling.

**Architecture Overview (layers):**
- Layer 0: Representation — Dual-track (Symbolic KG + Neural LLM), confidence-gated arbitration
- Layer 1: Storage — Episodic (saliency-tagged events) + Semantic (generalized patterns), bidirectional compensation, temporary binding via context weights
- Layer 2: Processing — Limited attention buffer (~4–7 chunks), forced chunking/schema, recurrent activation loop
- Layer 3: Output Regulation — Cognitive load monitoring, scaffolding, dual-coding multimodal
- Axis: Consolidation–Forgetting–Restructuring Engine — Periodic offline process, saliency-driven (user reaction + repetition + pivot detection)

**Current Implementation Status (2026-02):**
- Mock LLM only (placeholder responses)
- Keyword-based retrieval (no embeddings/vectors yet)
- JSON-based KG & episodic/semantic stores
- Manual / auto consolidation trigger
- CLI demo only

**Key Hypotheses to Validate:**
1. Limited buffer forces better abstraction than unlimited context.
2. Confidence-gated symbolic override reduces hallucinations more than pure RAG.
3. Saliency signals (reaction strength + repeat count) enable meaningful long-term consolidation without brute-force summarization.

**Next Milestones (priority order):**
1. Replace MockLLM with real API/local model
2. Add sentence-transformers + FAISS/Chroma for semantic retrieval
3. Implement dynamic context weighting for temporary binding
4. Add logging/visualization of buffer changes & KG updates
5. Run long multi-session conversations to test consolidation effects

Feel free to feed this section directly into any LLM as context for code suggestions, experiments, or critiques.