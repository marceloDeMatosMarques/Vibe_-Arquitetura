import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pyperclip

# Import our custom modules
import database as db
from prompt_manager import PromptManager
import code_analyzer

# Setup CTK visual parameters
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Design Color Palette
COLOR_BG = "#1e1e2e"
COLOR_SIDEBAR = "#11111b"
COLOR_CARD = "#252538"
COLOR_TEXT_FG = "#cdd6f4"
COLOR_TEXT_MUTED = "#a6adc8"
COLOR_ACCENT = "#89b4fa"      # Soft blue
COLOR_SUCCESS = "#a6e3a1"     # Light green
COLOR_WARNING = "#f9e2af"     # Yellow
COLOR_ALERT = "#f38ba8"       # Rose red
COLOR_HOVER = "#45475a"
COLOR_BORDER = "#313244"

# 14 Steps Definitions
AUDIT_STEPS_INFO = [
    {"step": 1, "title": "1. Enviar Descrição do Sistema", "desc": "Envie o resumo do produto, personas, objetivos e escopo geral para a IA se situar."},
    {"step": 2, "title": "2. Enviar Estrutura de Pastas", "desc": "Envie a árvore de diretórios atual do seu projeto. Útil para validar modularidade."},
    {"step": 3, "title": "3. Solicitar Análise Arquitetural", "desc": "Peça uma auditoria da arquitetura geral do sistema e sua modularidade."},
    {"step": 4, "title": "4. Enviar Módulos Principais", "desc": "Envie os arquivos-chave dos seus módulos principais para auditoria detalhada."},
    {"step": 5, "title": "5. Solicitar Análise Clean Code & SOLID", "desc": "Peça uma análise aprofundada de acoplamento, coesão, Clean Code e princípios SOLID."},
    {"step": 6, "title": "6. Enviar Configurações & Autenticação", "desc": "Envie variáveis de ambiente exemplificadas, dependências e setup de segurança."},
    {"step": 7, "title": "7. Solicitar Análise de Segurança", "desc": "Peça uma auditoria com foco em vulnerabilidades comuns (OWASP, SQLi, CSRF, etc.)."},
    {"step": 8, "title": "8. Enviar Testes", "desc": "Envie a estrutura atual de testes (unitários, integração ou e2e) para validação."},
    {"step": 9, "title": "9. Solicitar Análise de Cobertura e Testabilidade", "desc": "Peça uma revisão sobre como testar melhor as regras de negócio de forma isolada."},
    {"step": 10, "title": "10. Enviar README / Documentações", "desc": "Envie os documentos de guia, ADRs ou READMEs atuais para revisão técnica."},
    {"step": 11, "title": "11. Solicitar Revisão de Documentação", "desc": "Peça uma validação se a documentação reflete fielmente o código existente."},
    {"step": 12, "title": "12. Solicitar Relatório Final", "desc": "Solicite o compilado geral de qualidade do código com uma nota de 0 a 10."},
    {"step": 13, "title": "13. Solicitar Plano de Refatoração", "desc": "Solicite o cronograma de melhorias prioritárias (curto, médio e longo prazo)."},
    {"step": 14, "title": "14. Solicitar Checklist para Próximos Projetos", "desc": "Gere uma lista de lições aprendidas e componentes reutilizáveis como templates."}
]

class VibeArchitectApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Database initialization
        db.init_db()
        
        # Scan and import templates from GUIA directory automatically on startup
        guia_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        PromptManager.scan_and_import_templates(guia_dir)

        # Configure Main Window
        self.title("VibeArchitect - Design de Sistemas & Auditoria IA")
        self.geometry("1100x750")
        self.configure(fg_color=COLOR_BG)
        
        # State variables
        self.active_project = None
        self.projects_list = []
        self.current_step = 1
        
        # UI Layout setup
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar setup
        self.create_sidebar()

        # Content frames container
        self.content_container = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Initialize content frames
        self.frames = {}
        self.create_frames()
        
        # Load project selection
        self.refresh_projects()
        
        # Select default view
        self.show_frame("dashboard")

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=240, fg_color=COLOR_SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(6, weight=1)
        
        # Logo text
        logo_label = ctk.CTkLabel(
            sidebar, 
            text="✨ VibeArchitect", 
            font=ctk.CTkFont(size=20, weight="bold"), 
            text_color=COLOR_ACCENT
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        subtitle_label = ctk.CTkLabel(
            sidebar, 
            text="Design & Auditoria Sólida", 
            font=ctk.CTkFont(size=12, slant="italic"), 
            text_color=COLOR_TEXT_MUTED
        )
        subtitle_label.grid(row=0, column=0, padx=20, pady=(45, 20), sticky="w")

        # Project Selector section
        project_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        project_frame.grid(row=1, column=0, padx=15, pady=(0, 20), sticky="ew")
        
        proj_title = ctk.CTkLabel(project_frame, text="Projeto Ativo:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_MUTED)
        proj_title.pack(anchor="w", padx=5)
        
        self.proj_combobox = ctk.CTkComboBox(project_frame, values=["Nenhum"], command=self.on_project_selected, width=200)
        self.proj_combobox.pack(pady=5)
        
        btn_new_proj = ctk.CTkButton(
            project_frame, 
            text="+ Novo Projeto", 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            height=26,
            command=self.show_new_project_dialog
        )
        btn_new_proj.pack(fill="x", pady=2)

        # Nav Buttons
        self.nav_buttons = {}
        nav_info = [
            ("dashboard", "📊 Dashboard"),
            ("config", "⚙️ Configurações"),
            ("ddd", "🧱 Modelagem DDD & Req"),
            ("audit", "🚀 Orquestrador (14 Passos)"),
            ("library", "📚 Biblioteca Prompts"),
            ("checklists", "✅ Checklists Qualidade")
        ]
        
        for i, (key, label) in enumerate(nav_info):
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                fg_color="transparent",
                text_color=COLOR_TEXT_FG,
                hover_color=COLOR_HOVER,
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=2 + i, column=0, padx=15, pady=5, sticky="ew")
            self.nav_buttons[key] = btn

    def create_frames(self):
        # Create different views
        self.frames["dashboard"] = self.create_dashboard_frame()
        self.frames["config"] = self.create_config_frame()
        self.frames["ddd"] = self.create_ddd_frame()
        self.frames["audit"] = self.create_audit_frame()
        self.frames["library"] = self.create_library_frame()
        self.frames["checklists"] = self.create_checklists_frame()
        
        # Grid all frames in the container and hide them
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

    def show_frame(self, frame_name):
        # Hide all frames
        for frame in self.frames.values():
            frame.grid_remove()
            
        # Reset nav buttons appearance
        for key, btn in self.nav_buttons.items():
            if key == frame_name:
                btn.configure(fg_color=COLOR_ACCENT, text_color="#11111b", hover_color=COLOR_ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_FG, hover_color=COLOR_HOVER)
                
        # Show chosen frame
        self.frames[frame_name].grid()
        self.refresh_frame_data(frame_name)

    def refresh_frame_data(self, frame_name):
        # Specific reload trigger when entering a view
        if frame_name == "dashboard":
            self.update_dashboard_ui()
        elif frame_name == "config":
            self.update_config_ui()
        elif frame_name == "ddd":
            self.update_ddd_ui()
        elif frame_name == "audit":
            self.update_audit_ui()
        elif frame_name == "checklists":
            self.update_checklists_ui()
        elif frame_name == "library":
            self.update_library_ui()

    def refresh_projects(self):
        self.projects_list = db.get_projects()
        names = [p["name"] for p in self.projects_list]
        if not names:
            self.proj_combobox.configure(values=["Nenhum"])
            self.proj_combobox.set("Nenhum")
            self.active_project = None
        else:
            self.proj_combobox.configure(values=names)
            if self.active_project:
                # Retain active if still in list
                matches = [p for p in self.projects_list if p["id"] == self.active_project["id"]]
                if matches:
                    self.active_project = matches[0]
                    self.proj_combobox.set(self.active_project["name"])
                else:
                    self.active_project = self.projects_list[0]
                    self.proj_combobox.set(self.active_project["name"])
            else:
                self.active_project = self.projects_list[0]
                self.proj_combobox.set(self.active_project["name"])
                
        # Trigger reload of active dashboard/frames
        self.refresh_frame_data("dashboard")

    def on_project_selected(self, val):
        if val == "Nenhum":
            self.active_project = None
        else:
            matches = [p for p in self.projects_list if p["name"] == val]
            if matches:
                self.active_project = matches[0]
        # Refresh current view
        for key, btn in self.nav_buttons.items():
            if btn.cget("fg_color") == COLOR_ACCENT:
                self.refresh_frame_data(key)
                break

    def show_new_project_dialog(self):
        # Open simple window to input project name
        dialog = ctk.CTkInputDialog(text="Digite o nome do novo projeto:", title="Novo Projeto")
        name = dialog.get_input()
        if name:
            # Create default structure fields
            default_stack = {
                "frontend": "React / Next.js",
                "backend": "Node.js / Express",
                "database": "PostgreSQL",
                "cache": "Redis",
                "messaging": "",
                "auth": "JWT / Token-based",
                "deploy": "Docker / VPS",
                "obs": ""
            }
            db.create_project(name, "Descrição do projeto...", default_stack, "")
            self.refresh_projects()
            messagebox.showinfo("Sucesso", f"Projeto '{name}' criado com sucesso!")

    # ==========================================
    # DASHBOARD VIEW
    # ==========================================
    def create_dashboard_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        
        # Header
        lbl_title = ctk.CTkLabel(frame, text="Dashboard do Projeto", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_title.pack(anchor="w", pady=(10, 5))
        
        self.lbl_active_proj_name = ctk.CTkLabel(frame, text="Sem projeto ativo", font=ctk.CTkFont(size=14, slant="italic"), text_color=COLOR_TEXT_MUTED)
        self.lbl_active_proj_name.pack(anchor="w", pady=(0, 20))
        
        # Stats container
        stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)
        
        # Stat Card 1: DDD Entities
        self.card_ddd = ctk.CTkFrame(stats_frame, fg_color=COLOR_CARD, width=180, height=100, border_width=1, border_color=COLOR_BORDER)
        self.card_ddd.pack(side="left", padx=10, expand=True, fill="both")
        self.lbl_num_entities = ctk.CTkLabel(self.card_ddd, text="0", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_ACCENT)
        self.lbl_num_entities.pack(pady=(15, 0))
        lbl_ent_desc = ctk.CTkLabel(self.card_ddd, text="Entidades DDD", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MUTED)
        lbl_ent_desc.pack(pady=(0, 15))
        
        # Stat Card 2: Requirements
        self.card_reqs = ctk.CTkFrame(stats_frame, fg_color=COLOR_CARD, width=180, height=100, border_width=1, border_color=COLOR_BORDER)
        self.card_reqs.pack(side="left", padx=10, expand=True, fill="both")
        self.lbl_num_reqs = ctk.CTkLabel(self.card_reqs, text="0", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_ACCENT)
        self.lbl_num_reqs.pack(pady=(15, 0))
        lbl_req_desc = ctk.CTkLabel(self.card_reqs, text="Requisitos Cadastrados", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MUTED)
        lbl_req_desc.pack(pady=(0, 15))
        
        # Stat Card 3: Audit Steps
        self.card_audit = ctk.CTkFrame(stats_frame, fg_color=COLOR_CARD, width=180, height=100, border_width=1, border_color=COLOR_BORDER)
        self.card_audit.pack(side="left", padx=10, expand=True, fill="both")
        self.lbl_num_audit = ctk.CTkLabel(self.card_audit, text="0 / 14", font=ctk.CTkFont(size=28, weight="bold"), text_color=COLOR_SUCCESS)
        self.lbl_num_audit.pack(pady=(15, 0))
        lbl_aud_desc = ctk.CTkLabel(self.card_audit, text="Etapas Concluídas", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_MUTED)
        lbl_aud_desc.pack(pady=(0, 15))

        # Progress bar
        self.progressbar = ctk.CTkProgressBar(frame, width=400, height=12, progress_color=COLOR_SUCCESS)
        self.progressbar.pack(pady=20)
        self.progressbar.set(0)

        # Quick actions panel
        actions_frame = ctk.CTkFrame(frame, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
        actions_frame.pack(fill="x", pady=20, padx=10)
        
        actions_title = ctk.CTkLabel(actions_frame, text="Ações Rápidas & Utilitários", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT)
        actions_title.pack(anchor="w", padx=15, pady=(10, 2))
        
        actions_inner = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions_inner.pack(padx=20, pady=(0, 15))
        
        btn_gen_docs = ctk.CTkButton(
            actions_inner, 
            text="📁 Gerar Documentação DDD", 
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#5fa0f0",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.export_ddd_docs
        )
        btn_gen_docs.pack(side="left", padx=15)
        
        btn_scan_guia = ctk.CTkButton(
            actions_inner, 
            text="🔄 Recarregar Pasta GUIA", 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.trigger_guia_scan
        )
        btn_scan_guia.pack(side="left", padx=15)
        
        btn_view_audit = ctk.CTkButton(
            actions_inner, 
            text="🚀 Ir Para Auditoria", 
            fg_color=COLOR_SUCCESS,
            text_color="#11111b",
            hover_color="#8ed088",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.show_frame("audit")
        )
        btn_view_audit.pack(side="left", padx=15)
        
        # Details panel
        self.txt_project_summary = ctk.CTkTextbox(frame, height=160, font=ctk.CTkFont(size=13), border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_SIDEBAR)
        self.txt_project_summary.pack(fill="both", expand=True, pady=10, padx=10)
        
        return frame

    def update_dashboard_ui(self):
        if not self.active_project:
            self.lbl_active_proj_name.configure(text="Nenhum projeto ativo selecionado. Crie ou selecione um projeto.")
            self.lbl_num_entities.configure(text="0")
            self.lbl_num_reqs.configure(text="0")
            self.lbl_num_audit.configure(text="0 / 14")
            self.progressbar.set(0)
            self.txt_project_summary.configure(state="normal")
            self.txt_project_summary.delete("1.0", "end")
            self.txt_project_summary.insert("end", "Selecione ou crie um projeto usando o menu lateral para iniciar.")
            self.txt_project_summary.configure(state="disabled")
            return
            
        p = self.active_project
        self.lbl_active_proj_name.configure(text=f"Diretório: {p['root_path'] or 'Não configurado'}")
        
        # Load counts
        ents = db.get_entities(p["id"])
        self.lbl_num_entities.configure(text=str(len(ents)))
        
        reqs_f = db.get_requirements(p["id"], "functional")
        reqs_nf = db.get_requirements(p["id"], "non_functional")
        self.lbl_num_reqs.configure(text=str(len(reqs_f) + len(reqs_nf)))
        
        # Audit steps completed
        completed_steps = 0
        for step in range(1, 15):
            step_data = db.get_audit_step(p["id"], step)
            if step_data and step_data.get("completed") == 1:
                completed_steps += 1
                
        self.lbl_num_audit.configure(text=f"{completed_steps} / 14")
        self.progressbar.set(completed_steps / 14)
        
        # Details text
        summary = f"=== RESUMO DO PROJETO: {p['name']} ===\n\n"
        summary += f"Descrição: {p['description']}\n\n"
        
        # Stack
        try:
            stack = json.loads(p["tech_stack"])
            summary += "Stack Tecnológica Cadastrada:\n"
            for k, v in stack.items():
                if v:
                    summary += f"  - {k.capitalize()}: {v}\n"
        except:
            summary += f"Stack: {p['tech_stack']}\n"
            
        summary += f"\nEntidades DDD de Domínio ({len(ents)}):\n"
        for ent in ents:
            summary += f"  * {ent['name']}: {ent['description']} (Propriedades: {', '.join(ent['properties'])})\n"
            
        self.txt_project_summary.configure(state="normal")
        self.txt_project_summary.delete("1.0", "end")
        self.txt_project_summary.insert("end", summary)
        self.txt_project_summary.configure(state="disabled")

    def trigger_guia_scan(self):
        guia_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        count = PromptManager.scan_and_import_templates(guia_dir)
        messagebox.showinfo("Scan Concluído", f"Escaneamento de templates concluído.\n{count} templates de prompt importados/atualizados.")

    def export_ddd_docs(self):
        if not self.active_project:
            messagebox.showwarning("Aviso", "Selecione um projeto ativo primeiro.")
            return
            
        p = self.active_project
        if not p["root_path"] or not os.path.exists(p["root_path"]):
            messagebox.showwarning("Aviso", "Por favor, configure uma pasta de destino válida para o projeto nas Configurações.")
            self.show_frame("config")
            return
            
        root_dir = p["root_path"]
        
        # Setup paths
        docs_dir = os.path.join(root_dir, "docs")
        product_dir = os.path.join(docs_dir, "product")
        arch_dir = os.path.join(docs_dir, "architecture")
        modules_dir = os.path.join(docs_dir, "modules")
        
        # Create dirs
        os.makedirs(product_dir, exist_ok=True)
        os.makedirs(arch_dir, exist_ok=True)
        os.makedirs(modules_dir, exist_ok=True)
        
        # Create Vision.md
        vision_content = f"""# Visão do Produto - {p['name']}

## Descrição Geral
{p['description']}

## Tecnologias Envolvidas
"""
        try:
            stack = json.loads(p["tech_stack"])
            for k, v in stack.items():
                if v:
                    vision_content += f"- **{k.capitalize()}**: {v}\n"
        except:
            vision_content += f"{p['tech_stack']}\n"
            
        with open(os.path.join(product_dir, "vision.md"), "w", encoding="utf-8") as f:
            f.write(vision_content)
            
        # Create requirements.md
        reqs_f = db.get_requirements(p["id"], "functional")
        reqs_nf = db.get_requirements(p["id"], "non_functional")
        
        reqs_content = f"# Requisitos do Sistema - {p['name']}\n\n"
        reqs_content += "## Requisitos Funcionais (RFs)\n"
        for r in reqs_f:
            reqs_content += f"- **{r['code']}**: {r['description']}\n"
            
        reqs_content += "\n## Requisitos Não Funcionais (RNFs)\n"
        for r in reqs_nf:
            reqs_content += f"- **{r['code']}**: {r['description']}\n"
            
        with open(os.path.join(product_dir, "requirements.md"), "w", encoding="utf-8") as f:
            f.write(reqs_content)
        # Duplicate to root docs folder for easier discovery
        with open(os.path.join(docs_dir, "requirements.md"), "w", encoding="utf-8") as f:
            f.write(reqs_content)
            
        # Create Domain modules
        ents = db.get_entities(p["id"])
        for ent in ents:
            ent_content = f"""# Módulo / Entidade: {ent['name']}

## Objetivo / Descrição
{ent['description']}

## Propriedades / Campos
"""
            for prop in ent['properties']:
                ent_content += f"- {prop}\n"
                
            ent_content += "\n## Métodos e Comportamentos\n"
            for meth in ent['methods']:
                ent_content += f"- {meth}\n"
                
            ent_content += "\n## Relacionamentos\n"
            for rel in ent['relationships']:
                ent_content += f"- {rel}\n"
                
            ent_content += "\n## Regras de Negócio e Invariantes\n"
            for rule in ent['rules']:
                ent_content += f"- {rule}\n"
                
            filename = f"{ent['name'].lower().replace(' ', '_')}.md"
            with open(os.path.join(modules_dir, filename), "w", encoding="utf-8") as f:
                f.write(ent_content)
                
        # Write ADR template
        adr_template = """# ADR 0001 - Decisão Inicial de Arquitetura

## Status
Aceito

## Contexto
Definição da estrutura modular inicial do sistema.

## Decisão
Adotar estrutura modular focada em desacoplamento e Domain-Driven Design (DDD).

## Consequências
- Alta coesão
- Facilidade em testar regras de negócio
- Modularidade estrita
"""
        with open(os.path.join(arch_dir, "0001-estrutura-arquitetural.md"), "w", encoding="utf-8") as f:
            f.write(adr_template)

        messagebox.showinfo("Exportação Concluída", f"Documentos exportados com sucesso para a pasta:\n{docs_dir}")

    # ==========================================
    # CONFIGURATIONS VIEW
    # ==========================================
    def create_config_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        
        # Scrollable container for forms
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, pady=10)
        
        lbl_title = ctk.CTkLabel(scroll, text="Configurações do Projeto", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_title.pack(anchor="w", pady=(10, 15))
        
        # Name Entry
        lbl_name = ctk.CTkLabel(scroll, text="Nome do Projeto:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_name.pack(anchor="w", pady=(5, 2))
        self.entry_name = ctk.CTkEntry(scroll, width=400)
        self.entry_name.pack(anchor="w", pady=(0, 10))
        
        # Description
        lbl_desc = ctk.CTkLabel(scroll, text="Descrição / Visão Geral:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_desc.pack(anchor="w", pady=(5, 2))
        self.txt_desc = ctk.CTkTextbox(scroll, height=80, width=500, border_width=1, border_color=COLOR_BORDER)
        self.txt_desc.pack(anchor="w", pady=(0, 10))
        
        # Path Folder Selector
        lbl_path = ctk.CTkLabel(scroll, text="Pasta Raiz do Projeto (Onde o código está localizado):", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_path.pack(anchor="w", pady=(5, 2))
        
        path_select_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        path_select_frame.pack(anchor="w", fill="x", pady=(0, 10))
        
        self.entry_root_path = ctk.CTkEntry(path_select_frame, width=400)
        self.entry_root_path.pack(side="left")
        
        btn_browse = ctk.CTkButton(
            path_select_frame, 
            text="Selecionar Pasta", 
            width=100, 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.browse_root_folder
        )
        btn_browse.pack(side="left", padx=10)
        
        # Tech Stack inputs
        lbl_stack = ctk.CTkLabel(scroll, text="Stack Tecnológica do Projeto", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT)
        lbl_stack.pack(anchor="w", pady=(15, 10))
        
        stack_frame = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
        stack_frame.pack(anchor="w", fill="x", pady=5)
        
        self.stack_entries = {}
        fields = [
            ("frontend", "Frontend (ex: Next.js, React, Tailwind):"),
            ("backend", "Backend / API Framework (ex: NestJS, FastAPI):"),
            ("database", "Banco de Dados Principal (ex: PostgreSQL, MySQL):"),
            ("cache", "Mecanismo de Cache (ex: Redis):"),
            ("messaging", "Filas / Mensageria (ex: RabbitMQ, Kafka):"),
            ("auth", "Autenticação & Autorização (ex: JWT, OAuth2):"),
            ("deploy", "Ambiente de Deploy & CI/CD (ex: Docker, GH Actions):"),
            ("obs", "Métricas & Observabilidade (ex: Sentry, Grafana):")
        ]
        
        for k, label_text in fields:
            lbl = ctk.CTkLabel(stack_frame, text=label_text, font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
            lbl.pack(anchor="w", padx=15, pady=(5, 2))
            ent = ctk.CTkEntry(stack_frame, width=450)
            ent.pack(anchor="w", padx=15, pady=(0, 5))
            self.stack_entries[k] = ent
            
        # Action Buttons
        actions = ctk.CTkFrame(scroll, fg_color="transparent")
        actions.pack(anchor="w", pady=20)
        
        btn_save = ctk.CTkButton(
            actions, 
            text="💾 Salvar Configurações", 
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#5fa0f0",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.save_project_config
        )
        btn_save.pack(side="left")
        
        btn_delete = ctk.CTkButton(
            actions, 
            text="🗑️ Excluir Projeto", 
            fg_color=COLOR_ALERT,
            text_color="#11111b",
            hover_color="#ea7a88",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.delete_current_project
        )
        btn_delete.pack(side="left", padx=15)
        
        return frame

    def update_config_ui(self):
        if not self.active_project:
            self.entry_name.delete(0, "end")
            self.txt_desc.delete("1.0", "end")
            self.entry_root_path.delete(0, "end")
            for ent in self.stack_entries.values():
                ent.delete(0, "end")
            return
            
        p = self.active_project
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, p["name"])
        
        self.txt_desc.delete("1.0", "end")
        self.txt_desc.insert("1.0", p["description"] or "")
        
        self.entry_root_path.delete(0, "end")
        self.entry_root_path.insert(0, p["root_path"] or "")
        
        try:
            stack = json.loads(p["tech_stack"])
        except:
            stack = {}
            
        for k, ent in self.stack_entries.items():
            ent.delete(0, "end")
            ent.insert(0, stack.get(k, ""))

    def browse_root_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_root_path.delete(0, "end")
            self.entry_root_path.insert(0, folder)

    def save_project_config(self):
        if not self.active_project:
            messagebox.showwarning("Aviso", "Nenhum projeto ativo para salvar.")
            return
            
        name = self.entry_name.get()
        desc = self.txt_desc.get("1.0", "end-1c")
        root = self.entry_root_path.get()
        
        stack = {}
        for k, ent in self.stack_entries.items():
            stack[k] = ent.get()
            
        db.update_project(self.active_project["id"], name, desc, stack, root)
        self.refresh_projects()
        messagebox.showinfo("Sucesso", "Configurações do projeto salvas com sucesso!")

    def delete_current_project(self):
        if not self.active_project:
            return
        
        confirm = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir o projeto '{self.active_project['name']}'?\nEsta ação é irreversível."
        )
        if confirm:
            db.delete_project(self.active_project["id"])
            self.active_project = None
            self.refresh_projects()
            self.show_frame("dashboard")

    # ==========================================
    # REQUIREMENTS AND DDD VIEW
    # ==========================================
    def create_ddd_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        
        lbl_title = ctk.CTkLabel(frame, text="Requisitos & Modelagem de Domínio DDD", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_title.pack(anchor="w", pady=(10, 10))
        
        # Sub Tabs
        self.ddd_tabs = ctk.CTkTabview(frame)
        self.ddd_tabs.pack(fill="both", expand=True)
        
        tab_reqs = self.ddd_tabs.add("📋 Requisitos")
        tab_entities = self.ddd_tabs.add("🧱 Entidades DDD")
        
        # --- TAB: REQUIREMENTS ---
        tab_reqs.grid_columnconfigure(0, weight=1)
        tab_reqs.grid_columnconfigure(1, weight=1)
        tab_reqs.grid_rowconfigure(0, weight=1)
        
        # Left side: Form
        req_form = ctk.CTkFrame(tab_reqs, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
        req_form.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        lbl_rf_title = ctk.CTkLabel(req_form, text="Adicionar Requisito", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT)
        lbl_rf_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        lbl_r_type = ctk.CTkLabel(req_form, text="Tipo de Requisito:", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_r_type.pack(anchor="w", padx=15, pady=(5, 2))
        self.combo_req_type = ctk.CTkComboBox(req_form, values=["Funcional (RF)", "Não Funcional (RNF)"])
        self.combo_req_type.pack(anchor="w", padx=15, pady=(0, 10))
        
        lbl_r_code = ctk.CTkLabel(req_form, text="Código (ex: RF01, RNF01):", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_r_code.pack(anchor="w", padx=15, pady=(5, 2))
        self.entry_req_code = ctk.CTkEntry(req_form, width=120)
        self.entry_req_code.pack(anchor="w", padx=15, pady=(0, 10))
        
        lbl_r_desc = ctk.CTkLabel(req_form, text="Descrição / Regra:", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_r_desc.pack(anchor="w", padx=15, pady=(5, 2))
        self.txt_req_desc = ctk.CTkTextbox(req_form, height=100, width=280, border_width=1, border_color=COLOR_BORDER)
        self.txt_req_desc.pack(anchor="w", padx=15, pady=(0, 15))
        
        btn_save_req = ctk.CTkButton(
            req_form, 
            text="Adicionar Requisito", 
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#5fa0f0",
            font=ctk.CTkFont(weight="bold"),
            command=self.save_requirement_item
        )
        btn_save_req.pack(anchor="w", padx=15, pady=10)
        
        # Right side: Requirements List
        req_list_container = ctk.CTkFrame(tab_reqs, fg_color="transparent")
        req_list_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        lbl_list_title = ctk.CTkLabel(req_list_container, text="Requisitos Cadastrados", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_list_title.pack(anchor="w", pady=5)
        
        self.reqs_scroll_frame = ctk.CTkScrollableFrame(req_list_container, fg_color=COLOR_SIDEBAR, border_width=1, border_color=COLOR_BORDER)
        self.reqs_scroll_frame.pack(fill="both", expand=True)

        # --- TAB: DDD ENTITIES ---
        tab_entities.grid_columnconfigure(0, weight=1)
        tab_entities.grid_columnconfigure(1, weight=1)
        tab_entities.grid_rowconfigure(0, weight=1)
        
        # Left side: Entity Form
        ent_form = ctk.CTkScrollableFrame(tab_entities, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
        ent_form.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        lbl_ent_title = ctk.CTkLabel(ent_form, text="Definir Entidade / Agregado", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT)
        lbl_ent_title.pack(anchor="w", padx=10, pady=(10, 10))
        
        self.active_entity_id = None
        
        lbl_e_name = ctk.CTkLabel(ent_form, text="Nome da Entidade:", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_e_name.pack(anchor="w", padx=10, pady=(5, 2))
        self.entry_ent_name = ctk.CTkEntry(ent_form, width=280)
        self.entry_ent_name.pack(anchor="w", padx=10, pady=(0, 10))
        
        lbl_e_desc = ctk.CTkLabel(ent_form, text="Descrição / Objetivo:", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_e_desc.pack(anchor="w", padx=10, pady=(5, 2))
        self.txt_ent_desc = ctk.CTkTextbox(ent_form, height=60, width=280, border_width=1, border_color=COLOR_BORDER)
        self.txt_ent_desc.pack(anchor="w", padx=10, pady=(0, 10))
        
        lbl_e_props = ctk.CTkLabel(ent_form, text="Propriedades / Campos (separados por vírgula):", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_e_props.pack(anchor="w", padx=10, pady=(5, 2))
        self.entry_ent_props = ctk.CTkEntry(ent_form, width=280)
        self.entry_ent_props.pack(anchor="w", padx=10, pady=(0, 10))
        
        lbl_e_meths = ctk.CTkLabel(ent_form, text="Métodos de Negócio (separados por vírgula):", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_e_meths.pack(anchor="w", padx=10, pady=(5, 2))
        self.entry_ent_meths = ctk.CTkEntry(ent_form, width=280)
        self.entry_ent_meths.pack(anchor="w", padx=10, pady=(0, 10))
        
        lbl_e_rels = ctk.CTkLabel(ent_form, text="Relacionamentos (separados por vírgula):", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_e_rels.pack(anchor="w", padx=10, pady=(5, 2))
        self.entry_ent_rels = ctk.CTkEntry(ent_form, width=280)
        self.entry_ent_rels.pack(anchor="w", padx=10, pady=(0, 10))
        
        lbl_e_rules = ctk.CTkLabel(ent_form, text="Regras de Negócio (separadas por vírgula):", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_e_rules.pack(anchor="w", padx=10, pady=(5, 2))
        self.entry_ent_rules = ctk.CTkEntry(ent_form, width=280)
        self.entry_ent_rules.pack(anchor="w", padx=10, pady=(0, 15))
        
        ent_actions = ctk.CTkFrame(ent_form, fg_color="transparent")
        ent_actions.pack(anchor="w", padx=10, pady=5)
        
        btn_save_ent = ctk.CTkButton(
            ent_actions, 
            text="Salvar Entidade", 
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#5fa0f0",
            font=ctk.CTkFont(weight="bold"),
            command=self.save_entity_item
        )
        btn_save_ent.pack(side="left")
        
        self.btn_clear_ent_form = ctk.CTkButton(
            ent_actions, 
            text="Limpar", 
            width=70, 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.clear_entity_form
        )
        self.btn_clear_ent_form.pack(side="left", padx=10)
        
        # Right side: Entities List
        ent_list_container = ctk.CTkFrame(tab_entities, fg_color="transparent")
        ent_list_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        lbl_ent_list = ctk.CTkLabel(ent_list_container, text="Entidades Cadastradas", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_ent_list.pack(anchor="w", pady=5)
        
        self.entities_scroll_frame = ctk.CTkScrollableFrame(ent_list_container, fg_color=COLOR_SIDEBAR, border_width=1, border_color=COLOR_BORDER)
        self.entities_scroll_frame.pack(fill="both", expand=True)
        
        return frame

    def update_ddd_ui(self):
        # Refresh lists
        self.refresh_requirements_list()
        self.refresh_entities_list()

    # --- Requirements Logic ---
    def save_requirement_item(self):
        if not self.active_project:
            return
        
        req_type_text = self.combo_req_type.get()
        req_type = "functional" if "Funcional" in req_type_text else "non_functional"
        code = self.entry_req_code.get().strip()
        desc = self.txt_req_desc.get("1.0", "end-1c").strip()
        
        if not code or not desc:
            messagebox.showwarning("Aviso", "Preencha o código e a descrição do requisito.")
            return
            
        db.save_requirement(self.active_project["id"], req_type, code, desc)
        
        # Clear fields
        self.entry_req_code.delete(0, "end")
        self.txt_req_desc.delete("1.0", "end")
        
        self.refresh_requirements_list()

    def refresh_requirements_list(self):
        # Clear frame
        for widget in self.reqs_scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.active_project:
            return
            
        reqs_f = db.get_requirements(self.active_project["id"], "functional")
        reqs_nf = db.get_requirements(self.active_project["id"], "non_functional")
        
        def render_section(title, items):
            lbl_sect = ctk.CTkLabel(self.reqs_scroll_frame, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_ACCENT)
            lbl_sect.pack(anchor="w", pady=(10, 5), padx=5)
            
            if not items:
                lbl_none = ctk.CTkLabel(self.reqs_scroll_frame, text="Nenhum requisito cadastrado.", font=ctk.CTkFont(size=11, slant="italic"), text_color=COLOR_TEXT_MUTED)
                lbl_none.pack(anchor="w", padx=15)
                return
                
            for item in items:
                row_f = ctk.CTkFrame(self.reqs_scroll_frame, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
                row_f.pack(fill="x", pady=3, padx=5)
                
                txt_lbl = ctk.CTkLabel(row_f, text=f"[{item['code']}] {item['description']}", wraplength=260, justify="left", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
                txt_lbl.pack(side="left", padx=10, pady=8, fill="both", expand=True)
                
                btn_del = ctk.CTkButton(
                    row_f, 
                    text="❌", 
                    width=25, 
                    height=25, 
                    fg_color="transparent", 
                    text_color=COLOR_ALERT, 
                    hover_color=COLOR_HOVER,
                    command=lambda r_id=item['id']: self.delete_requirement_item(r_id)
                )
                btn_del.pack(side="right", padx=5)
                
        render_section("Requisitos Funcionais (RFs):", reqs_f)
        render_section("Requisitos Não Funcionais (RNFs):", reqs_nf)

    def delete_requirement_item(self, req_id):
        db.delete_requirement(req_id)
        self.refresh_requirements_list()

    # --- Entities Logic ---
    def save_entity_item(self):
        if not self.active_project:
            return
            
        name = self.entry_ent_name.get().strip()
        desc = self.txt_ent_desc.get("1.0", "end-1c").strip()
        props = [p.strip() for p in self.entry_ent_props.get().split(",") if p.strip()]
        meths = [m.strip() for m in self.entry_ent_meths.get().split(",") if m.strip()]
        rels = [r.strip() for r in self.entry_ent_rels.get().split(",") if r.strip()]
        rules = [r.strip() for r in self.entry_ent_rules.get().split(",") if r.strip()]
        
        if not name or not desc:
            messagebox.showwarning("Aviso", "Preencha o nome e a descrição da entidade.")
            return
            
        db.save_entity(
            self.active_project["id"], 
            self.active_entity_id, 
            name, desc, props, meths, rels, rules
        )
        
        self.clear_entity_form()
        self.refresh_entities_list()

    def clear_entity_form(self):
        self.active_entity_id = None
        self.entry_ent_name.delete(0, "end")
        self.txt_ent_desc.delete("1.0", "end")
        self.entry_ent_props.delete(0, "end")
        self.entry_ent_meths.delete(0, "end")
        self.entry_ent_rels.delete(0, "end")
        self.entry_ent_rules.delete(0, "end")
        self.btn_clear_ent_form.configure(text="Limpar")

    def edit_entity_item(self, item):
        self.active_entity_id = item["id"]
        
        self.entry_ent_name.delete(0, "end")
        self.entry_ent_name.insert(0, item["name"])
        
        self.txt_ent_desc.delete("1.0", "end")
        self.txt_ent_desc.insert("1.0", item["description"])
        
        self.entry_ent_props.delete(0, "end")
        self.entry_ent_props.insert(0, ", ".join(item["properties"]))
        
        self.entry_ent_meths.delete(0, "end")
        self.entry_ent_meths.insert(0, ", ".join(item["methods"]))
        
        self.entry_ent_rels.delete(0, "end")
        self.entry_ent_rels.insert(0, ", ".join(item["relationships"]))
        
        self.entry_ent_rules.delete(0, "end")
        self.entry_ent_rules.insert(0, ", ".join(item["rules"]))
        
        self.btn_clear_ent_form.configure(text="Cancelar")

    def refresh_entities_list(self):
        # Clear list frame
        for widget in self.entities_scroll_frame.winfo_children():
            widget.destroy()
            
        if not self.active_project:
            return
            
        ents = db.get_entities(self.active_project["id"])
        if not ents:
            lbl_none = ctk.CTkLabel(self.entities_scroll_frame, text="Nenhuma entidade modelada.", font=ctk.CTkFont(size=11, slant="italic"), text_color=COLOR_TEXT_MUTED)
            lbl_none.pack(anchor="w", padx=15, pady=10)
            return
            
        for item in ents:
            box = ctk.CTkFrame(self.entities_scroll_frame, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
            box.pack(fill="x", pady=5, padx=5)
            
            # Header
            lbl_name = ctk.CTkLabel(box, text=item["name"], font=ctk.CTkFont(size=13, weight="bold"), text_color=COLOR_ACCENT)
            lbl_name.pack(anchor="w", padx=12, pady=(8, 2))
            
            lbl_desc = ctk.CTkLabel(box, text=item["description"], font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG, wraplength=250, justify="left")
            lbl_desc.pack(anchor="w", padx=12, pady=(0, 5))
            
            # Details preview
            details = f"Propriedades: {', '.join(item['properties'])}\n"
            details += f"Métodos: {', '.join(item['methods'])}\n"
            details += f"Regras: {', '.join(item['rules'])}"
            
            lbl_details = ctk.CTkLabel(box, text=details, font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_MUTED, justify="left", wraplength=250)
            lbl_details.pack(anchor="w", padx=12, pady=(2, 8))
            
            # Buttons row
            btn_row = ctk.CTkFrame(box, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(0, 8))
            
            btn_edit = ctk.CTkButton(
                btn_row, 
                text="✏️ Editar", 
                width=60, 
                height=24, 
                fg_color=COLOR_BORDER,
                hover_color=COLOR_HOVER,
                text_color=COLOR_TEXT_FG,
                font=ctk.CTkFont(size=10),
                command=lambda val=item: self.edit_entity_item(val)
            )
            btn_edit.pack(side="left")
            
            btn_del = ctk.CTkButton(
                btn_row, 
                text="🗑️ Excluir", 
                width=60, 
                height=24, 
                fg_color="transparent", 
                text_color=COLOR_ALERT, 
                hover_color=COLOR_HOVER,
                font=ctk.CTkFont(size=10),
                command=lambda ent_id=item['id']: self.delete_entity_item(ent_id)
            )
            btn_del.pack(side="left", padx=10)

    def delete_entity_item(self, ent_id):
        db.delete_entity(ent_id)
        self.refresh_entities_list()

    # ==========================================
    # WORKFLOW AUDIT ORCHESTRATOR VIEW
    # ==========================================
    def create_audit_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        
        # Header Step Navigator
        nav_header = ctk.CTkFrame(frame, fg_color=COLOR_SIDEBAR, height=60, border_width=1, border_color=COLOR_BORDER)
        nav_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        nav_header.grid_columnconfigure(1, weight=1)
        
        btn_prev = ctk.CTkButton(
            nav_header, 
            text="◀ Ant", 
            width=60, 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.prev_audit_step
        )
        btn_prev.pack(side="left", padx=10, pady=10)
        
        self.step_options = [f"Passo {s['step']}: {s['title']}" for s in AUDIT_STEPS_INFO]
        self.combo_step_select = ctk.CTkComboBox(nav_header, values=self.step_options, width=320, command=self.on_step_combobox_changed)
        self.combo_step_select.pack(side="left", padx=10, pady=10)
        
        btn_next = ctk.CTkButton(
            nav_header, 
            text="Próx ▶", 
            width=60, 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.next_audit_step
        )
        btn_next.pack(side="left", padx=10, pady=10)
        
        self.lbl_step_status = ctk.CTkLabel(nav_header, text="PENDENTE", font=ctk.CTkFont(weight="bold"), text_color=COLOR_ALERT)
        self.lbl_step_status.pack(side="right", padx=15)
        
        # Instructions Label
        self.lbl_step_desc = ctk.CTkLabel(
            frame, 
            text="Descrição da etapa de auditoria...", 
            font=ctk.CTkFont(size=12, slant="italic"), 
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
            justify="left"
        )
        self.lbl_step_desc.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Split Pane for Prompt & Response
        panes = ctk.CTkFrame(frame, fg_color="transparent")
        panes.grid(row=2, column=0, sticky="nsew")
        panes.grid_columnconfigure(0, weight=1)
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(0, weight=1)
        
        # Left Side: Generated Prompt & Context Injector
        prompt_box = ctk.CTkFrame(panes, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
        prompt_box.grid(row=0, column=0, sticky="nsew", padx=5)
        prompt_box.grid_rowconfigure(1, weight=1)
        
        # Top tools
        ptools = ctk.CTkFrame(prompt_box, fg_color="transparent")
        ptools.pack(fill="x", padx=10, pady=5)
        
        # Combobox of templates
        self.combo_prompt_template = ctk.CTkComboBox(ptools, values=["Padrão"], width=200, command=self.on_template_selected_changed)
        self.combo_prompt_template.pack(side="left", pady=5)
        
        self.btn_copy_prompt = ctk.CTkButton(
            ptools, 
            text="📋 Copiar Prompt", 
            fg_color=COLOR_SUCCESS,
            text_color="#11111b",
            hover_color="#8ed088",
            font=ctk.CTkFont(weight="bold"),
            command=self.copy_active_prompt
        )
        self.btn_copy_prompt.pack(side="right", padx=5, pady=5)
        
        btn_refresh_prompt = ctk.CTkButton(
            ptools, 
            text="🔄 Recarregar", 
            width=70, 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.refresh_generated_prompt
        )
        btn_refresh_prompt.pack(side="right", padx=5, pady=5)
        
        # Main text view
        self.txt_generated_prompt = ctk.CTkTextbox(prompt_box, font=ctk.CTkFont(family="Consolas", size=11), border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_SIDEBAR)
        self.txt_generated_prompt.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Bottom context injector
        context_frame = ctk.CTkFrame(prompt_box, fg_color="transparent")
        context_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        lbl_ctx = ctk.CTkLabel(context_frame, text="Injetar Contexto / Código de Módulo:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_ctx.pack(anchor="w")
        
        ctx_row = ctk.CTkFrame(context_frame, fg_color="transparent")
        ctx_row.pack(fill="x", pady=2)
        
        self.entry_context_filepath = ctk.CTkEntry(ctx_row, placeholder_text="caminho/do/arquivo.ts ou deixe em branco para colar texto", width=220)
        self.entry_context_filepath.pack(side="left", fill="x", expand=True)
        
        btn_browse_ctx = ctk.CTkButton(
            ctx_row, 
            text="Selecionar", 
            width=70, 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.browse_context_file
        )
        btn_browse_ctx.pack(side="left", padx=5)
        
        btn_load_configs = ctk.CTkButton(
            ctx_row, 
            text="Configurações", 
            width=80, 
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#5fa0f0",
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self.inject_project_configs
        )
        btn_load_configs.pack(side="left", padx=2)
        
        self.txt_extra_context = ctk.CTkTextbox(context_frame, height=90, font=ctk.CTkFont(family="Consolas", size=10), border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_SIDEBAR)
        self.txt_extra_context.pack(fill="x", pady=5)
        
        # Right Side: AI Response Editor & Saver
        response_box = ctk.CTkFrame(panes, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
        response_box.grid(row=0, column=1, sticky="nsew", padx=5)
        response_box.grid_rowconfigure(1, weight=1)
        
        rtools = ctk.CTkFrame(response_box, fg_color="transparent")
        rtools.pack(fill="x", padx=10, pady=5)
        
        lbl_r_title = ctk.CTkLabel(rtools, text="Resposta da Auditoria Técnica da IA", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_r_title.pack(side="left", pady=5)
        
        btn_save_response = ctk.CTkButton(
            rtools, 
            text="💾 Salvar Resposta & Concluir", 
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#5fa0f0",
            font=ctk.CTkFont(weight="bold"),
            command=self.save_current_audit_step
        )
        btn_save_response.pack(side="right", pady=5)
        
        self.txt_ai_response = ctk.CTkTextbox(response_box, font=ctk.CTkFont(size=12), border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_SIDEBAR)
        self.txt_ai_response.pack(fill="both", expand=True, padx=10, pady=(5, 15))
        
        return frame

    def update_audit_ui(self):
        if not self.active_project:
            self.lbl_step_status.configure(text="SEM PROJETO", text_color=COLOR_TEXT_MUTED)
            self.txt_generated_prompt.configure(state="normal")
            self.txt_generated_prompt.delete("1.0", "end")
            self.txt_generated_prompt.insert("end", "Crie ou selecione um projeto ativo para iniciar o fluxo.")
            self.txt_generated_prompt.configure(state="disabled")
            self.txt_ai_response.delete("1.0", "end")
            return
            
        step_info = AUDIT_STEPS_INFO[self.current_step - 1]
        self.combo_step_select.set(self.step_options[self.current_step - 1])
        self.lbl_step_desc.configure(text=step_info["desc"])
        
        # Load templates in dropdown
        templates = PromptManager.get_all_templates()
        template_names = list(templates.keys())
        self.combo_prompt_template.configure(values=template_names)
        
        # Find and preset standard template for this step if matching
        mapping = PromptManager.get_default_step_prompt_mapping()
        preferred_prefix = mapping.get(self.current_step, "")
        
        selected_template = "Nenhum"
        for tname in template_names:
            if tname.startswith(preferred_prefix) or preferred_prefix.startswith(tname):
                selected_template = tname
                break
                
        if selected_template == "Nenhum" and template_names:
            selected_template = template_names[0]
            
        self.combo_prompt_template.set(selected_template)
        
        # Load existing responses/history from database for this step
        step_data = db.get_audit_step(self.active_project["id"], self.current_step)
        
        self.txt_ai_response.delete("1.0", "end")
        if step_data:
            if step_data.get("response_content"):
                self.txt_ai_response.insert("end", step_data["response_content"])
            if step_data.get("completed") == 1:
                self.lbl_step_status.configure(text="CONCLUÍDO", text_color=COLOR_SUCCESS)
            else:
                self.lbl_step_status.configure(text="PENDENTE", text_color=COLOR_WARNING)
        else:
            self.lbl_step_status.configure(text="PENDENTE", text_color=COLOR_WARNING)
            
        self.refresh_generated_prompt()

    def on_step_combobox_changed(self, val):
        idx = self.step_options.index(val)
        self.current_step = idx + 1
        self.update_audit_ui()

    def on_template_selected_changed(self, val):
        self.refresh_generated_prompt()

    def prev_audit_step(self):
        if self.current_step > 1:
            self.current_step -= 1
            self.update_audit_ui()

    def next_audit_step(self):
        if self.current_step < 14:
            self.current_step += 1
            self.update_audit_ui()

    def refresh_generated_prompt(self):
        if not self.active_project:
            return
            
        tname = self.combo_prompt_template.get()
        templates = PromptManager.get_all_templates()
        template_content = templates.get(tname, "Aguardando template...")
        
        # Dynamic inputs
        p = self.active_project
        ents = db.get_entities(p["id"])
        reqs_f = db.get_requirements(p["id"], "functional")
        reqs_nf = db.get_requirements(p["id"], "non_functional")
        
        # Load folder structure if path set
        folder_tree = ""
        if p["root_path"] and os.path.exists(p["root_path"]):
            folder_tree = code_analyzer.generate_folder_tree(p["root_path"])
            
        extra = self.txt_extra_context.get("1.0", "end-1c").strip()
        
        interpolated = PromptManager.interpolate(
            template_content, 
            p, 
            requirements_list=reqs_f + reqs_nf, 
            entities_list=ents, 
            folder_structure=folder_tree,
            extra_context=extra
        )
        
        self.txt_generated_prompt.configure(state="normal")
        self.txt_generated_prompt.delete("1.0", "end")
        self.txt_generated_prompt.insert("end", interpolated)
        
        # Adjust visual copy button
        self.btn_copy_prompt.configure(text="📋 Copiar Prompt", fg_color=COLOR_SUCCESS)

    def copy_active_prompt(self):
        content = self.txt_generated_prompt.get("1.0", "end-1c")
        pyperclip.copy(content)
        self.btn_copy_prompt.configure(text="✅ Copiado!", fg_color=COLOR_ACCENT)

    def browse_context_file(self):
        if not self.active_project or not self.active_project["root_path"]:
            messagebox.showwarning("Aviso", "Por favor, defina a pasta raiz do projeto nas configurações primeiro.")
            return
            
        initial_dir = self.active_project["root_path"]
        filepath = filedialog.askopenfilename(initialdir=initial_dir)
        if filepath:
            self.entry_context_filepath.delete(0, "end")
            self.entry_context_filepath.insert(0, filepath)
            
            # Load contents
            contents = code_analyzer.read_file_content(filepath)
            self.txt_extra_context.delete("1.0", "end")
            self.txt_extra_context.insert("end", f"// Arquivo: {os.path.basename(filepath)}\n\n{contents}")
            self.refresh_generated_prompt()

    def inject_project_configs(self):
        if not self.active_project or not self.active_project["root_path"]:
            messagebox.showwarning("Aviso", "Selecione um projeto e configure a pasta raiz primeiro.")
            return
            
        root = self.active_project["root_path"]
        configs = code_analyzer.read_key_config_files(root)
        if not configs:
            messagebox.showinfo("Informação", "Nenhum arquivo de configuração padrão encontrado na pasta raiz.")
            return
            
        self.txt_extra_context.delete("1.0", "end")
        joined = ""
        for name, text in configs.items():
            joined += f"--- ARQUIVO: {name} ---\n{text}\n\n"
            
        self.txt_extra_context.insert("end", joined)
        self.refresh_generated_prompt()

    def save_current_audit_step(self):
        if not self.active_project:
            return
            
        prompt = self.txt_generated_prompt.get("1.0", "end-1c")
        response = self.txt_ai_response.get("1.0", "end-1c")
        
        if not response.strip():
            messagebox.showwarning("Aviso", "Cole a resposta obtida da IA antes de salvar.")
            return
            
        db.save_audit_step(
            self.active_project["id"], 
            self.current_step, 
            prompt, 
            response, 
            completed=1
        )
        self.lbl_step_status.configure(text="CONCLUÍDO", text_color=COLOR_SUCCESS)
        messagebox.showinfo("Sucesso", f"Resposta da Etapa {self.current_step} salva com sucesso!")

    # ==========================================
    # PROMPT LIBRARY EDITOR VIEW
    # ==========================================
    def create_library_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        
        lbl_title = ctk.CTkLabel(frame, text="Biblioteca & Editor de Prompts IA", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_title.pack(anchor="w", pady=(10, 10))
        
        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.pack(fill="x", pady=5)
        
        lbl_sel = ctk.CTkLabel(top_bar, text="Selecionar Template:", font=ctk.CTkFont(size=12), text_color=COLOR_TEXT_FG)
        lbl_sel.pack(side="left", padx=5)
        
        self.combo_lib_templates = ctk.CTkComboBox(top_bar, values=[], width=320, command=self.on_lib_template_selected)
        self.combo_lib_templates.pack(side="left", padx=10)
        
        btn_new_temp = ctk.CTkButton(
            top_bar, 
            text="+ Novo", 
            width=70, 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.create_new_prompt_template
        )
        btn_new_temp.pack(side="left", padx=5)
        
        btn_save_temp = ctk.CTkButton(
            top_bar, 
            text="💾 Salvar Alterações", 
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#5fa0f0",
            font=ctk.CTkFont(weight="bold"),
            command=self.save_prompt_template_changes
        )
        btn_save_temp.pack(side="right", padx=5)
        
        self.txt_template_editor = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=11), border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_SIDEBAR)
        self.txt_template_editor.pack(fill="both", expand=True, pady=(5, 15), padx=5)
        
        return frame

    def update_library_ui(self):
        templates = PromptManager.get_all_templates()
        names = list(templates.keys())
        self.combo_lib_templates.configure(values=names)
        
        if names:
            curr = self.combo_lib_templates.get()
            if curr not in names:
                curr = names[0]
                self.combo_lib_templates.set(curr)
            self.on_lib_template_selected(curr)
        else:
            self.txt_template_editor.delete("1.0", "end")

    def on_lib_template_selected(self, val):
        templates = PromptManager.get_all_templates()
        content = templates.get(val, "")
        self.txt_template_editor.delete("1.0", "end")
        self.txt_template_editor.insert("end", content)

    def create_new_prompt_template(self):
        dialog = ctk.CTkInputDialog(text="Digite o nome do novo template:", title="Novo Template de Prompt")
        name = dialog.get_input()
        if name:
            db.save_template(name, "Escreva o prompt aqui...")
            self.update_library_ui()
            self.combo_lib_templates.set(name)
            self.on_lib_template_selected(name)

    def save_prompt_template_changes(self):
        name = self.combo_lib_templates.get()
        if not name:
            return
            
        content = self.txt_template_editor.get("1.0", "end-1c")
        db.save_template(name, content)
        messagebox.showinfo("Sucesso", f"Template '{name}' atualizado com sucesso!")

    # ==========================================
    # CHECKLISTS VIEW
    # ==========================================
    def create_checklists_frame(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        
        lbl_title = ctk.CTkLabel(frame, text="Checklists de Qualidade & Revisão Técnica", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_title.pack(anchor="w", pady=(10, 10))
        
        # Category Selector bar
        cat_bar = ctk.CTkFrame(frame, fg_color="transparent")
        cat_bar.pack(fill="x", pady=5)
        
        lbl_cat = ctk.CTkLabel(cat_bar, text="Categoria de Auditoria:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_FG)
        lbl_cat.pack(side="left", padx=5)
        
        self.combo_checklist_cat = ctk.CTkComboBox(
            cat_bar, 
            values=[
                "Qualidade de Código (Monólito/Modular)",
                "Pull Request (Revisão Técnica)",
                "Segurança (OWASP Top 10)",
                "Documentação (ADRs, APIs)",
                "Testes & Cobertura"
            ],
            width=280,
            command=self.on_checklist_cat_changed
        )
        self.combo_checklist_cat.pack(side="left", padx=10)
        
        btn_reset = ctk.CTkButton(
            cat_bar, 
            text="Resetar Padrões", 
            width=110, 
            fg_color=COLOR_BORDER,
            hover_color=COLOR_HOVER,
            text_color=COLOR_TEXT_FG,
            command=self.reset_checklist_defaults
        )
        btn_reset.pack(side="right", padx=5)
        
        # Add Custom item
        add_frame = ctk.CTkFrame(frame, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
        add_frame.pack(fill="x", pady=10, padx=5)
        
        lbl_add = ctk.CTkLabel(add_frame, text="Adicionar Item:", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_FG)
        lbl_add.pack(side="left", padx=15, pady=10)
        
        self.entry_new_chk_item = ctk.CTkEntry(add_frame, width=450, placeholder_text="Escreva uma regra/item customizado para esta categoria...")
        self.entry_new_chk_item.pack(side="left", padx=5, pady=10, fill="x", expand=True)
        
        btn_add_chk = ctk.CTkButton(
            add_frame, 
            text="+ Inserir", 
            width=70, 
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#5fa0f0",
            font=ctk.CTkFont(weight="bold"),
            command=self.add_custom_checklist
        )
        btn_add_chk.pack(side="right", padx=15, pady=10)
        
        # Checklists list
        self.checklists_scroll = ctk.CTkScrollableFrame(frame, fg_color=COLOR_SIDEBAR, border_width=1, border_color=COLOR_BORDER)
        self.checklists_scroll.pack(fill="both", expand=True, pady=(5, 15), padx=5)
        
        return frame

    def get_active_checklist_cat_code(self):
        val = self.combo_checklist_cat.get()
        if "Qualidade" in val:
            return "quality"
        elif "Pull Request" in val:
            return "pr"
        elif "Segurança" in val:
            return "security"
        elif "Documentação" in val:
            return "docs"
        elif "Testes" in val:
            return "test"
        return "quality"

    def on_checklist_cat_changed(self, val):
        self.update_checklists_ui()

    def update_checklists_ui(self):
        # Clear list
        for widget in self.checklists_scroll.winfo_children():
            widget.destroy()
            
        if not self.active_project:
            lbl_none = ctk.CTkLabel(self.checklists_scroll, text="Selecione um projeto ativo para usar os checklists.", font=ctk.CTkFont(size=12, slant="italic"), text_color=COLOR_TEXT_MUTED)
            lbl_none.pack(anchor="w", padx=20, pady=20)
            return
            
        cat = self.get_active_checklist_cat_code()
        items = db.get_checklists(self.active_project["id"], cat)
        
        if not items:
            lbl_none = ctk.CTkLabel(self.checklists_scroll, text="Nenhum item cadastrado para esta categoria.", font=ctk.CTkFont(size=12, slant="italic"), text_color=COLOR_TEXT_MUTED)
            lbl_none.pack(anchor="w", padx=20, pady=20)
            return
            
        for item in items:
            row = ctk.CTkFrame(self.checklists_scroll, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER)
            row.pack(fill="x", pady=4, padx=10)
            
            # Use boolean state
            is_checked = (item["is_checked"] == 1)
            
            # Checkbox control (binding local variables via lambda check event)
            var = tk.BooleanVar(value=is_checked)
            cb = ctk.CTkCheckBox(
                row, 
                text=item["item_text"], 
                variable=var,
                text_color=COLOR_TEXT_FG,
                font=ctk.CTkFont(size=12),
                command=lambda item_id=item["id"], var_ref=var: self.on_checklist_toggle(item_id, var_ref.get())
            )
            cb.pack(side="left", padx=15, pady=10, fill="both", expand=True)
            
            btn_del = ctk.CTkButton(
                row, 
                text="❌", 
                width=25, 
                height=25, 
                fg_color="transparent", 
                text_color=COLOR_ALERT, 
                hover_color=COLOR_HOVER,
                command=lambda item_id=item["id"]: self.delete_checklist_item(item_id)
            )
            btn_del.pack(side="right", padx=10)

    def on_checklist_toggle(self, item_id, val):
        db.toggle_checklist_item(item_id, val)

    def add_custom_checklist(self):
        if not self.active_project:
            return
            
        text = self.entry_new_chk_item.get().strip()
        if not text:
            return
            
        cat = self.get_active_checklist_cat_code()
        db.add_custom_checklist_item(self.active_project["id"], cat, text)
        
        self.entry_new_chk_item.delete(0, "end")
        self.update_checklists_ui()

    def delete_checklist_item(self, item_id):
        db.delete_checklist_item(item_id)
        self.update_checklists_ui()

    def reset_checklist_defaults(self):
        if not self.active_project:
            return
            
        confirm = messagebox.askyesno(
            "Confirmar Reset", 
            "Deseja redefinir os checklists desta categoria para os padrões originais?\nSuas personalizações e marcações serão apagadas."
        )
        if confirm:
            cat = self.get_active_checklist_cat_code()
            # Delete items of category
            conn = db.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM checklists WHERE project_id = ? AND category = ?",
                (self.active_project["id"], cat)
            )
            conn.commit()
            conn.close()
            
            # Seed default category again
            db.seed_checklists_for_project(self.active_project["id"])
            self.update_checklists_ui()

# Start application
if __name__ == "__main__":
    app = VibeArchitectApp()
    app.mainloop()
