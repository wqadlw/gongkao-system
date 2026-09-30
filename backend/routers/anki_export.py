"""Anki 牌组导出路由（genanki）— 手机端 Anki/AnkiDroid 导入 .apkg 直接刷题"""
import os
import re as _re
from datetime import datetime
from urllib.parse import unquote as _unquote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db, DB_PATH, Question
from services.question_bank import safe_media_path, BANK_DIR

router = APIRouter(prefix="/api/anki", tags=["Anki导出"])

ANKI_MODEL_CSS = (
    ".card { font-family: -apple-system, 'Microsoft YaHei', sans-serif; font-size: 15px; "
    "text-align: left; color: #1f2937; background: #ffffff; padding: 16px; line-height: 1.7; }"
    ".card img { max-width: 100%; }"
    ".q-tag { color: #6b7280; font-size: 12px; margin-bottom: 8px; }"
    ".answer-box { background: #eef2ff; border-left: 3px solid #4f46e5; padding: 10px 12px; border-radius: 6px; margin-top: 10px; }"
    ".analysis-box { background: #f9fafb; border-radius: 6px; padding: 10px 12px; margin-top: 10px; font-size: 14px; }"
)


def _escape_html(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")


@router.get("/export")
def export_anki_deck(db: Session = Depends(get_db)):
    try:
        import genanki
    except ImportError:
        raise HTTPException(status_code=400, detail="未安装 genanki：请在后端 venv 执行 pip install genanki")

    questions = db.query(Question).order_by(Question.id).all()
    if not questions:
        raise HTTPException(status_code=400, detail="题库为空，无内容可导出")

    model = genanki.Model(
        1852724001,
        "公考行测题卡",
        fields=[{"name": "Question"}, {"name": "Answer"}, {"name": "Analysis"}, {"name": "Tags"}],
        templates=[{
            "name": "问答题卡",
            "qfmt": '<div class="q-tag">{{Tags}}</div><div>{{Question}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer"><div class="answer-box"><b>答案：{{Answer}}</b></div>'
                    '<div class="analysis-box">{{Analysis}}</div>',
        }],
        css=ANKI_MODEL_CSS,
    )
    deck = genanki.Deck(2059400110, "公考行测知识库")

    media_files = []
    img_re = _re.compile(r'src="/api/question-bank/media\?path=([^"]+)"')
    bank_root = os.path.normpath(BANK_DIR)

    def process_media(html_text: str) -> str:
        """把指向本系统媒体接口的图片转为 Anki 媒体文件引用；路径规范化后
        必须仍落在真题仓库根目录内，越界一律丢弃"""
        def repl(m):
            rel = _unquote(m.group(1)).replace("\\", "/")
            if not rel or "\x00" in rel:
                return m.group(0)
            abs_path = os.path.normpath(os.path.join(bank_root, rel))
            if not abs_path.startswith(bank_root + os.sep):
                return m.group(0)
            abs_path = safe_media_path(rel) or ""
            if not abs_path or not os.path.isfile(abs_path):
                return m.group(0)
            basename = os.path.basename(abs_path)
            if basename not in media_files:
                media_files.append(abs_path)
            return f'src="{basename}"'
        return img_re.sub(repl, html_text)

    for q in questions:
        tag_path = " / ".join([x for x in (q.level1, q.level2, q.level3, q.level4, q.level5) if x])
        front = process_media(_escape_html(q.question_raw))
        back = _escape_html(q.answer or "")
        analysis_parts = [q.normal_solve, q.quick_solve, q.break_logic, q.step_detail]
        analysis = process_media(_escape_html("\n\n".join([p for p in analysis_parts if p])))
        note = genanki.Note(
            model=model,
            fields=[front, back, analysis, _escape_html(tag_path or "未分类")],
            guid=genanki.guid_for(q.id),
        )
        deck.add_note(note)

    export_dir = os.path.join(os.path.dirname(DB_PATH), "exports")
    os.makedirs(export_dir, exist_ok=True)
    filename = f"gongkao_anki_{datetime.now().strftime('%Y%m%d_%H%M%S')}.apkg"
    filepath = os.path.join(export_dir, filename)
    genanki.Package(deck, media_files=media_files).write_to_file(filepath)
    return FileResponse(
        filepath, filename=filename,
        media_type="application/octet-stream",
        headers={"X-Note-Count": str(len(questions)), "X-Media-Count": str(len(media_files))},
    )
