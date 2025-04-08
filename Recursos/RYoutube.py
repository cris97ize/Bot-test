import yt_dlp
import discord
import asyncio
from discord import FFmpegPCMAudio
from PlaylistBot import agregar_a_cola, obtener_proxima_cancion, obtener_cola

async def play_next(ctx):
    """Reproduce la siguiente canción en la cola"""
    voice_client = ctx.guild.voice_client
    if not voice_client or not voice_client.is_connected():
        return

    next_song = obtener_proxima_cancion()
    if next_song:
        await playyoutube(ctx, next_song)
    else:
        await voice_client.disconnect()
        await ctx.send("🎶 Lista de reproducción finalizada")

def Ysugerencia(query):
    """Busca una canción en YouTube y devuelve la URL"""
    ydl_opts = {
        'format': 'bestaudio',
        'default_search': 'ytsearch',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in info and info['entries']:
                return f"https://www.youtube.com/watch?v={info['entries'][0]['url']}"
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    
    return None

def obtenerlista(url_lista):
    """Obtiene todas las canciones de una lista de YouTube"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True
    }

    canciones = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_lista, download=False)
            
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        url = f"https://www.youtube.com/watch?v={entry['id']}"
                        canciones.append(url)
                
                print(f"Lista obtenida con {len(canciones)} canciones")
                return canciones
    except Exception as e:
        print(f"Error al obtener lista: {e}")
    
    return []

async def playyoutube(ctx, song):
    """Reproduce una canción desde YouTube"""
    voice_client = ctx.guild.voice_client
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0',
        'noplaylist': True
    }

    ffmpeg_options = {
        'options': '-vn',
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    }

    try:
        # Verificar si es una URL de lista
        if 'list=' in song:
            canciones = obtenerlista(song)
            if canciones:
                for cancion in canciones:
                    agregar_a_cola(cancion)
                
                await ctx.send(f"🎵 Playlist agregada: {len(canciones)} canciones")
                if not voice_client.is_playing():
                    await play_next(ctx)
                return
            else:
                await ctx.send("❌ No se pudo obtener la lista de reproducción")
                return

        # Procesar canción individual
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song, download=False)
            
            # Manejar resultados de búsqueda
            if 'entries' in info:
                info = info['entries'][0]
            
            if not info:
                await ctx.send("❌ No se encontró la canción")
                return

            url = info['url']
            title = info.get('title', 'Canción desconocida')
            duration = info.get('duration', 0)

            # Configurar fuente de audio
            audio_source = discord.FFmpegPCMAudio(
                source=url,
                **ffmpeg_options
            )

            # Reproducir o encolar
            if voice_client.is_playing() or voice_client.is_paused():
                agregar_a_cola(song)
                await ctx.send(f"🎶 Añadido a la cola: **{title}** ({duration}s)")
            else:
                def after_playing(error):
                    coro = play_next(ctx)
                    fut = asyncio.run_coroutine_threadsafe(coro, voice_client.loop)
                    try:
                        fut.result()
                    except:
                        pass

                voice_client.play(audio_source, after=after_playing)
                await ctx.send(f"🎵 Reproduciendo: **{title}** ({duration}s)")

    except Exception as e:
        print(f"Error en reproducción: {str(e)}")
        await ctx.send("❌ Error al procesar la canción")
        if voice_client.is_connected():
            await play_next(ctx)