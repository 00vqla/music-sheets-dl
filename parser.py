__all__ = ['parse_input']
import os
import re
import pandas as pd
from io import StringIO

def _find_column(columns, keyword):
    norm_keyword = re.sub(r'[^a-z0-9]', '', keyword.lower())
    for col in columns:
        norm_col = re.sub(r'[^a-z0-9]', '', col.lower())
        if norm_col.endswith('s') and not norm_keyword.endswith('s'):
            norm_col_singular = norm_col[:-1]
        else:
            norm_col_singular = norm_col
        if norm_keyword in norm_col or norm_keyword in norm_col_singular:
            return col
    return None

def get_csv_from_url(url):
    import requests
    if 'googleusercontent.com' in url and 'format=csv' in url:
        try:
            response = requests.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Failed to download CSV from URL: {e}")
            return None
    if 'docs.google.com/spreadsheets' in url:
        id_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        gid_match = re.search(r'[?&]gid=([0-9]+)', url)
        if id_match:
            spreadsheet_id = id_match.group(1)
            gid = gid_match.group(1) if gid_match else '0'
            csv_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
            try:
                response = requests.get(csv_url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                content = response.text
                if content and len(content) > 100:
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
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Failed to download CSV from URL: {e}")
            return None

def parse_input(file=None, link=None):
    """
    Parse a CSV file or Google Sheets link and return (df, eras, name_col, link_col, length_col, quality_col) or (None, error_message)
    """
    if file:
        if not os.path.exists(file):
            return None, 'File not found.'
        header_row_index = None
        with open(file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if line.strip() and not all(x == ',' for x in line.strip()):
                    header_row_index = i
                    break
        if header_row_index is None:
            return None, 'Could not find a valid header row in the CSV file.'
        try:
            df = pd.read_csv(file, header=header_row_index, engine='python', dtype=str)
        except Exception as e:
            return None, f'Failed to parse CSV: {e}'
    elif link:
        csv_content = get_csv_from_url(link)
        if not csv_content:
            return None, 'Failed to download spreadsheet. Please check the link.'
        try:
            df = pd.read_csv(StringIO(csv_content), dtype=str)
        except Exception as e:
            return None, f'Failed to parse CSV: {e}'
    else:
        return None, 'No file or link provided.'
    df.columns = [col.strip() for col in df.columns]
    name_col = _find_column(df.columns, 'songs') or _find_column(df.columns, 'name') or _find_column(df.columns, 'title')
    link_col = _find_column(df.columns, 'link')
    length_col = _find_column(df.columns, 'available length')
    quality_col = _find_column(df.columns, 'quality')
    if not name_col or not link_col:
        return None, f'Could not find required columns. Available columns: {list(df.columns)}'
    valid_rows = df[df[link_col].notnull() & (df[link_col].str.strip() != '')]
    eras = valid_rows['Era'].dropna().drop_duplicates().tolist()
    if not eras:
        return None, 'No eras found in the file.'
    return (df, eras, name_col, link_col, length_col, quality_col), None 