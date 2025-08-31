import os 
import uuid
import logging
from dotenv import load_dotenv 
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue, PicklePersistence

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Carrega variáveis de ambiente
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

def escape_markdown(texto: str) -> str:
    """Função mantida para outras partes do bot, mas não usada no start."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in texto)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem de boas-vindas com texto simples para garantir o funcionamento."""
    texto_boas_vindas = """Olá! Bem-vindo ao seu Bot de Lembretes Pessoal. ⏰

Aqui está como você pode me usar:

1. Criar um Lembrete
Use o comando: /lembrete <tempo> <mensagem>
Exemplo: /lembrete 10m Ligar para a reunião
(Unidades de tempo válidas: s, m, h, d)

2. Ver Seus Lembretes
Use o comando: /meuslembretes
Isso listará todos os lembretes agendados.

3. Cancelar um Lembrete
Use o comando: /cancelar <ID>
Exemplo: /cancelar a3f7b

Comece criando seu primeiro lembrete!"""
    
    await update.message.reply_text(texto_boas_vindas)

async def enviar_lembrete(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia a mensagem de lembrete formatada."""
    job = context.job
    mensagem_escapada = escape_markdown(job.data)
    await context.bot.send_message(job.chat_id, text=f"🔔 Lembrete: *{mensagem_escapada}*", parse_mode='MarkdownV2')

async def lembrete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Agenda um novo lembrete."""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text("Uso incorreto! Tente: /lembrete <tempo> <mensagem>")
        return

    tempo_str = args[0]
    mensagem = " ".join(args[1:])
    
    try:
        valor_tempo = int(tempo_str[:-1])
        unidade_tempo = tempo_str[-1].lower()

        if unidade_tempo == 's':
            delay = valor_tempo
        elif unidade_tempo == 'm':
            delay = valor_tempo * 60
        elif unidade_tempo == 'h':
            delay = valor_tempo * 3600
        elif unidade_tempo == 'd':
            delay = valor_tempo * 86400
        else:
            await update.message.reply_text("Unidade de tempo inválida. Use 's', 'm', 'h' ou 'd'.")
            return

    except (ValueError, IndexError):
        await update.message.reply_text("Formato de tempo inválido. Exemplo: 10s, 5m, 1h.")
        return
        
    chat_id = update.effective_message.chat_id
    job_name = str(uuid.uuid4())
    
    context.job_queue.run_once(
        enviar_lembrete,
        delay,
        chat_id=chat_id,
        data=mensagem,
        name=job_name
    )
    
    # CORREÇÃO: Adicionado '\' antes de '!' para escapar o caractere especial.
    await update.message.reply_text(rf"✅ Ok\! Lembrete agendado para daqui a `{escape_markdown(tempo_str)}`\.", parse_mode='MarkdownV2')

async def meus_lembretes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra ao usuário todos os lembretes agendados."""
    tarefas_agendadas = context.job_queue.jobs()
    tarefas_do_usuario = [job for job in tarefas_agendadas if job.chat_id == update.effective_chat.id]

    if not tarefas_do_usuario:
        await update.message.reply_text("Você não tem nenhum lembrete agendado.")
        return
        
    # MUDANÇA: Simplificado para texto puro para evitar erros de markdown na lista.
    texto_lista = "Seus lembretes agendados:\n\n"
    for job in tarefas_do_usuario:
        mensagem_lembrete = job.data
        id_curto = job.name.split('-')[0]
        
        texto_lista += f"ID: {id_curto} - Lembrete: {mensagem_lembrete}\n"
        
    texto_lista += "\nPara cancelar, use /cancelar <ID>."
    
    await update.message.reply_text(texto_lista)

async def cancelar_lembrete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela um lembrete agendado."""
    try:
        id_para_cancelar = context.args[0]
    except IndexError:
        await update.message.reply_text("Uso incorreto. Envie o ID do lembrete. Ex: /cancelar a3f7b")
        return
        
    tarefas_encontradas = [job for job in context.job_queue.jobs() if job.name.startswith(id_para_cancelar) and job.chat_id == update.effective_chat.id]
    
    if not tarefas_encontradas:
        await update.message.reply_text("Não encontrei nenhum lembrete com esse ID.")
        return
        
    for job in tarefas_encontradas:
        job.schedule_removal()
        
    await update.message.reply_text(f"✅ Lembrete com ID {id_para_cancelar} foi cancelado.")

def main() -> None:
    """Inicia o bot e o mantém rodando."""
    if not TOKEN:
        logging.error("O token do Telegram não foi encontrado! Verifique seu arquivo .env")
        return

    persistence = PicklePersistence(filepath="bot_persistence")

    application = (
        Application.builder()
        .token(TOKEN)
        .persistence(persistence)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("lembrete", lembrete)) 
    application.add_handler(CommandHandler("meuslembretes", meus_lembretes))
    application.add_handler(CommandHandler("cancelar", cancelar_lembrete))

    print("Bot iniciado... Pressione Ctrl+C para parar.")
    application.run_polling()

if __name__ == '__main__':
    main()
