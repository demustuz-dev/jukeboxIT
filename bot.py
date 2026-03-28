import os, logging, json, tempfile, traceback, random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
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

DAILY_LIMIT = 60

# ── Liste canzoni per mood ────────────────────────────────────────────────────

MOOD_ENERGICO = [
    "AC/DC - Thunderstruck", "AC/DC - Back in Black", "AC/DC - Highway to Hell",
    "Metallica - Enter Sandman", "Metallica - Master of Puppets", "Metallica - One",
    "Nirvana - Smells Like Teen Spirit", "Nirvana - Come as You Are",
    "Foo Fighters - Everlong", "Foo Fighters - Best of You",
    "Green Day - Basket Case", "Green Day - American Idiot", "Green Day - Boulevard of Broken Dreams",
    "The Offspring - Come Out and Play", "The Offspring - Self Esteem",
    "Rage Against the Machine - Killing in the Name",
    "Rage Against the Machine - Bulls on Parade",
    "System of a Down - Chop Suey", "System of a Down - B.Y.O.B.",
    "Slipknot - Wait and Bleed", "Slipknot - Duality",
    "Linkin Park - In the End", "Linkin Park - Numb", "Linkin Park - Breaking the Habit",
    "Muse - Uprising", "Muse - Supermassive Black Hole", "Muse - Knights of Cydonia",
    "Queens of the Stone Age - No One Knows",
    "The White Stripes - Seven Nation Army",
    "Arctic Monkeys - R U Mine?", "Arctic Monkeys - Brianstorm",
    "Blink-182 - All the Small Things", "Blink-182 - What's My Age Again?",
    "Sum 41 - In Too Deep", "Sum 41 - Fat Lip",
    "Paramore - Misery Business", "Paramore - Ignorance",
    "My Chemical Romance - Welcome to the Black Parade",
    "My Chemical Romance - I'm Not Okay",
    "Fall Out Boy - Sugar We're Goin Down",
    "Panic! at the Disco - I Write Sins Not Tragedies",
    "Iron Maiden - The Trooper", "Iron Maiden - Run to the Hills",
    "Judas Priest - Breaking the Law", "Judas Priest - Painkiller",
    "Black Sabbath - Paranoid", "Black Sabbath - Iron Man",
    "Ozzy Osbourne - Crazy Train",
    "Deep Purple - Smoke on the Water", "Deep Purple - Highway Star",
    "Led Zeppelin - Whole Lotta Love", "Led Zeppelin - Rock and Roll",
    "The Rolling Stones - Jumpin' Jack Flash",
    "Guns N' Roses - Welcome to the Jungle", "Guns N' Roses - Paradise City",
    "Aerosmith - Walk This Way",
    "Van Halen - Jump", "Van Halen - Panama",
    "Bon Jovi - Livin' on a Prayer", "Bon Jovi - You Give Love a Bad Name",
    "Bruce Springsteen - Born to Run",
    "Tom Petty - I Won't Back Down",
    "Red Hot Chili Peppers - Can't Stop", "Red Hot Chili Peppers - Give It Away",
    "Pearl Jam - Even Flow", "Pearl Jam - Alive",
    "Soundgarden - Black Hole Sun", "Soundgarden - Spoonman",
    "Alice in Chains - Rooster", "Alice in Chains - Would?",
    "Stone Temple Pilots - Plush",
    "Audioslave - Like a Stone", "Audioslave - Cochise",
    "The Killers - Mr. Brightside", "The Killers - Somebody Told Me",
    "Interpol - Obstacle 1",
    "Franz Ferdinand - Take Me Out",
    "Kaiser Chiefs - I Predict a Riot",
    "The Hives - Hate to Say I Told You So",
    "The Strokes - Last Nite", "The Strokes - Reptilia",
    "Wolfmother - Woman",
    "Airbourne - Runnin' Wild",
    "Motörhead - Ace of Spades",
    "Ramones - Blitzkrieg Bop", "Ramones - I Wanna Be Sedated",
    "Sex Pistols - Anarchy in the U.K.",
    "The Clash - Should I Stay or Should I Go",
    "The Clash - London Calling",
    # Italiani
    "Subsonica - Nuvole Rapide", "Subsonica - Tutti i Miei Sbagli",
    "Verdena - Valvonauta", "Verdena - Nel Caso",
    "Afterhours - Male di Miele", "Afterhours - Quello che non c'è",
    "Litfiba - El Diablo", "Litfiba - Tex",
    "CCCP - Curami", "CCCP - Punk Islam",
    "CSI - Giù la testa",
    "Ministri - In questa città", "Ministri - Senza Titolo",
    "Tre Allegri Ragazzi Morti - La mia ragazza è un grande cane",
    "Le Luci della Centrale Elettrica - Senza di te non sono capace",
    "Marlene Kuntz - Nuotando nell'aria",
    "Massimo Volume - Lungo i bordi",
    "Perturbazione - La donna di un mio amico",
    "Zu - Ostia",
    "Julie's Haircut - Inverno Nucleare",
    "Giardini di Mirò - Punk. Not Diet.",
    "Lacuna Coil - Swamped", "Lacuna Coil - Heaven's a Lie",
    "Donatello - Cane Marrone",
    "Fast Animals and Slow Kids - Velocità",
    "Baustelle - La guerra è finita",
    "Zen Circus - L'anima non conta",
    "Diaframma - Siberia",
    "Timoria - Sangue Impazzito",
    "Negrita - Cambio", "Negrita - In ogni atomo",
    "Stadio - Acqua e sapone",
    "883 - Rotta per casa di Dio",
    "Vasco Rossi - Albachiara", "Vasco Rossi - Vita spericolata",
    "Zucchero - Dune Mosse",
    "Almamegretta - Figli di Annibale",
    "99 Posse - Curre Curre Guagliò",
    "Assalti Frontali - Roma Capoccia",
    "Linea 77 - Kakkoi",
    "Rezophonic - The One",
    "Vanilla Sky - Drops of Jupiter",
    "A Perfect Circle - Judith",
    "Tool - Schism", "Tool - Sober",
    "Deftones - Change", "Deftones - My Own Summer",
    "Korn - Freak on a Leash", "Korn - Blind",
    "Disturbed - Down with the Sickness",
    "Breaking Benjamin - The Diary of Jane",
    "Three Days Grace - Animal I Have Become",
    "Shinedown - Second Chance",
    "Seether - Fake It",
    "Hinder - Lips of an Angel",
    "Nickelback - How You Remind Me",
    "Creed - With Arms Wide Open",
    "Godsmack - I Stand Alone",
    "Staind - It's Been a While",
    "Evanescence - Going Under", "Evanescence - Bring Me to Life",
    "Within Temptation - What Have You Done",
    "Nightwish - Nemo",
    "HIM - Join Me in Death",
    "The 69 Eyes - Lost Boys",
    "Rammstein - Du Hast", "Rammstein - Sonne",
    "KMFDM - Drug Against War",
    "Marilyn Manson - The Beautiful People",
    "Nine Inch Nails - Closer", "Nine Inch Nails - Head Like a Hole",
    "Ministry - Jesus Built My Hotrod",
    "Danko Jones - First Date",
    "Monster Magnet - Space Lord",
    "Fu Manchu - King of the Road",
    "Clutch - Electric Worry",
    "Mastodon - Blood and Thunder",
    "Baroness - Take My Bones Away",
    "Gojira - L'Enfant Sauvage",
    "Meshuggah - Bleed",
    "Converge - All We Love We Leave Behind",
    "Refused - New Noise",
    "At the Drive-In - One Armed Scissor",
    "The Mars Volta - L'Via L'Viaquez",
    "Biffy Clyro - Mountains",
    "Frank Turner - Recovery",
    "Dropkick Murphys - I'm Shipping Up to Boston",
    "Flogging Molly - Drunken Lullabies",
    "Gogol Bordello - Start Wearing Purple",
    "The Gaslight Anthem - The '59 Sound",
]

MOOD_FELICE = [
    "Pharrell Williams - Happy",
    "Katrina and the Waves - Walking on Sunshine",
    "Katy Perry - Roar", "Katy Perry - Firework", "Katy Perry - Teenage Dream",
    "Dua Lipa - Levitating", "Dua Lipa - Don't Start Now", "Dua Lipa - Physical",
    "Lizzo - Good as Hell", "Lizzo - Juice",
    "Bruno Mars - Uptown Funk", "Bruno Mars - 24K Magic", "Bruno Mars - Treasure",
    "Mark Ronson - Uptown Funk",
    "Justin Timberlake - Can't Stop the Feeling",
    "Carly Rae Jepsen - Call Me Maybe",
    "Meghan Trainor - All About That Bass",
    "Taylor Swift - Shake It Off", "Taylor Swift - 22",
    "Ariana Grande - 7 Rings", "Ariana Grande - Thank U Next",
    "Beyoncé - Love on Top", "Beyoncé - Crazy in Love",
    "Lady Gaga - Just Dance", "Lady Gaga - Bad Romance",
    "Rihanna - We Found Love", "Rihanna - Only Girl",
    "Nicki Minaj - Super Bass",
    "Kesha - TiK ToK",
    "Miley Cyrus - Party in the U.S.A.",
    "Selena Gomez - Come & Get It",
    "One Direction - What Makes You Beautiful",
    "Jonas Brothers - Sucker",
    "BTS - Dynamite",
    "BlackPink - How You Like That",
    "Kylie Minogue - Can't Get You Out of My Head",
    "Spice Girls - Wannabe",
    "Backstreet Boys - Everybody",
    "NSYNC - Bye Bye Bye",
    "Britney Spears - ...Baby One More Time", "Britney Spears - Toxic",
    "Christina Aguilera - Genie in a Bottle",
    "Destiny's Child - Survivor",
    "TLC - No Scrubs",
    "En Vogue - Don't Let Go",
    "Gloria Gaynor - I Will Survive",
    "Donna Summer - Hot Stuff",
    "ABBA - Dancing Queen", "ABBA - Gimme! Gimme! Gimme!",
    "Bee Gees - Stayin' Alive",
    "Michael Jackson - Don't Stop 'Til You Get Enough",
    "Michael Jackson - Billie Jean",
    "Prince - Let's Go Crazy",
    "David Bowie - Let's Dance",
    "Earth, Wind & Fire - September",
    "Stevie Wonder - Sir Duke",
    "Chic - Le Freak",
    "Sister Sledge - We Are Family",
    "Village People - Y.M.C.A.",
    "Rick James - Super Freak",
    "Nile Rodgers - Good Times",
    "Daft Punk - Get Lucky", "Daft Punk - Around the World",
    "Calvin Harris - Summer", "Calvin Harris - Feel So Close",
    "Avicii - Wake Me Up", "Avicii - Levels",
    "David Guetta - Titanium", "David Guetta - When Love Takes Over",
    "Zedd - Clarity",
    "Martin Garrix - Animals",
    "Kygo - Firestone",
    "Clean Bandit - Rather Be",
    "Mark Ronson - Valerie",
    "Amy Winehouse - Valerie",
    "Adele - Rolling in the Deep",
    "Ed Sheeran - Shape of You", "Ed Sheeran - Happier",
    "Harry Styles - Watermelon Sugar",
    "Post Malone - Sunflower",
    "Billie Eilish - bad guy",
    "Olivia Rodrigo - good 4 u",
    "Doja Cat - Say So",
    "Megan Thee Stallion - Savage",
    "Cardi B - I Like It",
    "Jack Harlow - What's Poppin",
    "Roddy Ricch - The Box",
    "24kGoldn - Mood",
    "Masked Wolf - Astronaut in the Ocean",
    "The Kid LAROI - Without You",
    "Lewis Capaldi - Someone You Loved",
    "Sam Smith - Stay With Me",
    "Hozier - Take Me to Church",
    # Italiani
    "Jovanotti - L'ombelico del mondo", "Jovanotti - Baciami ancora",
    "Zucchero - Senza una donna",
    "Eros Ramazzotti - Più bella cosa",
    "Laura Pausini - La solitudine",
    "Elisa - Luce",
    "Negramaro - Mentre tutto scorre",
    "Giorgia - Di sole e d'azzurro",
    "Fiorella Mannoia - Quello che le donne non dicono",
    "Ligabue - Certe notti",
    "Vasco Rossi - Sally",
    "883 - Come mai", "883 - Nord sud ovest est",
    "Articolo 31 - Domani smetto",
    "Eiffel 65 - Blue (Da Ba Dee)",
    "Alex Britti - Solo una volta",
    "Lucio Battisti - Emozioni",
    "Lucio Dalla - Caruso",
    "Francesco De Gregori - La donna cannone",
    "Fabrizio De André - La canzone di Marinella",
    "Paolo Conte - Via con me",
    "Pino Daniele - Napule è",
    "Riccardo Cocciante - Margherita",
    "Umberto Tozzi - Ti amo",
    "Antonello Venditti - Notte prima degli esami",
    "Gianna Nannini - Bello e impossibile",
    "Irene Grandi - Bruci la città",
    "Claudio Baglioni - Questo piccolo grande amore",
    "Tiziano Ferro - Ed ero contentissimo",
    "Marco Mengoni - L'essenziale",
    "Fedez - Cigno nero",
    "Ghali - DNA",
    "Mahmood - Soldi",
    "Annalisa - Bellissima",
    "Blanco - La canzone nostra",
    "Sangiovanni - Malibu",
    "Aka 7even - Loca",
    "Boomdabash - Non ti dico no",
    "The Kolors - Everytime",
    "Gabry Ponte - Luna",
    "Prezioso - Tell Me Why",
    "Corona - The Rhythm of the Night",
    "Sandy Marton - People from Ibiza",
    "Gigi D'Agostino - L'amour toujours",
    "Robert Miles - Children",
    "Mauro Picotto - Iguana",
    "Molella - Gimme Some Lovin",
    "Alexia - Summer Is Crazy",
    "Haiducii - Dragostea Din Tei",
    "O-Zone - Dragostea Din Tei",
    "Tarkan - Şımarık",
    "Loona - Vamos a la Playa",
    "Los del Rio - Macarena",
    "Ricky Martin - Livin' la Vida Loca",
    "Marc Anthony - Vivir Mi Vida",
    "Shakira - Hips Don't Lie",
    "Jennifer Lopez - On the Floor",
    "Pitbull - Give Me Everything",
    "Enrique Iglesias - Bailando",
    "Bad Bunny - Dakiti",
    "J Balvin - Con Calma",
    "Maluma - Felices los 4",
]

MOOD_TRISTE = [
    "Adele - Someone Like You", "Adele - Hello", "Adele - When We Were Young",
    "Sam Smith - Stay With Me", "Sam Smith - Too Good at Goodbyes",
    "Lewis Capaldi - Someone You Loved", "Lewis Capaldi - Before You Go",
    "Billie Eilish - when the party's over", "Billie Eilish - ilomilo",
    "Taylor Swift - All Too Well", "Taylor Swift - The 1", "Taylor Swift - exile",
    "Olivia Rodrigo - drivers license", "Olivia Rodrigo - traitor",
    "Lana Del Rey - Summertime Sadness", "Lana Del Rey - Young and Beautiful",
    "Amy Winehouse - Back to Black", "Amy Winehouse - Love Is a Losing Game",
    "The Weeknd - Call Out My Name", "The Weeknd - Wicked Games",
    "Frank Ocean - Forrest Gump", "Frank Ocean - Thinking Bout You",
    "James Arthur - Say You Won't Let Go",
    "Shawn Mendes - Treat You Better",
    "Justin Bieber - Ghost",
    "Ed Sheeran - The A Team", "Ed Sheeran - Supermarket Flowers",
    "Coldplay - The Scientist", "Coldplay - Fix You", "Coldplay - Warning Sign",
    "Radiohead - Creep", "Radiohead - Fake Plastic Trees",
    "R.E.M. - Everybody Hurts",
    "The Fray - How to Save a Life",
    "Snow Patrol - Chasing Cars",
    "Damien Rice - The Blower's Daughter",
    "James Blunt - You're Beautiful", "James Blunt - Goodbye My Lover",
    "Keane - Somewhere Only We Know",
    "Elbow - One Day Like This",
    "Sigur Rós - Hoppípolla",
    "Bon Iver - Skinny Love", "Bon Iver - Holocene",
    "Iron & Wine - Naked As We Came",
    "Nick Drake - Pink Moon",
    "Elliott Smith - Between the Bars",
    "Jeff Buckley - Hallelujah", "Jeff Buckley - Last Goodbye",
    "Simon & Garfunkel - The Sound of Silence",
    "Johnny Cash - Hurt",
    "Bob Dylan - Don't Think Twice, It's All Right",
    "Leonard Cohen - Hallelujah",
    "Cat Stevens - Father and Son",
    "Eric Clapton - Tears in Heaven",
    "Phil Collins - Another Day in Paradise",
    "Sting - Fragile",
    "Peter Gabriel - Don't Give Up",
    "Enya - Only Time",
    "Mazzy Star - Fade into You",
    "The Smiths - There Is a Light That Never Goes Out",
    "The Cure - Pictures of You", "The Cure - Lovesong",
    "Joy Division - Love Will Tear Us Apart",
    "Portishead - Glory Box", "Portishead - Roads",
    "Massive Attack - Teardrop",
    "Trentemøller - Moan",
    "Cigarettes After Sex - Nothing's Gonna Hurt You Baby",
    "Cigarettes After Sex - Apocalypse",
    "Beach House - Space Song",
    "Men I Trust - Numb",
    "Novo Amor - Anchor",
    "Phoebe Bridgers - Funeral", "Phoebe Bridgers - Motion Sickness",
    "boygenius - Me & My Dog",
    "Lucy Dacus - Night Shift",
    "Soccer Mommy - Your Dog",
    "Mitski - Nobody", "Mitski - Washing Machine Heart",
    "Julien Baker - Appointments",
    "Hand Habits - what lovers do",
    "Big Thief - Not",
    "Weyes Blood - Andromeda",
    "Angel Olsen - Shut Up Kiss Me",
    "Sharon Van Etten - Comeback Kid",
    "Sufjan Stevens - Death with Dignity",
    "Mount Eerie - Real Death",
    "William Fitzsimmons - Passion",
    "Gregory Alan Isakov - The Stable Song",
    "Iron & Wine - Flightless Bird",
    "Fleet Foxes - White Winter Hymnal",
    "Daughter - Youth", "Daughter - Medicine",
    "Birdy - Skinny Love",
    "Aurora - Running with the Wolves",
    "Agnes Obel - Riverside",
    # Italiani
    "Fabrizio De André - Canzone dell'amore perduto",
    "Fabrizio De André - Bocca di rosa",
    "Lucio Battisti - Pensieri e parole",
    "Lucio Dalla - Anna e Marco",
    "Francesco De Gregori - Rimmel",
    "Francesco De Gregori - Viva l'Italia",
    "Paolo Conte - Azzurro",
    "Pino Daniele - Quando",
    "Claudio Baglioni - E tu",
    "Antonello Venditti - Amici mai",
    "Vasco Rossi - Ogni volta",
    "Ligabue - Ho ancora la forza",
    "Elisa - Almeno tu nell'universo",
    "Laura Pausini - Non c'è",
    "Giorgia - Come saprei",
    "Zucchero - Miserere",
    "Eros Ramazzotti - Se bastasse una canzone",
    "Tiziano Ferro - Il mondo è nostro",
    "Marco Mengoni - Guerriero",
    "Mahmood - Barrio",
    "Coez - È sempre bello",
    "Calcutta - Cosa mi manchi a fare",
    "Liberato - 9 maggio",
    "Ultimo - Il ballo delle incertezze",
    "Irama - Nera",
    "Blanco - Blu celeste",
    "Sangiovanni - Lady",
    "Gazzelle - Destri",
    "Wrongonyou - Giacomo",
    "Brunori Sas - Al di là dell'amore",
    "Carmen Consoli - L'ultimo bacio",
    "Tiromancino - Due destini",
    "Noemi - Vuoto a perdere",
    "Alex Britti - Oggi sono io",
    "Mario Venuti - Trovare te",
    "Max Gazzè - La vita com'è",
    "Niccolò Fabi - Capire",
    "Samuele Bersani - Giudizi universali",
    "Giovanni Allevi - Come sei davvero",
    "Einaudi - Una Mattina",
    "Nino D'Angelo - Un nuovo giorno",
    "Peppino Di Capri - Malafemmena",
    "Roberto Murolo - Reginella",
]

MOOD_TRANQUILLO = [
    "Cigarettes After Sex - Nothing's Gonna Hurt You Baby",
    "Cigarettes After Sex - Apocalypse",
    "Cigarettes After Sex - K.",
    "Cigarettes After Sex - Tejano Blue",
    "Cigarettes After Sex - Touch",
    "Beach House - Space Song", "Beach House - Myth",
    "Men I Trust - Tailwhip", "Men I Trust - Show Me How",
    "Novo Amor - Anchor", "Novo Amor - Birthplace",
    "Tycho - Awake", "Tycho - Dive",
    "Bonobo - Kong", "Bonobo - Black Sands",
    "Nils Frahm - Says",
    "Ólafur Arnalds - Near Light",
    "Ludovico Einaudi - Una Mattina", "Ludovico Einaudi - Experience",
    "Max Richter - On the Nature of Daylight",
    "Johann Johannsson - The Sun's Gone Dim",
    "Brian Eno - An Ending (Ascent)",
    "Harold Budd - Abandoned Cities",
    "Stars of the Lid - Requiem for Dying Mothers",
    "Explosions in the Sky - The First Breath After Coma",
    "Mogwai - Auto Rock",
    "Godspeed You! Black Emperor - The Dead Flag Blues",
    "65daysofstatic - Radio Protector",
    "Hammock - Tape Recorder",
    "The Album Leaf - Eastern Leaves",
    "This Will Destroy You - Quiet",
    "Sufjan Stevens - Death with Dignity",
    "Iron & Wine - Flightless Bird",
    "Fleet Foxes - White Winter Hymnal",
    "Bon Iver - Holocene", "Bon Iver - Re: Stacks",
    "Nick Drake - Pink Moon",
    "Elliott Smith - Miss Misery",
    "Mazzy Star - Fade into You",
    "Portishead - Roads",
    "Massive Attack - Teardrop",
    "Burial - Archangel",
    "Boards of Canada - Roygbiv",
    "Aphex Twin - Avril 14th",
    "Bibio - Lovers' Carvings",
    "Jon Hopkins - Open Eye Signal",
    "Four Tet - Butterfly",
    "Caribou - Sun",
    "Nicolas Jaar - Space Is Only Noise If You Can See",
    "Floating Points - LesAlpx",
    "Catching Flies - Silhouettes",
    "Tom Misch - Beautiful Escape",
    "Jordan Rakei - Shoot to Kill",
    "Alfa Mist - Antiphon",
    "Hania Rani - Eden",
    "Joep Beving - Sleeping Lotus",
    "Anouar Brahem - Conte de L'Incroyable Amour",
    "Balmorhea - Settler",
    "Hammock - Oblivion",
    "Marconi Union - Weightless",
    "Air - La Femme d'Argent",
    "Air - All I Need",
    "Zero 7 - In the Waiting Line",
    "Groove Armada - At the River",
    "Morcheeba - The Sea",
    "Portishead - Sour Times",
    "Tricky - Hell is Around the Corner",
    "Sneaker Pimps - 6 Underground",
    "Lamb - Gorecki",
    "Hooverphonic - 2 Wicky",
    "Goldfrapp - Utopia",
    "Röyksopp - Remind Me",
    "Kings of Convenience - Toxic Girl",
    "Feist - 1234",
    "Norah Jones - Come Away with Me",
    "Diana Krall - The Look of Love",
    "Melody Gardot - Our Love Is Easy",
    "Esperanza Spalding - Black Gold",
    "José González - Heartbeats",
    "Nick Mulvey - Fever to the Form",
    "Ben Howard - Only Love",
    "John Martyn - Solid Air",
    "Tim Buckley - Song to the Siren",
    "Talk Talk - Life's What You Make It",
    "Cocteau Twins - Heaven or Las Vegas",
    "This Mortal Coil - Song to the Siren",
    "Dead Can Dance - The Host of Seraphim",
    "Lisa Gerrard - Now We Are Free",
    "Enya - Orinoco Flow",
    "Loreena McKennitt - The Mummers' Dance",
    "Sade - By Your Side", "Sade - Smooth Operator",
    "Maxwell - Fortunate",
    "D'Angelo - Untitled (How Does It Feel)",
    "Erykah Badu - On & On",
    "Lauryn Hill - Ex-Factor",
    # Italiani
    "Sauna - Saudade",
    "Saudade - Il suono del silenzio",
    "Colapesce Dimartino - Musica Leggerissima",
    "Gazzelle - Destri",
    "Calcutta - Cosa mi manchi a fare",
    "Wrongonyou - Giacomo",
    "Brunori Sas - Al di là dell'amore",
    "Niccolò Fabi - Capire",
    "Max Gazzè - La vita com'è",
    "Samuele Bersani - Giudizi universali",
    "Carmen Consoli - L'ultimo bacio",
    "Giovanni Allevi - Come sei davvero",
    "Einaudi - Nuvole Bianche",
    "Einaudi - Le Onde",
    "Paolo Conte - Via con me",
    "Fabrizio De André - Canzone del maggio",
    "Francesco De Gregori - La leva calcistica della classe '68",
    "Lucio Battisti - Il mio canto libero",
    "Pino Daniele - Quando",
    "Enzo Avitabile - Jamme Jà",
    "Mia Martini - Almeno tu nell'universo",
    "Ornella Vanoni - L'appuntamento",
    "Patty Pravo - La bambola",
    "Milva - La fiamma",
    "Nada - Ma che freddo fa",
    "Caterina Caselli - Insieme a te non ci sto più",
    "Riccardo Cocciante - Cervo a primavera",
    "Roberto Vecchioni - Luci a San Siro",
    "Antonello Venditti - Ci vorrebbe il mare",
    "Claudio Baglioni - Con tutto l'amore che ho",
    "Tiromancino - Due destini",
    "Subsonica - Aurora Sogna",
    "Afterhours - Voglio una pelle splendida",
    "Marlene Kuntz - Lieve",
    "Perturbazione - L'amore ai tempi del colera",
]

MOOD_AMOREVOLE = [
    "Ed Sheeran - Perfect", "Ed Sheeran - Thinking Out Loud",
    "John Legend - All of Me",
    "Bruno Mars - Just the Way You Are", "Bruno Mars - Marry You",
    "Michael Bublé - Haven't Met You Yet", "Michael Bublé - Everything",
    "Frank Sinatra - Fly Me to the Moon", "Frank Sinatra - The Way You Look Tonight",
    "Dean Martin - That's Amore",
    "Nat King Cole - Unforgettable",
    "Elvis Presley - Can't Help Falling in Love",
    "The Beatles - Something", "The Beatles - And I Love Her",
    "Van Morrison - Into the Mystic", "Van Morrison - Crazy Love",
    "Eric Clapton - Wonderful Tonight",
    "Elton John - Your Song",
    "Lionel Richie - Hello", "Lionel Richie - Endless Love",
    "Whitney Houston - I Will Always Love You",
    "Celine Dion - My Heart Will Go On",
    "Mariah Carey - Always Be My Baby",
    "Boyz II Men - I'll Make Love to You",
    "Brian McKnight - Back at One",
    "Luther Vandross - A House Is Not a Home",
    "Barry White - Can't Get Enough of Your Love",
    "Marvin Gaye - Let's Get It On", "Marvin Gaye - Sexual Healing",
    "Al Green - Let's Stay Together",
    "Stevie Wonder - Isn't She Lovely",
    "Otis Redding - (Sittin' On) The Dock of the Bay",
    "Sam Cooke - Wonderful World",
    "Ben E. King - Stand By Me",
    "The Righteous Brothers - Unchained Melody",
    "Etta James - At Last",
    "Nina Simone - I Put a Spell on You",
    "Norah Jones - Come Away with Me",
    "Diana Krall - The Look of Love",
    "Sade - Your Love Is King",
    "Anita Baker - Sweet Love",
    "Maxwell - This Woman's Work",
    "D'Angelo - Lady",
    "Alicia Keys - If I Ain't Got You",
    "John Mayer - Your Body Is a Wonderland",
    "Jason Mraz - I'm Yours",
    "Jack Johnson - Better Together",
    "James Taylor - You've Got a Friend",
    "Paul Simon - 50 Ways to Leave Your Lover",
    "Simon & Garfunkel - The Sound of Silence",
    "Bob Dylan - Make You Feel My Love",
    "Adele - Make You Feel My Love",
    "Taylor Swift - Lover", "Taylor Swift - Enchanted",
    "Beyoncé - Halo", "Beyoncé - Love on Top",
    "Rihanna - We Found Love",
    "Ariana Grande - Into You",
    "Dua Lipa - Levitating",
    "Harry Styles - Adore You",
    "Shawn Mendes - Mercy",
    "Camila Cabello - Never Be the Same",
    "Selena Gomez - Rare",
    "Justin Bieber - Love Yourself",
    "One Direction - Little Things",
    "Coldplay - Yellow", "Coldplay - The Scientist",
    "Snow Patrol - Open Your Eyes",
    "Kodaline - All I Want",
    "Hozier - From Eden",
    "James Arthur - Say You Won't Let Go",
    "George Michael - Careless Whisper",
    "Wham! - Careless Whisper",
    "Pet Shop Boys - Always on My Mind",
    "Simply Red - If You Don't Know Me by Now",
    "Wet Wet Wet - Love Is All Around",
    "Take That - Back for Good",
    "Savage Garden - Truly Madly Deeply",
    "Seal - Kiss from a Rose",
    "Roxette - It Must Have Been Love",
    "A-ha - Take On Me",
    "Cyndi Lauper - Time After Time",
    "Madonna - Crazy for You",
    "Pat Benatar - We Belong",
    "Air Supply - Making Love Out of Nothing at All",
    "Christopher Cross - Sailing",
    "Chicago - You're the Inspiration",
    "Foreigner - I Want to Know What Love Is",
    "Journey - Open Arms",
    "REO Speedwagon - Can't Fight This Feeling",
    "Toto - I'll Be Over You",
    # Italiani
    "Eros Ramazzotti - Più bella cosa", "Eros Ramazzotti - Cose della vita",
    "Tiziano Ferro - Il mondo è nostro", "Tiziano Ferro - Perdono",
    "Marco Mengoni - L'essenziale", "Marco Mengoni - Solo due giganti",
    "Laura Pausini - La solitudine", "Laura Pausini - Strani amori",
    "Giorgia - Come saprei", "Giorgia - Di sole e d'azzurro",
    "Elisa - Luce", "Elisa - Come per magia",
    "Negramaro - Mentre tutto scorre", "Negramaro - Amore che torni",
    "Claudio Baglioni - Questo piccolo grande amore",
    "Antonello Venditti - Ogni volta",
    "Vasco Rossi - Ogni volta",
    "Ligabue - Certe notti",
    "Zucchero - Senza una donna",
    "Pino Daniele - Yes I Know My Way",
    "Lucio Battisti - Il mio canto libero",
    "Lucio Dalla - Caruso",
    "Fabrizio De André - La canzone di Marinella",
    "Francesco De Gregori - La donna cannone",
    "Paolo Conte - Via con me",
    "Riccardo Cocciante - Margherita",
    "Umberto Tozzi - Ti amo",
    "Mia Martini - Almeno tu nell'universo",
    "Ornella Vanoni - L'appuntamento",
    "Patty Pravo - La bambola",
    "Caterina Caselli - Insieme a te non ci sto più",
    "Jovanotti - Baciami ancora",
    "Alex Britti - Solo una volta",
    "Irama - Nera",
    "Ultimo - Il ballo delle incertezze",
    "Coez - È sempre bello",
    "Calcutta - Cosa mi manchi a fare",
    "Gazzelle - Destri",
    "Liberato - 9 maggio",
    "Colapesce Dimartino - Musica Leggerissima",
    "Mahmood - Dorado",
    "Blanco - La canzone nostra",
]

MOOD_GANGSTER = [
    "Notorious B.I.G. - Hypnotize", "Notorious B.I.G. - Big Poppa",
    "Tupac - California Love", "Tupac - All Eyez on Me", "Tupac - Hit 'Em Up",
    "Jay-Z - 99 Problems", "Jay-Z - Empire State of Mind",
    "Nas - N.Y. State of Mind", "Nas - Hate Me Now",
    "Eminem - Lose Yourself", "Eminem - Slim Shady", "Eminem - Without Me",
    "Dr. Dre - Still D.R.E.", "Dr. Dre - The Next Episode",
    "Snoop Dogg - Drop It Like It's Hot", "Snoop Dogg - Gin and Juice",
    "50 Cent - In da Club", "50 Cent - Many Men",
    "Kanye West - POWER", "Kanye West - Stronger",
    "Kendrick Lamar - HUMBLE.", "Kendrick Lamar - DNA.", "Kendrick Lamar - Money Trees",
    "J. Cole - No Role Modelz", "J. Cole - Power Trip",
    "Drake - God's Plan", "Drake - HYFR",
    "Travis Scott - Goosebumps", "Travis Scott - Antidote",
    "Lil Wayne - A Milli", "Lil Wayne - Got Money",
    "Nicki Minaj - Anaconda", "Nicki Minaj - Monster",
    "Cardi B - Bodak Yellow",
    "Megan Thee Stallion - Savage",
    "21 Savage - Rockstar",
    "Post Malone - Rockstar",
    "Lil Uzi Vert - XO Tour Llif3",
    "Juice WRLD - Lucid Dreams",
    "XXXTentacion - SAD!",
    "Polo G - Pop Out",
    "Roddy Ricch - The Box",
    "DaBaby - Rockstar",
    "Lil Baby - Drip Too Hard",
    "Young Thug - Havana",
    "Future - Mask Off",
    "Meek Mill - Dreams and Nightmares",
    "Rick Ross - Hustlin'",
    "Wale - The Need to Know",
    "Big Sean - Blessings",
    "A$AP Rocky - Praise the Lord",
    "Tyler, the Creator - EARFQUAKE",
    "Childish Gambino - This Is America",
    "Chance the Rapper - No Problem",
    "Run-DMC - It's Tricky",
    "Public Enemy - Fight the Power",
    "Ice Cube - It Was a Good Day",
    "NWA - Straight Outta Compton",
    "Wu-Tang Clan - C.R.E.A.M.",
    "Mobb Deep - Shook Ones Pt. II",
    "Rakim - Paid in Full",
    "Big L - Ebonics",
    "Busta Rhymes - Put Your Hands Where My Eyes Could See",
    "DMX - X Gon' Give It to Ya",
    "Ja Rule - Always on Time",
    "Ludacris - Move Bitch",
    "T.I. - Whatever You Like",
    "Lil Jon - Get Low",
    "Three 6 Mafia - Stay Fly",
    "Gucci Mane - Lemonade",
    "Young Jeezy - Soul Survivor",
    "Boosie Badazz - Wipe Me Down",
    "Kevin Gates - 2 Phones",
    "Fetty Wap - Trap Queen",
    "Rae Sremmurd - No Type",
    "Desiigner - Panda",
    "Chief Keef - Faneto",
    "Chance the Rapper - Cocoa Butter Kisses",
    "Vic Mensa - U Mad",
    "Saba - PROM / KING",
    "Joey Bada$$ - Land of the Free",
    "Flatbush Zombies - Palm Trees",
    "Denzel Curry - Bulls on Parade",
    "JID - Never",
    "Isaiah Rashad - RIP Kevin Miller",
    "Smino - Wild Irish Roses",
    "Noname - Diddy Bop",
    "Mick Jenkins - Drowning",
    "Freddie Gibbs - Thuggin",
    "Boldy James - Moochie",
    "Conway the Machine - Lemon",
    "Westside Gunn - Allah Sent Me",
    # Italiani
    "Capo Plaza - 23 6451",
    "Sfera Ebbasta - Visionaire", "Sfera Ebbasta - Rockstar",
    "Ghali - DNA", "Ghali - Cara Italia",
    "Tedua - Palco",
    "Marracash - Noi loro gli altri", "Marracash - Crudelia",
    "Fabri Fibra - Fenomeno", "Fabri Fibra - Applausi per Fibra",
    "Club Dogo - Fragili", "Club Dogo - Tutto quel che ho",
    "Salmo - 90MIN", "Salmo - Sparare alla luna",
    "Nitro - Sharingan",
    "Rkomi - Insuperabile",
    "Lazza - Tutto il giorno",
    "Shiva - Butterfly",
    "Geolier - I p' me tu p' te",
    "Guè - Madreperla",
    "Luchè - Potere",
    "Emis Killa - Parole di ghiaccio",
    "Jake La Furia - Replay",
    "Mondo Marcio - Non sei tu",
    "Ensi - Stai calmo",
    "Dutch Nazari - Un'altra estate",
    "Murubutu - L'uomo che vide l'infinito",
    "Willie Peyote - Cemento armato",
    "Mecna - Note blu",
    "Carl Brave - Fotografia",
    "Franco126 - Polaroid",
    "Coez - Faccio un casino",
    "Calcutta - Cosa mi manchi a fare",
    "Liberato - Tu t'e scurdat' 'e me",
    "Clementino - Cos cos cos",
    "Rocco Hunt - A modo mio",
    "Nayt - Hype",
    "Pyrex - Ancora qui",
]

MOODS = {
    "energico": ("⚡ Energico", MOOD_ENERGICO),
    "felice": ("😄 Felice", MOOD_FELICE),
    "triste": ("😢 Triste", MOOD_TRISTE),
    "tranquillo": ("😌 Tranquillo", MOOD_TRANQUILLO),
    "amorevole": ("❤️ Amorevole", MOOD_AMOREVOLE),
    "gangster": ("🎤 Gangster", MOOD_GANGSTER),
}

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
    response = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {'title': name, 'description': 'Playlist del giorno - JukeBox IT'},
            'status': {'privacyStatus': 'public'}
        }
    ).execute()

    playlist_id = response['id']
    daily_state = {
        'date': today,
        'playlist_id': playlist_id,
        'track_ids': set(),
        'count': 0
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

    today = date.today().strftime('%d-%m-%Y')
    if daily_state.get('date') == today:
        if daily_state.get('count', 0) >= DAILY_LIMIT:
            await update.message.reply_text(
                f'🚫 Limite giornaliero raggiunto! ({DAILY_LIMIT} brani)\n'
                f'La playlist si resetta domani mattina. 🎵'
            )
            return

    try:
        youtube = get_youtube_client()
        search_response = youtube.search().list(
            part='snippet', q=query, type='video',
            videoCategoryId='10', maxResults=1
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
        playlist_id = get_or_create_playlist(youtube)

        if video_id in daily_state['track_ids']:
            await update.message.reply_text(
                f'⚠️ "{video_title}" è già nella playlist di oggi!'
            )
            return

        youtube.playlistItems().insert(
            part='snippet',
            body={'snippet': {
                'playlistId': playlist_id,
                'resourceId': {'kind': 'youtube#video', 'videoId': video_id}
            }}
        ).execute()

        daily_state['track_ids'].add(video_id)
        daily_state['count'] = daily_state.get('count', 0) + 1
        remaining = DAILY_LIMIT - daily_state['count']

        if remaining == 10:
            await update.message.reply_text(
                f'✅ {user} ha aggiunto:\n🎵 {video_title}\n'
                f'📋 Playlist: jukebox it - {daily_state["date"]}\n\n'
                f'⚠️ Attenzione: mancano solo 10 brani al limite giornaliero!'
            )
        else:
            await update.message.reply_text(
                f'✅ {user} ha aggiunto:\n🎵 {video_title}\n'
                f'📋 Playlist: jukebox it - {daily_state["date"]}'
            )

    except Exception as e:
        logger.error(f'Errore completo: {traceback.format_exc()}')
        await update.message.reply_text('❌ Si è verificato un errore. Riprova tra qualche istante.')

async def add_song_from_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aggiunge un brano suggerito dal mood alla playlist."""
    query = update.callback_query
    await query.answer()

    song = query.data.replace("add_mood:", "")
    user = query.from_user.first_name

    today = date.today().strftime('%d-%m-%Y')
    if daily_state.get('date') == today:
        if daily_state.get('count', 0) >= DAILY_LIMIT:
            await query.message.reply_text(
                f'🚫 Limite giornaliero raggiunto! ({DAILY_LIMIT} brani)'
            )
            return

    try:
        youtube = get_youtube_client()
        search_response = youtube.search().list(
            part='snippet', q=song, type='video',
            videoCategoryId='10', maxResults=1
        ).execute()

        items = search_response.get('items', [])
        if not items:
            await query.message.reply_text(f'🔍 Brano non trovato: "{song}"')
            return

        video_id    = items[0]['id']['videoId']
        video_title = items[0]['snippet']['title']
        playlist_id = get_or_create_playlist(youtube)

        if video_id in daily_state['track_ids']:
            await query.message.reply_text(f'⚠️ "{video_title}" è già nella playlist di oggi!')
            return

        youtube.playlistItems().insert(
            part='snippet',
            body={'snippet': {
                'playlistId': playlist_id,
                'resourceId': {'kind': 'youtube#video', 'videoId': video_id}
            }}
        ).execute()

        daily_state['track_ids'].add(video_id)
        daily_state['count'] = daily_state.get('count', 0) + 1

        await query.message.reply_text(
            f'✅ {user} ha aggiunto:\n🎵 {video_title}\n'
            f'📋 Playlist: jukebox it - {daily_state["date"]}'
        )

    except Exception as e:
        logger.error(f'Errore add_song_from_mood: {traceback.format_exc()}')
        await query.message.reply_text('❌ Si è verificato un errore. Riprova.')

async def mood_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce la selezione del mood e mostra 5 canzoni casuali."""
    query = update.callback_query
    await query.answer()

    mood_key = query.data.replace("mood:", "")
    if mood_key not in MOODS:
        return

    mood_label, mood_list = MOODS[mood_key]
    canzoni = random.sample(mood_list, 5)

    testo = f"{mood_label} — 5 brani consigliati:\n\n"
    keyboard = []

    for i, canzone in enumerate(canzoni, 1):
        testo += f"{i}. {canzone}\n"
        keyboard.append([InlineKeyboardButton(
            f"➕ Aggiungi: {canzone}",
            callback_data=f"add_mood:{canzone}"
        )])

    keyboard.append([InlineKeyboardButton("🔄 Altri 5 brani", callback_data=f"mood:{mood_key}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=testo, reply_markup=reply_markup)

async def mood_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra i bottoni degli stati d'animo."""
    keyboard = [
        [
            InlineKeyboardButton("⚡ Energico", callback_data="mood:energico"),
            InlineKeyboardButton("😄 Felice", callback_data="mood:felice"),
        ],
        [
            InlineKeyboardButton("😢 Triste", callback_data="mood:triste"),
            InlineKeyboardButton("😌 Tranquillo", callback_data="mood:tranquillo"),
        ],
        [
            InlineKeyboardButton("❤️ Amorevole", callback_data="mood:amorevole"),
            InlineKeyboardButton("🎤 Gangster", callback_data="mood:gangster"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎵 Come ti senti oggi? Scegli il tuo mood:",
        reply_markup=reply_markup
    )

async def show_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not daily_state.get('playlist_id'):
        await update.message.reply_text(
            '📋 Nessuna playlist ancora oggi. Usa /add per aggiungere il primo brano!'
        )
        return

    pid       = daily_state['playlist_id']
    url       = f'https://music.youtube.com/playlist?list={pid}'
    count     = daily_state.get('count', 0)
    remaining = DAILY_LIMIT - count
    await update.message.reply_text(
        f'📋 Playlist di oggi ({daily_state["date"]}): {count} brani\n'
        f'🎵 Brani rimanenti oggi: {remaining}/{DAILY_LIMIT}\n{url}'
    )

async def regole_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '📋 Regole del JukeBox IT:\n\n'
        '🎵 Come aggiungere un brano:\n'
        'Usa il comando /add seguito dal titolo e artista\n'
        'Esempio: /add Bohemian Rhapsody - Queen\n\n'
        '🎭 Vuoi ispirazione? Usa /mood per brani in base al tuo stato d\'animo!\n\n'
        '📌 Regole:\n'
        '• Ogni brano può essere aggiunto una sola volta al giorno (no doppioni)\n'
        f'• Limite massimo: {DAILY_LIMIT} brani al giorno\n'
        '• La playlist si rinnova automaticamente ogni mattina\n\n'
        '📱 Comandi disponibili:\n'
        '/add Titolo - Artista  →  Aggiunge un brano\n'
        '/mood                  →  Brani per stato d\'animo\n'
        '/playlist              →  Link alla playlist di oggi\n'
        '/regole                →  Mostra queste regole\n'
        '/help                  →  Mostra i comandi'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🎵 JukeBox IT — Comandi:\n\n'
        '/add Titolo - Artista  →  Aggiunge un brano alla playlist\n'
        '/mood                  →  Brani per stato d\'animo\n'
        '/playlist              →  Link alla playlist + brani rimanenti\n'
        '/regole                →  Regole del JukeBox\n'
        '/help                  →  Mostra questo messaggio'
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('add',      add_song))
    app.add_handler(CommandHandler('mood',     mood_cmd))
    app.add_handler(CommandHandler('playlist', show_playlist))
    app.add_handler(CommandHandler('regole',   regole_cmd))
    app.add_handler(CommandHandler('help',     help_cmd))
    app.add_handler(CallbackQueryHandler(mood_callback,      pattern='^mood:'))
    app.add_handler(CallbackQueryHandler(add_song_from_mood, pattern='^add_mood:'))
    logger.info('Bot JukeBox IT avviato.')
    app.run_polling()

if __name__ == '__main__':
    main()
