import os
import re
import requests
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError, COMM

def extract_id(url):
    match = re.search(r'pillowcase\.su/f/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

def sanitize_folder_name(name):
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()

def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip(' .')
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def download_file(url, dest_folder, title, progress_callback=None):
    if 'pillowcase.su' in url:
        file_id = extract_id(url)
        if not file_id:
            msg = f"[Error] Could not extract file ID from pillowcase.su URL: {url}\n"
            print(msg.strip())
            if progress_callback:
                progress_callback(msg)
            return None, None
        api_url = f"https://api.pillowcase.su/api/download/{file_id}.mp3"
    elif 'music.froste.lol/song/' in url:
        match = re.search(r'music\.froste\.lol/song/([a-zA-Z0-9]+)', url)
        if not match:
            msg = f"[Error] Could not extract song ID from froste.lol URL: {url}\n"
            print(msg.strip())
            if progress_callback:
                progress_callback(msg)
            return None, None
        song_id = match.group(1)
        api_url = f"https://music.froste.lol/song/{song_id}/download"
    else:
        msg = f"[Error] Unsupported host for URL: {url}\n"
        print(msg.strip())
        if progress_callback:
            progress_callback(msg)
        return None, None
    try:
        with requests.get(api_url, stream=True) as r:
            r.raise_for_status()
            content_type = r.headers.get('Content-Type', '').lower()
            ext = '.mp3'
            if 'wav' in content_type:
                ext = '.wav'
            elif 'm4a' in content_type or 'mp4' in content_type:
                ext = '.m4a'
            elif 'flac' in content_type:
                ext = '.flac'
            if title and title.strip():
                safe_title = sanitize_filename(title)
                local_filename = os.path.join(dest_folder, f"{safe_title}{ext}")
            else:
                fallback_id = file_id if 'pillowcase.su' in url else song_id
                local_filename = os.path.join(dest_folder, f"{fallback_id}{ext}")
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        msg = f"Downloaded: {api_url} -> {local_filename}\n"
        print(msg.strip())
        if progress_callback:
            progress_callback(msg)
        return local_filename, ext
    except Exception as e:
        msg = f"Failed to download {api_url}: {e}\n"
        print(msg.strip())
        if progress_callback:
            progress_callback(msg)
        return None, None

def embed_metadata(mp3_path, title, artist=None, composer=None, progress_callback=None):
    try:
        audio = EasyID3(mp3_path)
    except ID3NoHeaderError:
        audio = EasyID3()
        audio.save(mp3_path)
        audio = EasyID3(mp3_path)
    audio['title'] = title
    if artist:
        audio['artist'] = artist
    if composer:
        audio['composer'] = composer
    try:
        audio['comment'] = 't.me/vqvlt'
    except Exception:
        id3 = ID3(mp3_path)
        id3.add(COMM(encoding=3, lang='eng', desc='', text='t.me/vqvlt'))
        id3.save(mp3_path)
    audio.save(mp3_path)
    msg = f"Embedded metadata into {mp3_path}\n"
    print(msg.strip())
    if progress_callback:
        progress_callback(msg)

def process_title_and_metadata(name, available_length, quality=None):
    composer = None
    prod_match = re.search(r'\(prod\. ([^)]+)\)', name, re.IGNORECASE)
    if prod_match:
        composer = prod_match.group(1).strip()
        name = name.replace(prod_match.group(0), '').strip()
    feat_match = re.search(r'\((feat\.[^)]+)\)', name, re.IGNORECASE)
    feat_str = ''
    if feat_match:
        feat_str = f" ({feat_match.group(1).title()})"
        name = re.sub(r'\((feat\.[^)]+)\)', '', name, flags=re.IGNORECASE).strip()
    artist = None
    title = name
    dash_split = name.split(' - ', 1)
    if len(dash_split) == 2:
        artist = dash_split[0].strip()
        title = dash_split[1].strip()
    if title.strip() == "???":
        paren_match = re.search(r'\(([^)]+)\)', name)
        if paren_match:
            alt_title = paren_match.group(1).replace(',', ' / ').replace('  ', ' ').strip()
            title = alt_title
        else:
            title = '???'
    else:
        paren_match = re.search(r'\(([^)]+)\)', title)
        if paren_match and not re.search(r'feat\.', paren_match.group(1), re.IGNORECASE):
            main_title = title.replace(paren_match.group(0), '').strip()
            alt_title = paren_match.group(1).replace(',', ' / ').replace('  ', ' ').strip()
            if main_title.strip() == '???' and alt_title.strip() != '???':
                title = alt_title
            elif alt_title.strip() == '???' and main_title.strip() != '???':
                title = main_title
            elif main_title.strip() != '' and alt_title.strip() != '':
                title = f"{main_title} / {alt_title}"
            else:
                title = main_title or alt_title
    title = re.sub(r'\[[^\]]*\]', '', title).strip()
    if isinstance(available_length, str):
        if available_length.strip().lower() == 'snippet':
            title = f"{title}{feat_str} (Snippet)"
        else:
            title = f"{title}{feat_str}"
    else:
        title = f"{title}{feat_str}"
    if isinstance(quality, str) and quality.strip().lower() == 'low quality':
        title = f"{title} (LQ)"
    title = title.replace('\n', ' ').replace('\r', ' ')
    title = re.sub(' +', ' ', title).strip()
    return title, artist, composer 