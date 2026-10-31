# Exit Criteria 範本 (Evidence-Bound Definition of Done)

**何時讀本文**：撰寫新技能的完工標準、檢查既有技能的 Exit Criteria，或決定 `exit-profile` 時。

---

## 1. 領域宣告

在 frontmatter 加入：

```yaml
exit-profile: visual   # visual | audio | tooling | director | governance | none
```

`audit_skills_contract.py` 依此欄位檢查技能是否含有通用核心與對應領域模組。

---

## 2. 通用核心（所有技能）

1. 驗證工具報告通過（Validator PASS）。
   - 該技能尚無 validator：在主約寫明替代檢查（例如結構檢查腳本），並標註待補。
   - 確實不適用：標示 `N/A` 並說明原因，不得留白。
2. CRITIC 獨立審查裁決已記錄。
3. 狀態快照已生成（`skill.state.json` 或 `update.state.json`）。
4. **失敗出口**：缺少對應客觀證據時，狀態只能是 `in_progress`、`hold` 或 `blocked`。程式碼能編譯、JSON 語法合法都不構成完成。

---

## 3. 領域模組

| exit-profile | 追加證據 |
| :--- | :--- |
| `visual` | 完整 Contact Sheet 存在且未被裁切成局部視窗，並檢視原圖；第一次測試前建立並持續維護 Cleanup Manifest |
| `audio` | 聲學分析報告（RMS/LUFS）與音畫同步無漂移的驗證 |
| `tooling` | 單元測試通過、結構無非預期變動、無臨時腳本殘留 |
| `director` | Coverage Map、資訊增益判定、成對交換測試（Swap Test）一致性 |
| `governance` | 計畫文檔、動態 Checklist、快照鏈；必要時子計畫已歸併 |
| `none` | 僅適用通用核心 |

**術語核對**：上表的工具與術語（RMS/LUFS 分析、Coverage Map、information_gain、Swap Test 等）在採用前，先在專案中搜尋確認真的存在；不存在者換成實際等價項，或移除。

---

## 4. 可直接貼用的範本

```markdown
## Exit Criteria (Evidence-Bound Definition of Done)

### 通用核心
1. 驗證工具報告通過（或 N/A：<原因>）。
2. CRITIC 獨立審查裁決已記錄。
3. 狀態快照已生成。

### 領域模組（exit-profile: <領域>）
- <依第 3 章表格填入對應證據>

### 失敗出口
缺少上述任一項客觀證據時，狀態標記為 `in_progress`、`hold` 或 `blocked`。
```

---

## 5. 撰寫檢查

- 每項證據都能由檔案、報告或狀態值客觀判定，不依賴 agent 自述「已確認」。
- 證據項目與領域相符：音訊技能不要求 Contact Sheet，視覺技能才需要 Cleanup Manifest。
- 前置條件放在前置階段（例如「第一次測試前建立 Cleanup Manifest」），不要放進收尾清單。
- 失敗出口文字存在，且狀態值與專案狀態機一致。
