# Batch Download Script for Music Trackers

A Python script that downloads music files from Google Sheets trackers, specifically designed for pillowcase.su hosted files. Automatically organizes downloads by era/album and embeds proper metadata.

## Features

- **Dynamic Era Selection**: Choose from available eras in the spreadsheet
- **Automatic Metadata Embedding**: 
  - Title formatting (removes grailed emojis, brackets, handles features)
  - Artist and producers extraction
  - Quality indicators (LQ for low quality, Snippet for snippets)

## New in Latest Version

- **Download All Eras at Once**: You can now select 'All Eras' to download every era in the tracker in one go.
- **Parallel Era Downloads**: When downloading all eras, the script processes each era simultaneously for much faster batch downloads.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/00vqla/spreadsheet-converter
   cd batch-download-spreadsheet
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the script:**
   ```bash
   python3 batch_download.py
   ```

2. **Enter the Google Sheets URL** when prompted (or direct CSV URL)

3. **Select an Era** from the available options

4. **Wait for downloads** - files will be organized in `downloads/[Era Name]/`

## Title Formatting Rules

The script automatically formats song titles according to these rules:

- **Features**: `(feat. Artist)` → `(Feat. Artist)`
- **Producers**: `(prod. Producer)` → Composer field
- **Alternative Titles**: `Title (Title 2)` → `Title / Title 2`
- **Quality**: Low Quality → `(LQ)`
- **Snippets**: Snippet → `(Snippet)`
- **Cleanup**: Removes emojis, square brackets, extra spaces

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

## File Structure

```
batch-download-spreadsheet/
├── batch_download.py          # Main script
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── LICENSE                   # License file
└── downloads/                # Downloaded files (created automatically)
    ├── Love Sick/
    ├── Heaven Or Hell/
    └── JACKBOYS/
```

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Disclaimer

This tool is for educational purposes. Please respect copyright and only download content you have permission to access. 
