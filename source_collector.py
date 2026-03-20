import os
import fnmatch

TARGET_EXT = [".py", ".js", ".jsx"]

# 제외할 폴더명
EXCLUDE_DIRS = {
    "venv",
    ".venv",
    "__pycache__",
    ".git",
}

# 제외할 파일명 / 패턴
EXCLUDE_PATTERNS = [
    "serviceAccountKey.json",
    ".env",
    ".env.example",
    "*.pyc",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.bmp",
    "*.ico",
    "*.svg",
]


def should_exclude_file(filename: str) -> bool:
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False


def dump_all_files(root=".", output_name="output.txt"):
    collected = []

    for dirpath, dirnames, filenames in os.walk(root):
        # 제외 폴더는 아예 탐색 안 하도록 수정
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for filename in filenames:
            if should_exclude_file(filename):
                continue

            _, ext = os.path.splitext(filename)
            if ext not in TARGET_EXT:
                continue

            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root)

            try:
                with open(full_path, "r", encoding="utf-8") as fp:
                    content = fp.read()
            except UnicodeDecodeError:
                try:
                    with open(full_path, "r", encoding="utf-8-sig") as fp:
                        content = fp.read()
                except Exception as e:
                    content = f"[READ ERROR: {e}]"
            except Exception as e:
                content = f"[READ ERROR: {e}]"

            collected.append(f'"""\n{content}\n""" {rel_path}')

    with open(output_name, "w", encoding="utf-8") as out:
        out.write("\n\n".join(collected))


dump_all_files(".")