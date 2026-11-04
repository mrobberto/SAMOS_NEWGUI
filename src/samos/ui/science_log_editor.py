"""Read-only exposure table with Comment-only editor for SAMOS science CSV logs."""
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from samos.system.science_comments import read_science, update_comment


def open_science_comment_editor(parent, path, select_latest=False):
    path = Path(path)
    win = tk.Toplevel(parent)
    win.title('Science Logbook — Edit Exposure Comments')
    win.geometry('1050x600')
    ttk.Label(win, text=str(path), wraplength=1000).pack(fill='x', padx=8, pady=5)
    ttk.Label(win, text='Only the Comment field is editable. Other acquisition values are protected.').pack(anchor='w', padx=8)
    frame = ttk.Frame(win)
    frame.pack(fill='both', expand=True, padx=8, pady=5)
    cols = ('utc','file','target','type','comment')
    tree = ttk.Treeview(frame, columns=cols, show='headings', height=13, selectmode='browse')
    for c, label, width in zip(cols, ('Date / local time','Filename','Target','Filter','Comment'), (180,250,145,110,325)):
        tree.heading(c, text=label)
        tree.column(c, width=width, anchor='w')
    tree.pack(side='left', fill='both', expand=True)
    sb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
    sb.pack(side='right', fill='y')
    tree.configure(yscrollcommand=sb.set)
    ttk.Label(win, text='Selected exposure comment:').pack(anchor='w', padx=8)
    editor = tk.Text(win, height=5, wrap='word')
    editor.pack(fill='x', padx=8, pady=4)
    status = tk.StringVar(value='')
    state = {'sha':None, 'rows':{}, 'selected':None}

    def select(_event=None):
        selected = tree.selection()
        state['selected'] = int(selected[0]) if selected else None
        editor.delete('1.0','end')
        if state['selected'] is not None:
            editor.insert('1.0', state['rows'][state['selected']][11])

    tree.bind('<<TreeviewSelect>>', select)

    def refresh():
        try:
            sha, allrows, candidates = read_science(path)
        except Exception as exc:
            messagebox.showerror('Science logbook', str(exc), parent=win)
            return
        tree.delete(*tree.get_children())
        state['sha'] = sha
        state['rows'] = {index: row for index, row in candidates}
        state['selected'] = None
        editor.delete('1.0','end')
        for i, r in candidates:
            tree.insert('', 'end', iid=str(i), values=(r[0]+' '+r[1], r[6], r[2], r[3], r[11]))
        status.set(f'{len(candidates)} exposure records; select one to edit its comment.')
        if select_latest and candidates:
            latest = str(candidates[-1][0])
            tree.selection_set(latest)
            tree.focus(latest)
            tree.see(latest)
            select()
            editor.focus_set()

    def save():
        idx = state['selected']
        if idx is None:
            messagebox.showinfo('Select an exposure','Select an exposure row first.',parent=win)
            return
        comment = editor.get('1.0','end-1c')
        old = state['rows'][idx][11]
        if comment == old:
            status.set('Comment unchanged.')
            return
        if not messagebox.askyesno('Save exposure comment',
                f'Update only the Comment field for:\n{state["rows"][idx][6]}?',parent=win):
            return
        try:
            update_comment(path, idx, comment, state['sha'])
        except Exception as exc:
            messagebox.showerror('Comment not saved',str(exc),parent=win)
            return
        saved_index = idx
        refresh()
        if tree.exists(str(saved_index)):
            tree.selection_set(str(saved_index))
            tree.focus(str(saved_index))
            tree.see(str(saved_index))
            select()
        status.set('Comment saved. Previous logbook preserved in a timestamped .bak file.')

    bar = ttk.Frame(win)
    bar.pack(fill='x',padx=8,pady=4)
    ttk.Button(bar,text='Refresh',command=refresh).pack(side='left',padx=3)
    ttk.Button(bar,text='Save Comment',command=save).pack(side='left',padx=3)
    ttk.Button(bar,text='Close',command=win.destroy).pack(side='right',padx=3)
    ttk.Label(win,textvariable=status).pack(anchor='w',padx=8,pady=4)
    refresh()
    return win
