# tracker-sheets-dl

Python script to download and tag music from Google Sheets trackers (with pillowcase.su links)

## Features

- **Multiple Input Sources**: Google Sheets URLs and local CSV files
- **Configurable Parallel Downloads**: Adjustable simultaneous download threads (1-10)
- **Automatic Metadata Embedding**: 
  - Title formatting (removes emojis, brackets, handles features)
  - Artist and producers extraction
  - Quality indicators (LQ for low quality, Snippet for snippets)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/00vqla/tracker-sheets-dl
   cd tracker-sheets-dl
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage
   ```bash
   python3 runner.py
   ```

## Example Output

```
Available Eras:
1. Love Sick
2. Heaven Or Hell
3. JACKBOYS

Enter the number of the Era you want to download: 1
Found 74 files to download for Era: Love Sick
Downloaded: https://api.pillowcase.su/api/download/abc123.mp3 -> downloads/Love Sick/abc123.mp3
Embedded metadata into downloads/Love Sick/abc123.mp3
```

## Title Formatting Rules

- **Features**: `(feat. Artist)` → `(Feat. Artist)`
- **Producers**: `(prod. Producer)` → Composer field
- **Alternative Titles**: `Title (Title 2)` → `Title / Title 2`
- **Quality**: Low Quality → `(LQ)`
- **Snippets**: Snippet → `(Snippet)`
- **Cleanup**: Removes emojis, square brackets, extra spaces

## Requirements

- Python 3.7+
- pandas
- requests
- mutagen

## Supported Spreadsheet Format

The program expects a CSV/spreadsheet with these columns:
- **Era**: Album/era name
- **Name**: Song title (with features, producers, etc.)
- **Link(s)**: pillowcase.su download links
- **Available Length**: Track type (Full, Snippet, OG File, etc.)
- **Quality**: Audio quality (Low Quality, CD Quality, etc.)
