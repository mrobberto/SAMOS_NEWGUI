"""
SAMOS Configuration tk Frame Class
"""
import csv
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import yaml

import tkinter as tk
import ttkbootstrap as ttk
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class ConfigPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMOS Configuration", **kwargs)
        self.logger.info("Setting up config page")

        # Set up directories frame
        frame = ttk.LabelFrame(self.main_frame, text="Files", borderwidth=2)
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        # RC1_FILES_LOGBOOK_V1 — show actual resolved output paths.
        self.files_loc = self.make_db_var(tk.StringVar, "config_files_storage_location", "module")
        self.custom_files_path = self.make_db_var(tk.StringVar, "config_custom_files_location", "")
        self.rc_base_path = tk.StringVar(value='')
        ttk.Label(frame, text="Output base directory:").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        for row, label, value in ((1,"In Module","module"), (2,"Home Directory","home"),
                                  (3,"Working Directory","cwd"),(4,"Custom Location","custom")):
            ttk.Radiobutton(frame, text=label, variable=self.files_loc, value=value,
                            command=self.set_files_base).grid(row=row,column=0,sticky=tk.W)
        ttk.Button(frame, text="Browse Custom…", command=self.rc_browse_custom).grid(
            row=4,column=1,sticky=tk.W,padx=3)
        ttk.Label(frame, text="Resolved base path:").grid(row=5,column=0,sticky=tk.W)
        ttk.Label(frame, textvariable=self.rc_base_path, wraplength=430).grid(
            row=5,column=1,columnspan=2,sticky=tk.W)
        ttk.Label(frame, text="SISI nightly FITS:").grid(row=6,column=0,sticky=tk.W)
        self.rc_sisi_path = tk.StringVar(value='')
        ttk.Label(frame, textvariable=self.rc_sisi_path, wraplength=430).grid(
            row=6,column=1,columnspan=2,sticky=tk.W)
        ttk.Label(frame, text="Reports for this night:").grid(row=7,column=0,sticky=tk.W)
        self.rc_reports_path = tk.StringVar(value='')
        ttk.Label(frame, textvariable=self.rc_reports_path, wraplength=430).grid(
            row=7,column=1,columnspan=2,sticky=tk.W)
        self.nightly_files_dir = self.make_db_var(tk.StringVar, "config_nightly_files_dir", "")
        ttk.Label(frame, text="Configured nightly location:").grid(row=8,column=0,sticky=tk.W)
        ttk.Label(frame, textvariable=self.nightly_files_dir, wraplength=430).grid(
            row=8,column=1,columnspan=2,sticky=tk.W)
        self.science_targets_dir = self.make_db_var(tk.StringVar, "config_science_targets_dir", "")
        ttk.Label(frame, text="Science target input directory:").grid(row=9,column=0,sticky=tk.W)
        ttk.Label(frame, textvariable=self.science_targets_dir, wraplength=430).grid(
            row=9,column=1,sticky=tk.W)
        ttk.Button(frame, text="Browse Inputs…", command=self.set_science_loc).grid(
            row=9,column=2,sticky=tk.W,padx=3)
        self.rc_refresh_paths()

        # Set up servers frame
        frame = ttk.LabelFrame(self.main_frame, text="Servers", borderwidth=2)
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        self.ip_loc = self.make_db_var(tk.StringVar, "config_ip_status", "disconnected")
        b = tk.Radiobutton(frame, text='Connected', variable=self.ip_loc, value='connected')
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text='Disconnected', variable=self.ip_loc, value='disconnected')
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)

        # Hardware Labels
        ttk.Label(frame, text="PCM").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="CCD").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="DMD").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="SOAR Telescope").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="SOAR SAMI").grid(row=5, column=0, sticky=TK_STICKY_ALL)

        # Status Indicator Frame
        self.status_box = tk.Canvas(frame, background="gray", width=50)
        self.status_box.grid(row=1, column=1, rowspan=5, sticky=TK_STICKY_ALL)
        self.status_box.create_oval(10, 10, 40, 40, fill=INDICATOR_LIGHT_PENDING_COLOR, outline=None, tags=["pcm_ind"])
        self.status_box.create_oval(10, 48, 40, 78, fill=INDICATOR_LIGHT_PENDING_COLOR, tags=["ccd_ind"], outline=None)
        self.status_box.create_oval(10, 86, 40, 116, fill=INDICATOR_LIGHT_PENDING_COLOR, tags=["dmd_ind"], outline=None)
        self.status_box.create_oval(10, 124, 40, 154, fill=INDICATOR_LIGHT_PENDING_COLOR, tags=["soar_ind"], outline=None)
        self.status_box.create_oval(10, 162, 40, 192, fill=INDICATOR_LIGHT_PENDING_COLOR, tags=["sami_ind"], outline=None)
        # Register the frame with PAR
        self.PAR.add_status_indicator(self.status_box, self.update_status_box)

        self.IP_PCM = self.make_db_var(tk.StringVar, "config_ip_pcm", "172.16.0.128:1000")
        tk.Entry(frame, width=20, textvariable=self.IP_PCM).grid(row=1, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_CCD = self.make_db_var(tk.StringVar, "config_ip_ccd", "172.16.0.245:80")
        tk.Entry(frame, width=20, textvariable=self.IP_CCD).grid(row=2, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_DMD = self.make_db_var(tk.StringVar, "config_ip_dmd", "172.16.0.141:8888")
        tk.Entry(frame, width=20, textvariable=self.IP_DMD).grid(row=3, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_SOAR = self.make_db_var(tk.StringVar, "config_ip_soar", "139.220.15.2:40050")
        tk.Entry(frame, width=20, textvariable=self.IP_SOAR).grid(row=4, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_SAMI = self.make_db_var(tk.StringVar, "config_ip_sami", "139.229.15:63")
        tk.Entry(frame, width=20, textvariable=self.IP_SAMI).grid(row=5, column=2, columnspan=2, sticky=TK_STICKY_ALL)

        b = ttk.Button(frame, text="Initialize Components", command=self.startup, bootstyle="success")
        b.grid(row=6, column=0, columnspan=2, sticky=TK_STICKY_ALL)

        # Observer Data
        frame = ttk.LabelFrame(self.main_frame, text="Observer Data", borderwidth=2)
        frame.grid(row=0, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)
        # Telescope
        ttk.Label(frame, text="Telescope").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.Telescope = self.make_db_var(tk.StringVar, "POTN_Telescope", "")
        ttk.Entry(frame, width=20, textvariable=self.Telescope).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # Program ID
        ttk.Label(frame, text="Program ID").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.Program_ID = self.make_db_var(tk.StringVar, "POTN_Program", "")
        ttk.Entry(frame, width=20, textvariable=self.Program_ID).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # Proposal Title
        ttk.Label(frame, text="Proposal Title").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.Proposal_Title = self.make_db_var(tk.StringVar, "POTN_Title", "")
        ttk.Entry(frame, width=20, textvariable=self.Proposal_Title).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        # Principal Investigator
        ttk.Label(frame, text="Principal Investigator").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.Principal_Investigator = self.make_db_var(tk.StringVar, "POTN_PI", "")
        ttk.Entry(frame, width=20, textvariable=self.Principal_Investigator).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        # Observer
        ttk.Label(frame, text="Observer").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.Observer = self.make_db_var(tk.StringVar, "POTN_Observer", "")
        ttk.Entry(frame, width=20, textvariable=self.Observer).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        # TO
        ttk.Label(frame, text="Telescope Operator ").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.Telescope_Operator = self.make_db_var(tk.StringVar, "POTN_Telescope_Operator", "")
        ttk.Entry(frame, width=20, textvariable=self.Telescope_Operator).grid(row=5, column=1, sticky=TK_STICKY_ALL)

        # Independent, persistent last-used folders for Resume Existing dialogs.
        # These are GUI navigation hints, not changes to active logbook paths.
        self._log_resume_dirs = {
            kind: self.make_db_var(tk.StringVar, 'log_resume_dir_' + kind, '')
            for kind in ('science', 'engineering')
        }

        # RC1: independent science and engineering logbooks.
        log_frame = ttk.LabelFrame(self.main_frame, text="Logbooks", borderwidth=2)
        log_frame.grid(row=1, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)
        self.science_log_label = tk.StringVar(value=str(self.PAR.logfile_name))
        self.engineering_log_label = tk.StringVar(value=str(getattr(parent, 'engineering_log_path', '')))
        for i, (label, variable, kind) in enumerate((
            ('Science (CSV)', self.science_log_label, 'science'),
            ('Engineering (text)', self.engineering_log_label, 'engineering'))):
            group = ttk.LabelFrame(log_frame, text=label)
            group.grid(row=i, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)
            ttk.Label(group, textvariable=variable, wraplength=380).grid(row=0, column=0, columnspan=3, sticky='w')
            ttk.Button(group, text='Create New', command=lambda k=kind:self.rc_create_log(k)).grid(row=1,column=0)
            ttk.Button(group, text='Resume Existing', command=lambda k=kind:self.rc_resume_log(k)).grid(row=1,column=1)
            ttk.Button(group, text='View / Refresh', command=lambda k=kind:self.rc_view_log(k)).grid(row=1,column=2)
            if kind == 'science':
                ttk.Button(group, text='Edit Comments', command=self.rc_edit_science_comments).grid(row=1,column=3)

        # Settings
        frame = ttk.LabelFrame(self.main_frame, text="Settings", borderwidth=2)
        frame.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL, padx=3, pady=3)

        self.logger.info("Finished setting up config page. Starting initial widget check.")
        self.set_enabled()
        self.logger.info("Finished initial widget check.")


    @check_enabled
    def set_files_base(self):
        'Apply radio selection, with cancel restoring the previous valid base.'
        old = getattr(self, '_rc_previous_base', None)
        if self.files_loc.get() == 'custom':
            if not self.rc_browse_custom():
                if old is not None:
                    self.files_loc.set(old[0])
                    self.custom_files_path.set(old[1])
                self.rc_refresh_paths()
                return
        if self.files_loc.get() != 'custom':
            self.rc_record_base_change(old)

    def rc_browse_custom(self):
        from tkinter import filedialog
        previous_mode = self.files_loc.get()
        previous_custom = self.custom_files_path.get()
        initial = Path(previous_custom).expanduser() if previous_custom else Path.home()
        if not initial.is_dir(): initial = Path.home()
        selection = filedialog.askdirectory(title='Select SAMOS output base directory',
                                            initialdir=str(initial), parent=self)
        if not selection:
            return False
        folder = Path(selection).expanduser().resolve()
        if not folder.is_dir():
            from tkinter import messagebox
            messagebox.showerror('Output directory', 'Selected folder does not exist.', parent=self)
            return False
        # Capture previous state even if the radio has already changed.
        old = getattr(self, '_rc_previous_base', (previous_mode, previous_custom, ''))
        self.custom_files_path.set(str(folder))
        self.files_loc.set('custom')
        self.rc_record_base_change(old)
        return True

    def rc_resolved_base(self):
        # Read-only resolution. Never mkdir while merely displaying a path.
        return Path(self.PAR.output_dir).expanduser().resolve()

    def rc_refresh_paths(self):
        try:
            base = self.rc_resolved_base()
            self.rc_base_path.set(str(base))
            self.rc_sisi_path.set(str(Path(self.PAR.fits_dir).expanduser().resolve()))
            reportdir = getattr(self.PAR, 'reports_dir', None)
            if reportdir is None:
                reportdir = base / 'reports' / f'SAMOS_{self.PAR.today_str}'
            self.rc_reports_path.set(str(Path(reportdir).expanduser().resolve()))
            self._rc_previous_base = (self.files_loc.get(), self.custom_files_path.get(), str(base))
        except (ValueError, OSError) as exc:
            self.rc_base_path.set(f'Invalid output directory: {exc}')

    def rc_log_base_snapshot(self):
        import csv
        from datetime import datetime, timezone
        stamp = datetime.now(timezone.utc).isoformat()
        try:
            base = str(self.rc_resolved_base())
        except (OSError, ValueError) as exc:
            self.logger.warning('Unable to record base directory: %s', exc)
            return
        event = f'BASE_DIRECTORY_SELECTED UTC={stamp} mode={self.files_loc.get()} path={base!r}'
        self.logger.info(event)
        science = Path(self.PAR.logfile_name)
        if science.is_file():
            with science.open('a', newline='', encoding='utf-8') as handle:
                csv.writer(handle).writerow([stamp[:10],stamp[11:19],
                    'CONFIG_EVENT','','','','','','','','',event])

    def rc_record_base_change(self, old):
        import csv
        from datetime import datetime, timezone
        self.rc_refresh_paths()
        new = getattr(self, '_rc_previous_base', None)
        if not old or not new or old == new:
            return
        stamp = datetime.now(timezone.utc).isoformat()
        event = (f'BASE_DIRECTORY_CHANGED UTC={stamp} mode={new[0]} '
                 f'old={old[2]!r} new={new[2]!r}')
        self.logger.info(event)
        # Insert a clearly flagged, 12-column configuration-event record.
        # Existing logbook files remain at their selected paths.
        science = Path(self.PAR.logfile_name)
        if science.is_file():
            with science.open('a', newline='', encoding='utf-8') as handle:
                csv.writer(handle).writerow([stamp[:10], stamp[11:19],
                    'CONFIG_EVENT','','','','','','','','',event])



    @check_enabled
    def set_science_loc(self):
        self.logger.info(f"Setting location to find science files")
        initial_dir = self.science_targets_dir.get()
        if self.science_targets_dir.get() == "":
            initial_dir = Path.cwd()
        initial_dir = Path(initial_dir)
        title = "Select Science Target Directory"
        custom_loc = tk.filedialog.askdirectory(initialdir=initial_dir, title=title)
        if custom_loc != "":
            custom_loc = Path(custom_loc)
            if custom_loc.is_dir():
                self.science_targets_dir.set(custom_loc.as_posix())


    def LogBookStartup(self):
        """Legacy callback: create science log if not initialized."""
        if not self.PAR.logbook_exists:
            self.PAR.new_science_logbook()
        self.science_log_label.set(str(self.PAR.logfile_name))

    def rc_create_log(self, kind):
        # SC3_AUTO_SESSION_RECOVERY_V1: persist selected logs after this UI action.
        self.after_idle(lambda: self.winfo_toplevel().save_observing_session())
        from tkinter import messagebox
        from samos.system.logbook_manager import make_new
        try:
            if kind=='science':
                p=self.PAR.new_science_logbook()
                self.science_log_label.set(str(p))
            else:
                p=make_new(self.PAR.reports_dir,'engineering_logbook','.log')
                self.winfo_toplevel().set_engineering_logbook(p,create=True)
                self.engineering_log_label.set(str(p))
        except Exception as exc:
            messagebox.showerror('Logbook error',str(exc),parent=self)

        self.rc_log_base_snapshot()

    def rc_resume_log(self, kind):
        # SC3_AUTO_SESSION_RECOVERY_V1: persist selected logs after this UI action.
        self.after_idle(lambda: self.winfo_toplevel().save_observing_session())
        """Resume a logbook, opening the last-used valid folder for its type."""
        from tkinter import filedialog, messagebox
        if kind not in ('science', 'engineering'):
            raise ValueError('Unrecognized logbook type')
        active = (self.science_log_label.get() if kind == 'science'
                  else self.engineering_log_label.get())
        remembered = self._log_resume_dirs[kind].get().strip()
        reports_dir = getattr(self.PAR, 'reports_dir', None)
        nightly_dir = Path(self.PAR.output_dir) / 'reports' / f'SAMOS_{self.PAR.today_str}'
        # Prefer previous user choice, then an existing active logbook,
        # then the actual nightly reports directory. Never default to a
        # stale temporary-directory parent or depend on os.getcwd().
        candidates = []
        if remembered:
            candidates.append(Path(remembered).expanduser())
        if active and Path(active).expanduser().is_file():
            candidates.append(Path(active).expanduser().parent)
        if reports_dir is not None:
            candidates.append(Path(reports_dir).expanduser())
        candidates.extend((nightly_dir, Path.home()))
        initial_dir = next((q for q in candidates if q.is_dir()), Path.home())
        active_path = Path(active).expanduser() if active else None
        initial_file = active_path.name if active_path is not None and active_path.is_file() and active_path.parent == initial_dir else None
        opts = dict(initialdir=str(initial_dir), parent=self,
                    title=f'Resume existing {kind} logbook',
                    filetypes=([('Science CSV logbook', '*.csv')]
                               if kind == 'science' else
                               [('Engineering logbook', '*.log *.txt'), ('All files', '*.*')]))
        if initial_file:
            opts['initialfile'] = initial_file
        p = filedialog.askopenfilename(**opts)
        if not p:
            return
        chosen = Path(p).expanduser()
        if not chosen.is_file():
            messagebox.showerror('Logbook error', 'Selected file does not exist.', parent=self)
            return
        try:
            if kind == 'science':
                self.PAR.resume_science_logbook(str(chosen))
                self.science_log_label.set(str(self.PAR.logfile_name))
            else:
                self.winfo_toplevel().set_engineering_logbook(str(chosen))
                self.engineering_log_label.set(str(chosen))
        except Exception as exc:
            messagebox.showerror('Logbook error', str(exc), parent=self)
            return
        # Only remember a folder when successfully resumed.
        self._log_resume_dirs[kind].set(str(chosen.resolve().parent))

    def rc_edit_science_comments(self):
        """Open the installed science logbook comment editor."""
        from tkinter import messagebox
        from samos.ui.science_log_editor import open_science_comment_editor
        path = Path(self.PAR.logfile_name)
        if not path.is_file():
            messagebox.showinfo('Science logbook',
                                'No active science logbook file exists.', parent=self)
            return
        open_science_comment_editor(self, path)

    def rc_view_log(self, kind):
        from tkinter import messagebox
        from pathlib import Path
        p=Path(self.science_log_label.get() if kind=='science' else self.engineering_log_label.get())
        if not p.is_file():
            messagebox.showinfo('Logbook','No logbook file exists at the displayed path.',parent=self)
            return
        window=tk.Toplevel(self)
        window.title(f'{kind.title()} logbook (read only)')
        window.geometry('950x550')
        ttk.Label(window,text=str(p),wraplength=900).pack(fill='x')
        area=tk.Frame(window);area.pack(fill='both',expand=True)
        scroll=tk.Scrollbar(area);scroll.pack(side='right',fill='y')
        viewer=tk.Text(area,wrap='none',yscrollcommand=scroll.set)
        viewer.pack(side='left',fill='both',expand=True)
        scroll.config(command=viewer.yview)
        def refresh():
            try:
                contents=p.read_text(encoding='utf-8',errors='replace')
                viewer.configure(state='normal');viewer.delete('1.0','end')
                viewer.insert('1.0',contents);viewer.configure(state='disabled')
            except OSError as exc:
                messagebox.showerror('Logbook error',str(exc),parent=window)
        ttk.Button(window,text='Refresh',command=refresh).pack()
        refresh()

    @check_enabled
    def startup(self):
        self.logger.info("CONFIG_GUI: entering startup.")
        if self.ip_loc.get() == "connected":
            self.PCM.initialize_motors()
            self.PCM.power_on()
            self.CCD.initialize_ccd()
            self.DMD.initialize()
            self.DMD._open()
            self.SOAR.echo_client()
        else:
            self.logger.info("Disconnected. Doing nothing.")
        self.update_status_box()
        self.logger.info("CONFIG_GUI: startup complete.")


    def update_status_box(self):
        if self.PCM.is_on:
            self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_ON_COLOR)
            if self.PCM.filter_moving or self.PCM.grism_moving:
                self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_PENDING_COLOR)
        else:
            self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        if self.CCD.ccd_on:
            self.status_box.itemconfig("ccd_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("ccd_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        if self.DMD.is_on:
            self.status_box.itemconfig("dmd_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("dmd_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        if self.SOAR.is_on:
            self.status_box.itemconfig("soar_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("soar_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        sami_status = False
        if sami_status:
            self.status_box.itemconfig("sami_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("sami_ind", fill=INDICATOR_LIGHT_OFF_COLOR)


    def set_enabled(self, run_from_main=False):
        super().set_enabled(run_from_main=run_from_main)
        # Logbook controls remain available regardless of the active file.
        # The file paths are maintained by rc_create_log and rc_resume_log.
