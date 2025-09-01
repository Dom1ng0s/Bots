import os 
import uuid
import logging
from dotenv import load_dotenv 
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, PicklePersistence
from datetime import datetime, timedelta

# --- Configuração Inicial ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


# --- Funções de Callback para Jobs ---

async def enviar_lembrete(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Função genérica chamada pelo JobQueue para enviar uma mensagem de lembrete."""
    try:
        job_data = context.job.data
        chat_id = job_data['chat_id']
        mensagem = job_data['mensagem']
        await context.bot.send_message(chat_id=chat_id, text=mensagem)
    except Exception as e:
        logger.error(f"Erro ao enviar lembrete para o chat_id {context.job.data.get('chat_id', 'N/A')}: {e}")


# --- Funções de Comando ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem de boas-vindas quando o comando /start é emitido."""
    texto_boas_vindas = (
        "Bem-vindo ao CheckList Bot!\n\n"
        "Aqui você pode organizar suas tarefas do dia a dia. "
        "Use /tutorial para ver todos os comandos disponíveis."
    )
    await update.message.reply_text(texto_boas_vindas)


async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fornece ao usuário um guia de como usar os comandos."""
    texto_tutorial = (
        "Guia de Comandos:\n\n"
        "🔹 /criartarefa <Prazo DD/MM/AAAA> - <Descrição da Tarefa>\n"
        "   _Cria uma nova tarefa com lembretes automáticos._\n\n"
        "🔹 /listartarefas\n"
        "   _Mostra todas as suas tarefas, ordenadas por urgência._\n\n"
        "🔹 /deletartarefa <Número da Tarefa>\n"
        "   _Apaga uma tarefa da sua lista._"
    )
    await update.message.reply_text(texto_tutorial, parse_mode='Markdown')


async def criar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cria uma nova tarefa e agenda notificações para a véspera e o dia do prazo."""
    if not context.args:
        await update.message.reply_text("Uso: /criartarefa <Prazo DD/MM/AAAA> - <Descrição>")
        return

    txt_tarefa = ' '.join(context.args)
    partes = txt_tarefa.split('-', 1)

    if len(partes) == 2:
        prazo_str = partes[0].strip()
        descricao = partes[1].strip()

        if not descricao:
            await update.message.reply_text("A descrição da tarefa não pode estar vazia.")
            return

        try:
            data_do_prazo = datetime.strptime(prazo_str, '%d/%m/%Y')

            nova_tarefa = {'id': str(uuid.uuid4()), 'descricao': descricao, 'prazo': prazo_str}
            
            if 'tarefas' not in context.user_data:
                context.user_data['tarefas'] = []
            context.user_data['tarefas'].append(nova_tarefa)

            # Agendamento de notificações
            chat_id = update.effective_chat.id
            notificacao_dia = data_do_prazo.replace(hour=9, minute=0, second=0)
            notificacao_vespera = (data_do_prazo - timedelta(days=1)).replace(hour=18, minute=0, second=0)

            msg_dia = f"⏰ HOJE É O DIA: Sua tarefa '{descricao}' vence hoje!"
            msg_vespera = f"🔔 Lembrete de Véspera: Sua tarefa '{descricao}' vence amanhã!"
            
            if notificacao_dia > datetime.now():
                context.job_queue.run_once(
                    enviar_lembrete, 
                    notificacao_dia, 
                    data={'chat_id': chat_id, 'mensagem': msg_dia}, 
                    name=f"job_dia_{nova_tarefa['id']}"
                )

            if notificacao_vespera > datetime.now():
                context.job_queue.run_once(
                    enviar_lembrete, 
                    notificacao_vespera, 
                    data={'chat_id': chat_id, 'mensagem': msg_vespera},
                    name=f"job_vespera_{nova_tarefa['id']}"
                )

            msg_sucesso = f"✅ Tarefa salva e lembretes agendados!\n\n*Tarefa:* {descricao}\n*Prazo:* {prazo_str}"
            await update.message.reply_text(msg_sucesso, parse_mode='Markdown')

        except ValueError:
            await update.message.reply_text("🗓️ Data inválida! Use o formato DD/MM/AAAA.")
    else:
        await update.message.reply_text("Formato inválido! 😬\nUse: /criartarefa <Prazo DD/MM/AAAA> - <Descrição>")


async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista todas as tarefas do usuário, ordenadas por prazo."""
    tarefas = context.user_data.get('tarefas')
    if not tarefas:
        await update.message.reply_text("Você ainda não tem tarefas cadastradas. Use /criartarefa para adicionar uma!")
        return
    
    try:
        tarefas_ordenadas = sorted(tarefas, key=lambda t: datetime.strptime(t['prazo'], '%d/%m/%Y'))
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao ordenar tarefas para o chat {update.effective_chat.id}: {e}")
        await update.message.reply_text("Ocorreu um erro ao tentar ordenar suas tarefas devido a um formato de data inválido em uma delas.")
        return

    texto_final = "📝 *Suas tarefas (ordenadas por urgência):*\n\n"
    for indice, tarefa in enumerate(tarefas_ordenadas, 1):
        texto_final += f"*{indice}* - {tarefa['descricao']} _(Prazo: {tarefa['prazo']})_\n"

    await update.message.reply_text(texto_final, parse_mode='Markdown')


async def deletar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deleta uma tarefa especificada pelo seu número na lista."""
    if len(context.args) != 1:
        await update.message.reply_text("Uso incorreto. Ex: /deletartarefa 2")
        return

    argumento = context.args[0]
    if not argumento.isdigit():
        await update.message.reply_text("Por favor, forneça um número válido.")
        return

    indice = int(argumento) - 1
    lista_original = context.user_data.get('tarefas')

    if not lista_original:
        await update.message.reply_text("Você não tem nenhuma tarefa para deletar.")
        return

    try:
        tarefas_ordenadas = sorted(lista_original, key=lambda t: datetime.strptime(t['prazo'], '%d/%m/%Y'))
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao ordenar tarefas para deleção no chat {update.effective_chat.id}: {e}")
        await update.message.reply_text("Ocorreu um erro ao processar suas tarefas. Verifique se todas têm datas válidas.")
        return

    if not (0 <= indice < len(tarefas_ordenadas)):
        await update.message.reply_text("Número de tarefa inválido. Use /listartarefas para ver os números.")
        return

    tarefa_a_deletar = tarefas_ordenadas[indice]
    id_a_deletar = tarefa_a_deletar['id']

    context.user_data['tarefas'] = [t for t in lista_original if t['id'] != id_a_deletar]
    
    descricao_deletada = tarefa_a_deletar['descricao']
    msg_confirmacao = f"🗑️ Tarefa '{descricao_deletada}' foi deletada com sucesso."
    await update.message.reply_text(msg_confirmacao)


# --- Função Principal ---

def main() -> None:
    """Inicia o bot e o mantém rodando."""
    if not TOKEN:
        logging.critical("O token do Telegram não foi encontrado! Verifique seu arquivo .env")
        return

    persistence = PicklePersistence(filepath="bot_persistence")
    application = Application.builder().token(TOKEN).persistence(persistence).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tutorial", tutorial))
    application.add_handler(CommandHandler("criartarefa", criar))
    application.add_handler(CommandHandler("listartarefas", listar))
    application.add_handler(CommandHandler("deletartarefa", deletar))
    
    logger.info("Bot iniciado...")
    application.run_polling()


if __name__ == '__main__':
    main()
