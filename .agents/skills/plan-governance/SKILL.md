---
name: plan-governance
description: >
  Use when drafting, reviewing, or approving a plan for an architecture upgrade, feature expansion,
  repair, refactor, or cross-module change (plan documents such as PLAN-*, UPDATE_PLAN, MASTER_PLAN).
  Guides risk-tiered Actor/Critic review (light / standard / high-risk), evidence-bound plan approval,
  DAG subtask decomposition, and independent subagent plan review via OMNISTATE.
  Triggers: 擬定計畫, 建立計畫, 計畫書, 升級計畫, 修復計畫, 改善計畫, PLAN-, UPDATE_PLAN, MASTER_PLAN.
  Do NOT use for single-line fixes, typo-level document edits, or executing an already approved task
  (use the owning skill for that task).
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
exit-profile: governance
---

# 計畫擬定與狀態治理 (Plan Governance & Risk-Tiered A/C GAN)

本技能規範架構計畫書如何被擬定、審查、核可，以及核可後如何分解為 OMNISTATE 子任務與驗收清單。
核心原則：**核可由客觀證據決定，不由作者宣告**。

---

## 0. 前置檢查與守門工具 (Preflight & Guardrails)

執行任何治理計畫前，強制調用 OMNISTATE 交易與狀態守門命令鏈：

| 步驟 | 實體命令 / 工具 | 用途 |
| :--- | :--- | :--- |
| **開始事務** | `omnistate begin --intent "<摘要>" --scope "<目錄>"` | 開啟受控事務邊界，鎖定修改範圍 |
| **記錄需求備忘** | `omnistate memo --prompt "<原始需求>" --ref "<文檔>"` | 固化使用者原始意圖與驗收背景 |
| **建立驗收清單** | `omnistate checklist add --title "<驗收項>" --acceptance "<標準>"` | 登記客觀驗收條目 |
| **拆解 DAG 子任務** | `omnistate subtask add --title "<任務>" --type <impl\|verif> --depends-on "<ID>"` | 建立嚴格依賴拓撲的有向無環圖 |
| **綁定驗收與任務** | `omnistate checklist link --check-id "<CHECK-ID>" --subtask-id "<TASK-ID>"` | 確保每條驗收條件皆有實作或驗證任務對應 |
| **獨立審查核可** | `omnistate plan-review --status APPROVED --agent "<CRITIC>"` | 獨立子代理人審查並核可計畫 |
| **硬閘門稽核** | `omnistate audit` | 自動驗證 PlanningGate、ScopeEnclosure、AntiLaziness |
| **事務結案與放行** | `omnistate finish --evidence "<證據清單>"` | 簽發 Git Pre-Commit Clearance Token |

---

## 1. 風險分級 (Risk Tiers)

| 級別 | 條件（預設，可由專案調整） | 流程與必備驗收 |
| :--- | :--- | :--- |
| **輕量 (Light)** | 單一模組、可逆、不改介面或 Schema | 意圖簡報 + Critic 單輪快審 + 3 必備章節 |
| **標準 (Standard)** | 跨模組，或改介面、流程、狀態機 | 三輪 A/C GAN + 規範性語句比對 + 6 必備章節 + OMNISTATE 子任務 DAG |
| **高風險 (High)** | 不可逆動作、Schema 變更、批次超過 10 個目標 | 三輪 A/C GAN + 試點 A/B + 故障注入 + 使用者簽核 + 10 必備章節 |

分級由 Actor 提出，Critic 或腳本確認；不確定時往高一級。

---

## 2. 計畫狀態與核可 (Plan States & Approval)

狀態依序為 `DRAFT` ➔ `REVIEWED` ➔ `PENDING_PILOT`（高風險專屬）➔ `APPROVED`。

- 狀態只能由獨立 Critic 審查及實體驗收工具確認；作者嚴禁直接自封 `APPROVED`。
- `APPROVED` 的客觀證據：
  1. 獨立攻防報告存在且輪數符合級別（輕量 1 輪，標準/高風險 3 輪）。
  2. 驗收清單（Checklist）與子任務（Subtasks）已完全建立且彼此綁定。
  3. 待使用者確認清單全數清空 (Pending = 0)。
  4. 高風險計畫：A/B 預先登記完成、試點結果記錄在案、使用者已親自簽核。
- 計畫須在頭部宣告 `scope_paths`。核心路徑被修改前，必須存在狀態為 `APPROVED` 的計畫。

---

## 3. A/C GAN 獨立審查機制

### 角色與獨立性
- **Actor**：提出架構、模組、路徑與驗收指標。
- **Critic**：獨立子代理人；只收到計畫與簡報，不看 Actor 的中間推理；工具嚴格限制為只讀 `[Read, Grep, Glob]`，嚴禁授予 Write 或 Bash。
- Critic 每項質疑必須引用具體檔案與行號；每輪記錄「這項發現使計畫改了什麼」。

### 三輪維度（標準與高風險）
1. **可行性與邊界**：是否偷懶或做表面工夫？是否破壞既有相容性？是否越界到其他代理人的管區？
2. **泛用性與跨模組一致**：是否只針對單一案例寫死？共用核心是否抽出？
3. **效能與負擔**：是否重複造輪子？效能指標須寫明量測方法與具體門檻。

### 退件上限
同一任務或同一計畫被退件 2 次強制停止，觸發 `ESCALATED`，列出爭議點交給使用者決定，不再自行循環。

---

## 4. 逐任務執行與依賴保證

計畫核可後，每個具體任務執行必須符合：
1. **DAG 拓撲順序**：前置任務狀態必須為 `PASS`，後續任務方可標記完成。
2. **邊界防禦**：修改檔案必須完全落在交易宣告之 `scope_paths` 內。
3. **無偷懶保證**：禁止殘留 `TODO`、`FIXME`、`pass` 或佔位 Stub。

---

## 5. Exit Criteria (Evidence-Bound Definition of Done)

本技能的任務僅在下列客觀證據齊備時標記為完成：
1. 計畫書已完整產出，包含風險分級、`scope_paths`、架構藍圖與驗收目標。
2. 獨立 A/C GAN 審查報告產出完畢，輪數符合標準。
3. OMNISTATE 交易已記錄需求備忘錄（`memo`）與驗收清單（`checklist`）。
4. 獨立審查官裁決已記錄至 OMNISTATE（`plan-review` 狀態為 `APPROVED` 或 `RESOLVED`）。
5. `omnistate audit` 閘門全數通過，取得放行憑證。

> [!CAUTION]
> **失敗出口 (Hold / Blocked)**：  
> 任一項證據缺失或審查未通過時，計畫狀態維持 `DRAFT` 或 `REVIEWED`，任務強制標記為 `hold` 或 `blocked`，嚴禁擅自進入實施階段。
