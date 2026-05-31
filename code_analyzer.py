import os
from pathlib import Path

# Directory and file ignore lists to keep the generated tree clean
IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", ".next", 
    "dist", "build", ".nuxt", "out", "target", ".idea", ".vscode", 
    "coverage", "tmp", "temp", "vendor"
}

IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    ".DS_Store", "thumbs.db", "vibe_architect.db"
}

def generate_folder_tree(root_path, max_depth=5):
    """
    Generates a textual tree representation of the folders and files in the root_path.
    """
    root = Path(root_path)
    if not root.exists() or not root.is_dir():
        return f"Caminho inválido ou não é um diretório: {root_path}"

    tree_lines = [f"{root.name}/"]
    
    def _build_tree(directory, depth, prefix=""):
        if depth > max_depth:
            tree_lines.append(f"{prefix}... (limite de profundidade atingido)")
            return
            
        try:
            # Sort directories first, then files
            entries = sorted(list(directory.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            tree_lines.append(f"{prefix}[Acesso Negado]")
            return
        
        # Filter entries
        entries = [
            e for e in entries 
            if (e.is_dir() and e.name not in IGNORE_DIRS) or 
               (e.is_file() and e.name not in IGNORE_FILES)
        ]
        
        count = len(entries)
        for i, entry in enumerate(entries):
            is_last = (i == count - 1)
            connector = "└── " if is_last else "├── "
            
            if entry.is_dir():
                tree_lines.append(f"{prefix}{connector}{entry.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                _build_tree(entry, depth + 1, new_prefix)
            else:
                tree_lines.append(f"{prefix}{connector}{entry.name}")

    _build_tree(root, 1)
    return "\n".join(tree_lines)

def read_key_config_files(root_path):
    """
    Looks for standard configuration files in the root_path and returns their contents.
    Useful for configs and auth check step (Step 6).
    """
    root = Path(root_path)
    configs = {}
    
    # List of common configuration files to search
    target_files = [
        "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
        "docker-compose.yml", "Dockerfile", ".env.example", 
        "prisma/schema.prisma", "schema.prisma", "src/shared/config/index.ts",
        "src/config/index.js", "src/config/config.json", "tsconfig.json"
    ]
    
    for relative_path in target_files:
        file_path = root / relative_path
        if file_path.exists() and file_path.is_file():
            try:
                # Read first 100 lines/8000 chars to avoid overloading context
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(8000)
                    if len(content) >= 8000:
                        content += "\n... [Conteúdo truncado para economizar espaço] ..."
                configs[relative_path] = content
            except Exception as e:
                configs[relative_path] = f"Erro ao ler arquivo: {e}"
                
    return configs

def read_file_content(absolute_path, max_chars=12000):
    """
    Reads the content of a specific file to be included in prompts.
    """
    path = Path(absolute_path)
    if not path.exists() or not path.is_file():
        return f"Arquivo não encontrado: {absolute_path}"
        
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_chars)
            if len(content) >= max_chars:
                content += "\n... [Conteúdo truncado para economizar espaço] ..."
            return content
    except Exception as e:
        return f"Erro ao ler arquivo: {e}"
