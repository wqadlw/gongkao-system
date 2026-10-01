"""
公考行测知识库系统 - 桌面版启动器
启动后端服务 → 自动打开浏览器 → 控制台显示状态（Ctrl+C 或关闭窗口退出）

打包（PyInstaller）：
    pyinstaller --name GongKaoDesktop --icon assets/icon.ico --add-data "frontend/dist;frontend_dist" desktop_launcher.py
数据目录：exe 同级的 data/（数据库、导图、备份均在此，卸载删目录即可）
"""
import os
import sys
import threading
import time
import webbrowser

# ---------- 路径解析：PyInstaller onefile 兼容 ----------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)          # exe 所在目录（用户数据根）
    BUNDLE_DIR = sys._MEIPASS                            # 解包临时目录（只读资源）
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

FRONTEND_DIST = os.path.join(BUNDLE_DIR, "frontend_dist")
if not os.path.isdir(FRONTEND_DIST):
    FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

# 用户数据目录：便携模式（exe 旁可写）用 data/；装进 Program Files 等只读位置时
# 自动落到 %LOCALAPPDATA%/GongKaoSystem/data，避免普通权限写入失败
import tempfile

_probe = os.path.join(BASE_DIR, "data")


def probe_writable(directory: str) -> bool:
    """用 tempfile 在目标目录创建探针并立即删除，验证目录可写"""
    try:
        with tempfile.NamedTemporaryFile(dir=directory, prefix=".write_test_", delete=False) as f:
            f.write(b"ok")
            probe = f.name
        os.remove(probe)
        return True
    except OSError:
        return False


try:
    os.makedirs(_probe, exist_ok=True)
    if not probe_writable(_probe):
        raise OSError("target dir not writable")
    DATA_DIR = _probe
except OSError:
    DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "GongKaoSystem", "data")
os.makedirs(DATA_DIR, exist_ok=True)
os.environ["GK_FRONTEND_DIST"] = FRONTEND_DIST
os.makedirs(DATA_DIR, exist_ok=True)
os.environ["GK_DATA_DIR"] = DATA_DIR

HOST, PORT = "127.0.0.1", 7080


def main():
    print("=" * 56)
    print("  公考行测知识库系统 v2.1 · 桌面版")
    print(f"  数据目录：{DATA_DIR}")
    print(f"  访问地址：http://{HOST}:{PORT}")
    print("  关闭本窗口即退出程序")
    print("=" * 56)

    # 后端启动前先改工作目录与 DB 路径（database.py 相对项目根拼路径）
    sys.path.insert(0, BUNDLE_DIR)

    import database
    database.DB_PATH = os.path.join(DATA_DIR, "gongkao.db")
    database.BASE_DIR = BUNDLE_DIR
    # 重算 engine 指向用户数据目录
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    database.engine = create_engine(
        f"sqlite:///{database.DB_PATH}", connect_args={"check_same_thread": False}
    )
    database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)
    database.get_db.__globals__["SessionLocal"] = database.SessionLocal

    from main import app  # noqa: E402  （database 已配置完成后再导入）
    import uvicorn  # noqa: E402

    def open_browser():
        time.sleep(1.8)
        webbrowser.open(f"http://{HOST}:{PORT}")

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()
