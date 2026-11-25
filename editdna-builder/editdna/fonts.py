# EditDNA — personal-use license, see LICENSE. (c) EditDNA. Do not redistribute or sell.
"""Free fonts (SIL Open Font License) from the google/fonts GitHub repo."""
import os, urllib.request
BASE = 'https://raw.githubusercontent.com/google/fonts/main/ofl/'
CATALOG = {   # name: (path in repo, vibe, scripts)
    'Anton': ('anton/Anton-Regular.ttf', 'tall condensed, loud', 'latin'),
    'Archivo Black': ('archivoblack/ArchivoBlack-Regular.ttf', 'heavy, modern', 'latin'),
    'Bebas Neue': ('bebasneue/BebasNeue-Regular.ttf', 'condensed caps, cinematic', 'latin'),
    'Bangers': ('bangers/Bangers-Regular.ttf', 'comic, playful', 'latin'),
    'Bungee': ('bungee/Bungee-Regular.ttf', 'signage, urban', 'latin'),
    'Russo One': ('russoone/RussoOne-Regular.ttf', 'tech, gaming', 'latin'),
    'Righteous': ('righteous/Righteous-Regular.ttf', 'retro, rounded', 'latin'),
    'Fredoka': ('fredoka/Fredoka[wdth,wght].ttf', 'soft rounded, friendly', 'latin'),
    'Poppins Bold': ('poppins/Poppins-Bold.ttf', 'clean geometric', 'latin'),
    'Poppins': ('poppins/Poppins-Regular.ttf', 'clean geometric body', 'latin'),
    'Montserrat': ('montserrat/Montserrat[wght].ttf', 'classic modern', 'latin'),
    'Inter': ('inter/Inter[opsz,wght].ttf', 'neutral UI body', 'latin'),
    'Space Grotesk': ('spacegrotesk/SpaceGrotesk[wght].ttf', 'techy body', 'latin'),
    'DM Serif Display': ('dmserifdisplay/DMSerifDisplay-Regular.ttf', 'elegant serif', 'latin'),
    'Playfair Display': ('playfairdisplay/PlayfairDisplay[wght].ttf', 'luxury serif', 'latin'),
    'Caveat': ('caveat/Caveat[wght].ttf', 'handwritten', 'latin'),
    'Permanent Marker': ('permanentmarker/PermanentMarker-Regular.ttf', 'marker, street', 'latin'),
    'JetBrains Mono': ('jetbrainsmono/JetBrainsMono[wght].ttf', 'code mono', 'latin'),
    'DM Mono': ('dmmono/DMMono-Medium.ttf', 'soft mono', 'latin'),
    'Space Mono': ('spacemono/SpaceMono-Regular.ttf', 'retro mono', 'latin'),
    'Cairo': ('cairo/Cairo[slnt,wght].ttf', 'arabic modern', 'arabic+latin'),
    'Tajawal Bold': ('tajawal/Tajawal-Bold.ttf', 'arabic clean bold', 'arabic+latin'),
    'Tajawal': ('tajawal/Tajawal-Regular.ttf', 'arabic clean body', 'arabic+latin'),
    'Changa': ('changa/Changa[wght].ttf', 'arabic techy', 'arabic+latin'),
    'Rakkas': ('rakkas/Rakkas-Regular.ttf', 'arabic display, decorative', 'arabic+latin'),
    'Lemonada': ('lemonada/Lemonada[wght].ttf', 'arabic rounded, fun', 'arabic+latin'),
    'Reem Kufi': ('reemkufi/ReemKufi[wght].ttf', 'arabic kufi, geometric', 'arabic+latin'),
    'El Messiri': ('elmessiri/ElMessiri[wght].ttf', 'arabic elegant', 'arabic+latin'),
    'Noto Kufi Arabic': ('notokufiarabic/NotoKufiArabic[wght].ttf', 'arabic neutral', 'arabic+latin'),
}


def get(name, dest):
    rel = CATALOG[name][0]; os.makedirs(dest, exist_ok=True); fn = os.path.basename(rel)
    out = os.path.join(dest, fn)
    if not os.path.exists(out): urllib.request.urlretrieve(BASE + urllib.request.quote(rel), out)
    return fn
