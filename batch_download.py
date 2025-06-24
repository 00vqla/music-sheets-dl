import os
import pandas as pd
import requests
import re
from mutagen.easyid3 import EasyID3
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
import regex

DOWNLOAD_DIR = 'downloads'

def extract_id(url):
    """Extract the file ID from a pillowcase.su link."""
    match = re.search(r'pillowcase\.su/f/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

def remove_emoji(text):
    # Remove all emoji and symbols using Unicode properties
    emoji_pattern = regex.compile(r'[\p{Emoji}\p{So}\p{Sk}\p{Cn}]', flags=regex.UNICODE)
    return emoji_pattern.sub('', text)

def sanitize_folder_name(name):
    # Remove or replace characters not allowed in folder names
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()

def sanitize_filename(filename):
    # Remove all emojis from filename
    filename = remove_emoji(filename)
    # Remove or replace characters not allowed in filenames
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length to avoid filesystem issues
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def download_file(file_id, dest_folder, title):
    api_url = f"https://api.pillowcase.su/api/download/{file_id}.mp3"
    # Download the file and detect its type
    try:
        with requests.get(api_url, stream=True) as r:
            r.raise_for_status()
            # Detect file type from Content-Type header
            content_type = r.headers.get('Content-Type', '').lower()
            ext = '.mp3'  # default
            if 'wav' in content_type:
                ext = '.wav'
            elif 'm4a' in content_type or 'mp4' in content_type:
                ext = '.m4a'
            elif 'flac' in content_type:
                ext = '.flac'
            # Use title as filename, fallback to file_id if title is empty
            if title and title.strip():
                safe_title = sanitize_filename(title)
                local_filename = os.path.join(dest_folder, f"{safe_title}{ext}")
            else:
                local_filename = os.path.join(dest_folder, f"{file_id}{ext}")
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded: {api_url} -> {local_filename}")
        return local_filename, ext
    except Exception as e:
        print(f"Failed to download {api_url}: {e}")
        return None, None

def embed_metadata(mp3_path, title, artist=None, composer=None):
    try:
        audio = EasyID3(mp3_path)
    except Exception:
        audio = EasyID3()
    audio['title'] = title
    if artist:
        audio['artist'] = artist
    if composer:
        audio['composer'] = composer
    audio.save(mp3_path)
    print(f"Embedded metadata into {mp3_path}")

def find_column(columns, keyword):
    for col in columns:
        if keyword.lower() in col.lower():
            return col
    return None

def process_title_and_metadata(name, available_length, quality=None):
    # Remove emoji from name for both filename and metadata
    name = remove_emoji(str(name))
    # Extract (prod. ...) for composer
    composer = None
    prod_match = re.search(r'\(prod\. ([^)]+)\)', name, re.IGNORECASE)
    if prod_match:
        composer = prod_match.group(1).strip()
        name = name.replace(prod_match.group(0), '').strip()
    # Extract (feat. ...) for title
    feat_match = re.search(r'\((feat\.[^)]+)\)', name, re.IGNORECASE)
    feat_str = ''
    if feat_match:
        feat_str = f" ({feat_match.group(1).title()})"
        # Remove from name to avoid duplication
        name = re.sub(r'\((feat\.[^)]+)\)', '', name, flags=re.IGNORECASE).strip()
    # If name is in format 'Artist - Title ...', split
    artist = None
    title = name
    dash_split = name.split(' - ', 1)
    if len(dash_split) == 2:
        artist = dash_split[0].strip()
        title = dash_split[1].strip()
    # Handle '???' titles by using text in parentheses or removing '???'
    if title.strip() == "???":
        # Look for text in parentheses after the '???'
        paren_match = re.search(r'\(([^)]+)\)', name)
        if paren_match:
            alt_title = paren_match.group(1).replace(',', ' / ').replace('  ', ' ').strip()
            title = alt_title
        else:
            title = '???'
    else:
        # Look for text in parentheses that's not already handled
        paren_match = re.search(r'\(([^)]+)\)', title)
        if paren_match and not re.search(r'feat\.', paren_match.group(1), re.IGNORECASE):
            main_title = title.replace(paren_match.group(0), '').strip()
            alt_title = paren_match.group(1).replace(',', ' / ').replace('  ', ' ').strip()
            # If either main_title or alt_title is '???', use only the other
            if main_title.strip() == '???' and alt_title.strip() != '???':
                title = alt_title
            elif alt_title.strip() == '???' and main_title.strip() != '???':
                title = main_title
            elif main_title.strip() != '' and alt_title.strip() != '':
                title = f"{main_title} / {alt_title}"
            else:
                title = main_title or alt_title
    # Remove square brackets from title
    title = re.sub(r'\[[^\]]*\]', '', title).strip()
    # Remove emoji from title (for both filename and metadata)
    title = remove_emoji(title)
    # Add (Snippet) if needed
    if isinstance(available_length, str):
        if available_length.strip().lower() == 'snippet':
            title = f"{title}{feat_str} (Snippet)"
        else:
            title = f"{title}{feat_str}"
    else:
        title = f"{title}{feat_str}"
    # Add (LQ) if quality is Low Quality
    if isinstance(quality, str) and quality.strip().lower() == 'low quality':
        title = f"{title} (LQ)"
    # Remove newlines from title
    title = title.replace('\n', ' ').replace('\r', ' ')
    # Clean up double spaces
    title = re.sub(' +', ' ', title).strip()
    return title, artist, composer

def get_csv_from_url(url):
    # If it's already a googleusercontent.com direct CSV link, use as-is
    if 'googleusercontent.com' in url and 'format=csv' in url:
        try:
            print(f"Trying to download from direct Googleusercontent CSV URL: {url}")
            response = requests.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Failed to download CSV from URL: {e}")
            return None
    # Convert Google Sheets URL to CSV export URL
    if 'docs.google.com/spreadsheets' in url:
        # Extract the spreadsheet ID and gid
        id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        gid_match = re.search(r'[?&]gid=([0-9]+)', url)
        if id_match:
            spreadsheet_id = id_match.group(1)
            gid = gid_match.group(1) if gid_match else '0'
            csv_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
            try:
                print(f"Trying to download from: {csv_url}")
                response = requests.get(csv_url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                content = response.text
                if content and len(content) > 100:  # Basic check for valid CSV content
                    print("Successfully downloaded CSV content")
                    return content
                else:
                    print(f"Received empty or invalid content from {csv_url}")
            except Exception as e:
                print(f"Failed to download from {csv_url}: {e}")
                return None
        else:
            print("Invalid Google Sheets URL format")
            return None
    else:
        # Assume it's a direct CSV URL
        try:
            print(f"Trying to download from direct URL: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Failed to download CSV from URL: {e}")
            return None

def process_era(df, selected_era, link_col, name_col, length_col, quality_col, results):
    era_folder = os.path.join(DOWNLOAD_DIR, sanitize_folder_name(selected_era))
    os.makedirs(era_folder, exist_ok=True)
    filtered = df[(df['Era'].str.strip().str.lower() == selected_era.strip().lower()) & (df[link_col].notnull()) & (df[link_col].str.strip() != '')]
    print(f"Found {len(filtered)} files to download for Era: {selected_era}")
    for idx, row in filtered.iterrows():
        url = row[link_col].strip()
        file_id = extract_id(url)
        name = row[name_col]
        available_length = row[length_col] if length_col else None
        quality = row[quality_col] if quality_col else None
        title, artist, composer = process_title_and_metadata(name, available_length, quality)
        if file_id:
            mp3_path, ext = download_file(file_id, era_folder, title)
            if mp3_path and title:
                if ext == '.mp3':
                    try:
                        embed_metadata(mp3_path, title, artist, composer)
                        results['tagged'].append(mp3_path)
                    except Exception as e:
                        print(f"[Warning] Tagging failed for {mp3_path}: {e}")
                        results['not_tagged'].append(mp3_path)
                else:
                    print(f"[Warning] Skipping tagging for non-MP3 file: {mp3_path}")
                    results['not_tagged'].append(mp3_path)
            else:
                results['failed'].append(f"{title} (id: {file_id})")
        else:
            print(f"Skipping invalid or non-pillowcase.su URL: {url}")
            results['failed'].append(f"{title} (id: {file_id})")

def main():
    print("Choose input method:")
    print("1. Google Sheets URL")
    print("2. Local CSV file")
    
    while True:
        try:
            choice = int(input("Enter your choice (1 or 2): "))
            if choice in [1, 2]:
                break
            else:
                print("Please enter 1 or 2.")
        except ValueError:
            print("Invalid input. Please enter 1 or 2.")
    
    if choice == 1:
        # Google Sheets URL method
        print("Enter the Google Sheets URL or direct CSV URL:")
        spreadsheet_url = input().strip()
        
        # Download CSV content
        csv_content = get_csv_from_url(spreadsheet_url)
        if not csv_content:
            print("Failed to download spreadsheet. Please check the URL and try again.")
            return
        
        # Parse CSV content
        try:
            df = pd.read_csv(StringIO(csv_content))
        except Exception as e:
            print(f"Failed to parse CSV: {e}")
            return
    else:
        # Local CSV file method
        print("Enter the path to your CSV file:")
        csv_path = input().strip()
        # Strip quotes if present
        if (csv_path.startswith('"') and csv_path.endswith('"')) or (csv_path.startswith("'") and csv_path.endswith("'")):
            csv_path = csv_path[1:-1].strip()
        
        # Check if file exists
        if not os.path.exists(csv_path):
            print(f"File not found: {csv_path}")
            return
        
        # --- Improved logic: Robust header row detection for multiline quoted headers ---
        required_keywords = ['era', 'name', 'link']
        header_row_index = None
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Read first 50 lines as a block
            block = ''.join([f.readline() for _ in range(50)])
            # Parse as CSV rows
            rows = list(csv.reader(block.splitlines()))
            for i, fields in enumerate(rows):
                # Normalize fields for matching
                norm_fields = [field.lower().replace('\n', ' ').replace(' ', '') for field in fields]
                match_count = 0
                for keyword in required_keywords:
                    if any(keyword in field for field in norm_fields):
                        match_count += 1
                # Check next row for real data (at least 2 non-empty fields)
                if match_count >= 3 and i+1 < len(rows):
                    next_fields = rows[i+1]
                    non_empty = sum(1 for f in next_fields if f.strip())
                    if non_empty >= 2:
                        header_row_index = i
                        break
        if header_row_index is None:
            print("Could not find a valid header row in the first 50 lines of the CSV file.")
            return
        # --- End improved logic ---
        try:
            df = pd.read_csv(csv_path, header=header_row_index, engine='python')
        except Exception as e:
            print(f"Failed to parse CSV file: {e}")
            return
    
    df.columns = [col.strip() for col in df.columns]
    name_col = find_column(df.columns, 'name')
    link_col = find_column(df.columns, 'link')
    length_col = find_column(df.columns, 'available length')
    quality_col = find_column(df.columns, 'quality')
    if not name_col or not link_col:
        print("Could not find required columns. Available columns:")
        print(list(df.columns))
        return
    # Only consider rows with a non-empty link for Era selection
    valid_rows = df[df[link_col].notnull() & (df[link_col].str.strip() != '')]
    # List eras in the order they appear (chronological)
    eras = valid_rows['Era'].dropna().drop_duplicates().tolist()
    print("Available Eras:")
    for idx, era in enumerate(eras):
        print(f"{idx+1}. {era}")
    print("0. All Eras")
    while True:
        try:
            era_choice = int(input(f"Enter the number of the Era you want to download (0 for All): "))
            if 0 <= era_choice <= len(eras):
                break
            else:
                print(f"Please enter a number between 0 and {len(eras)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    if era_choice == 0:
        selected_eras = eras
    else:
        selected_eras = [eras[era_choice-1]]
    results = {'tagged': [], 'not_tagged': [], 'failed': []}
    if len(selected_eras) == 1:
        process_era(df, selected_eras[0], link_col, name_col, length_col, quality_col, results)
    else:
        print(f"Processing {len(selected_eras)} eras in parallel...")
        from threading import Lock
        lock = Lock()
        def thread_safe_process(*args):
            # Wrap process_era to make results thread-safe
            local_results = {'tagged': [], 'not_tagged': [], 'failed': []}
            process_era(*args, local_results)
            with lock:
                results['tagged'].extend(local_results['tagged'])
                results['not_tagged'].extend(local_results['not_tagged'])
                results['failed'].extend(local_results['failed'])
        with ThreadPoolExecutor(max_workers=min(8, len(selected_eras))) as executor:
            futures = [executor.submit(thread_safe_process, df, era, link_col, name_col, length_col, quality_col) for era in selected_eras]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing an era: {e}")
    # Print summary
    print("\n--- Download Summary ---")
    print(f"\nDownloaded and tagged successfully ({len(results['tagged'])}):")
    for f in results['tagged']:
        print(f"  {f}")
    print(f"\nDownloaded but not tagged due to file format or error ({len(results['not_tagged'])}):")
    for f in results['not_tagged']:
        print(f"  {f}")
    print(f"\nFailed to download ({len(results['failed'])}):")
    for f in results['failed']:
        print(f"  {f}")

if __name__ == '__main__':
    main() 