import os
import json
import database as db

def generate_all_docs():
    db.init_db()
    projects = db.get_projects()
    project = None
    
    for p in projects:
        if p["name"] == "Meditação & Promessas":
            project = p
            break
            
    if not project:
        print("Erro: Projeto 'Meditação & Promessas' não encontrado no banco de dados.")
        return
        
    # We will use the workspace path C:\Users\Marcelo\Documents\GUIA\meditacao_promessas
    root_dir = "C:\\Users\\Marcelo\\Documents\\GUIA\\meditacao_promessas"
    project["root_path"] = root_dir
    db.update_project(project["id"], project["name"], project["description"], json.loads(project["tech_stack"]), root_dir)
    
    docs_dir = os.path.join(root_dir, "docs")
    product_dir = os.path.join(docs_dir, "product")
    arch_dir = os.path.join(docs_dir, "architecture")
    modules_dir = os.path.join(docs_dir, "modules")
    
    os.makedirs(product_dir, exist_ok=True)
    os.makedirs(arch_dir, exist_ok=True)
    os.makedirs(modules_dir, exist_ok=True)
    
    # 1. Create vision.md
    vision_content = f"""# Visão do Produto - {project['name']}

## Descrição Geral
{project['description']}

## Tecnologias Envolvidas
"""
    try:
        stack = json.loads(project["tech_stack"])
        for k, v in stack.items():
            if v:
                vision_content += f"- **{k.capitalize()}**: {v}\n"
    except Exception:
        vision_content += f"{project['tech_stack']}\n"
        
    with open(os.path.join(product_dir, "vision.md"), "w", encoding="utf-8") as f:
        f.write(vision_content)
    print("Gerado: docs/product/vision.md")

    # 2. Create requirements.md
    reqs_f = db.get_requirements(project["id"], "functional")
    reqs_nf = db.get_requirements(project["id"], "non_functional")
    
    reqs_content = f"# Requisitos do Sistema - {project['name']}\n\n"
    reqs_content += "## Requisitos Funcionais (RFs)\n"
    for r in reqs_f:
        reqs_content += f"- **{r['code']}**: {r['description']}\n"
        
    reqs_content += "\n## Requisitos Não Funcionais (RNFs)\n"
    for r in reqs_nf:
        reqs_content += f"- **{r['code']}**: {r['description']}\n"
        
    with open(os.path.join(product_dir, "requirements.md"), "w", encoding="utf-8") as f:
        f.write(reqs_content)
    print("Gerado: docs/product/requirements.md")
    
    # 3. Create Domain modules
    ents = db.get_entities(project["id"])
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
    print(f"Gerado: {len(ents)} especificações em docs/modules/")
            
    # 4. Write ADR template
    adr_template = """# ADR 0001 - Decisão Inicial de Arquitetura

## Status
Aceito

## Contexto
Definição da estrutura modular inicial do sistema.

## Decisão
Adotar estrutura modular baseada em Clean Architecture, SOLID e Domain-Driven Design (DDD).

## Consequências
- Alta coesão
- Facilidade em testar regras de negócio
- Modularidade estrita
- Facilidade de desenvolvimento paralelo (anúncios e acesso pago)
"""
    with open(os.path.join(arch_dir, "0001-estrutura-arquitetural.md"), "w", encoding="utf-8") as f:
        f.write(adr_template)
    print("Gerado: docs/architecture/0001-estrutura-arquitetural.md")
    print("Sucesso: Toda a documentação gerada com sucesso!")

if __name__ == "__main__":
    generate_all_docs()
