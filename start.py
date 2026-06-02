import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "web")
DIST_DIR = os.path.join(WEB_DIR, "dist")


def build_frontend() -> bool:
    if not os.path.isdir(WEB_DIR):
        print("[ERROR] web/ directory not found", file=sys.stderr)
        return False

    need_build = not os.path.isdir(DIST_DIR)

    if not need_build:
        return True

    print("[INFO] Building frontend...")
    npm_path = "npm.cmd" if sys.platform == "win32" else "npm"
    result = subprocess.run(
        [npm_path, "run", "build"],
        cwd=WEB_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("[ERROR] Frontend build failed:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False

    print("[INFO] Frontend built successfully")
    return True


def main() -> None:
    if not build_frontend():
        sys.exit(1)

    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"[INFO] Open http://localhost:{port} in your browser")
    print(f"[INFO] Press Ctrl+C to stop")

    uvicorn.run("server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()