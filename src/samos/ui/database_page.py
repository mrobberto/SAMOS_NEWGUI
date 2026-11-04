"""Read-only Settings.yaml browser for the existing SAMOS notebook.
This page never writes to YAML or calls hardware control methods.
"""
import csv
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
import yaml
from .common_frame import SAMOSFrame


def load_records(path):
    with Path(path).open('r',encoding='utf-8') as handle:
        data=yaml.safe_load(handle)
    if not isinstance(data,dict):
        raise ValueError('Settings YAML must contain a mapping')
    rows=[]
    for key,val in sorted(data.items()):
        if isinstance(val,list) and len(val)==3:
            v,t,prev=val
            rows.append((str(key),str(v),str(t),str(prev),'OK'))
        else:
            rows.append((str(key),repr(val),'','','INVALID'))
    return rows


class DatabasePage(SAMOSFrame):
    def __init__(self,parent,container,**kwargs):
        super().__init__(parent,container,'Settings Database — READ ONLY',**kwargs)
        self.filename=Path(self.db.db_path)
        self.records=[]
        page=self.main_frame
        page.columnconfigure(0,weight=1)
        page.rowconfigure(0,weight=1)
        notebook=ttk.Notebook(page)
        notebook.grid(row=0,column=0,sticky='nsew')
        settings_tab=ttk.Frame(notebook)
        history_tab=ttk.Frame(notebook)
        notebook.add(settings_tab,text='Settings.yaml')
        notebook.add(history_tab,text='DMD Mask History')
        root=settings_tab
        root.columnconfigure(0,weight=1)
        root.rowconfigure(2,weight=1)
        top=ttk.Frame(root,padding=8);top.grid(row=0,column=0,sticky='ew')
        self.path_label=ttk.Label(top,text=str(self.filename));self.path_label.pack(side='left',fill='x',expand=True)
        ttk.Button(top,text='Refresh',command=self.refresh).pack(side='left',padx=3)
        ttk.Button(top,text='Export CSV…',command=self.export_csv).pack(side='left',padx=3)
        bar=ttk.Frame(root,padding=(8,0,8,6));bar.grid(row=1,column=0,sticky='ew')
        ttk.Label(bar,text='Filter:').pack(side='left')
        self.filter_var=tk.StringVar()
        self.filter_var.trace_add('write',lambda *_:self.populate())
        ttk.Entry(bar,textvariable=self.filter_var).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Label(bar,text='Saved GUI state; not live hardware telemetry').pack(side='left')
        table=ttk.Frame(root);table.grid(row=2,column=0,sticky='nsew',padx=8)
        table.rowconfigure(0,weight=1);table.columnconfigure(0,weight=1)
        keys=('parameter','current','changed','previous','status')
        self.tree=ttk.Treeview(table,columns=keys,show='headings')
        for key,label,width in zip(keys,('Parameter','Current','Last update (timezone unspecified)','Previous','Record'),(230,210,220,200,80)):
            self.tree.heading(key,text=label);self.tree.column(key,width=width,anchor='w')
        self.tree.grid(row=0,column=0,sticky='nsew')
        scroll=ttk.Scrollbar(table,orient='vertical',command=self.tree.yview)
        scroll.grid(row=0,column=1,sticky='ns');self.tree.configure(yscrollcommand=scroll.set)
        self.status=ttk.Label(root,text='',padding=8);self.status.grid(row=3,column=0,sticky='ew')
        self._build_dmd_history(history_tab)
        self.refresh()

    def _build_dmd_history(self, root):
        from .dmd_history_reader import read_dmd_history
        self._read_dmd_history=read_dmd_history
        self.dmd_log_path=Path(getattr(self.parent,'ops_log_path',self.PAR.output_dir / 'operations.jsonl'))
        root.columnconfigure(0,weight=1)
        root.rowconfigure(2,weight=1)
        header=ttk.Frame(root,padding=8);header.grid(row=0,column=0,sticky='ew')
        ttk.Label(header,text=str(self.dmd_log_path)).pack(side='left',fill='x',expand=True)
        ttk.Button(header,text='Refresh DMD History',command=self.refresh_dmd).pack(side='right',padx=3)
        bar=ttk.Frame(root,padding=(8,0,8,6));bar.grid(row=1,column=0,sticky='ew')
        ttk.Label(bar,text='Filter mask:').pack(side='left')
        self.dmd_filter=tk.StringVar()
        self.dmd_filter.trace_add('write',lambda *_:self.populate_dmd())
        ttk.Entry(bar,textvariable=self.dmd_filter).pack(side='left',fill='x',expand=True,padx=8)
        frame=ttk.Frame(root);frame.grid(row=2,column=0,sticky='nsew',padx=8)
        frame.columnconfigure(0,weight=1);frame.rowconfigure(0,weight=1)
        columns=('utc','mask','source','modified','created','status','load_id')
        self.dmd_tree=ttk.Treeview(frame,columns=columns,show='headings',height=10)
        for key,label,width in zip(columns,('UTC','Mask filename','Source','Modified','Version created','Result','Load ID'),(175,340,65,75,105,150,270)):
            self.dmd_tree.heading(key,text=label)
            self.dmd_tree.column(key,width=width,anchor='w')
        self.dmd_tree.grid(row=0,column=0,sticky='nsew')
        scroll=ttk.Scrollbar(frame,orient='vertical',command=self.dmd_tree.yview)
        scroll.grid(row=0,column=1,sticky='ns');self.dmd_tree.configure(yscrollcommand=scroll.set)
        detail_frame=ttk.Frame(root,padding=8);detail_frame.grid(row=3,column=0,sticky='nsew')
        ttk.Label(detail_frame,text='Selected request and result (read only)').pack(anchor='w')
        self.dmd_detail=tk.Text(detail_frame,height=9,wrap='word',state='disabled')
        self.dmd_detail.pack(fill='both',expand=True)
        self.dmd_tree.bind('<<TreeviewSelect>>',self.show_dmd_detail)
        self.dmd_status=ttk.Label(root,text='',padding=8);self.dmd_status.grid(row=4,column=0,sticky='ew')
        self.dmd_rows=[];self.dmd_shown=[]
        self.refresh_dmd()

    def refresh_dmd(self):
        try:
            self.dmd_rows=self._read_dmd_history(self.dmd_log_path)
        except (OSError,UnicodeError,ValueError) as exc:
            self.dmd_rows=[]
            self.dmd_status.configure(text=f'Unable to read history: {exc}')
        self.populate_dmd()

    def populate_dmd(self):
        self.dmd_tree.delete(*self.dmd_tree.get_children())
        needle=self.dmd_filter.get().casefold()
        self.dmd_shown=[r for r in self.dmd_rows if needle in (r['mask']+' '+r['status']+' '+r['load_id']).casefold()]
        for i,row in enumerate(self.dmd_shown):
            values=(row['utc'],row['mask'],row['source'],str(row['modified']),str(row['created']),row['status'],row['load_id'])
            self.dmd_tree.insert('','end',iid=str(i),values=values)
        if not self.dmd_log_path.is_file():
            message=f'No operations.jsonl at {self.dmd_log_path} — this demo session may use a temporary output directory.'
        else:
            message=f'{len(self.dmd_shown)} / {len(self.dmd_rows)} DMD requests — READ ONLY; controller return is not hardware confirmation.'
        self.dmd_status.configure(text=message)
        self._set_dmd_detail('Select a request to inspect its JSON record.')

    def _set_dmd_detail(self,text):
        self.dmd_detail.configure(state='normal')
        self.dmd_detail.delete('1.0','end')
        self.dmd_detail.insert('1.0',text)
        self.dmd_detail.configure(state='disabled')

    def show_dmd_detail(self,event=None):
        import json
        selected=self.dmd_tree.selection()
        if not selected:return
        row=self.dmd_shown[int(selected[0])]
        self._set_dmd_detail(json.dumps({'request':row['request'],'result':row['result']},indent=2,sort_keys=True))

    def set_enabled(self,run_from_main=False):
        # Prevent the default SAMOSFrame implementation from triggering
        # a recursive global update; this page only displays database data.
        return

    def refresh(self):
        try:
            self.records=load_records(self.filename)
        except Exception as exc:
            self.records=[]
            messagebox.showerror('Database read error',f'{self.filename}\n{exc}\nNo changes were made.')
        self.populate()

    def populate(self):
        self.tree.delete(*self.tree.get_children())
        needle=self.filter_var.get().casefold()
        matches=[r for r in self.records if needle in ' '.join(r).casefold()]
        for row in matches:self.tree.insert('', 'end',values=row)
        self.status.configure(text=f'{len(matches)} / {len(self.records)} records — READ ONLY')

    def export_csv(self):
        dest=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if not dest:return
        if not messagebox.askyesno('Export settings?','The export includes network configuration and saved values. Export to a restricted location?'):return
        with open(dest,'w',newline='',encoding='utf-8') as handle:
            writer=csv.writer(handle);writer.writerow(['parameter','current','changed','previous','status']);writer.writerows(self.records)
