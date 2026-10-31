# 攻防報告格式與核可證據 (AC-GAN Audit Report & Approval Evidence)

**何時讀本文**：撰寫 `AC_GAN_<TOPIC>_AUDIT_REPORT.md`、判定計畫能否設為 `APPROVED`，或執行 P4 獨立驗證時。

---

## 1. 報告格式

報告固定為獨立檔，與計畫放在同一目錄，檔名 `AC_GAN_<TOPIC>_AUDIT_REPORT.md`。

```markdown
# AC_GAN 攻防報告：<TOPIC>

- 計畫編號：
- 風險級別：
- Critic 執行方式：獨立子代理人，工具 [Read, Grep, Glob]

## 第 N 輪：<維度>
### Actor 提案
（摘要）

### Critic 發現
| # | 發現 | 引用（檔案與行號） | 嚴重度 |
| :-: | :--- | :--- | :---: |

### 修改紀錄
| 發現 # | 計畫的修改 | 位置 |
| :-: | :--- | :--- |

### 本輪結論
通過 | 退件（第幾次）
（若本輪無發現，須說明客觀理由。）
```

- 退件達 2 次時，報告末尾觸發「升級事項 (ESCALATED)」，列出爭議點交使用者裁決。

---

## 2. `APPROVED` 客觀證據清單

由確定性檢查腳本 `python omnistate plan-review` 自動逐項確認：全部符合方可晉級。

| # | 證據項目 | 輕量 | 標準 | 高風險 | 檢驗方式 |
| :-: | :--- | :-: | :-: | :-: | :--- |
| **1** | 計畫頭部欄位齊全 (`risk_tier`, `status`, `scope_paths`) | v | v | v | 腳本 Regex 解析 |
| **2** | 攻防報告檔存在，輪數符合級別 (輕量1輪，標準/高風險3輪) | v | v | v | 檔案存在性與標題計數 |
| **3** | 每輪有具體發現、引用行號與修改紀錄 | v | v | v | 報告內容與 Git Commit 對照 |
| **4** | 規範性語句比對 (Must/Never Clause Diff) | | v | v | `diff_critic.py` (遺失數 = 0) |
| **5** | 驗收表與預先登記清單 (`ab_registry/`) | | v | v | 檔案於執行前已存在 |
| **6** | 必備章節齊全 | v | v | v | 依級別比對章節結構 |
| **7** | 待使用者確認清單已清空 | | v | v | `pending_user_decisions.md` (Pending = 0) |
| **8** | 試點 A/B 通過與 F1~F7 故障注入達成 | | | v | 實測報告 PASS (含 agent_run) |
| **9** | 指標可重現性驗證通過 | | | v | `verify_report.py` (100% MATCH) |
| **10**| 使用者簽核紀錄 | | | v | 使用者於對談或計畫中簽署放行 |

---

## 3. 狀態轉換法規

- `DRAFT` ➔ `REVIEWED`：證據 1～4 齊備。
- `REVIEWED` ➔ `PENDING_PILOT`：高風險計畫，證據 5～7 齊備，開始試點。
- `REVIEWED`（或 `PENDING_PILOT`）➔ `APPROVED`：所需證據全數齊備。
- 任何證據缺失、被撤回或計畫內容在核可後被修改，狀態自動強制退回 `DRAFT`。
