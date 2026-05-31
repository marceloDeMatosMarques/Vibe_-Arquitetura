import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vibe_architect.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Projects
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        tech_stack TEXT, -- JSON string
        root_path TEXT
    );
    """)
    
    # 2. Requirements (RFs and RNFs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        req_type TEXT, -- 'functional' or 'non_functional'
        code TEXT, -- e.g., RF01, RNF01
        description TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)
    
    # 3. DDD Entities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        properties TEXT, -- JSON string list
        methods TEXT, -- JSON string list
        relationships TEXT, -- JSON string list
        rules TEXT, -- JSON string list
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)
    
    # 4. Audit Steps
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        step_number INTEGER,
        prompt_content TEXT,
        response_content TEXT,
        completed INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(project_id, step_number),
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)
    
    # 5. Templates (Prompts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        content TEXT
    );
    """)
    
    # 6. Checklists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        category TEXT, -- 'quality', 'pr', 'security', 'docs', 'test'
        item_text TEXT NOT NULL,
        is_checked INTEGER DEFAULT 0,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    conn.close()

# --- Project Operations ---

def get_projects():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY id DESC")
    rows = cursor.fetchall()
    projects = [dict(r) for r in rows]
    conn.close()
    return projects

def create_project(name, description, tech_stack, root_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (name, description, tech_stack, root_path) VALUES (?, ?, ?, ?)",
        (name, description, json.dumps(tech_stack), root_path)
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Seed default checklists for the project
    seed_checklists_for_project(project_id)
    
    return project_id

def update_project(project_id, name, description, tech_stack, root_path):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE projects SET name = ?, description = ?, tech_stack = ?, root_path = ? WHERE id = ?",
        (name, description, json.dumps(tech_stack), root_path, project_id)
    )
    conn.commit()
    conn.close()

def delete_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

# --- Requirements Operations ---

def get_requirements(project_id, req_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM requirements WHERE project_id = ? AND req_type = ? ORDER BY code ASC",
        (project_id, req_type)
    )
    rows = cursor.fetchall()
    reqs = [dict(r) for r in rows]
    conn.close()
    return reqs

def save_requirement(project_id, req_type, code, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if exists to update, else insert
    cursor.execute(
        "SELECT id FROM requirements WHERE project_id = ? AND req_type = ? AND code = ?",
        (project_id, req_type, code)
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE requirements SET description = ? WHERE id = ?",
            (description, row['id'])
        )
    else:
        cursor.execute(
            "INSERT INTO requirements (project_id, req_type, code, description) VALUES (?, ?, ?, ?)",
            (project_id, req_type, code, description)
        )
    conn.commit()
    conn.close()

def delete_requirement(req_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM requirements WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()

# --- DDD Entities Operations ---

def get_entities(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entities WHERE project_id = ?", (project_id,))
    rows = cursor.fetchall()
    entities = []
    for r in rows:
        d = dict(r)
        d['properties'] = json.loads(d['properties']) if d['properties'] else []
        d['methods'] = json.loads(d['methods']) if d['methods'] else []
        d['relationships'] = json.loads(d['relationships']) if d['relationships'] else []
        d['rules'] = json.loads(d['rules']) if d['rules'] else []
        entities.append(d)
    conn.close()
    return entities

def save_entity(project_id, entity_id, name, description, properties, methods, relationships, rules):
    conn = get_db_connection()
    cursor = conn.cursor()
    props_str = json.dumps(properties)
    meths_str = json.dumps(methods)
    rels_str = json.dumps(relationships)
    rules_str = json.dumps(rules)
    
    if entity_id:
        cursor.execute(
            "UPDATE entities SET name = ?, description = ?, properties = ?, methods = ?, relationships = ?, rules = ? WHERE id = ?",
            (name, description, props_str, meths_str, rels_str, rules_str, entity_id)
        )
    else:
        cursor.execute(
            "INSERT INTO entities (project_id, name, description, properties, methods, relationships, rules) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, name, description, props_str, meths_str, rels_str, rules_str)
        )
    conn.commit()
    conn.close()

def delete_entity(entity_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entities WHERE id = ?", (entity_id,))
    conn.commit()
    conn.close()

# --- Audit Steps Operations ---

def get_audit_step(project_id, step_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM audit_steps WHERE project_id = ? AND step_number = ?",
        (project_id, step_number)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_audit_step(project_id, step_number, prompt_content, response_content, completed=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM audit_steps WHERE project_id = ? AND step_number = ?",
        (project_id, step_number)
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE audit_steps SET prompt_content = ?, response_content = ?, completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (prompt_content, response_content, completed, row['id'])
        )
    else:
        cursor.execute(
            "INSERT INTO audit_steps (project_id, step_number, prompt_content, response_content, completed) VALUES (?, ?, ?, ?, ?)",
            (project_id, step_number, prompt_content, response_content, completed)
        )
    conn.commit()
    conn.close()

# --- Template Operations ---

def get_templates():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates ORDER BY name ASC")
    rows = cursor.fetchall()
    templates = {r['name']: r['content'] for r in rows}
    conn.close()
    return templates

def save_template(name, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO templates (name, content) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET content = ?",
        (name, content, content)
    )
    conn.commit()
    conn.close()

# --- Checklist Operations ---

def get_checklists(project_id, category):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM checklists WHERE project_id = ? AND category = ? ORDER BY id ASC",
        (project_id, category)
    )
    rows = cursor.fetchall()
    items = [dict(r) for r in rows]
    conn.close()
    return items

def toggle_checklist_item(item_id, is_checked):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE checklists SET is_checked = ? WHERE id = ?",
        (1 if is_checked else 0, item_id)
    )
    conn.commit()
    conn.close()

def add_custom_checklist_item(project_id, category, item_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO checklists (project_id, category, item_text, is_checked) VALUES (?, ?, ?, 0)",
        (project_id, category, item_text)
    )
    conn.commit()
    conn.close()

def delete_checklist_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM checklists WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def seed_checklists_for_project(project_id):
    default_checklists = {
        "quality": [
            "README.md claro e atualizado",
            ".env.example atualizado e com todas as variáveis necessárias",
            "Docker / docker-compose configurado e rodando localmente",
            "Testes automatizados configurados e passando",
            "CI/CD configurado (GitHub Actions ou similar)",
            "Linter e Formatter configurados (ex. ESLint, Prettier, Black)",
            "Estrutura de pastas consistente com o padrão escolhido",
            "ADRs criados para decisões importantes de design",
            "Logs estruturados implementados",
            "Tratamento global de exceções/erros ativo"
        ],
        "pr": [
            "A branch está atualizada com a branch principal",
            "Não há arquivos temporários ou de build versionados",
            "Mensagens de commit claras e seguindo Conventional Commits",
            "O código passou nos testes locais",
            "O build de produção roda sem erros",
            "Nenhuma credencial ou secret foi deixada no código",
            "Não existem trechos de código comentados sem explicação",
            "A documentação do módulo afetado foi atualizada"
        ],
        "security": [
            "Autenticação robusta (JWT, OAuth2) com expiração segura",
            "Autorização e controle de permissões (RBAC/ABAC) ativo",
            "Validação rigorosa de todos os inputs no backend (ex. Zod, Pydantic)",
            "Proteção contra SQL Injection (uso de ORM ou queries parametrizadas)",
            "Proteção contra Cross-Site Scripting (XSS) e Cross-Site Request Forgery (CSRF)",
            "Rate limit ativado nas rotas públicas críticas",
            "CORS devidamente configurado (sem wildcard '*' em produção)",
            "Secrets armazenados de forma segura (Vault, GitHub Secrets, AWS Secrets)",
            "Hash seguro de senhas usando bcrypt ou argon2",
            "Nenhuma exposição acidental de chaves de API nos logs ou respostas"
        ],
        "docs": [
            "Documentação de Arquitetura geral criada",
            "Cada módulo possui seu arquivo README explicativo",
            "Casos de uso e fluxos principais documentados",
            "API documentada com OpenAPI/Swagger",
            "Instruções claras de setup do ambiente de desenvolvimento local",
            "Documentação de deploy e variáveis de ambiente em produção"
        ],
        "test": [
            "Testes unitários cobrem as regras de negócio críticas do domínio",
            "Mocks e stubs bem isolados para serviços externos e bancos",
            "Testes de integração para verificar fluxos com o banco de dados",
            "Testes de API cobrindo caminhos felizes e tratamentos de erro",
            "Pirâmide de testes equilibrada (muitos testes unitários, alguns de integração, poucos E2E)"
        ]
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    for cat, items in default_checklists.items():
        for item in items:
            cursor.execute(
                "INSERT INTO checklists (project_id, category, item_text, is_checked) VALUES (?, ?, ?, 0)",
                (project_id, cat, item)
            )
    conn.commit()
    conn.close()
