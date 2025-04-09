import yt_dlp
import discord
import asyncio
from urllib.parse import urlparse, parse_qs
from discord import FFmpegPCMAudio
from .PlaylistBot import agregar_a_cola, obtener_proxima_cancion, obtener_cola

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
    """Busca una canción en YouTube y devuelve la URL limpia"""
    # Limpieza de URLs malformadas
    if 'youtube.com/watch?v=https://' in query:
        query = query.split('v=')[-1].split('&')[0]
        return f"https://www.youtube.com/watch?v={query}"
    
    if 'youtube.com/watch?' in query:
        parsed = urlparse(query)
        video_id = parse_qs(parsed.query).get('v', [''])[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    
    # Búsqueda normal si no es URL
    ydl_opts = {
        'format': 'bestaudio',
        'default_search': 'ytsearch1',
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
    """Obtiene canciones de una lista de YouTube"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'playlist_items': '1-100'  # Límite de 100 canciones
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_lista, download=False)
            return [
                f"https://www.youtube.com/watch?v={entry['id']}"
                for entry in info.get('entries', [])
                if entry
            ]
    except Exception as e:
        print(f"Error al obtener lista: {e}")
        return []

async def playyoutube(ctx, song):
    """Reproduce audio desde YouTube con sanitización de URLs"""
    # FIX 1: URLs duplicadas (caso crítico)
    if 'watch?v=https://' in song:
        song = song.split('v=')[-1].split('&')[0]
        song = f"https://www.youtube.com/watch?v={song}"
    
    # FIX 2: URLs con parámetros extra
    elif 'youtube.com/watch?' in song:
        parsed = urlparse(song)
        video_id = parse_qs(parsed.query).get('v', [''])[0]
        if video_id:
            song = f"https://www.youtube.com/watch?v={video_id}"
    
    voice_client = ctx.guild.voice_client
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'source_address': '0.0.0.0',
        'noplaylist': True,
        'extract_flat': False
    }

    ffmpeg_opts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    try:
        # Manejo de listas
        if 'list=' in song:
            canciones = obtenerlista(song)
            if canciones:
                for cancion in canciones:
                    agregar_a_cola(cancion)
                await ctx.send(f"🎵 Playlist agregada ({len(canciones)} canciones)")
                if not voice_client.is_playing():
                    await play_next(ctx)
                return
            else:
                await ctx.send("❌ No se pudo obtener la lista")
                return

        # Procesar canción individual
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(song, download=False)
            
            if 'entries' in info:  # Resultado de búsqueda
                info = info['entries'][0]
            
            if not info:
                await ctx.send("❌ Video no encontrado")
                return

            audio_source = FFmpegPCMAudio(
                source=info['url'],
                **ffmpeg_opts
            )

            def after_playing(error):
                if error:
                    print(f"Error after_playing: {error}")
                asyncio.run_coroutine_threadsafe(play_next(ctx), voice_client.loop)

            if voice_client.is_playing() or voice_client.is_paused():
                agregar_a_cola(song)
                await ctx.send(f"🎶 Añadido a cola: {info.get('title', '?')}")
            else:
                voice_client.play(audio_source, after=after_playing)
                await ctx.send(f"🎵 Reproduciendo: {info.get('title', '?')}")

    except yt_dlp.DownloadError as e:
        await ctx.send("❌ Error al descargar (¿URL válida?)")
        print(f"DownloadError: {e}")
    except discord.ClientException as e:
        await ctx.send("❌ Error de conexión con Discord")
        print(f"ClientException: {e}")
    except Exception as e:
        await ctx.send("❌ Error inesperado")
        print(f"Error en playyoutube: {e}")
        if voice_client.is_connected():
            await play_next(ctx)
