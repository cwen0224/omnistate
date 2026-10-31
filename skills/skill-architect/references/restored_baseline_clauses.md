# Restored Baseline Normative Clauses — skill-architect-nexus

> 來源：`git show af38003:.agents/skills/skill-architect-nexus/SKILL.md`（逐字保留原章節與識別字，未改寫）。
> 效力：與 SKILL.md 本文同等具約束力。

---
name: skill-architect-nexus
description: >
  Use when the user or OMNISTATE Governance asks to "create a new skill", "build a SKILL.md", "design an agent skill",
  "audit or refactor an existing skill", or when codifying a recurring procedural workflow into a production-grade Agent Skill.
  Enforces OMNISTATE Governance Plan Governance: progressive disclosure (<500 lines), explicit least-privilege allowed-tools,
  positive actor specifications, schema invariance protection, zero abstract negative prompts, and 3-Round A/C GAN defense.
  Do NOT use for one-off casual prompt polishing or raw code snippets that do not require reusable packaging.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# OMNISTATE Governance 專案級代理技能架構師 (Skill Architect Nexus)

本技能為 **9 號代理人 (OMNISTATE Governance)** 專屬之元技能（Meta-Skill），專職負責為本專案建立、稽核與升級符合 **Agent Skills Specification v0.1.0** 與 **OMNISTATE Governance 治理體系** 的生產級技能。

---

---

## 1. 核心工程哲學與剛性紅線

任何由本技能建立或審查的技能，必須嚴格遵循以下六大治理原則：

1. **三層漸進式揭露 (Progressive Disclosure)**：
   - Tier 1: Frontmatter Metadata 常駐 (~100 tokens)。
   - Tier 2: 核心 `SKILL.md` 嚴格限制在 **500 行以內**（建議 $\le 300$ 行），預防注意力衰減。
   - Tier 3: 詳盡規格移至 `references/`，可執行邏輯移至 `scripts/`，並確保 100% 實體檔案存在，杜絕任何虛構斷鏈路徑。
2. **最小權限契約 (`allowed-tools`)**：
   - 每個技能必須明確宣告最小權限工具清單。
   - **審查官 (Critic) 角色**：依防禦性原則僅開放 `[Read, Grep, Glob]` 查詢工具，隔絕破壞性操作。
   - **總監/編劇 (Director/Actor) 角色**：賦予 `[Read, Write, Edit, Grep, Glob]`。
   - **工程/算圖 (Engineer) 角色**：始得開放 `Bash` 執行權限。
3. **徹底肅清抽象反向提示詞 (Abolish Abstract Negative Prompts)**：
   - **Actor 正向引導**：工作手冊純粹描述「輸入規格」、「預期輸出」與「標準路徑」，保持認知焦點清晰。
   - **Critic 自由抓漏**：所有邊界防禦、異常攔截與品質紅線，全數收編為 Critic 端的獨立審查標準。
4. **JSON 結構不變性 (Schema Invariance)**：
   - 嚴格保護既有工作流定義的 JSON Schema、鍵值命名（如 `trigger_frame`, `camera_intent` 等），改動必須完全向後相容。
5. **六要素觸發導向 Description**：
   - 採用 `Use when...` 具體描述觸發情境與正向關鍵詞，並以排他條款劃定負向排他邊界。
7. **說明書本質與範本輔助 (Declarative Intent & Template Driven)**：
   - 說明書只寫「系統功能」與「特定硬體/介面特性」，嚴禁對 LLM 進行常識思考的過程微管理。
   - 廢除硬性限制如何一步步生成 JSON 的冗餘文字，改以乾淨外置之 `template.json` 作為結構輔助。
   - 人類即可做出的直覺判斷交給 Actor 自主發揮，所有是否合規、格式是否突變之裁量權，全數交由 Critic 自由抓漏把關。

---

---

## 2. 建立新技能的五步標準作業流程 (5-Stage SOP)

---

### 階段一：意圖對齊與角色定錨 (Role & Tools Framing)
1. 確定技能名稱（kebab-case，如 `my-feature-director`）。
2. 確定角色分類：`Critic`、`Director`、`Actor` 或 `Engineer`。
3. 依角色指派最小權限 `allowed-tools`。
4. 收集使用者召回語句（Trigger Phrases），反向推導 `description` 的 `Use when...`。

---

### 階段二：撰寫正向工作手冊 (Positive Actor Body)
1. 確保核心檔名為精確大小寫的 `SKILL.md`。
2. 結構編排：
   - `## 1. 職責與輸入前置條件 (Inputs & Preconditions)`
   - `## 2. 核心正向工作流程 (Step-by-Step Execution Workflow)`
   - `## 3. 輸出介面與標準資料結構 (Output Schema / JSON Contract)`
   - `## 4. 漸進式揭露索引 (Progressive Disclosure Index)`
3. **正向化重構檢查**：通篇檢視是否含有負向禁令詞彙，全數轉寫為正向執行期待值。

---

### 階段三：漸進式揭露資源落地 (Tier 3 Fulfillment)
1. 若規格超過 80 行，移至 `references/<spec-name>.md`（可參考治理母計畫 [plan_governance_master_spec.md](references/plan_governance_master_spec.md)）。
2. 若涉及確定性計算或資料轉換，撰寫 `scripts/<helper>.py`。
3. **斷鏈實體驗證**：確認所有在 `SKILL.md` 中引用的相對路徑，磁碟上皆存在實體檔案。
