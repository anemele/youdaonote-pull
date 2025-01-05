from pathlib import Path

from youdaonote_pull.convert import YoudaoNoteConvert

THIS_DIR = Path(__file__).parent


def test_covert_xml_to_markdown_content():
    """
    测试 xml 转换 markdown
    python test.py YoudaoNoteCovert.test_covert_xml_to_markdown_content
    """
    content = YoudaoNoteConvert._covert_xml_to_markdown_content(THIS_DIR / "test.note")
    with open(THIS_DIR / "test.md", encoding="utf-8") as fp:
        content_target = fp.read()
    # CRLF => \r\n, LF => \n
    assert content.replace("\r\n", "\n") == content_target


def test_html_to_markdown():
    """
    测试 html 转换 markdown
    :return:
    """
    from markdownify import markdownify as md

    new_content = md(
        """<div><span style='color: rgb(68, 68, 68); line-height: 1.5; font-family: "Monaco","Consolas","Lucida Console","Courier New","serif"; font-size: 12px; background-color: rgb(247, 247, 247);'><a href="http://bbs.pcbeta.com/viewthread-1095891-1-1.html">http://bbs.pcbeta.com/viewthread-1095891-1-1.html</a></span></div>"""
    )
    expected_content = """<http://bbs.pcbeta.com/viewthread-1095891-1-1.html>"""
    assert new_content == expected_content


def test_covert_json_to_markdown_content():
    """
    测试 json 转换 markdown
    python test.py YoudaoNoteCovert.test_covert_json_to_markdown_content
    """
    content = YoudaoNoteConvert._covert_json_to_markdown_content(THIS_DIR / "test.json")
    with open(THIS_DIR / "test-json.md", encoding="utf-8") as fp:
        content_target = fp.read()
    # CRLF => \r\n, LF => \n
    assert content.replace("\r\n", "\n") == content_target


def test_covert_json_to_markdown_single_line():
    """
    测试 json 转换 markdown 单行富文本
    python test.py YoudaoNoteCovert.test_covert_json_to_markdown_single_line
    """
    line = YoudaoNoteConvert._covert_json_to_markdown_content(
        THIS_DIR / "test-convert.json"
    )
    with open(THIS_DIR / "test-convert.md", encoding="utf-8") as fp:
        target = fp.read()
    # CRLF => \r\n, LF => \n
    assert line.replace("\r\n", "\n") == target
