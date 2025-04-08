import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from Comandos.Play import setup_music_commands

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('token_discord')

# Configuración de intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

# Crear instancia del bot
bot = commands.Bot(
    command_prefix='|',
    intents=intents,
    help_command=None  # Deshabilitamos el help por defecto para personalizarlo
)

@bot.event
async def on_ready():
    """Evento cuando el bot está listo"""
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="música | |help"
        ),
        status=discord.Status.online
    )
    print(f'Bot conectado como {bot.user.name}')
    
    # Configurar comandos de música
    setup_music_commands(bot)

@bot.command()
async def help(ctx):
    """Muestra los comandos disponibles"""
    embed = discord.Embed(
        title="🎵 Comandos del Bot de Música",
        description="Prefijo: `|`",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🎶 Música",
        value=(
            "`p <canción/url>` - Reproduce o añade a cola\n"
            "`skip` - Salta la canción actual\n"
            "`queue` - Muestra la cola de reproducción\n"
            "`pause` - Pausa la reproducción\n"
            "`resume` - Reanuda la reproducción\n"
            "`q` - Desconecta el bot\n"
            "`clear` - Limpia la cola"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Otros Comandos",
        value=(
            "`help` - Muestra esta ayuda\n"
            "`info` - Muestra información del bot"
        ),
        inline=False
    )
    
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command()
async def info(ctx):
    """Información básica del bot"""
    embed = discord.Embed(
        title="🤖 Información del Bot",
        description="Bot de música para Discord con soporte para listas de reproducción",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Desarrollador", value="[Tu nombre]", inline=True)
    embed.add_field(name="Versión", value="1.0", inline=True)
    embed.add_field(name="Prefijo", value="`|`", inline=True)
    embed.add_field(name="Librería", value="discord.py", inline=True)
    embed.add_field(name="Soporte", value="[Servidor de soporte](https://discord.gg/tulink)", inline=True)
    
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    """Evento para procesar mensajes"""
    # Ignorar mensajes del propio bot
    if message.author == bot.user:
        return
    
    # Respuesta automática a saludos
    if message.content.lower() in ('hola', 'hello', 'hi'):
        await message.channel.send(f'¡Hola {message.author.mention}! Usa `|help` para ver mis comandos')
    
    # Procesar comandos
    await bot.process_commands(message)

def run_bot():
    """Función principal para iniciar el bot"""
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("Error: Token inválido. Verifica tu archivo .env")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    run_bot()