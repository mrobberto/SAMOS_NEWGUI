"""Read-only browser for SAMOS SISI pixel-mask .reg/.jpg pairs.

This module intentionally does not import SAMOS instrument or DMD controllers.
It never reads or modifies GUI hardware state, and never writes files.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MaskEntry:
    region: Path
    preview: Path | None
    relative: Path


def default_pixel_root() -> Path:
    """Find src/samos/data/regions/pixels from src/samos/ui/ here."""
    return Path(__file__).resolve().parents[1] / "data" / "regions" / "pixels"


def inventory(root: Path) -> list[MaskEntry]:
    """Read-only inventory. Only .reg files are browsed, not orphan .jpg files."""
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Pixel-mask directory does not exist: {root}")
    result = []
    for region in root.rglob('*'):
        if region.suffix.lower() != '.reg' or not region.is_file() or region.is_symlink():
            continue
        # Disallow symlinked intermediate directories from linking outside this tree.
        if not region.resolve().is_relative_to(root):
            continue
        # Per-mask preview, located beside the region by the naming convention.
        preferred = region.with_suffix('.jpg')
        fallback = region.parent / 'previews' / (region.stem + '.jpg')
        preview = next((p for p in (preferred, fallback)
                        if p.is_file() and not p.is_symlink() and
                        p.resolve().is_relative_to(root)), None)
        result.append(MaskEntry(region, preview, region.relative_to(root)))
    return sorted(result, key=lambda x: str(x.relative).casefold())


def filtered_entries(entries: Iterable[MaskEntry], search: str) -> list[MaskEntry]:
    key = search.casefold().strip()
    return [e for e in entries if key in str(e.relative).casefold()]


def browser_window(parent, root: Path | None = None):
    """Open the read-only viewer on the Tk main thread. No hardware connection."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from PIL import Image, ImageTk

    initial_root = Path(root) if root is not None else default_pixel_root()

    class Browser(tk.Toplevel):
        def __init__(self):
            super().__init__(parent)
            self.title('SAMOS Pixel Mask Browser — PREVIEW ONLY / NO DMD SEND')
            self.geometry('1140x790')
            self.minsize(760, 510)
            self._root = initial_root.expanduser().resolve()
            self._entries: list[MaskEntry] = []
            self._by_iid: dict[str, MaskEntry] = {}
            self._photo = None
            self._selected: MaskEntry | None = None
            self._image = None
            self._image_error: str | None = None
            self._search = tk.StringVar(self)
            self._location = tk.StringVar(self, value=str(self._root))
            self._detail = tk.StringVar(self, value='Select a .reg mask to inspect its JPEG.')
            self._counts = tk.StringVar(self)

            banner = ttk.Frame(self, padding=8)
            banner.pack(fill='x')
            ttk.Label(banner, text='SISI Pixel Mask Browser', font=('TkDefaultFont', 15, 'bold')).pack(side='left')
            ttk.Label(banner, text='READ ONLY  •  NO DMD SEND', foreground='#9b362e').pack(side='right')

            toolbar = ttk.Frame(self, padding=(8, 2, 8, 4))
            toolbar.pack(fill='x')
            ttk.Button(toolbar, text='Choose folder...', command=self._choose_folder).pack(side='left')
            ttk.Button(toolbar, text='Refresh', command=self._refresh).pack(side='left', padx=6)
            ttk.Label(toolbar, text='Filter:').pack(side='left', padx=(12, 4))
            search_entry = ttk.Entry(toolbar, textvariable=self._search, width=32)
            search_entry.pack(side='left')
            self._search.trace_add('write', lambda *_: self._populate())
            ttk.Label(toolbar, textvariable=self._counts).pack(side='right')
            ttk.Label(self, textvariable=self._location, anchor='w', padding=(8,0)).pack(fill='x')

            main = ttk.Panedwindow(self, orient='horizontal')
            main.pack(fill='both', expand=True, padx=8, pady=6)
            navigator = ttk.Frame(main)
            canvas_area = ttk.Frame(main)
            main.add(navigator, weight=2)
            main.add(canvas_area, weight=3)

            self._tree = ttk.Treeview(navigator, show='tree', selectmode='browse')
            yscroll = ttk.Scrollbar(navigator, orient='vertical', command=self._tree.yview)
            self._tree.configure(yscrollcommand=yscroll.set)
            self._tree.pack(side='left', fill='both', expand=True)
            yscroll.pack(side='right', fill='y')
            self._tree.bind('<<TreeviewSelect>>', self._select)

            self._preview_label = tk.Label(canvas_area, bg='black', fg='white',
                                           text='Select a mask', anchor='center')
            self._preview_label.pack(fill='both', expand=True)
            self._preview_label.bind('<Configure>', lambda _: self._redraw())
            ttk.Label(canvas_area, textvariable=self._detail, wraplength=600,
                      anchor='w', justify='left').pack(fill='x', pady=5)
            ttk.Label(self, text='JPEG preview in SISI image-pixel coordinates; independent of the live DMD-state display. '
                                  'Missing previews: run regions_to_jpg.py --apply in pixels/.',
                      padding=(8, 4), wraplength=1050).pack(fill='x')
            self._refresh()

        def _choose_folder(self):
            selected = filedialog.askdirectory(parent=self, initialdir=str(self._root),
                                               title='Select a regions/pixels folder')
            if selected:
                self._root = Path(selected).resolve()
                self._location.set(str(self._root))
                self._refresh()

        def _refresh(self):
            try:
                self._entries = inventory(self._root)
            except (OSError, ValueError) as exc:
                messagebox.showwarning('Pixel Mask Browser', str(exc), parent=self)
                self._entries = []
            self._selected = None
            self._image = None
            self._image_error = None
            self._detail.set('Select a .reg mask to inspect its JPEG.')
            self._populate()
            self._redraw()

        def _populate(self):
            self._tree.delete(*self._tree.get_children())
            self._by_iid.clear()
            current = filtered_entries(self._entries, self._search.get())
            folders = {(): ''}
            for i, entry in enumerate(current):
                parent_id = ''
                parts = entry.relative.parts
                for depth in range(1, len(parts)):
                    key = parts[:depth]
                    if key not in folders:
                        folders[key] = self._tree.insert(parent_id, 'end', text=parts[depth-1], open=True)
                    parent_id = folders[key]
                mark = '  [JPG]' if entry.preview else '  [no JPG]'
                iid = self._tree.insert(parent_id, 'end', text=entry.region.stem + mark)
                self._by_iid[iid] = entry
            self._counts.set(f'{len(current)} masks / {sum(e.preview is not None for e in current)} previews')

        def _select(self, _event=None):
            ids = self._tree.selection()
            if not ids or ids[0] not in self._by_iid:
                return
            entry = self._by_iid[ids[0]]
            self._selected = entry
            self._image = None
            self._image_error = None
            if entry.preview:
                try:
                    with Image.open(entry.preview) as src:
                        self._image = src.convert('RGB').copy()
                except (OSError, ValueError) as exc:
                    self._image_error = str(exc)
            self._detail.set(f'Mask: {entry.relative}\n'
                             f'Preview: {entry.preview.relative_to(self._root) if entry.preview else "NOT FOUND"}\n'
                             'PREVIEW ONLY — no mask is loaded or sent to the DMD.')
            self._redraw()

        def _redraw(self):
            label = self._preview_label
            w, h = max(label.winfo_width(), 80), max(label.winfo_height(), 80)
            if self._image is None:
                label.configure(image='', text=(self._image_error or
                    ('No JPEG for this mask; run regions_to_jpg.py --apply.'
                     if self._selected else 'Select a mask')), bg='black', fg='white')
                self._photo = None
                return
            # Never rescale to a different aspect ratio or auto-center mask geometry.
            img = self._image.copy()
            resampling = getattr(Image, 'Resampling', Image).LANCZOS
            img.thumbnail((max(w-8,1), max(h-8,1)), resampling)
            self._photo = ImageTk.PhotoImage(img, master=self)
            label.configure(image=self._photo, text='', bg='black')

    return Browser()


if __name__ == '__main__':
    import sys
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else default_pixel_root()
    win = browser_window(root, folder)
    win.protocol('WM_DELETE_WINDOW', root.destroy)
    root.mainloop()
