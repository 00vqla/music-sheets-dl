import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from parser import parse_input
from downloader import download_file, embed_metadata, sanitize_folder_name, process_title_and_metadata
from io import StringIO

DOWNLOAD_DIR = 'downloads'

def process_era(df, selected_era, link_col, name_col, length_col, quality_col, results, max_workers=4):
    era_folder = os.path.join(DOWNLOAD_DIR, sanitize_folder_name(selected_era))
    os.makedirs(era_folder, exist_ok=True)
    filtered = df[(df['Era'].str.strip().str.lower() == selected_era.strip().lower()) & (df[link_col].notnull()) & (df[link_col].str.strip() != '')]
    print(f"Found {len(filtered)} files to download for Era: {selected_era}")
    era_results = {'tagged': [], 'not_tagged': [], 'failed': []}
    from threading import Lock
    results_lock = Lock()
    
    def download_and_tag(row_data):
        idx, row = row_data
        url = row[link_col].strip()
        name = row[name_col]
        available_length = row[length_col] if length_col else None
        quality = row[quality_col] if quality_col else None
        title, artist, composer = process_title_and_metadata(name, available_length, quality)
        mp3_path, ext = download_file(url, era_folder, title)
        if mp3_path and title:
            if ext == '.mp3':
                try:
                    print(f"[INFO] Tagging: {mp3_path}")
                    embed_metadata(mp3_path, title, artist, composer)
                    with results_lock:
                        era_results['tagged'].append(mp3_path)
                except Exception as e:
                    print(f"[Warning] Tagging failed for {mp3_path}: {e}")
                    with results_lock:
                        era_results['not_tagged'].append(mp3_path)
            else:
                print(f"[Warning] Skipping tagging for non-MP3 file: {mp3_path}")
                with results_lock:
                    era_results['not_tagged'].append(mp3_path)
        else:
            print(f"[Error] Failed to download: {title} (url: {url})")
            with results_lock:
                era_results['failed'].append(f"{title} (url: {url})")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_and_tag, (idx, row)) for idx, row in filtered.iterrows()]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in download task: {e}")
    
    results['tagged'].extend(era_results['tagged'])
    results['not_tagged'].extend(era_results['not_tagged'])
    results['failed'].extend(era_results['failed'])

def main():
    try:
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
        
        print("\nDownload Configuration:")
        print("Enter the number of simultaneous downloads (1-10, recommended: 4-6):")
        
        while True:
            try:
                max_workers = int(input("Number of simultaneous downloads: "))
                if 1 <= max_workers <= 10:
                    break
                else:
                    print("Please enter a number between 1 and 10.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        print(f"\nWill download up to {max_workers} files simultaneously.")
        
        if choice == 1:
            print("Enter the Google Sheets URL or direct CSV URL:")
            spreadsheet_url = input().strip()
            result, error = parse_input(link=spreadsheet_url)
        else:
            print("Enter the path to your CSV file:")
            csv_path = input().strip()
            if (csv_path.startswith('"') and csv_path.endswith('"')) or (csv_path.startswith("'") and csv_path.endswith("'")):
                csv_path = csv_path[1:-1].strip()
            result, error = parse_input(file=csv_path)
        
        if error:
            print(f"Error: {error}")
            return
        
        df, eras, name_col, link_col, length_col, quality_col = result
        
        valid_rows = df[df[link_col].notnull() & (df[link_col].str.strip() != '')]
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
            process_era(df, selected_eras[0], link_col, name_col, length_col, quality_col, results, max_workers)
        else:
            print(f"Processing {len(selected_eras)} eras in parallel...")
            with ThreadPoolExecutor(max_workers=min(8, len(selected_eras))) as executor:
                futures = [executor.submit(process_era, df, era, link_col, name_col, length_col, quality_col, results, max_workers) for era in selected_eras]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error processing an era: {e}")
        
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
    
    except KeyboardInterrupt:
        print("\nProcess cancelled by user.")
        exit(0)

if __name__ == '__main__':
    main() 