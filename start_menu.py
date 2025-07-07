import tkinter as tk
from PIL import Image, ImageTk
import os

ICON_DIR = 'png icons'

ICON_SIZE = (32, 32)  # Smaller icon
SMALL_ICON_SIZE = (16, 16)
LOGO_SIZE = (28, 28)
CIRCLE_BG = '#f3f4f6'
ICON_GRAY = '#6b7280'
BUTTON_BG = '#e5e7eb'  # Lighter button background
BUTTON_FG = '#222'     # Dark text
BUTTON_ACTIVE_BG = '#0f172a'
CARD_BG = 'white'
CARD_BORDER = '#e5e7eb'
APP_BG = '#f7fafd'

def load_icon(name, size=ICON_SIZE, colorize_gray=False):
    path = os.path.join(ICON_DIR, name)
    img = Image.open(path).convert('RGBA').resize(size, Image.Resampling.LANCZOS)
    if colorize_gray:
        # Convert black to gray
        datas = img.getdata()
        newData = []
        for item in datas:
            if item[0] < 50 and item[1] < 50 and item[2] < 50 and item[3] > 0:
                newData.append((107, 114, 128, item[3]))  # #6b7280
            else:
                newData.append(item)
        img.putdata(newData)
    return ImageTk.PhotoImage(img)

def load_small_icon(name):
    return load_icon(name, size=SMALL_ICON_SIZE, colorize_gray=True)

def load_logo_icon(name):
    return load_icon(name, size=LOGO_SIZE, colorize_gray=True)

def circle_icon(canvas, icon_img, x, y, r):
    # Draw a circle and put the icon in the center
    circle = canvas.create_oval(x - r, y - r, x + r, y + r, fill=CIRCLE_BG, outline='')
    canvas.create_image(x, y, image=icon_img)
    return circle

class ArtistSelectUI(tk.Frame):
    ARTISTS = [
        {"name": "Taylor Swift", "tracks": 245},
        {"name": "The Beatles", "tracks": 213},
        {"name": "Drake", "tracks": 189},
        {"name": "Ariana Grande", "tracks": 156},
        {"name": "Ed Sheeran", "tracks": 134},
        {"name": "Billie Eilish", "tracks": 67},
        {"name": "Post Malone", "tracks": 89},
        {"name": "Olivia Rodrigo", "tracks": 34},
    ]
    def __init__(self, master, icon_img, on_back):
        super().__init__(master, bg=APP_BG)
        self.icon_img = icon_img
        self.on_back = on_back
        self._build_ui()

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self, bg=APP_BG)
        top.pack(fill='x', pady=(30, 0), padx=40)
        back_btn = tk.Button(top, text='←  Back', font=('Segoe UI', 11, 'bold'), bg=APP_BG, fg='#222', bd=0, cursor='hand2', command=self.on_back, activebackground=APP_BG, activeforeground='#222')
        back_btn.pack(side='left')
        title = tk.Label(top, text='Select an Artist', font=('Segoe UI', 20, 'bold'), bg=APP_BG, fg='#111')
        title.pack(side='left', padx=(20, 0))
        # Subtitle
        subtitle = tk.Label(self, text='Choose from our curated collection of artist discographies', font=('Segoe UI', 12), bg=APP_BG, fg='#64748b')
        subtitle.pack(anchor='w', padx=40, pady=(0, 18))
        # Main content frame with margin
        content_frame = tk.Frame(self, bg=APP_BG)
        content_frame.pack(fill='both', expand=True, padx=40)
        # Search bar
        search_entry = tk.Entry(content_frame, font=('Segoe UI', 11), relief=tk.FLAT, bg='#f3f4f6', justify='left')
        search_entry.pack(fill='x', ipady=8, pady=(0, 18))
        search_entry.insert(0, 'Search for an artist...')
        # Cards grid
        grid = tk.Frame(content_frame, bg=APP_BG)
        grid.pack()
        self.artist_cards = []
        for i, artist in enumerate(self.ARTISTS):
            card = tk.Frame(grid, bg='white', bd=0, highlightthickness=1, highlightbackground='#e5e7eb')
            card.grid(row=i//3, column=i%3, padx=18, pady=18, ipadx=8, ipady=8, sticky='nsew')
            # Icon
            icon_canvas = tk.Canvas(card, width=48, height=48, bg='white', highlightthickness=0)
            icon_canvas.pack(pady=(18, 0), anchor='w', padx=18)
            circle_icon(icon_canvas, self.icon_img, 24, 24, 24)
            # Track badge
            badge = tk.Label(card, text=f'{artist["tracks"]} tracks', font=('Segoe UI', 9, 'bold'), bg='#f3f4f6', fg='#222', bd=0, relief='flat')
            badge.place(x=120, y=18)
            # Name
            name = tk.Label(card, text=artist['name'], font=('Segoe UI', 13, 'bold'), bg='white', fg='#111', anchor='w', justify='left')
            name.pack(pady=(12, 0), anchor='w', padx=18, fill='x')
            # Track count
            track_count = tk.Label(card, text=f'# {artist["tracks"]} total tracks', font=('Segoe UI', 10), bg='white', fg='#444', anchor='w', justify='left')
            track_count.pack(anchor='w', padx=18, fill='x')
            # Discography
            discog = tk.Label(card, text='🗂 Complete discography', font=('Segoe UI', 10), bg='white', fg='#444', anchor='w', justify='left')
            discog.pack(pady=(0, 12), anchor='w', padx=18, fill='x')
            # Select button
            select_btn = tk.Button(
                card,
                text='Select Artist',
                font=('Segoe UI', 11, 'bold'),
                bg='#e5e7eb',
                fg='#222',
                activebackground='#d1d5db',
                activeforeground='#222',
                bd=0,
                relief='flat',
                cursor='hand2',
                padx=10,
                pady=8,
                highlightthickness=1,
                highlightbackground='#d1d5db',
                borderwidth=1,
                anchor='w',
                justify='left'
            )
            select_btn.pack(pady=(0, 18), fill='x', padx=12, anchor='w')
            self.artist_cards.append(card)

class ModernUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Batch Music Downloader')
        self.geometry('1100x900')
        self.configure(bg=APP_BG)
        self.icon_images = {}
        self.small_icons = {}
        self.logo_icon = None
        self._load_icons()
        self._build_layout()

    def _load_icons(self):
        icon_files = [
            'file_csv.png', 'file_music.png', 'upload_file.png', 'browse_artists.png',
            'download_threads.png', 'era.png', 'download_location.png', 'check_mark.png',
            'options.png', 'info.png'
        ]
        for fname in icon_files:
            self.icon_images[fname] = load_icon(fname, colorize_gray=True)
            self.small_icons[fname] = load_small_icon(fname)
        self.logo_icon = load_logo_icon('file_csv.png')

    def _card(self, parent, width=340, height=340):
        card = tk.Frame(parent, bg=CARD_BG, bd=0, highlightthickness=1, highlightbackground=CARD_BORDER)
        card.configure(width=width, height=height)
        card.pack_propagate(False)
        card.grid_propagate(False)
        return card

    def _main_card_content(self, card, icon, title, desc, bullets, button_text, button_icon):
        content = tk.Frame(card, bg=CARD_BG)
        content.pack(expand=True, fill='both', padx=24, pady=18)
        # Smaller circular icon background
        canvas = tk.Canvas(content, width=48, height=48, bg=CARD_BG, highlightthickness=0)
        canvas.pack(pady=(0, 10))
        circle_icon(canvas, icon, 24, 24, 24)
        # Title
        title_label = tk.Label(content, text=title, font=('Segoe UI', 15, 'bold'), bg=CARD_BG, fg='#222')
        title_label.pack(pady=(0, 8))
        # Description
        desc_label = tk.Label(content, text=desc, font=('Segoe UI', 11), bg=CARD_BG, fg='#444', wraplength=270, justify='center')
        desc_label.pack(pady=(0, 10))
        # Bullets
        for bullet in bullets:
            bullet_label = tk.Label(content, text='\u2713 ' + bullet, font=('Segoe UI', 10), bg=CARD_BG, fg='#555', anchor='w', justify='left')
            bullet_label.pack(anchor='w', padx=32)
        # Large, wide, dark button with white text and icon, rounded corners
        btn_frame = tk.Frame(content, bg=CARD_BG)
        btn_frame.pack(pady=(22, 0), fill='x')
        if button_text == 'Browse Files':
            btn = tk.Button(
                btn_frame,
                text=button_text,
                image=button_icon,
                compound='left',
                font=('Segoe UI', 13, 'bold'),
                bg=BUTTON_BG,
                fg=BUTTON_FG,
                activebackground=BUTTON_ACTIVE_BG,
                activeforeground='white',
                bd=0,
                padx=18,
                pady=10,
                cursor='hand2',
                relief='flat',
                highlightthickness=0,
                borderwidth=0,
                width=24,
                command=self._upload_file_dialog
            )
        elif button_text == 'Browse Artists':
            btn = tk.Button(
                btn_frame,
                text=button_text,
                image=button_icon,
                compound='left',
                font=('Segoe UI', 13, 'bold'),
                bg=BUTTON_BG,
                fg=BUTTON_FG,
                activebackground=BUTTON_ACTIVE_BG,
                activeforeground='white',
                bd=0,
                padx=18,
                pady=10,
                cursor='hand2',
                relief='flat',
                highlightthickness=0,
                borderwidth=0,
                width=24,
                command=self._show_artist_select
            )
        else:
            btn = tk.Button(
                btn_frame,
                text=button_text,
                image=button_icon,
                compound='left',
                font=('Segoe UI', 13, 'bold'),
                bg=BUTTON_BG,
                fg=BUTTON_FG,
                activebackground=BUTTON_ACTIVE_BG,
                activeforeground='white',
                bd=0,
                padx=18,
                pady=10,
                cursor='hand2',
                relief='flat',
                highlightthickness=0,
                borderwidth=0,
                width=24
            )
        btn.pack(ipadx=40, ipady=8, fill='x', expand=True)
        btn.configure(overrelief='flat')
        btn_frame.configure(padx=8, pady=2)
        return btn

    def _upload_file_dialog(self):
        from tkinter import filedialog, messagebox
        filetypes = [
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx;*.xls"),
            ("All files", "*.*")
        ]
        filepath = filedialog.askopenfilename(title="Select CSV/Spreadsheet File", filetypes=filetypes)
        if filepath:
            filename = os.path.basename(filepath)
            # Optionally update the button text or show a message
            messagebox.showinfo("File Selected", f"You selected: {filename}")

    def _show_artist_select(self):
        # Remove all widgets from root window
        for widget in self.winfo_children():
            widget.destroy()
        # Show artist select UI
        artist_ui = ArtistSelectUI(self, self.icon_images['file_music.png'], self._show_main_menu)
        artist_ui.pack(expand=True, fill='both')

    def _show_main_menu(self):
        for widget in self.winfo_children():
            widget.destroy()
        self._build_layout()

    def _build_layout(self):
        # Main container
        container = tk.Frame(self, bg=APP_BG)
        container.pack(expand=True)
        # Welcome title
        title = tk.Label(container, text='Welcome to Batch Music Downloader', font=('Segoe UI', 22, 'bold'), bg=APP_BG, fg='#222')
        title.pack(pady=(40, 6))
        subtitle = tk.Label(container, text='Choose how you want to begin your batch music download journey. Upload your own files or explore our curated artist database.', font=('Segoe UI', 12), bg=APP_BG, fg='#444', wraplength=700, justify='center')
        subtitle.pack(pady=(0, 30))
        # Cards row
        cards_row = tk.Frame(container, bg=APP_BG)
        cards_row.pack(pady=(0, 30))
        # Browse Files card
        files_card = self._card(cards_row)
        files_card.grid(row=0, column=0, padx=32)
        self._main_card_content(
            files_card,
            self.icon_images['file_csv.png'],
            'Browse Files',
            'Upload your own CSV or spreadsheet files to batch download music.',
            ['CSV & Excel support', 'Custom era selection', 'Flexible import options'],
            'Upload Files',
            self.small_icons['upload_file.png']
        )
        # Browse Artists card
        artists_card = self._card(cards_row)
        artists_card.grid(row=0, column=1, padx=32)
        self._main_card_content(
            artists_card,
            self.icon_images['file_music.png'],
            'Browse Artists',
            'Explore our curated database of artists with pre-loaded data ready for download.',
            ['Curated artist database', 'Pre-loaded analytics', 'Quick start option'],
            'Browse Artists',
            self.small_icons['browse_artists.png']
        )

if __name__ == '__main__':
    app = ModernUI()
    app.mainloop() 