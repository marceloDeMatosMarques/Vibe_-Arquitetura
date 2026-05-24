import database as db
import json
import os

def seed():
    print("Iniciando a carga de dados para o projeto Meditação & Promessas...")
    db.init_db()
    
    # 1. Check if the project already exists to avoid duplication
    projects = db.get_projects()
    project_id = None
    for p in projects:
        if p["name"] == "Meditação & Promessas":
            project_id = p["id"]
            print(f"Projeto 'Meditação & Promessas' já existe com ID {project_id}. Atualizando dados...")
            break
            
    # Tech stack config
    tech_stack = {
        "frontend": "Next.js, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query",
        "backend": "Node.js, TypeScript, NestJS, Prisma ORM, Redis, BullMQ",
        "database": "MySQL 8 (via CloudPanel na Hostinger)",
        "cache": "Redis (via CloudPanel)",
        "messaging": "Evolution API (WhatsApp)",
        "auth": "JWT / Cookie Session (HTTP-only)",
        "deploy": "Hostinger VPS, CloudPanel, Cloudflare",
        "obs": "Sentry, PM2 logs, Pino"
    }
    
    description = (
        "Plataforma devocional cristã com posts, cards de meditação, promessas bíblicas, "
        "áudio blog por IA (TTS), player de música de referência (YouTube/Spotify), "
        "controle de limite de envios WhatsApp, captação de leads, anúncios (AdSense) "
        "e acesso pago premium."
    )
    
    root_path = "c:\\Users\\Marcelo\\Documents\\GUIA\\meditacao_promessas"
    
    if not project_id:
        project_id = db.create_project(
            "Meditação & Promessas", 
            description, 
            tech_stack, 
            root_path
        )
        print(f"Projeto criado com ID: {project_id}")
    else:
        db.update_project(project_id, "Meditação & Promessas", description, tech_stack, root_path)

    # 2. Seed Requirements
    requirements_data = [
        # Functional
        ("functional", "RF01", "Cadastro e autenticação de usuários (Login/Registro) com controle de perfis (Visitor, Free, Premium, Admin)."),
        ("functional", "RF02", "Controle de acesso pago (Planos Free vs Assinatura Premium)."),
        ("functional", "RF03", "CRUD de categorias temáticas para organizar devocionais por dores da alma (medo, ansiedade, cansaço)."),
        ("functional", "RF04", "CRUD de Posts/Meditações devocionais com versão formatada para Web e versão formatada para WhatsApp."),
        ("functional", "RF05", "Áudio blog: upload de áudio narrado (MP3) ou geração automática usando IA de Texto para Fala (TTS)."),
        ("functional", "RF06", "Associação de música de referência (Embed YouTube iframe, preview de 30s Spotify/Deezer)."),
        ("functional", "RF07", "Envio manual de posts pelo WhatsApp e integração com Evolution API no backend."),
        ("functional", "RF08", "Captura sutil de Leads (nome, whatsapp, email) após limite de 5 envios gratuitos do visitante."),
        ("functional", "RF09", "Processamento de pagamentos (Stripe / Mercado Pago) e recepção de webhooks de assinatura."),
        ("functional", "RF10", "Exibição de anúncios do Google AdSense para usuários gratuitos, ocultando-os automaticamente para Premium."),
        ("functional", "RF11", "Métricas de posts: contagem de views, envios, salvamentos e plays de áudio."),
        ("functional", "RF12", "Sistema de avaliação por estrelas (1 a 5) com algoritmo de cálculo de posts em alta (Hot Score)."),
        
        # Non-Functional
        ("non_functional", "RNF01", "Banco de dados MySQL 8 hospedado e gerenciado via CloudPanel."),
        ("non_functional", "RNF02", "Armazenamento persistente de áudios (MP3) e imagens de destaque no Cloudflare R2 (API S3)."),
        ("non_functional", "RNF03", "Gerenciamento de processos Node.js com PM2 e Nginx configurados no VPS da Hostinger."),
        ("non_functional", "RNF04", "Uso de CDN Cloudflare para proteção DDoS, SSL automático (Full strict) e cache (exceto caminhos de API)."),
        ("non_functional", "RNF05", "Processamento em background assíncrono para filas de envio WhatsApp usando Redis e BullMQ."),
        ("non_functional", "RNF06", "Estrutura do backend seguindo Clean Architecture, SOLID e modularidade DDD."),
        ("non_functional", "RNF07", "Autenticação segura via cookies HTTP-only para mitigar ataques XSS."),
        ("non_functional", "RNF08", "Desempenho com tempo de resposta do blog público abaixo de 200ms por requisição.")
    ]
    
    # Clean previous requirements for this project to refresh
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM requirements WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM entities WHERE project_id = ?", (project_id,))
    conn.commit()
    conn.close()
    
    for r_type, code, desc in requirements_data:
        db.save_requirement(project_id, r_type, code, desc)
    print(f"Cadastrados {len(requirements_data)} requisitos.")

    # 3. Seed Entities (DDD Model)
    entities_data = [
        {
            "name": "User",
            "description": "Representa uma pessoa cadastrada na plataforma com perfis de acesso definidos.",
            "properties": ["id (UUID)", "nome (string)", "email (string)", "whatsapp (string)", "password_hash (string)", "role (enum)", "status (enum)", "created_at (datetime)", "updated_at (datetime)"],
            "methods": ["criarConta()", "atualizarPerfil()", "alterarSenha()", "alterarPapel()", "bloquearConta()"],
            "relationships": ["User possui muitas Subscriptions", "User realiza WhatsAppSends", "User cria PostRatings"],
            "rules": ["Usuário bloqueado fica impossibilitado de realizar envios", "Papel premium depende de assinatura ativa", "E-mail e WhatsApp devem ser únicos no banco de dados"]
        },
        {
            "name": "Post",
            "description": "Entidade central do sistema. Armazena a mensagem devocional cristã com suas versões site e WhatsApp.",
            "properties": ["id (UUID)", "titulo (string)", "slug (string)", "conteudo_site (text)", "conteudo_whatsapp (text)", "dor_titulo (string)", "dor_descricao (text)", "versiculo_texto (text)", "versiculo_ref (string)", "promessa_texto (text)", "promessa_ref (string)", "status (enum)", "is_premium (boolean)", "is_featured (boolean)", "author_id (FK)", "category_id (FK)", "image_id (FK)", "audio_id (FK)", "published_at (datetime)"],
            "methods": ["publicar()", "agendar()", "arquivar()", "gerarConteudoWhatsApp()", "associarMídia()"],
            "relationships": ["Post pertence a Category", "Post possui uma MediaImage", "Post possui um AudioBlog", "Post possui uma MusicReference", "Post possui estatísticas PostStats"],
            "rules": ["Post publicado deve possuir obrigatoriamente título, slug, conteúdo do site e conteúdo WhatsApp", "O slug deve ser único e não deve ser alterado após a publicação"]
        },
        {
            "name": "Category",
            "description": "Permite organizar as meditações/posts devocionais por temática e dores emocionais.",
            "properties": ["id (UUID)", "titulo (string)", "slug (string)", "descricao (text)", "color_hex (string)", "icon (string)", "is_active (boolean)", "sort_order (integer)"],
            "methods": ["ativar()", "desativar()", "alterarOrdem()"],
            "relationships": ["Category possui muitos Posts"],
            "rules": ["Título e slug são de preenchimento obrigatório", "Sort order define a ordenação visual de navegação no menu"]
        },
        {
            "name": "MediaImage",
            "description": "Armazena metadados e referências das imagens de destaque dos posts focando em SEO.",
            "properties": ["id (UUID)", "title (string)", "slug (string)", "description (text)", "alt (string)", "url (string)", "thumb_url (string)", "format (enum)", "width (integer)", "height (integer)", "size_kb (integer)"],
            "methods": ["upload()", "gerarThumbnail()", "validarTamanho()"],
            "relationships": ["MediaImage associada a Post"],
            "rules": ["O campo 'alt' é obrigatório para otimização de acessibilidade e SEO", "Validar tamanho e formato antes de persistir upload"]
        },
        {
            "name": "AudioBlog",
            "description": "Áudio MP3 narrado da mensagem devocional para leitura dinâmica auditiva.",
            "properties": ["id (UUID)", "title (string)", "slug (string)", "description (text)", "mp3_url (string)", "duration_seconds (integer)", "size_kb (integer)", "generated_by_ai (boolean)", "voice (string)", "source_text (text)", "status (enum)"],
            "methods": ["gerarViaTTS()", "uploadMP3()", "validarDuracao()"],
            "relationships": ["AudioBlog associado a Post"],
            "rules": ["O áudio pode ser gerado dinamicamente via serviço de IA (Azure/ElevenLabs) ou upload manual"]
        },
        {
            "name": "MusicReference",
            "description": "Vínculo de uma música/vídeo de referência do YouTube, Spotify ou Deezer à meditação.",
            "properties": ["id (UUID)", "post_id (FK)", "artist (string)", "title (string)", "youtube_url (string)", "youtube_video_id (string)", "spotify_url (string)", "deezer_url (string)", "preview_url (string)", "display_type (enum)"],
            "methods": ["extrairVideoId()", "buscarPreviewSpotify()"],
            "relationships": ["MusicReference pertence ao Post"],
            "rules": ["Não baixar áudio do YouTube diretamente (usar player embed iframe oficial)", "Previews de música externa limitados a 30 segundos"]
        },
        {
            "name": "WhatsAppSend",
            "description": "Registro histórico individual de cada mensagem compartilhada via WhatsApp.",
            "properties": ["id (UUID)", "user_id (FK)", "post_id (FK)", "destination_number (string)", "origin_number (string)", "message_body (text)", "status (enum)", "type (enum)", "ip_address (string)", "device_hash (string)", "error_message (text)", "sent_at (datetime)"],
            "methods": ["enviar()", "atualizarStatus()", "registrarErro()"],
            "relationships": ["WhatsAppSend pertence a User", "WhatsAppSend pertence a Post"],
            "rules": ["Toda tentativa de envio de WhatsApp deve ser registrada", "As falhas de envio devem registrar o código/descrição do erro retornado pela API"]
        },
        {
            "name": "SendLimit",
            "description": "Controla os limites de tráfego e cota diária por IP, usuário ou dispositivo para evitar spam.",
            "properties": ["id (UUID)", "identifier (string)", "identifier_type (enum)", "date (date)", "count (integer)", "blocked_until (datetime)"],
            "methods": ["incrementarContagem()", "verificarBloqueio()", "resetarDiario()"],
            "relationships": [],
            "rules": ["Visitantes sem cadastro: limite de 5 envios diários por dispositivo (localStorage/IP)", "Usuários livres (Lead/Free): limite de 20 envios diários", "Usuários premium possuem cota de envios ilimitada"]
        },
        {
            "name": "Lead",
            "description": "Pessoa capturada no funil de envios da plataforma após esgotamento de envios gratuitos.",
            "properties": ["id (UUID)", "name (string)", "whatsapp (string)", "email (string)", "source (enum)", "post_id (FK)", "ip_address (string)", "device_hash (string)", "converted (boolean)", "user_id (FK)"],
            "methods": ["capturar()", "converterEmUsuario()", "vincularPostOrigem()"],
            "relationships": ["Lead associado a Post", "Lead se converte em User"],
            "rules": ["A captura do Lead é obrigatória após o visitante exceder 5 envios diários gratuitos", "O preenchimento do nome e número de WhatsApp é obrigatório no modal"]
        },
        {
            "name": "Plan",
            "description": "Representa os planos de assinatura disponíveis na plataforma (Mensal, Anual).",
            "properties": ["id (UUID)", "name (string)", "slug (string)", "description (text)", "price (decimal)", "currency (string)", "interval (enum)", "send_limit (integer)", "features (json)", "is_active (boolean)"],
            "methods": ["ativar()", "desativar()", "atualizarPreco()"],
            "relationships": ["Plan possui muitas Subscriptions"],
            "rules": ["O plano deve possuir preço, limite técnico e indicação de status ativo"]
        },
        {
            "name": "Subscription",
            "description": "Assinatura do usuário controlando o ciclo de acesso ao conteúdo pago premium.",
            "properties": ["id (UUID)", "user_id (FK)", "plan_id (FK)", "gateway (enum)", "gateway_subscription_id (string)", "status (enum)", "amount_paid (decimal)", "started_at (datetime)", "ends_at (datetime)", "next_billing_at (datetime)", "canceled_at (datetime)"],
            "methods": ["iniciar()", "cancelar()", "renovar()", "suspenderInadimplente()"],
            "relationships": ["Subscription pertence a User", "Subscription possui muitos Payments"],
            "rules": ["Pagamento aprovado ativa ou renova a assinatura do usuário", "Cancelamento mantém o acesso do usuário premium ativo até o final do período já pago"]
        },
        {
            "name": "Payment",
            "description": "Registro financeiro de cada cobrança processada pelo gateway de pagamento.",
            "properties": ["id (UUID)", "subscription_id (FK)", "user_id (FK)", "gateway (enum)", "gateway_payment_id (string)", "amount (decimal)", "currency (string)", "status (enum)", "method (enum)", "paid_at (datetime)"],
            "methods": ["processar()", "receberWebhook()", "reembolsar()"],
            "relationships": ["Payment pertence a User", "Payment pertence a Subscription"],
            "rules": ["A assinatura só é ativada após a notificação de confirmação do gateway", "Webhooks financeiros devem validar a chave de assinatura enviada pelo gateway"]
        },
        {
            "name": "AdZone",
            "description": "Representa as zonas de inserção de publicidade (Google AdSense) espalhadas na plataforma.",
            "properties": ["id (UUID)", "name (string)", "slug (string)", "description (text)", "format (string)", "position (enum)", "adsense_slot (string)", "is_active (boolean)"],
            "methods": ["exibir()", "ocultarParaPremium()"],
            "relationships": [],
            "rules": ["Os anúncios da AdZone só devem ser renderizados se o usuário logado for FREE ou VISITANTE (premium não vê anúncios)"]
        },
        {
            "name": "PostStats",
            "description": "Acumulador de métricas de engajamento do post devocional.",
            "properties": ["id (UUID)", "post_id (FK)", "views_total (integer)", "views_today (integer)", "views_week (integer)", "views_month (integer)", "whatsapp_sends (integer)", "saves (integer)", "audio_plays (integer)", "rating_average (decimal)", "rating_count (integer)", "hot_score (decimal)", "is_hot (boolean)"],
            "methods": ["registrarView()", "registrarPlay()", "registrarEnvio()", "calcularHotScore()"],
            "relationships": ["PostStats pertence ao Post"],
            "rules": ["O Hot Score é calculado baseado na fórmula: ((Views * 1.5) + (Sends * 3) + (Saves * 2) + (Plays * 1)) / (T + 2)^1.8"]
        },
        {
            "name": "PostRating",
            "description": "Avaliação por estrelas fornecida por usuários ou visitantes aos devocionais.",
            "properties": ["id (UUID)", "post_id (FK)", "user_id (FK)", "device_hash (string)", "stars (integer)", "created_at (datetime)"],
            "methods": ["avaliar()"],
            "relationships": ["PostRating pertence ao Post", "PostRating pertence a User"],
            "rules": ["O post pode receber apenas uma avaliação (1 a 5 estrelas) por dispositivo (hash) ou usuário logado"]
        }
    ]
    
    for ent in entities_data:
        db.save_entity(
            project_id,
            None,
            ent["name"],
            ent["description"],
            ent["properties"],
            ent["methods"],
            ent["relationships"],
            ent["rules"]
        )
    print(f"Cadastradas {len(entities_data)} entidades DDD.")
    print("Carga concluída com sucesso! Banco de dados atualizado.")

if __name__ == "__main__":
    seed()
