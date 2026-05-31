# ✨ VibeArchitect

> **Design de Sistemas & Auditoria com IA — para arquitetos e desenvolvedores que levam qualidade a sério.**

VibeArchitect é uma aplicação desktop que centraliza o ciclo de vida arquitetural de projetos de software. Com ele você gerencia requisitos, modela domínios com DDD, gera prompts otimizados para auditoria com IA e acompanha checklists de qualidade — tudo em uma interface escura e fluida.

---

## Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura](#2-arquitetura)
3. [Estrutura de Pastas](#3-estrutura-de-pastas)
4. [Módulos](#4-módulos)
5. [Como Rodar Localmente](#5-como-rodar-localmente)
6. [Variáveis de Ambiente](#6-variáveis-de-ambiente)
7. [Banco de Dados](#7-banco-de-dados)
8. [Fluxos e Funcionalidades](#8-fluxos-e-funcionalidades)
9. [Testes](#9-testes)
10. [Deploy](#10-deploy)
11. [Observabilidade](#11-observabilidade)
12. [Decisões Arquiteturais (ADRs)](#12-decisões-arquiteturais-adrs)
13. [Guia de Contribuição](#13-guia-de-contribuição)

---

## 1. Visão Geral do Sistema

### Propósito

VibeArchitect é uma ferramenta de **produtividade para arquitetos e desenvolvedores** que precisam:

- Organizar e documentar a arquitetura de seus projetos.
- Modelar domínios usando **DDD** (Domain-Driven Design).
- Gerenciar **requisitos funcionais (RFs) e não-funcionais (RNFs)**.
- Executar um **fluxo de auditoria em 14 passos** com prompts prontos para IA (Claude, ChatGPT, etc.).
- Checar qualidade via **checklists** categorizados (qualidade, PR, segurança, docs, testes).

### Usuário-alvo

- Desenvolvedores back-end e full-stack.
- Arquitetos de software.
- Tech leads que precisam sistematizar revisões de código e arquitetura.

### Tecnologias

| Camada | Tecnologia |
|---|---|
| Interface | Python + CustomTkinter (dark mode, tema Catppuccin) |
| Armazenamento | SQLite (arquivo local `vibe_architect.db`) |
| Clipboard | pyperclip |
| Templates | Arquivos `.md.txt` importados automaticamente |

---

## 2. Arquitetura

VibeArchitect é uma **aplicação desktop monolítica com separação em camadas**:

```
┌────────────────────────────────────────────┐
│              main.py (UI Layer)            │
│   CustomTkinter · 6 Views · Event Driven  │
├────────────────────────────────────────────┤
│           prompt_manager.py               │
│   Template Engine · Interpolação          │
├────────────────────────────────────────────┤
│            code_analyzer.py               │
│   Folder Tree · File Reader               │
├────────────────────────────────────────────┤
│              database.py                  │
│   SQLite · CRUD · Seeding                 │
├────────────────────────────────────────────┤
│           vibe_architect.db               │
│   SQLite · 6 tabelas · FK ON              │
└────────────────────────────────────────────┘
```

### Fluxo de Dados Principal

```
Usuário seleciona projeto
        │
        ▼
UI chama database.py (get_*)
        │
        ▼
PromptManager.interpolate()
  └─ Injeta dados do projeto no template
        │
        ▼
Prompt pronto → copiado via pyperclip
        │
        ▼
Usuário cola no LLM (Claude, ChatGPT)
        │
        ▼
Resposta colada de volta → salva no audit_steps
```

### Inicialização

1. `db.init_db()` — cria as tabelas SQLite se não existirem.
2. `PromptManager.scan_and_import_templates(guia_dir)` — varre o diretório pai em busca de arquivos `*.md.txt` e os importa como templates.
3. UI é montada e o primeiro projeto da lista é selecionado automaticamente.

---

## 3. Estrutura de Pastas

```
vibe_architect/
├── main.py                  # Ponto de entrada. Toda a UI (6 views)
├── database.py              # Acesso ao banco SQLite. CRUD completo
├── prompt_manager.py        # Gerenciamento de templates e interpolação
├── code_analyzer.py         # Geração de árvore de pastas e leitura de arquivos
├── generate_docs.py         # Script utilitário para exportar docs de projeto
├── seed_meditacao.py        # Script de seed de dados de exemplo
├── vibe_architect.db        # Banco SQLite local (gerado em runtime)
└── __pycache__/             # Cache Python (ignorar no VCS)
```

**Diretório pai esperado (`GUIA/`):**

```
GUIA/
├── vibe_architect/          # Este projeto
├── *.md.txt                 # Templates de prompt (importados automaticamente)
└── [outros projetos]/       # Projetos gerenciados pelo VibeArchitect
```

---

## 4. Módulos

### `main.py` — Interface & Orquestração

Ponto de entrada da aplicação. Contém a classe `VibeArchitectApp` (subclasse de `ctk.CTk`) e todas as 6 views:

| View | Chave | Descrição |
|---|---|---|
| Dashboard | `dashboard` | Cards com métricas: entidades DDD, requisitos, passos de auditoria concluídos |
| Configurações | `config` | Edição de nome, descrição, stack tecnológica e caminho raiz do projeto |
| Modelagem DDD & Req | `ddd` | CRUD de entidades DDD (propriedades, métodos, relacionamentos, regras) e requisitos (RF/RNF) |
| Orquestrador 14 Passos | `audit` | Fluxo guiado de auditoria com IA. Gera e copia prompts, salva respostas |
| Biblioteca de Prompts | `library` | Visualização dos templates importados dos arquivos `.md.txt` |
| Checklists de Qualidade | `checklists` | Checklists categorizados: qualidade, PR, segurança, docs, testes |

**Constantes de design (paleta Catppuccin Mocha):**

```python
COLOR_BG      = "#1e1e2e"   # Fundo principal
COLOR_SIDEBAR = "#11111b"   # Sidebar
COLOR_CARD    = "#252538"   # Cards
COLOR_ACCENT  = "#89b4fa"   # Azul suave (destaques, botão ativo)
COLOR_SUCCESS = "#a6e3a1"   # Verde claro
COLOR_WARNING = "#f9e2af"   # Amarelo
COLOR_ALERT   = "#f38ba8"   # Rosa/vermelho
```

---

### `database.py` — Camada de Dados

Toda interação com SQLite. Sem ORM — queries diretas com `sqlite3`. Foreign keys habilitadas via `PRAGMA foreign_keys = ON`.

| Função | Descrição |
|---|---|
| `init_db()` | Cria todas as tabelas se não existirem |
| `get/create/update/delete_project()` | CRUD de projetos |
| `get/save/delete_requirement()` | CRUD de requisitos (RF/RNF) |
| `get/save/delete_entity()` | CRUD de entidades DDD |
| `get/save_audit_step()` | Salva progresso dos 14 passos |
| `get/save_template()` | Upsert de templates de prompt |
| `get/toggle/add/delete_checklist_item()` | CRUD de checklists |
| `seed_checklists_for_project()` | Popula checklists padrão em novo projeto |

---

### `prompt_manager.py` — Motor de Templates

Responsável por importar templates e interpolá-los com dados do projeto.

| Método | Descrição |
|---|---|
| `scan_and_import_templates(guia_dir)` | Varre `*.md.txt` no diretório GUIA e faz upsert no banco |
| `get_all_templates()` | Retorna dict `{nome: conteúdo}` de todos os templates |
| `interpolate(template, project, ...)` | Substitui placeholders com dados reais do projeto |
| `get_default_step_prompt_mapping()` | Mapeia cada um dos 14 passos ao template ideal |

**Placeholders suportados na interpolação:**

| Placeholder | Substituído por |
|---|---|
| `{PROJECT_NAME}` | Nome do projeto |
| `{PROJECT_DESC}` | Descrição do projeto |
| `{TECH_STACK}` | Stack tecnológica formatada |
| `[COLE A ÁRVORE DE PASTAS AQUI]` | Árvore gerada pelo `code_analyzer` |
| `[COLE AQUI A DESCRIÇÃO DO SEU DOMÍNIO]` | Descrição + stack + requisitos + DDD |
| `[COLE AQUI O CÓDIGO/ARQUIVO]` | Conteúdo de arquivo selecionado |
| `{EXTRA_CONTEXT}` | Contexto adicional passado pelo usuário |

---

### `code_analyzer.py` — Análise de Código

Utilitário de leitura de sistema de arquivos para alimentar os prompts.

| Função | Descrição |
|---|---|
| `generate_folder_tree(root_path, max_depth=5)` | Gera árvore textual de diretórios (estilo `tree`) |
| `read_key_config_files(root_path)` | Lê arquivos de config padrão (`package.json`, `Dockerfile`, etc.) |
| `read_file_content(absolute_path, max_chars=12000)` | Lê conteúdo de um arquivo específico (truncado) |

**Diretórios ignorados na árvore:** `.git`, `node_modules`, `venv`, `__pycache__`, `.next`, `dist`, `build`, etc.

---

### `generate_docs.py` — Exportador de Documentação

Script utilitário standalone que lê um projeto do banco e gera arquivos Markdown estruturados em:

```
<root_path>/docs/
├── product/
│   ├── vision.md
│   └── requirements.md
├── architecture/
│   └── 0001-estrutura-arquitetural.md
└── modules/
    └── <entidade>.md  (um arquivo por entidade DDD)
```

**Uso:**
```bash
python generate_docs.py
```

---

### `seed_meditacao.py` — Dados de Exemplo

Script de seed que popula o banco com dados de um projeto de exemplo ("Meditação & Promessas"). Útil para desenvolvimento e demonstração.

---

## 5. Como Rodar Localmente

### Pré-requisitos

- Python 3.10 ou superior
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repo>
cd vibe_architect

# 2. Crie um ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install customtkinter pyperclip
```

### Executar

```bash
python main.py
```

O banco `vibe_architect.db` é criado automaticamente na primeira execução.

### Templates de Prompt (opcional)

Coloque arquivos `*.md.txt` no diretório pai (`GUIA/`) para que sejam importados automaticamente como templates na inicialização. Exemplo:

```
GUIA/
├── 1.Prompt mestre para auditoria completa do sistema.md.txt
├── 2.Prompt para analisar apenas a estrutura de pastas.md.txt
└── vibe_architect/
```

---

## 6. Variáveis de Ambiente

VibeArchitect **não utiliza variáveis de ambiente**. É uma aplicação desktop local sem configuração externa.

O único caminho configurável é o `root_path` de cada projeto, definido via interface na view **Configurações**.

O caminho do banco SQLite é calculado dinamicamente:

```python
# database.py
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vibe_architect.db")
```

---

## 7. Banco de Dados

**Tecnologia:** SQLite 3 (arquivo local)  
**Localização:** `vibe_architect/vibe_architect.db`  
**Foreign Keys:** habilitadas (`PRAGMA foreign_keys = ON`)

### Modelo de Dados

```
projects
  id, name, description, tech_stack (JSON), root_path
      │
      ├── requirements
      │     id, project_id, req_type ('functional'|'non_functional'), code, description
      │
      ├── entities
      │     id, project_id, name, description
      │     properties (JSON list), methods (JSON list)
      │     relationships (JSON list), rules (JSON list)
      │
      ├── audit_steps
      │     id, project_id, step_number (1-14)
      │     prompt_content, response_content
      │     completed (0|1), updated_at
      │
      └── checklists
            id, project_id, category, item_text, is_checked

templates
  id, name (UNIQUE), content
```

### Diagrama ER Simplificado

```
projects (1) ──< requirements (N)
projects (1) ──< entities     (N)
projects (1) ──< audit_steps  (N)  [UNIQUE project_id + step_number]
projects (1) ──< checklists   (N)
templates  (independente)
```

### Checklists Padrão

Ao criar um projeto, `seed_checklists_for_project()` popula automaticamente 5 categorias:

| Categoria | Exemplos |
|---|---|
| `quality` | README atualizado, Docker configurado, CI/CD ativo |
| `pr` | Branch atualizada, sem secrets no código, commits claros |
| `security` | JWT com expiração, validação de inputs, rate limit |
| `docs` | Arquitetura documentada, API com OpenAPI/Swagger |
| `test` | Testes unitários nas regras de negócio, pirâmide equilibrada |

---

## 8. Fluxos e Funcionalidades

### Os 14 Passos de Auditoria com IA

O Orquestrador guia o usuário por um fluxo estruturado de auditoria de código com IA:

| Passo | Ação | Template Mapeado |
|---|---|---|
| 1 | Enviar Descrição do Sistema | Prompt completo e prático |
| 2 | Enviar Estrutura de Pastas | Análise de estrutura de pastas |
| 3 | Solicitar Análise Arquitetural | Prompt mestre de auditoria |
| 4 | Enviar Módulos Principais | Análise de módulo específico |
| 5 | Solicitar Análise Clean Code & SOLID | Foco em Clean Code |
| 6 | Enviar Configurações & Autenticação | Prompt de segurança |
| 7 | Solicitar Análise de Segurança | Prompt de segurança (OWASP) |
| 8 | Enviar Testes | DDD — classes e métodos |
| 9 | Solicitar Cobertura e Testabilidade | DDD — agregados e value objects |
| 10 | Enviar README / Documentações | Prompt de documentação |
| 11 | Solicitar Revisão de Documentação | Prompt de documentação |
| 12 | Solicitar Relatório Final | Relatório de auditoria 0–10 |
| 13 | Solicitar Plano de Refatoração | Prompt do dia a dia |
| 14 | Solicitar Checklist de Lições Aprendidas | Template reutilizável |

### Modelagem DDD

Na view **Modelagem DDD & Req**, para cada entidade é possível registrar:

- Nome e descrição
- Propriedades / campos
- Métodos e comportamentos
- Relacionamentos com outras entidades
- Regras de negócio e invariantes

---

## 9. Testes

Atualmente o projeto **não possui uma suíte de testes automatizados**.

### Sugestão de Cobertura Prioritária

Para quem quiser contribuir com testes, as áreas de maior valor são:

1. **`database.py`** — Testar CRUD de projetos, entidades e requisitos com banco in-memory (`:memory:`).
2. **`prompt_manager.py`** — Testar a interpolação de templates com dados mockados.
3. **`code_analyzer.py`** — Testar `generate_folder_tree` com um diretório temporário (`tmp_path` do pytest).

### Como rodar testes (quando implementados)

```bash
pip install pytest
pytest tests/
```

---

## 10. Deploy

VibeArchitect é uma aplicação **desktop local**. Não requer servidor ou infraestrutura em nuvem.

### Distribuição como Executável

Use **PyInstaller** para gerar um executável standalone:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name VibeArchitect main.py
```

O executável será gerado em `dist/VibeArchitect.exe` (Windows) ou `dist/VibeArchitect` (Linux/macOS).

> **Atenção:** O banco `vibe_architect.db` é criado no mesmo diretório do executável na primeira execução. Para distribuição, certifique-se de que o usuário tem permissão de escrita no diretório de instalação.

### Empacotamento com Templates

Para incluir os arquivos `.md.txt` de templates no pacote, adicione-os via `--add-data`:

```bash
pyinstaller --onefile --windowed \
  --add-data "*.md.txt;." \
  --name VibeArchitect main.py
```

---

## 11. Observabilidade

Atualmente o projeto usa `print()` para logging básico (visível no terminal de execução).

### Logs Existentes

| Módulo | Evento Registrado |
|---|---|
| `prompt_manager.py` | Erro ao importar template: `Error importing template {filename}: {e}` |
| `generate_docs.py` | Arquivo gerado: `Gerado: docs/product/vision.md` |
| `generate_docs.py` | Erro: projeto não encontrado |

### Melhorias Recomendadas

Para evoluir a observabilidade:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
```

Substituir todos os `print()` por `logging.info()` / `logging.error()` nos módulos de lógica (`database.py`, `prompt_manager.py`).

---

## 12. Decisões Arquiteturais (ADRs)

### ADR 001 — SQLite como banco de dados local

**Status:** Aceito

**Contexto:** A aplicação é desktop, single-user, sem necessidade de acesso concorrente ou remoto.

**Decisão:** Usar SQLite. Zero configuração, sem servidor, banco vive como arquivo único junto ao executável.

**Consequências:** Simplicidade operacional total. Limitação: não escala para uso multi-usuário ou remoto.

---

### ADR 002 — CustomTkinter como framework de UI

**Status:** Aceito

**Contexto:** Necessidade de UI desktop com tema escuro e visual moderno em Python puro, sem dependências pesadas.

**Decisão:** Usar `customtkinter`, que estende `tkinter` com suporte nativo a dark mode, widgets estilizados e tema configurável.

**Consequências:** Interface visualmente agradável com mínima dependência. Limitação: menor ecossistema que frameworks como PyQt/PySide.

---

### ADR 003 — Templates como arquivos `.md.txt` externos

**Status:** Aceito

**Contexto:** Os prompts de IA precisam ser editáveis sem recompilar o código, e devem funcionar como arquivos de texto simples para versionamento no Git.

**Decisão:** Templates vivem como arquivos `*.md.txt` no diretório GUIA e são importados automaticamente no banco SQLite na inicialização.

**Consequências:** Fácil edição e versionamento dos prompts. Importação automática garante que o banco sempre reflita os arquivos mais recentes.

---

### ADR 004 — Sem ORM (queries SQLite diretas)

**Status:** Aceito

**Contexto:** Schema simples, operações diretas, sem necessidade de migrações complexas.

**Decisão:** Usar `sqlite3` nativo do Python com queries SQL diretas.

**Consequências:** Menor overhead, sem dependência de SQLAlchemy ou similar. Trade-off: sem migrações automáticas de schema (uso de `CREATE TABLE IF NOT EXISTS`).

---

## 13. Guia de Contribuição

### Pré-requisitos

- Python 3.10+
- Git

### Setup

```bash
git clone <url-do-repo>
cd vibe_architect
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install customtkinter pyperclip
```

### Convenções de Código

- **PEP 8** para estilo Python.
- Funções de banco de dados ficam em `database.py`.
- Lógica de UI fica em `main.py`.
- Nenhuma lógica de negócio dentro dos callbacks da UI — delegar para os módulos.

### Como adicionar uma nova view

1. Crie o método `create_<nome>_frame(self)` em `VibeArchitectApp`.
2. Adicione à lista `nav_info` em `create_sidebar()`.
3. Registre no dicionário `self.frames` em `create_frames()`.
4. Implemente `update_<nome>_ui(self)` e adicione o `elif` em `refresh_frame_data()`.

### Como adicionar um novo template de prompt

Crie um arquivo `<numero>.<nome>.md.txt` no diretório `GUIA/`. Ele será importado automaticamente na próxima inicialização.

### Convenção de Commits

Usar [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: adicionar view de relatório de auditoria
fix: corrigir interpolação quando tech_stack é vazio
docs: atualizar README com instrução de deploy
refactor: mover lógica de seed para database.py
```

### Branches

| Branch | Propósito |
|---|---|
| `main` | Código estável, pronto para distribuição |
| `feat/<nome>` | Nova funcionalidade |
| `fix/<nome>` | Correção de bug |
| `docs/<nome>` | Atualizações de documentação |

### Pull Request Checklist

- [ ] Testes adicionados (quando aplicável)
- [ ] `README.md` atualizado se comportamento externo mudou
- [ ] Sem credenciais ou paths absolutos hardcoded
- [ ] UI testada manualmente: dashboard, DDD, audit, checklists

---

*Gerado em 2026-05-24 · VibeArchitect*
