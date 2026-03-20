import os, logging, json, tempfile, traceback
from datetime import date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN non trovato!")

def get_youtube_client():
    token_data = os.environ.get('GOOGLE_TOKEN')
    if token_data:
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        tmp.write(token_data)
        tmp.flush()
        token_file = tmp.name
    else:
        token_file = 'google_token.json'

    creds = Credentials.from_authorized_user_file(
        token_file,
        scopes=['https://www.googleapis.com/auth/youtube']
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds)

daily_state: dict = {}

def get_or_create_playlist(youtube) -> str:
    today = date.today().strftime('%d-%m-%Y')
    global daily_state

    if daily_state.get('date') == today:
        return daily_state['playlist_id']

    name = f'jukebox it - {today}'
    logger.info(f'Creo playlist: {name}')

    response = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title': name,
                'description': 'Playlist del giorno - JukeBox IT'
            },
            'status': {
                'privacyStatus': 'public'
            }
        }
    ).execute()

    playlist_id = response['id']
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
        youtube = get_youtube_client()

        logger.info(f'Ricerca brano: {query}')
        search_response = youtube.search().list(
            part='snippet',
            q=query,
            type='video',
            videoCategoryId='10',
            maxResults=1
        ).execute()

        items = search_response.get('items', [])
        if not items:
            await update.message.reply_text(
                f'🔍 Brano non trovato: "{query}"\n'
                f'Prova con un formato diverso, es. /add Artista - Titolo'
            )
            return

        video_id    = items[0]['id']['videoId']
        video_title = items[0]['snippet']['title']
        channel     = items[0]['snippet']['channelTitle']

        logger.info(f'Brano trovato: {video_title} ({video_id})')

        playlist_id = get_or_create_playlist(youtube)

        if video_id in daily_state['track_ids']:
            await update.message.reply_text(
                f'⚠️ "{video_title}" è già nella playlist di oggi!'
            )
            return

        youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        ).execute()

        daily_state['track_ids'].add(video_id)

        await update.message.reply_text(
            f'✅ {user} ha aggiunto:\n'
            f'🎵 {video_title}\n'
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
