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


@bot.slash_command(name="tempo", description="Traz informações sobre o tempo ao vivo.")
async def tempo(interaction: nextcord.Interaction, cidade: str):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={cidade}"
        f"&appid={WEATHER_API_KEY}"
        f"&lang=pt_br"  
    )

    try:
        resposta = requests.get(url, timeout=5)
        
        resposta.raise_for_status()

        dados_clima = resposta.json()

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

        await interaction.response.send_message(embed=embed)

    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            await interaction.response.send_message(
                f"❌ Não consegui encontrar a cidade **'{cidade}'**. Por favor, verifique o nome e tente novamente."
            )
        elif err.response.status_code == 401:
            print("Erro 401: Chave da API inválida. Verifique seu arquivo .env.")
            await interaction.response.send_message(
                "❌ Ocorreu um erro de configuração no bot. O administrador foi notificado."
            )
        else:
            await interaction.response.send_message(
                f"❌ Ocorreu um erro com a API do clima (Código: {err.response.status_code}). Tente novamente mais tarde."
            )
    except requests.exceptions.RequestException:
        await interaction.response.send_message(
            "❌ Não foi possível conectar à API do clima. Verifique sua conexão ou tente novamente mais tarde."
        )

@bot.slash_command(name="dolar",description="Traz a cotação do dolar ao vivo.")
async def cotacao_dolar(interaction: nextcord.Interaction):


    url = "https://api.frankfurter.app/latest?from=USD&to=BRL"

    resposta = requests.get(url)

    if resposta.status_code == 200:
        dados = resposta.json()
        ##print(dados)
        taxa_brl = float(dados['rates']['BRL'])
        data_atualizacao = dados['date']
        embed = nextcord.Embed(
            title="💵 Cotação do Dólar",
            description=f"1 Dólar Americano (USD) equivale a **R$ {taxa_brl:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."),
            color=nextcord.Color.blue()
        )
        
        embed.set_footer(text=f"Dados do Banco Central Europeu | Atualizado em: {data_atualizacao}")

        await interaction.response.send_message(embed=embed)
    else:
        print("A")
        await interaction.response.send_message("Falha ao buscar a cotação do dólar.")




@bot.slash_command(name="euro",description="Traz a cotação do Euro ao vivo.")
async def cotacao_euro(interaction: nextcord.Interaction):


    url = "https://api.frankfurter.app/latest?from=EUR&to=BRL"

    resposta = requests.get(url)

    if resposta.status_code == 200:
        dados = resposta.json()
        ##print(dados)
        taxa_brl = float(dados['rates']['BRL'])
        data_atualizacao = dados['date']
        embed = nextcord.Embed(
            title="💵 Cotação do Euro",
            description=f"1 Euro (EUR) equivale a **R$ {taxa_brl:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."),
            color=nextcord.Color.blue()
        )
        
        embed.set_footer(text=f"Dados do Banco Central Europeu | Atualizado em: {data_atualizacao}")

        await interaction.response.send_message(embed=embed)
    else:
        print("A")
        await interaction.response.send_message("Falha ao buscar a cotação do Euro.")
    




bot.run(TOKEN)
