import os, logging, json, tempfile
from datetime import date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from ytmusicapi import YTMusic

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']

oauth_data = os.environ.get('YTMUSIC_OAUTH')
if oauth_data:
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.write(oauth_data)
    tmp.flush()
    ytmusic = YTMusic(tmp.name)
else:
    ytmusic = YTMusic('oauth.json')

daily_state: dict = {}

def get_or_create_playlist() -> str:
    today = date.today().strftime('%d-%m-%Y')
    global daily_state

    if daily_state.get('date') == today:
        return daily_state['playlist_id']

    name = f'jukebox it - {today}'
    playlist_id = ytmusic.create_playlist(
        title=name,
        description='Playlist del giorno - JukeBox IT'
    )
    daily_state = {
        'date': today,
        'playlist_id': playlist_id,
        'track_ids': set()
    }
    logger.info(f'Nuova playlist creata: {name} ({playlist_id})')
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

        playlist_id = get_or_create_playlist()

        if track_id in daily_state['track_ids']:
            await update.message.reply_text(
                f'⚠️ "{track_name}" di {artist} è già nella playlist di oggi!'
            )
            return

        ytmusic.add_playlist_items(playlist_id, [track_id])
        daily_state['track_ids'].add(track_id)

        await update.message.reply_text(
            f'✅ {user} ha aggiunto:\n'
            f'🎵 {track_name} — {artist}\n'
            f'📋 Playlist: jukebox it - {daily_state["date"]}'
        )

    except Exception as e:
        logger.error(f'Errore in add_song: {e}')
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
