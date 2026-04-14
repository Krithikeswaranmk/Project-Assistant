import ast
import os

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "dist", "build", "__pycache__"}
MAX_FILE_SIZE = 500 * 1024
MAX_CHUNKS = 500


def detect_language(file_path: str) -> str:
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
        ".rb": "ruby",
        ".rs": "rust",
        ".cpp": "cpp",
        ".c": "c",
        ".md": "markdown",
        ".txt": "text",
        ".rst": "restructuredtext",
    }
    _, ext = os.path.splitext(file_path.lower())
    return extension_map.get(ext, "unknown")


def _is_binary(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            sample = f.read(1024)
        return b"\x00" in sample
    except OSError:
        return True


def _python_chunks(content: str, rel_path: str) -> list[dict]:
    chunks = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return chunks

    if rel_path.endswith("__init__.py"):
        statements = [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
        if not statements:
            return chunks

    lines = content.splitlines()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        if (end - start + 1) < 3:
            continue
        segment = ast.get_source_segment(content, node)
        if not segment:
            segment = "\n".join(lines[start - 1 : end])
        chunks.append(
            {
                "type": "class" if isinstance(node, ast.ClassDef) else "function",
                "name": node.name,
                "code": segment,
                "file": rel_path,
                "language": "python",
                "start_line": start,
            }
        )
    return chunks


def _line_chunks(content: str, rel_path: str, language: str) -> list[dict]:
    lines = content.splitlines()
    window = 40
    overlap = 5
    step = max(1, window - overlap)
    chunks = []
    for i in range(0, len(lines), step):
        block = lines[i : i + window]
        if not block:
            continue
        chunks.append(
            {
                "type": "lines",
                "code": "\n".join(block),
                "file": rel_path,
                "language": language,
                "start_line": i + 1,
            }
        )
    return chunks


def _doc_chunks(content: str, rel_path: str) -> list[dict]:
    chunks = []
    for paragraph in content.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        chunks.append(
            {
                "type": "doc",
                "code": paragraph,
                "file": rel_path,
                "language": "markdown",
                "start_line": 1,
            }
        )
    return chunks


def chunk_repository(repo_path: str) -> list[dict]:
    chunks: list[dict] = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file_name in files:
            rel_root = os.path.relpath(root, repo_path)
            rel_path = os.path.normpath(os.path.join(rel_root, file_name)) if rel_root != "." else file_name

            if any(part in SKIP_DIRS for part in rel_path.split(os.sep)):
                continue
            if file_name == ".env":
                continue

            abs_path = os.path.join(root, file_name)
            try:
                size = os.path.getsize(abs_path)
            except OSError:
                continue
            if size > MAX_FILE_SIZE or _is_binary(abs_path):
                continue

            language = detect_language(file_name)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except OSError:
                continue

            if file_name.endswith(".py"):
                chunks.extend(_python_chunks(content, rel_path))
            elif file_name.endswith((".md", ".txt", ".rst")):
                chunks.extend(_doc_chunks(content, rel_path))
            elif file_name.endswith((".js", ".ts", ".java", ".cpp", ".c", ".go", ".rb", ".rs", ".tsx", ".jsx")):
                chunks.extend(_line_chunks(content, rel_path, language))

            if len(chunks) >= MAX_CHUNKS:
                return chunks[:MAX_CHUNKS]

    return chunks[:MAX_CHUNKS]
