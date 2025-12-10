# Long Report Generation Roadmap

**Version**: 1.0
**Date**: 2025-12-10
**Status**: In Progress

## Executive Summary

Test-Smithの長文レポート生成機能を改善するためのロードマップ。世界の主要リサーチエージェント（GPT Researcher, Stanford STORM, Anthropic Multi-Agent System）の手法を参考に、2フェーズアーキテクチャを採用する。

## Problem Statement

### 現在の問題
1. **内容品質**: 13サブタスクを実行しても、レポート内容がクエリと無関係
2. **分量不足**: comprehensive モード（目標10,000語）で32行・2KBしか生成されない
3. **言語不一致**: 日本語クエリに英語で回答
4. **メタ記述**: 実際の調査内容ではなく、システム内部プロセスを説明

### 根本原因
- リサーチ収集とレポート執筆が**単一のSynthesizerノード**に詰め込まれている
- サブタスク結果が構造化されておらず、品質検証もない
- レポート生成に失敗しても再試行メカニズムがない

---

## Research: 世界のリサーチエージェント手法

### 1. GPT Researcher
**Repository**: https://github.com/assafelovic/gpt-researcher

#### アーキテクチャ: 6エージェントパイプライン
```
Researcher → Editor → Reviewer → Revisor → Writer → Publisher
```

#### 各エージェントの役割
| Agent | Role |
|-------|------|
| Researcher | 指定トピックの深い調査を行う自律エージェント |
| Editor | リサーチのアウトラインと構造を計画 |
| Reviewer | 基準に照らして調査結果の正確性を検証 |
| Revisor | Reviewerのフィードバックに基づき修正 |
| Writer | 最終レポートのコンパイルと執筆 |
| Publisher | PDF/Word/Markdown等の形式で出力 |

#### Deep Research Mode特徴
- **Breadth**: 各レベルで複数の検索クエリを生成
- **Depth**: 各ブランチで再帰的に深掘り
- **Concurrent Processing**: async/awaitで並列実行
- **Smart Context Management**: 全ブランチの発見を自動統合
- 出力: **2K+ words (5-6 pages)**

#### 核心的洞察
> "リサーチと執筆は別エージェントで行う"

---

### 2. Stanford STORM
**Repository**: https://github.com/stanford-oval/storm
**Paper**: Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking

#### アーキテクチャ: 2段階アプローチ
```
┌─────────────────────────────────────┐
│        Pre-writing Stage            │
│  - Internet research                │
│  - Reference collection             │
│  - Outline generation               │
│  - Mind map construction            │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         Writing Stage               │
│  - Generate from outline            │
│  - Use references for citations     │
│  - Multi-perspective synthesis      │
└─────────────────────────────────────┘
```

#### Pre-writing Stageの3ステップ
1. **Perspective Discovery**: トピック調査における多様な視点を発見
2. **Conversation Simulation**: 異なる視点を持つライターがトピック専門家に質問するシミュレーション
3. **Information Curation**: 収集情報をアウトラインに整理

#### Mind Map
- 収集情報を階層的概念構造に整理
- 人間とシステム間の共有概念空間を構築
- 長い議論での認知負荷を軽減

#### 評価結果
- 組織化: **+25%** 向上
- カバレッジ: **+10%** 向上
- 70,000人以上がライブプレビューを試用

#### 核心的洞察
> "アウトライン駆動の生成は品質を大幅に向上させる"

---

### 3. Anthropic Multi-Agent Research System
**Source**: https://www.anthropic.com/engineering/multi-agent-research-system

#### アーキテクチャ
```
User Query
    ↓
Lead Agent (戦略策定、サブエージェント生成)
    ↓
Subagents (並列で異なる側面を探索)
    ↓
Lead Agent (結果統合、追加調査要否判断)
    ↓
CitationAgent (引用配置)
    ↓
Final Report
```

#### サブエージェントへの指示要件
- **Objective**: 明確な目標
- **Output Format**: 出力形式
- **Tools & Sources**: 使用ツールとソース
- **Task Boundaries**: タスク境界

> "詳細なタスク記述がなければ、エージェントは作業を重複させたり、ギャップを残したり、必要な情報を見つけられなかったりする"

#### 品質管理
1. **Extended Thinking**: ツール結果後に品質評価、ギャップ特定
2. **LLM-as-Judge**: 事実精度、引用精度、完全性、ソース品質を評価
3. **Human Testing**: 自動評価が見逃すエッジケースをキャッチ

#### 核心的洞察
> "品質管理は多層的に行う必要がある"

---

## Proposed Architecture

### 2フェーズアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                      PHASE 1: RESEARCH                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │Master Planner│ →  │  Subtask     │ →  │   Result     │      │
│  │              │    │  Research    │    │  Aggregator  │      │
│  │ (decompose)  │    │  (parallel)  │    │  (validate)  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                  ↓              │
│                           structured_findings.json              │
│                           (品質検証済み構造化データ)              │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      PHASE 2: WRITING                           │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Outline    │ →  │   Section    │ →  │   Reviewer   │      │
│  │  Generator   │    │   Writer     │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                  ↓              │
│                                          ┌──────────────┐      │
│                         (if fail) ← ←    │   Revisor    │      │
│                                          └──────────────┘      │
│                                                  ↓              │
│                              final_report.md (品質基準達成)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Research Collection Enhancement

#### 1.1 Structured Research Storage
**Goal**: サブタスク結果を構造化JSONで保存

```python
@dataclass
class SubtaskFinding:
    subtask_id: str
    query: str
    focus_area: str
    language: str  # 検出された言語
    findings: list[str]  # 発見事項
    sources: list[dict]  # ソース情報
    quality_score: float  # 0.0-1.0
    relevance_score: float  # クエリとの関連性
    metadata: dict
```

**Files to modify**:
- `src/schemas.py`: SubtaskFinding スキーマ追加
- `src/nodes/analyzer_node.py`: 構造化出力生成

#### 1.2 Subtask Result Quality Validation
**Goal**: 各サブタスク結果の品質を検証

**検証項目**:
- [ ] 言語一致（クエリ言語 = 結果言語）
- [ ] 内容関連性（クエリトピックに関連）
- [ ] メタ記述禁止（システム内部説明を含まない）
- [ ] 最小文字数達成

**Files to create**:
- `src/utils/result_validator.py`: 品質検証ユーティリティ

#### 1.3 Result Aggregator Node
**Goal**: 全サブタスク結果を統合・整理

**機能**:
- 低品質結果のフィルタリング
- 重複情報の除去
- テーマ別クラスタリング
- structured_findings.json 出力

**Files to create**:
- `src/nodes/result_aggregator_node.py`

---

### Phase 2: Writer Graph (Option A)

#### 2.1 Outline Generator Node
**Goal**: 収集リサーチからアウトライン生成

**入力**: structured_findings.json
**出力**:
```python
@dataclass
class ReportOutline:
    title: str
    executive_summary_points: list[str]
    sections: list[OutlineSection]
    conclusion_points: list[str]
    target_word_count: int

@dataclass
class OutlineSection:
    heading: str
    subheadings: list[str]
    relevant_findings: list[str]  # finding IDs
    target_word_count: int
```

**Files to create**:
- `src/nodes/outline_generator_node.py`
- `src/prompts/outline_generator_prompt.py`

#### 2.2 Section Writer Node
**Goal**: セクションごとにリサーチから執筆

**特徴**:
- 各セクションを独立して生成
- 関連findingsのみを参照
- 目標語数を意識した生成

**Files to create**:
- `src/nodes/section_writer_node.py`
- `src/prompts/section_writer_prompt.py`

#### 2.3 Reviewer Node
**Goal**: 生成レポートの品質検証

**検証項目**:
- [ ] 語数達成（min/target）
- [ ] 言語一致
- [ ] 内容カバレッジ（全サブタスクをカバー）
- [ ] 構造品質（見出し、段落）
- [ ] メタ記述禁止

**Files to create**:
- `src/nodes/report_reviewer_node.py`
- `src/prompts/report_reviewer_prompt.py`

#### 2.4 Revisor Node
**Goal**: Reviewerフィードバックに基づく修正

**機能**:
- 不足セクションの追加
- 薄いセクションの拡充
- 言語修正
- 最大3回のリビジョン

**Files to create**:
- `src/nodes/report_revisor_node.py`
- `src/prompts/report_revisor_prompt.py`

#### 2.5 Writer Graph Assembly
**Goal**: 新グラフとして組み立て

```python
# src/graphs/writer_graph.py
class WriterGraphBuilder(BaseGraphBuilder):
    """
    Dedicated graph for long-form report writing.

    Takes structured_findings from Phase 1 and produces
    quality-validated final report.
    """
```

---

## Timeline (Estimated)

| Phase | Task | Complexity |
|-------|------|------------|
| 1.1 | Structured Research Storage | Medium |
| 1.2 | Quality Validation | Medium |
| 1.3 | Result Aggregator | Medium |
| 2.1 | Outline Generator | High |
| 2.2 | Section Writer | High |
| 2.3 | Reviewer | Medium |
| 2.4 | Revisor | Medium |
| 2.5 | Writer Graph Assembly | High |

---

## Success Metrics

### Phase 1
- [ ] サブタスク結果がJSON形式で保存される
- [ ] 品質スコア < 0.5 の結果がフィルタリングされる
- [ ] 言語不一致の結果が検出・警告される

### Phase 2
- [ ] comprehensive モードで 6,000語以上のレポート生成
- [ ] 日本語クエリに日本語レポート
- [ ] 全サブタスクの内容がレポートに反映
- [ ] メタ記述が含まれない
- [ ] 品質基準未達時の自動再生成

---

## References

1. [GPT Researcher - GitHub](https://github.com/assafelovic/gpt-researcher)
2. [GPT Researcher Deep Research Mode](https://docs.gptr.dev/docs/gpt-researcher/gptr/deep_research)
3. [Stanford STORM - GitHub](https://github.com/stanford-oval/storm)
4. [Stanford STORM Research Project](https://storm-project.stanford.edu/research/storm/)
5. [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
6. [LangChain State of AI Agents Report](https://www.langchain.com/stateofaiagents)
7. [Marktechpost 2025 Agentic AI Report](https://www.marktechpost.com/2025/05/21/marktechpost-releases-2025-agentic-ai-and-ai-agents-report-a-technical-landscape-of-ai-agents-and-agentic-ai/)

---

## Appendix: Current Architecture Analysis

### 現在の問題点詳細

#### Synthesizerの過負荷
現在のHIERARCHICAL_SYNTHESIZER_PROMPTは以下を1回のLLM呼び出しで要求:
1. 全サブタスク結果の理解
2. 統合と構造化
3. 言語判定と一致
4. 目標語数の達成
5. 引用配置

これは単一のLLM呼び出しには過大なタスク。

#### サブタスク結果の品質問題
```python
# 現在: 生の文字列として保存
subtask_results: dict[str, str]

# 問題: 品質、言語、関連性の検証なし
```

#### レポート生成失敗時の対応
```python
# 現在: 警告を出すだけで短いレポートをそのまま出力
if word_count < min_words:
    print(f"⚠️ Report is {word_count} words, below minimum")
# → 再生成メカニズムなし
```
