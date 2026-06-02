import os
import subprocess
import sys
import webbrowser
import socket


HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "web")
DIST_DIR = os.path.join(WEB_DIR, "dist")


def find_free_port(start: int = 8000) -> int:
    port = start
    while port < 8100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start


def build_frontend() -> bool:
    if os.path.isdir(DIST_DIR):
        return True

    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        subprocess.run([npm, "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: npm not found. Install Node.js from https://nodejs.org/", file=sys.stderr)
        print("       Then re-run this script.\n", file=sys.stderr)
        return False

    print("Building frontend...")
    result = subprocess.run([npm, "run", "build"], cwd=WEB_DIR, capture_output=True, text=True)

    if result.returncode != 0:
        print("Build failed:", result.stderr, file=sys.stderr)
        return False

    return True


def main() -> None:
    if not build_frontend():
        sys.exit(1)

    import uvicorn

    port = find_free_port()
    url = f"http://localhost:{port}"

    print(f"\n  UE Blueprint Visualizer")
    print(f"  {'─' * 40}")
    print(f"  Open:  {url}")
    print(f"  {'─' * 40}\n")

    webbrowser.open(url)
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()