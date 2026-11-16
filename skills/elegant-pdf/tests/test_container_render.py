"""Verify ::: fenced div containers render to styled <div> blocks."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from md2elegant import md_to_html

def test_quote_box_renders_as_div():
    md = "::: quote-box\nhello\n:::"
    html = md_to_html(md)
    assert '<div class="quote-box">' in html, f"expected div.quote-box, got: {html}"
    assert "hello" in html

def test_intro_block_renders():
    md = "::: intro-block\n命中规则\n:::"
    html = md_to_html(md)
    assert '<div class="intro-block">' in html

def test_memo_section_with_nested_title():
    # 嵌套规则：外长内短（外 4 冒号、内 3 冒号），与 code fence 一致
    md = ":::: memo-section\n::: memo-title\n关键边界\n:::\n内容\n::::"
    html = md_to_html(md)
    assert '<div class="memo-section">' in html
    assert '<div class="memo-title">' in html
    assert "关键边界" in html
    assert "内容" in html
    # 严格验证内容被包在 memo-section 内（在 close 之前）
    section_open = html.index('<div class="memo-section">')
    section_close = html.index('</div>', section_open)  # 外层最后一个 </div>
    # 最后一个 </div> 才是外层 memo-section 的闭合
    last_close = html.rindex('</div>')
    assert "内容" in html[section_open:last_close + 6], f"内容应在 memo-section 内，html={html}"

def test_section_note_renders():
    md = "::: section-note\n这是边注\n:::"
    html = md_to_html(md)
    assert '<div class="section-note">' in html

def test_theorem_renders():
    md = "::: theorem\n定理 1：连续函数一致连续\n:::"
    html = md_to_html(md)
    assert '<div class="theorem">' in html

def test_unknown_class_degrades_gracefully():
    """未注册的类名不应崩，内容仍在。"""
    md = "::: unknown-class\nstill here\n:::"
    html = md_to_html(md)
    assert "still here" in html

def test_standard_markdown_still_works():
    md = "# 标题\n\n段落\n\n- 列表项"
    html = md_to_html(md)
    assert "<h1" in html and "标题" in html
    assert "<ul" in html or "<li" in html

if __name__ == "__main__":
    test_quote_box_renders_as_div()
    test_intro_block_renders()
    test_memo_section_with_nested_title()
    test_section_note_renders()
    test_theorem_renders()
    test_unknown_class_degrades_gracefully()
    test_standard_markdown_still_works()
    print("✓ all container tests passed")