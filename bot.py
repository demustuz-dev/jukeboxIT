import os, logging, json, tempfile, traceback
from datetime import date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from ytmusicapi import YTMusic

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN non trovato!")

ytmusic = YTMusic('ytmusic_auth.json')

daily_state: dict = {}

def get_or_create_playlist() -> str:
    today = date.today().strftime('%d-%m-%Y')
    global daily_state

    if daily_state.get('date') == today:
        return daily_state['playlist_id']

    name = f'jukebox it - {today}'
    logger.info(f'Creo playlist: {name}')
    playlist_id = ytmusic.create_playlist(
        title=name,
        description='Playlist del giorno - JukeBox IT'
    )
    logger.info(f'Playlist creata con ID: {playlist_id}')
    daily_state = {
        'date': today,
        'playlist_id': playlist_id,
        'track_ids': set()
    }
    return playlist_id

async def add_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            '❌ Formato: /add Titolo - Artista\n'
            'Esempio: /add Bohemian Rhapsody - Queen'
        )
        return

    query = ' '.join(context.args)
    user  = update.effective_user.first_name

    try:
        logger.info(f'Ricerca brano: {query}')
        results = ytmusic.search(query, filter='songs', limit=1)

        if not results:
            await update.message.reply_text(
                f'🔍 Brano non trovato: "{query}"\n'
                f'Prova con un formato diverso, es. /add Artista - Titolo'
            )
            return

        track      = results[0]
        track_id   = track['videoId']
        track_name = track['title']
        artist     = track['artists'][0]['name']

        logger.info(f'Brano trovato: {track_name} - {artist} ({track_id})')

        playlist_id = get_or_create_playlist()

        if track_id in daily_state['track_ids']:
            await update.message.reply_text(
                f'⚠️ "{track_name}" di {artist} è già nella playlist di oggi!'
            )
            return

        logger.info(f'Aggiungo brano {track_id} alla playlist {playlist_id}')
        ytmusic.add_playlist_items(playlist_id, [track_id])
        daily_state['track_ids'].add(track_id)

        await update.message.reply_text(
            f'✅ {user} ha aggiunto:\n'
            f'🎵 {track_name} — {artist}\n'
            f'📋 Playlist: jukebox it - {daily_state["date"]}'
        )

    except Exception as e:
        logger.error(f'Errore completo: {traceback.format_exc()}')
        await update.message.reply_text(
            '❌ Si è verificato un errore. Riprova tra qualche istante.'
        )

async def show_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not daily_state.get('playlist_id'):
        await update.message.reply_text(
            '📋 Nessuna playlist ancora oggi. '
            'Usa /add per aggiungere il primo brano!'
        )
        return

    pid   = daily_state['playlist_id']
    url   = f'https://music.youtube.com/playlist?list={pid}'
    count = len(daily_state['track_ids'])
    await update.message.reply_text(
        f'📋 Playlist di oggi ({daily_state["date"]}): {count} brani\n{url}'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🎵 JukeBox IT — Comandi:\n\n'
        '/add Titolo - Artista  →  Aggiunge un brano alla playlist\n'
        '/playlist              →  Link alla playlist di oggi\n'
        '/help                  →  Mostra questo messaggio'
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('add',      add_song))
    app.add_handler(CommandHandler('playlist', show_playlist))
    app.add_handler(CommandHandler('help',     help_cmd))
    logger.info('Bot JukeBox IT avviato.')
    app.run_polling()

if __name__ == '__main__':
    main()
