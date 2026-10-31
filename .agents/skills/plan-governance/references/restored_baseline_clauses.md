# Restored Baseline Normative Clauses — plan-governance-gan

> 來源：`git show checkpoint-pre-ecosystem-refactor-20261024:.agents/skills/plan-governance-gan/SKILL.md`（逐字保留原章節，未改寫）。
> 補回原因：先前瘦身重構時這些規範條文遺失（共 16 條），經 `diff_normative_clauses` 偵測。
> 效力：與 SKILL.md 本文同等具約束力。若與本文衝突，以本文較新的條款為準，並將衝突回報給使用者。



---

# 計畫擬定剛性防線 (Plan Governance & 3-Round A/C GAN Protocol)

> [!CRITICAL]
> **全域計畫防繞過禁令 (Plan Anti-Bypass Gate)**  
> 凡是涉及到「撰寫新計畫書」、「系統升級方案」、「跨模組重構」或「架構變更」時，**本技能強制處於最高優先級**。  
> 任何代理人（不論是 OMNISTATE Governance、主管代理人或個別專家）**絕對不准繞過本技能直接定稿或開始寫程式碼**！

---

---

## 1. 核心子技能樹與自動繼承 (Sub-Skills Dependency)

當本技能被觸發時，代理人必須**自動關聯並繼承**以下兩個核心子技能，確保治理標準完全對齊：
1. **[progressive-engineering-governance](file:///c:/dev/Project/.agents/skills/progressive-engineering-governance/SKILL.md)**：提供代碼體積預算、無頭驗收工具庫與 3-Round A/C GAN 剛性審查維度。
2. **[centaur-collaboration-principle](file:///c:/dev/Project/.agents/skills/centaur-collaboration-principle/SKILL.md)**：提供半人馬分工原則（AI 管語意決策，程式管時間軸與數學比對）。

---

---

## 2. 剛性三輪 Actor/Critic GAN 流程 (3-Round A/C GAN Loop)

任何計畫書在宣告完成之前，必須在 Context 中或獨立檔案明確執行以下三輪對抗辯證：

---

### 🥊 第一輪：可行性與邊界防護 (Feasibility & Boundary)
- **Actor**：提出初始架構、涉及模組與實作路徑。
- **Critic 審查與質疑**：
  - **🚨 核心靈魂質問 (Anti-Cheating Check)**：
    > **「這就是開發者要的嗎？還是其實這只是在偷懶，嘗試做表面工夫通過人工檢查？」**  
    > 嚴格稽查 Actor 是否又在 JSON 裡手寫死板常數（如硬填 trigger_frame）來矇混過關！是否真正建立了可編輯、基於 Ref 與動態欄位的底層架構？
  - 是否破壞既有模組相容性（Breaking Changes）？
  - 是否在 UI / 載入階段過度拋出致命錯誤，導致即時預覽崩潰？
  - 邊界是否過度跨界侵入其他代理人的管區？
- **收斂要求**：Actor 必須依據 Critic 退件理由修正介面，改採診斷報告化（Diagnostic Findings）與合約轉譯器。

---

### 🥊 第二輪：泛用性與跨模組一致 (Generality & Modularity)
- **Actor**：提出修訂後的模組結構與類別設計。
- **Critic 審查與質疑**：
  - **嚴禁特例硬編碼 (Anti-Overfitting)**：是否只針對本次特定 Bug 寫死邏輯？
  - **跨模組通用性**：當同樣邏輯套用至 15_Montage、7_Designer、5_Chat、3_Caption 時是否能通用？
  - **標準統一性**：靜態預檢（Pre-flight）與動態無頭採樣（Headless）是否共用同一個合約核心？
- **收斂要求**：Actor 抽出底層通用 Core，消除特例，確保全域適用。

---

### 🥊 第三輪：效能負擔與算力極限 (Performance & Overhead)
- **Actor**：提出效能與驗收指標。
- **Critic 審查與質疑**：
  - **算力浪費審查**：是否在渲染或無頭每影格進行沉重的音訊波形 FFT、頻譜或影像像素卷積？
  - **重複造輪子審查**：是否重複執行離線資產庫中已有的數據？
  - **零負擔剛性約束**：動態遙測單格耗時必須 $<0.1\text{ms}$，對實體渲染速度的負擔必須接近 **0%**。
- **收斂要求**：Actor 改採宣告式查詢（Declarative Lookup），確保計算量為 $O(1)$ 或純區間比對。

---

---

## 3. 執行中任務意圖預審與防偷懶攔截機制 (Runtime Intent Pre-Check & Anti-Cheating Gate)

> [!CRITICAL]
> **執行期動態阻斷門禁 (Runtime Execution Interceptor)**  
> 計畫書制定完成並進入實施階段後，**禁止 Actor 自行盲目執行任務代碼**！  
> 在處理每一個具體子任務（Task / Sub-plan）前，Actor 必須強制發起「意圖簡短報告」，由 CRITIC 先行審查並取得放行。

---

### 📋 1. Actor 任務執行前置報告 (Actor Pre-Execution Intent Brief)
Actor 在讀取到當前任務項目後，必須向 CRITIC 輸出結構化簡短報告，說明：
- `task_id`: 當前任務編號與名稱
- `target_modules`: 預計修改的具體檔案路徑清單
- `approach_summary`: 即將採取的實作做法簡述（杜絕任何表面工夫或猜測）
- `verification_plan`: 預計如何親眼/親耳驗收實體成果（拒絕純看 JSON 報表，必須具備實體影格或代碼接口貫通性驗證）

---

### 🛑 2. CRITIC 即時攔截與退件條件 (Zero Superficial Tolerance)
CRITIC 收到 Actor 的前置報告後，若發現以下任一情況，**必須立即亮紅燈攔截，禁止 Actor 執行**：
1. **與原計畫環節要求衝突 (Plan Conflict)**：
   - Actor 試圖更改計畫既定的架構邊界、跳過特定驗收工具、或採用與前序 A/C GAN 結論相悖的手段。
2. **試圖做表面工夫 (Superficial & Cheating Anti-Pattern)**：
   - **硬編碼常數假冒動態**：例如在外部 JSON 隨意塞死板數字（如 `trigger_frame: 0` 或猜測的 `relative_ratio`），假冒演算法動態計算。
   - **粗暴遮蔽假冒排版修復**：例如在畫面上疊加全域黑底色塊、覆蓋遮罩來掩蓋組件內部文字破版或寫死問題。
   - **報表驗收假冒實體驗收**：只打算檢查 Python 輸出或 JSON 檔案欄位是否存在，而沒有計畫抽取實體影格（Contact Sheet）或檢查代碼 Props 接口是否真正貫通。
   - **組件內部硬編碼假文字**：未真正打通 `text` 接口，試圖依賴組件既有 Mock 常數（如「台北夜行」）矇混過關。

---

## 4. 計畫書交付標準 (Mandatory Plan Deliverables)

任何合法生效的計畫書必須包含以下不可或缺的標籤與章節：
1. **頭部戳記**：
   ```markdown
   **審查狀態**：APPROVED (經過三輪 A/C GAN 攻防通過)
   **治理規範**：[plan-governance-gan](file:///c:/dev/Project/.agents/skills/plan-governance-gan/SKILL.md)
   ```
2. **附帶攻防報告**：必須附有 `AC_GAN_<TOPIC>_AUDIT_REPORT.md` 或在計畫書內部保留完整三輪攻防記錄。
3. **驗收工具鏈指名**：必須指明調用官方工具（如 `headless_preview_report.py`、`material_observer.py`、`preflight_inspector.py`），嚴禁私自手寫免洗腳本。

---

## 原版 frontmatter description（逐字）

專案計畫擬定之剛性防線 (Plan Governance & 3-Round A/C GAN)。任何架構升級、功能擴充、修復或重構計畫書擬定時強制觸發，規範必須經過三輪 Actor/Critic GAN 遞迴辯證 (可行性、泛用性、效能負擔) 與子技能自動掛載。觸發詞：擬定計畫, 建立計畫, 計畫書, 升級計畫, 修復計畫, 改善計畫, PLAN-, UPDATE_PLAN, MASTER_PLAN.
