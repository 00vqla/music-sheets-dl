import os
import pandas as pd
import requests
import re
from mutagen.easyid3 import EasyID3

DOWNLOAD_DIR = 'downloads'

def extract_id(url):
    """Extract the file ID from a pillowcase.su link."""
    match = re.search(r'pillowcase\.su/f/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

def remove_emoji(text):
    # Remove all emoji using regex
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002700-\U000027BF"  # Dingbats
        u"\U000024C2-\U0001F251"  # Enclosed characters
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def sanitize_folder_name(name):
    # Remove or replace characters not allowed in folder names
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()

def sanitize_filename(filename):
    # Remove or replace characters not allowed in filenames
    # Replace invalid characters with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length to avoid filesystem issues
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def download_file(file_id, dest_folder, title):
    api_url = f"https://api.pillowcase.su/api/download/{file_id}.mp3"
    # Use title as filename, fallback to file_id if title is empty
    if title and title.strip():
        safe_title = sanitize_filename(title)
        local_filename = os.path.join(dest_folder, f"{safe_title}.mp3")
    else:
        local_filename = os.path.join(dest_folder, f"{file_id}.mp3")
    
    try:
        with requests.get(api_url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded: {api_url} -> {local_filename}")
        return local_filename
    except Exception as e:
        print(f"Failed to download {api_url}: {e}")
        return None

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
    # Remove emoji
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
    # Handle "???" titles by using text in parentheses
    if title.strip() == "???":
        # Look for text in parentheses after the "???"
        paren_match = re.search(r'\(([^)]+)\)', name)
        if paren_match:
            title = paren_match.group(1).strip()
    # Handle other parentheses as alternative titles
    else:
        # Look for text in parentheses that's not already handled
        paren_match = re.search(r'\(([^)]+)\)', title)
        if paren_match and not re.search(r'feat\.', paren_match.group(1), re.IGNORECASE):
            main_title = title.replace(paren_match.group(0), '').strip()
            alt_title = paren_match.group(1).strip()
            title = f"{main_title} / {alt_title}"
    # Remove square brackets from title
    title = re.sub(r'\[[^\]]*\]', '', title).strip()
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
    # Convert Google Sheets URL to CSV export URL
    if 'docs.google.com/spreadsheets' in url:
        # Extract the spreadsheet ID
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if match:
            spreadsheet_id = match.group(1)
            # Try different CSV export URLs
            csv_urls = [
                f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=0",
                f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv",
                f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&gid=0"
            ]
            
            for csv_url in csv_urls:
                try:
                    print(f"Trying to download from: {csv_url}")
                    response = requests.get(csv_url, timeout=30)
                    response.raise_for_status()
                    content = response.text
                    if content and len(content) > 100:  # Basic check for valid CSV content
                        print("Successfully downloaded CSV content")
                        return content
                    else:
                        print(f"Received empty or invalid content from {csv_url}")
                except Exception as e:
                    print(f"Failed to download from {csv_url}: {e}")
                    continue
            
            print("All CSV export attempts failed. The spreadsheet might be:")
            print("- Not publicly accessible")
            print("- Requiring authentication")
            print("- Flagged as suspicious by Google")
            print("- Using a different sharing format")
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
            df = pd.read_csv(pd.StringIO(csv_content))
        except Exception as e:
            print(f"Failed to parse CSV: {e}")
            return
    else:
        # Local CSV file method
        print("Enter the path to your CSV file:")
        csv_path = input().strip()
        
        # Check if file exists
        if not os.path.exists(csv_path):
            print(f"File not found: {csv_path}")
            return
        
        # Parse CSV file
        try:
            df = pd.read_csv(csv_path)
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
    eras = sorted(valid_rows['Era'].dropna().unique())
    print("Available Eras:")
    for idx, era in enumerate(eras):
        print(f"{idx+1}. {era}")
    while True:
        try:
            era_choice = int(input("Enter the number of the Era you want to download: "))
            if 1 <= era_choice <= len(eras):
                selected_era = eras[era_choice-1]
                break
            else:
                print(f"Please enter a number between 1 and {len(eras)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    # Create subfolder for the selected Era
    era_folder = os.path.join(DOWNLOAD_DIR, sanitize_folder_name(selected_era))
    os.makedirs(era_folder, exist_ok=True)
    # Filter rows
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
            mp3_path = download_file(file_id, era_folder, title)
            if mp3_path and title:
                embed_metadata(mp3_path, title, artist, composer)
        else:
            print(f"Skipping invalid or non-pillowcase.su URL: {url}")

if __name__ == '__main__':
    main() 