import os
import glob
import re
from database import save_template, get_templates

class PromptManager:
    @staticmethod
    def scan_and_import_templates(guia_dir):
        """
        Scans the specified directory for *.md.txt files and imports/updates them in the database.
        """
        if not os.path.exists(guia_dir):
            return 0
        
        search_pattern = os.path.join(guia_dir, "*.md.txt")
        files = glob.glob(search_pattern)
        imported_count = 0
        
        for file_path in files:
            filename = os.path.basename(file_path)
            # Remove extension to get template name
            template_name = os.path.splitext(os.path.splitext(filename)[0])[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                save_template(template_name, content)
                imported_count += 1
            except Exception as e:
                print(f"Error importing template {filename}: {e}")
                
        return imported_count

    @staticmethod
    def get_all_templates():
        """
        Returns a dictionary of all templates from the database.
        """
        return get_templates()

    @staticmethod
    def interpolate(template_content, project_dict, requirements_list=None, entities_list=None, folder_structure="", extra_context=""):
        """
        Replaces placeholders in the template with actual project data.
        """
        if not template_content:
            return ""
        
        # Build tech stack string
        stack_info = ""
        if project_dict.get("tech_stack"):
            import json
            try:
                stack = json.loads(project_dict["tech_stack"])
                stack_info = "\n".join([f"- {k.capitalize()}: {v}" for k, v in stack.items() if v])
            except Exception:
                stack_info = str(project_dict["tech_stack"])
                
        # Build requirements string
        reqs_str = ""
        if requirements_list:
            reqs_str = "\n".join([f"- {r['code']}: {r['description']}" for r in requirements_list])
            
        # Build entities string
        entities_str = ""
        if entities_list:
            for ent in entities_list:
                entities_str += f"\n### Entidade: {ent['name']}\n"
                entities_str += f"- Descrição: {ent['description']}\n"
                if ent.get('properties'):
                    entities_str += f"- Propriedades: {', '.join(ent['properties'])}\n"
                if ent.get('methods'):
                    entities_str += f"- Métodos/Funções: {', '.join(ent['methods'])}\n"
                if ent.get('relationships'):
                    entities_str += f"- Relacionamentos: {', '.join(ent['relationships'])}\n"
                if ent.get('rules'):
                    entities_str += f"- Regras associadas: {', '.join(ent['rules'])}\n"

        # Build full domain description
        project_desc = project_dict.get("description", "")
        domain_desc = f"{project_desc}\n\nStack:\n{stack_info}"
        if reqs_str:
            domain_desc += f"\n\nRequisitos:\n{reqs_str}"
        if entities_str:
            domain_desc += f"\n\nModelagem de Domínio (DDD):\n{entities_str}"

        result = template_content
        
        # Standard variables
        result = result.replace("{PROJECT_NAME}", project_dict.get("name", ""))
        result = result.replace("{PROJECT_DESC}", project_desc)
        result = result.replace("{TECH_STACK}", stack_info)
        
        # Standard prompt placeholders from md files
        result = result.replace("[COLE A ÁRVORE DE PASTAS AQUI]", folder_structure or "[Nenhuma árvore de pastas gerada ou selecionada]")
        result = result.replace("[COLE AQUI A DESCRIÇÃO DO SEU DOMÍNIO]", domain_desc)
        result = result.replace("[COLE A DESCRIÇÃO DO NEGÓCIO]", domain_desc)
        result = result.replace("[COLE A DESCRIÇÃO DO SEU DOMÍNIO]", domain_desc)
        
        # Fallback placeholders
        if extra_context:
            result = result.replace("[COLE AQUI O CÓDIGO/ARQUIVO]", extra_context)
            result = result.replace("[COLE O CÓDIGO AQUI]", extra_context)
            result = result.replace("[COLE O CONTEÚDO AQUI]", extra_context)
            # General append if no explicit placeholder but extra_context is provided
            if "[COLE" not in template_content and "{EXTRA_CONTEXT}" not in template_content:
                result += f"\n\n--- Contexto/Código Adicional ---\n{extra_context}"
        
        result = result.replace("{EXTRA_CONTEXT}", extra_context)
        
        return result

    @staticmethod
    def get_default_step_prompt_mapping():
        """
        Returns a mapping of step number (1-14) to preferred template names.
        We will search by prefix in the templates database.
        """
        return {
            1: "10.Melhor prompt completo e prático", # Envia descrição
            2: "2.Prompt para analisar apenas a estrutura de pastas", # Envia estrutura
            3: "1.Prompt mestre para auditoria completa do sistema", # Análise arquitetural
            4: "3.Prompt para analisar um módulo específico", # Envia módulos
            5: "4.Prompt para revisar código com foco em Clean Code e SOLID", # Clean Code e SOLID
            6: "5. Prompt para segurança", # Configs e Autenticação
            7: "5. Prompt para segurança", # Análise de segurança
            8: "DDD.Prompt específico para classes, propriedades e métodos", # Envia testes / código
            9: "DDD.Prompt para DDD agregados e value objects", # Cobertura/testabilidade/DDD
            10: "6.Prompt para documentação do projeto", # Envia README/docs
            11: "6.Prompt para documentação do projeto", # Revisão de docs
            12: "7.Prompt para gerar relatório final de auditoria", # Relatório final
            13: "9.Prompt curto para usar no dia a dia", # Refatoração
            14: "8.Prompt para transformar o projeto em template reutilizável" # Checklist / templates
        }
