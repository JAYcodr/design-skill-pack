# fpdf2 CJK PDF Fallback for macOS

> 当 WeasyPrint 因系统依赖缺失无法渲染中文时使用。
> 适用场景：内容固定的报告、资讯汇总、数据表格为主的 PDF。

## 前置条件

```bash
pip3 install fpdf2       # 已验证版本 2.8.4
# 字体：使用系统内置 Arial Unicode MS
ls /Library/Fonts/Arial\ Unicode.ttf   # macOS 内置
```

## API 注意事项 (fpdf2 2.8.4)

| 旧 API (已弃用) | 新 API |
|---|---|
| `cell(..., ln=True)` | `cell(..., new_x="LMARGIN", new_y="NEXT")` |
| `cell(..., ln=False)` | `cell(..., new_x="LMARGIN", new_y="RIGHT")` |

- `add_font()` 不需要 `uni=True` 参数（v2.5.1 已弃用）
- `cell()` 默认垂直间距用 `ln()` 控制
- 表格用 `table()` 方法，自动处理分页
- 无 `circle()` / `ellipse()` — 用 `rect()` 模拟图形元素

## 字体选用策略

| 字体 | 路径 | 格式 | 适用场景 |
|------|------|------|----------|
| **Arial Unicode MS** | `/Library/Fonts/Arial Unicode.ttf` | TrueType (4MB) | 通用中文 + 英文，覆盖所有 Unicode |
| **Source Han Sans SC VF** | `~/Library/Fonts/SourceHanSansSC-VF.ttf` | TrueType Variable Font | 需要思源黑体的排版，但需测试兼容性 |
| **PingFang SC** | `/System/Library/Fonts/PingFang.ttc` | TrueType Collection | 需从 TTC 提取，fpdf2 不直接支持 |

**结论**：Arial Unicode MS 最可靠，fpdf2 直接支持。

## 完整示例结构

```python
from fpdf import FPDF

class Report(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("CJK", "", 7)
            self.set_text_color(100, 100, 100)
            self.cell(0, 4, "文档标题 | 副标题", align="C",
                      new_x="LMARGIN", new_y="NEXT")
            self.ln(6)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("CJK", "", 7)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f"— {self.page_no()} —", align="C")

pdf = Report()
pdf.add_font("CJK", "", "/Library/Fonts/Arial Unicode.ttf")

# 封面
pdf.add_page()
pdf.set_font("CJK", "B", 28)
pdf.cell(0, 15, "报告标题", new_x="LMARGIN", new_y="NEXT")

# 正文
pdf.set_font("CJK", "", 9)
pdf.multi_cell(0, 5, "段落文字内容……")

# 表格
pdf.table(
    headers=["游戏名称", "折扣", "价格"],
    data=[
        ["Persona 5 Royal", "65% OFF", "EUR 20.99"],
        ["Unicorn Overlord", "50% OFF", "EUR 29.99"],
    ],
    col_widths=[90, 40, 60]
)

pdf.output("output.pdf")
```

## 已知陷阱

1. **字体加粗**：Arial Unicode.ttf 包含 Regular 和 Bold，注册为 `"B"` style 即可。
2. **分页**：`set_auto_page_break(True, 18)` — 18mm 底部边距。
3. **中文标点**：Arial Unicode 覆盖全角标点，无需额外处理。
4. **PDF 大小**：含嵌入字体约 200-300KB，优于 WeasyPrint 的 75KB 空壳。
