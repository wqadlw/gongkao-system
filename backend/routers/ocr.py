"""OCR 路由 — 离线截图识别题干（RapidOCR，ONNX Runtime，零联网）

可选依赖：rapidocr-onnxruntime 未安装时接口返回 400 并提示安装。
识别结果为按阅读顺序拼接的纯文本，供录入页预填题干，公式部分仍建议交给 AI 处理。
"""
from fastapi import APIRouter, HTTPException, UploadFile

router = APIRouter(prefix="/api/ocr", tags=["OCR识别"])

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            raise HTTPException(
                status_code=400,
                detail="未安装 rapidocr-onnxruntime：请在后端 venv 执行 pip install rapidocr-onnxruntime",
            )
        _engine = RapidOCR()
    return _engine


@router.post("")
async def ocr_image(file: UploadFile):
    """识别上传图片中的文字，返回按行拼接的文本与置信度过滤后的行数"""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片超过 10MB 限制")

    import numpy as np

    try:
        import cv2

        arr = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    except ImportError:
        from PIL import Image
        import io

        arr = np.array(Image.open(io.BytesIO(content)).convert("RGB"))[:, :, ::-1]

    if arr is None:
        raise HTTPException(status_code=400, detail="无法解析图片文件")

    result, _ = _get_engine()(arr)
    lines = [item[1] for item in (result or []) if len(item) >= 2 and item[1].strip()]
    return {
        "text": "\n".join(lines),
        "line_count": len(lines),
        "file_name": file.filename or "",
    }
