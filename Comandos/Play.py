import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import yt_dlp
from Recursos.RYoutube import *
from Recursos.PlaylistBot import *

def setup_music_commands(bot):
    @bot.command(name='p', help='Reproduce una canción o agrega a la cola')
    async def play(ctx, *, query):
        try:
            # Verificar si el usuario está en un canal de voz
            if not ctx.author.voice:
                return await ctx.send("🚫 Debes estar en un canal de voz para usar este comando")
            
            voice_client = ctx.voice_client
            
            # Conectar al canal si no está conectado
            if not voice_client:
                voice_client = await ctx.author.voice.channel.connect()
            
            # Manejar listas de reproducción
            if 'list=' in query:
                playlist = obtenerlista(query)
                if not playlist:
                    return await ctx.send("❌ No se pudo obtener la lista de reproducción")
                
                for song in playlist:
                    agregar_a_cola(song)
                
                await ctx.send(f"🎵 Se agregaron {len(playlist)} canciones a la cola")
                
                # Reproducir si no hay nada sonando
                if not voice_client.is_playing():
                    await play_next(ctx)
                return
            
            # Manejar búsqueda individual
            song_url = query if query.startswith('http') else Ysugerencia(query)
            if not song_url:
                return await ctx.send("❌ No se encontró la canción")
            
            # Agregar a la cola o reproducir inmediatamente
            if voice_client.is_playing() or voice_client.is_paused():
                agregar_a_cola(song_url)
                await ctx.send("🎶 Canción agregada a la cola")
            else:
                await playyoutube(ctx, song_url)
                
        except Exception as e:
            print(f"Error en comando play: {e}")
            await ctx.send("❌ Ocurrió un error al procesar tu solicitud")

    @bot.command(name='q', help='Sale del canal de voz')
    async def quit(ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_connected():
            limpiar_cola()
            await voice_client.disconnect()
            await ctx.send("👋 Desconectado del canal de voz")
        else:
            await ctx.send("🤔 No estoy conectado a ningún canal de voz")

    @bot.command(name='skip', help='Salta la canción actual')
    async def skip(ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await ctx.send("⏭️ Canción saltada")
        else:
            await ctx.send("❌ No hay nada reproduciéndose")

    @bot.command(name='queue', help='Muestra la cola de reproducción')
    async def show_queue(ctx):
        current_queue = obtener_cola()
        if not current_queue:
            return await ctx.send("📭 La cola está vacía")
        
        message = "🎵 **Cola de reproducción:**\n"
        for i, song in enumerate(current_queue[:10], 1):
            # Extraer ID del video para mostrar enlaces más limpios
            video_id = song.split('v=')[1][:11] if 'v=' in song else '...'
            message += f"{i}. https://youtu.be/{video_id}\n"
        
        if len(current_queue) > 10:
            message += f"\nY {len(current_queue) - 10} canciones más..."
        
        await ctx.send(message)

    @bot.command(name='pause', help='Pausa la reproducción')
    async def pause(ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send("⏸️ Reproducción pausada")
        else:
            await ctx.send("❌ No hay nada reproduciéndose")

    @bot.command(name='resume', help='Reanuda la reproducción')
    async def resume(ctx):
        voice_client = ctx.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ Reproducción reanudada")
        else:
            await ctx.send("❌ La reproducción no está pausada")

    @bot.command(name='clear', help='Limpia la cola de reproducción')
    async def clear_queue(ctx):
        limpiar_cola()
        await ctx.send("🧹 Cola de reproducción limpiada")

    async def play_next(ctx):
        """Función para reproducir la siguiente canción en la cola"""
        voice_client = ctx.voice_client
        if not voice_client or not voice_client.is_connected():
            return

        next_song = obtener_proxima_cancion()
        if next_song:
            await playyoutube(ctx, next_song)
        else:
            await voice_client.disconnect()
            await ctx.send("🎶 Reproducción finalizada")
