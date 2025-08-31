import nextcord
import os
import asyncio
import requests
from nextcord.ext import commands
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
TOKEN = os.getenv('TOKEN')
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Define as intenções do bot (Intents)
intents = nextcord.Intents.all()

# Cria a instância do bot
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Eventos do Bot ---

@bot.event
async def on_ready():
    """Este evento é acionado quando o bot se conecta com sucesso ao Discord."""
    print(f'✅ Login bem-sucedido como {bot.user}!')
    print(f'✅ ID do Bot: {bot.user.id}')
    print('✅ O bot está online e pronto para uso.')
    print('--------------------------------------')

# --- Comandos de Calculadora (Simples, não precisam de defer) ---

@bot.slash_command(name="somar", description="Soma dois números que você escolher.")
async def somar_numeros(interaction: nextcord.Interaction, numero1: int, numero2: int):
    resultado = numero1 + numero2
    await interaction.response.send_message(f"O resultado de {numero1} + {numero2} = {resultado}")

@bot.slash_command(name="subtrair", description="Subtrai dois números que você escolher.")
async def subtrair_numeros(interaction: nextcord.Interaction, numero1: int, numero2: int):
    resultado = numero1 - numero2
    await interaction.response.send_message(f"O resultado de {numero1} - {numero2} = {resultado}")

@bot.slash_command(name="multiplicar", description="Multiplica dois números que você escolher.")
async def multiplicar_numeros(interaction: nextcord.Interaction, numero1: int, numero2: int):
    resultado = numero1 * numero2
    await interaction.response.send_message(f"O resultado de {numero1} x {numero2} = {resultado}")

@bot.slash_command(name="dividir", description="Divide dois números que você escolher.")
async def dividir_numeros(interaction: nextcord.Interaction, numero1: int, numero2: int):
    if numero2 == 0:
        await interaction.response.send_message("Erro: Não é possível dividir por zero.")
        return
        
    resultado = numero1 / numero2
    await interaction.response.send_message(f"O resultado de {numero1} / {numero2} = {resultado}")

# --- Comandos de Utilidade ---

@bot.slash_command(name="temporizador", description="Avisa após x unidades de tempo.")
async def temporizador(interaction: nextcord.Interaction, tempo: int, unidade: str):
    unidades_validas = ["segundos", "minutos", "horas"]
    if unidade.lower() not in unidades_validas:
        await interaction.response.send_message(f"Unidade inválida. Use uma das seguintes: {', '.join(unidades_validas)}", ephemeral=True)
        return
    
    if unidade.lower() == "segundos":
        segundos_totais = tempo 
    elif unidade.lower() == "minutos":
        segundos_totais = tempo * 60
    elif unidade.lower() == "horas":
        segundos_totais = tempo * 3600
    
    # Resposta inicial rápida
    await interaction.response.send_message(f"Ok, {interaction.user.mention}! Temporizador definido para {tempo} {unidade}.")

    # Tarefa em segundo plano para enviar o aviso depois
    async def esperar_e_avisar():
        await asyncio.sleep(segundos_totais)
        await interaction.followup.send(f"⏰ **Bip bip, {interaction.user.mention}!** O seu temporizador de {tempo} {unidade} acabou!")

    asyncio.create_task(esperar_e_avisar())

# --- Comandos com API (Corrigidos com defer e followup) ---

@bot.slash_command(name="tempo", description="Traz informações sobre o tempo ao vivo.")
async def tempo(interaction: nextcord.Interaction, cidade: str):
    # AVISA o Discord que o comando está sendo processado
    await interaction.response.defer()

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={cidade}&appid={WEATHER_API_KEY}&lang=pt_br"
    )

    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        dados_clima = resposta.json()

        # Extração e formatação dos dados
        nome_cidade = dados_clima['name']
        temp_kelvin = dados_clima['main']['temp']
        sensacao_kelvin = dados_clima['main']['feels_like']
        descricao = dados_clima['weather'][0]['description'].capitalize()
        umidade = dados_clima['main']['humidity']
        velocidade_vento = dados_clima['wind']['speed']
        icone_clima = dados_clima['weather'][0]['icon']
        url_icone = f"http://openweathermap.org/img/wn/{icone_clima}@2x.png"
        
        temperatura_celsius = temp_kelvin - 273.15
        sensacao_celsius = sensacao_kelvin - 273.15
        velocidade_vento_kmh = velocidade_vento * 3.6

        # Criação do Embed
        embed = nextcord.Embed(
            title=f"🌦️ Clima em {nome_cidade}",
            description=f"**{descricao}**",
            color=nextcord.Color.blue()
        )
        embed.set_thumbnail(url=url_icone)
        embed.add_field(name="🌡️ Temperatura", value=f"{temperatura_celsius:.1f}°C", inline=True)
        embed.add_field(name="🤔 Sensação Térmica", value=f"{sensacao_celsius:.1f}°C", inline=True)
        embed.add_field(name="💧 Umidade", value=f"{umidade}%", inline=True)
        embed.add_field(name="🍃 Vento", value=f"{velocidade_vento_kmh:.1f} km/h", inline=True)
        embed.set_footer(text="Dados fornecidos por OpenWeatherMap")

        # ENVIA a resposta final usando followup
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Ocorreu um erro no comando /tempo: {e}")
        # ENVIA a mensagem de erro usando followup
        await interaction.followup.send(f"❌ Não consegui encontrar o tempo para a cidade '{cidade}'. Verifique se o nome está correto e tente novamente.")

@bot.slash_command(name="dolar", description="Traz a cotação do dólar ao vivo.")
async def dolar(interaction: nextcord.Interaction):
    # AVISA o Discord que o comando está sendo processado
    await interaction.response.defer()
    
    url = "https://api.frankfurter.app/latest?from=USD&to=BRL"

    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        
        dados = resposta.json()
        
        taxa_brl = float(dados['rates']['BRL'])
        data_atualizacao = dados['date']
        
        embed = nextcord.Embed(
            title="💵 Cotação do Dólar",
            description=f"1 Dólar Americano (USD) equivale a **R$ {taxa_brl:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."),
            color=nextcord.Color.green()
        )
        embed.set_footer(text=f"Dados do Banco Central Europeu | Atualizado em: {data_atualizacao}")

        # ENVIA a resposta final usando followup
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        print(f"Ocorreu um erro no comando /dolar: {e}")
        # ENVIA a mensagem de erro usando followup
        await interaction.followup.send("❌ Desculpe, não consegui buscar a cotação do dólar agora. Tente novamente mais tarde.")

@bot.slash_command(name="euro", description="Traz a cotação do Euro ao vivo.")
async def euro(interaction: nextcord.Interaction):
    # AVISA o Discord que o comando está sendo processado
    await interaction.response.defer()
    
    url = "https://api.frankfurter.app/latest?from=EUR&to=BRL"

    try:
        resposta = requests.get(url, timeout=10)
        resposta.raise_for_status()
        
        dados = resposta.json()
        
        taxa_brl = float(dados['rates']['BRL'])
        data_atualizacao = dados['date']
        
        embed = nextcord.Embed(
            title="💶 Cotação do Euro",
            description=f"1 Euro (EUR) equivale a **R$ {taxa_brl:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."),
            color=nextcord.Color.dark_blue()
        )
        embed.set_footer(text=f"Dados do Banco Central Europeu | Atualizado em: {data_atualizacao}")

        # ENVIA a resposta final usando followup
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Ocorreu um erro no comando /euro: {e}")
        # ENVIA a mensagem de erro usando followup
        await interaction.followup.send("❌ Desculpe, não consegui buscar a cotação do Euro agora. Tente novamente mais tarde.")

# --- Inicia o Bot ---
bot.run(TOKEN)
