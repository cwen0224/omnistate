---
name: skill-architect
description: >
  Use when the user or project asks to "create a new skill", "build a SKILL.md", "design an agent skill",
  "audit a skill", "refactor / slim down an existing skill", "fix skill frontmatter or broken links",
  or when codifying a recurring procedural workflow into a reusable Agent Skill.
  Guides skill creation and safe refactoring: progressive disclosure, least-privilege allowed-tools,
  three-class prohibition triage, schema invariance, evidence-bound exit criteria, and anti-regression review.
  Do NOT use for one-off prompt polishing, raw code snippets that need no reusable packaging,
  or runtime pipeline execution (use the owning pipeline skill instead).
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
exit-profile: governance
---

# 通用代理技能架構師 (Skill Architect)

本技能是代理人體系的元技能（Meta-Skill）：負責**建立**與**安全重構**符合 Agent Skills Specification v0.1.0 的高質量技能。
審查由獨立的唯讀 Critic 角色執行，本技能負責產出與交付規格證據。

---

## 0. 前置檢查 (Preflight)

開工前確認工作環境是否具備基本檢查與狀態管理工具：

| 工具 / 命令 | 用途 |
| :--- | :--- |
| `omnistate begin --intent "<技能重構/新建>"` | 鎖定受控邊界，防止改動蔓延 |
| 靜態規格稽核腳本 / 語法檢查器 | 結構、連結、權限、控制字元、frontmatter 檢查 |
| Git 版本比對工具 (`git diff`) | 新舊版本特徵覆蓋、規範性語句零遺失比對 |
| 程式碼硬守門模組 | 避免破壞檔案系統或覆寫核心配置 |

---

## 1. 六大治理原則

1. **三層漸進式揭露 (Progressive Disclosure)**
   - Tier 1：frontmatter 常駐（`name`, `description`, `allowed-tools`, `exit-profile`）。
   - Tier 2：`SKILL.md`，建議行數 <= 150 行，硬上限 500 行。
   - Tier 3：`references/`（深度規範、資料字典）與 `scripts/`（確定性驗證腳本）。
   - 主約引用的相對路徑必須存在實體檔案。
2. **最小權限 `allowed-tools` (Least Privilege)**
   - 依技能**實際需要**授予：需要執行 CLI 或腳本才給 `Bash`；純分析僅給 `[Read, Grep, Glob]`；產生檔案加 `Write, Edit`。
   - 審查官（Critic）固定為唯讀 `[Read, Grep, Glob]`。
3. **禁令三類分流 (Prohibition Triage)**
   - **A 類 (抽象品質要求)**：轉化為 Critic 審查檢核點。
   - **B 類 (破壞邊界/不可逆危險動作)**：主約宣告並由程式硬閘門強制守門。
   - **C 類 (路由排他邊界)**：留在 description 的 `Do NOT use for...` 語句中。
4. **Schema 不變性 (Schema Invariance)**
   - 既有介面欄位與資料結構變更必須向下相容。
5. **觸發導向 description**
   - 包含觸發情境、使用者召回詞、排他邊界，標準格式以 `Use when...` 起首、`Do NOT use for...` 收尾。
6. **證據綁定的完工與防退步**
   - 每個技能必須具備可客觀查核的 Exit Criteria 與明確的失敗出口（Hold / Blocked）。

---

## 2. 建立新技能 SOP

### 階段一：定錨
1. 技能名稱使用 kebab-case。
2. 判定角色與職責邊界（Critic / Director / Actor / Engineer / Governance）。
3. 判定 `exit-profile`（`governance`、`tooling`、`director` 等）。
4. 撰寫觸發導向的 `description` 與配置最小權限 `allowed-tools`。

### 階段二：撰寫主約 (`SKILL.md`)
1. 職責與輸入前置條件。
2. 核心正向工作流程與資料規格。
3. Exit Criteria（客觀交付物 + 失敗出口）。
4. 漸進式揭露索引（指向 `references/`）。

### 階段三：Tier 3 落地
1. 複雜長篇規範移至 `references/`，可執行的測試或驗收邏輯置於 `scripts/`。
2. 檢查所有連結路徑是否真實存在。

### 階段四：獨立審查與驗收
1. 檢查 ASCII 控制字元、代碼塊閉合與格式完整度。
2. 唯讀 Critic 審查權限是否最小化、Exit Criteria 是否客觀。
3. 驗證通過後標記為完成。

---

## 3. Exit Criteria (Evidence-Bound Definition of Done)

本技能的任務僅在下列證據齊備時標記為完成：
1. `SKILL.md` 格式完全符合 YAML frontmatter 與 Markdown 語法標準。
2. 無殘留 ASCII 控制字元與未閉合代碼塊。
3. 引用之 `references/` 或 `scripts/` 檔案路徑真實存在。
4. `allowed-tools` 與 `exit-profile` 已完整正確宣告。
5. 包含明確之失敗出口定義。

> [!CAUTION]
> **失敗出口 (Hold / Blocked)**：  
> 若格式損毀、權限過度宣告或依賴檔案缺失，狀態強制標記為 `hold` 或 `blocked`，嚴禁交付。
