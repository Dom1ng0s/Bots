import nextcord
import os
import asyncio
import requests
from nextcord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

intents = nextcord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Login bem-sucedido como {bot.user}!')
    print(f'✅ ID do Bot: {bot.user.id}')
    print('✅ O bot está online e pronto para uso.')
    print('--------------------------------------')


@bot.slash_command(name="somar", description="soma dois numeros que voce escolher.")
async def somar_numeros(interaction: nextcord.Interaction, numero1: int, numero2: int):
    resultado = numero1 + numero2
    await interaction.response.send_message(f"O resultado de {numero1} + {numero2} = {resultado}")

@bot.slash_command(name="subtrair", description="Subtrai dois numeros que voce escolher.")
async def subtrair_numeros(interaction: nextcord.Interaction, numero1: int, numero2:int):
    resultado = numero1 - numero2
    await interaction.response.send_message(f"O resultado de {numero1} - {numero2} = {resultado}")

@bot.slash_command(name="multiplicar",description="Multiplica dois numeros que voce escolher.")
async def multiplicar_numeros(interaction: nextcord.Interaction, numero1: int, numero2:int):
    resultado = numero1 * numero2
    await interaction.response.send_message(f"O resultado de {numero1} x {numero2} = {resultado}")

@bot.slash_command(name="dividir",description="Divide dois numeros que voce escolher.")
async def dividir_numeros(interaction: nextcord.Interaction, numero1: int, numero2:int):
    if numero2 == 0:
        await interaction.response.send_message("Erro: Não é possível dividir por zero.")
        return
        
    resultado = numero1 / numero2
    await interaction.response.send_message(f"O resultado de {numero1} / {numero2} = {resultado}")

@bot.slash_command(name="temporizador",description="Avisa apos x unidades de tempo.")
async def temporizador(interaction: nextcord.Interaction, tempo: int, unidade: str):
    unidades_validas = ["segundos", "minutos", "horas"]
    if unidade.lower() not in unidades_validas:
        await interaction.response.send_message(f"Unidade inválida. Use uma das seguintes: {', '.join(unidades_validas)}", ephemeral=True)
        return
    
    if unidade.lower() == "segundos":
        segundos_totais = tempo 
    elif unidade.lower() == "minutos":
        segundos_totais = tempo*60
    elif unidade.lower() == "horas":
        segundos_totais = tempo*3600
    
    await interaction.response.send_message(f"Ok, {interaction.user.mention}! Temporizador definido para {tempo} {unidade}.")

    async def esperar_e_avisar():
        await asyncio.sleep(segundos_totais)
        await interaction.followup.send(f"⏰ **Bip bip, {interaction.user.mention}!** O seu temporizador de {tempo} {unidade} acabou!")

    asyncio.create_task(esperar_e_avisar())

@bot.slash_command(name="tempo",description="traz informacoes sobre o tempo ao vivo.")
async def tempo(interaction: nextcord.Interaction, cidade: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={WEATHER_API_KEY}"
    resposta = requests.get(url)
    if resposta.status_code == 200:
        ##print(resposta.status_code)
        ##await interaction.response.send_message("Buscando informações...")
        dados_clima = resposta.json()
        ##print(dados_clima)

        nome_cidade = dados_clima['name']
        temp_kelvin = dados_clima['main']['temp']
        temperatura_celsius = temp_kelvin - 273.15
        descricao = dados_clima['weather'][0]['description']
        umidade = dados_clima['main']['humidity']

        mensagem = (
                f"🌦️ **Tempo agora em {nome_cidade}**\n"
                f"--------------------------------------\n"
                f"🌡️ **Temperatura:** {temperatura_celsius:.1f}°C\n"
                f"📝 **Descrição:** {descricao.capitalize()}\n" 
                f"💧 **Umidade:** {umidade}%\n"
            )
        await interaction.response.send_message(mensagem)

    else:
        await interaction.response.send_message(f"Não consegui encontrar o tempo para a cidade '{cidade}'. Tem certeza que o nome está correto?")




bot.run(TOKEN)
