import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import sys
from PIL import Image, ImageTk
import solver
import pickle

# --- PALETTE VORTEX UI (Dark Mode) ---
COLOR_BG_MAIN = "#1e1e1e"       # Sfondo finestra
COLOR_BG_CARD = "#252526"       # Sfondo schede
COLOR_ACCENT = "#007acc"        # Blu Elettrico
COLOR_ACCENT_HOVER = "#0098ff"  # Blu più chiaro per hover
COLOR_TEXT = "#e1e1e1"          # Bianco sporco
COLOR_TEXT_DIM = "#a0a0a0"      # Testo secondario
COLOR_INPUT_BG = "#3c3c3c"      # Sfondo caselle input
COLOR_BORDER = "#3e3e42"        # Bordi
COLOR_SUCCESS = "#4ec9b0"       # Verde acqua

# FONT DIMENSIONI
FONT_SIZE_BASE = 11
FONT_SIZE_TITLE = 21
FONT_SIZE_BTN = 12

FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Roboto"

def get_base_path():
    if getattr(sys, 'frozen', False): return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_image_path(image_name):
    base_path = get_base_path()
    paths = [os.path.join(base_path, p, image_name) for p in ["", "assets", "images"]]
    for path in paths:
        if os.path.exists(path): return path
    return None

def get_main_script_path():
    base_path = get_base_path()
    paths = [os.path.join(base_path, "main.py"), "main.py"]
    for path in paths:
        if os.path.exists(path): return path
    return "main.py"

def get_input_file_smart(nome_file):
    cwd = os.getcwd()
    current_dir_name = os.path.basename(cwd)
    paths_to_check = [
        os.path.join(cwd, nome_file),
        os.path.join(cwd, "Dati_input", nome_file)
    ]
    if current_dir_name == "PS-VRP":
        paths_to_check.insert(0, os.path.join(cwd, "Dati_input", nome_file))
    elif current_dir_name == "progettoIS":
        paths_to_check.insert(0, os.path.join(cwd, "PS-VRP", "Dati_input", nome_file))

    for path in paths_to_check:
        if os.path.exists(path): return path
    return ""

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Schedulatore del Taglio")
        self.root.geometry("1000x850") 
        self.root.configure(bg=COLOR_BG_MAIN)

        try:
            icon = get_image_path("istituto_stampa_s_r_l__logo.png")
            if icon: self.root.iconphoto(True, tk.PhotoImage(file=icon))
        except: pass

        # File Inputs
        self.file_commesse = tk.StringVar(value=get_input_file_smart("Commesse_da_tagliare.xlsx"))
        self.file_macchine = tk.StringVar(value=get_input_file_smart("Scheda_Macchine_Taglio.xlsx"))
        self.file_veicoli = tk.StringVar(value=get_input_file_smart("vettori.xlsx"))
        
        # Parametri
        self.alfa_val = tk.DoubleVar(value=0.7)
        self.alfa_str = tk.StringVar(value="0.7")
        self.beta_val = tk.StringVar(value="0.1") 
        self.iter_val = tk.StringVar(value="10")

        self.setup_styles()
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        try: style.theme_use('clam')
        except: pass 
        
        style.configure(".", background=COLOR_BG_MAIN, foreground=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_BASE))
        style.configure("Card.TFrame", background=COLOR_BG_CARD, relief="flat")
        style.configure("Card.TLabelframe", background=COLOR_BG_CARD, relief="solid", borderwidth=1, bordercolor=COLOR_BORDER)
        style.configure("Card.TLabelframe.Label", background=COLOR_BG_CARD, foreground=COLOR_ACCENT, font=(FONT_FAMILY, FONT_SIZE_BASE + 1, "bold"))
        style.configure("Card.TLabel", background=COLOR_BG_CARD, foreground=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_BASE))
        style.configure("Title.TLabel", background=COLOR_BG_MAIN, foreground=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_TITLE, "bold"))
        
        style.configure("Primary.TButton", font=(FONT_FAMILY, FONT_SIZE_BTN, "bold"), background=COLOR_ACCENT, foreground="white", borderwidth=0, focusthickness=0, padding=10)
        style.map("Primary.TButton", background=[('active', COLOR_ACCENT_HOVER), ('disabled', '#444444')])
        
        style.configure("Secondary.TButton", font=(FONT_FAMILY, FONT_SIZE_BASE), background="#3e3e42", foreground=COLOR_TEXT, borderwidth=0, focusthickness=0)
        style.map("Secondary.TButton", background=[('active', "#505050")])
        
        style.configure("TEntry", fieldbackground=COLOR_INPUT_BG, foreground="white", insertcolor="white", borderwidth=0, font=(FONT_FAMILY, FONT_SIZE_BASE))
        style.configure("Horizontal.TScale", background=COLOR_BG_CARD, troughcolor=COLOR_INPUT_BG, sliderthickness=15)

    def create_card(self, parent, title=None):
        if title: 
            f = ttk.LabelFrame(parent, text=f" {title} ", style="Card.TLabelframe", padding=15)
        else:
            f = ttk.Frame(parent, style="Card.TFrame", padding=15)
        return f

    def setup_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=25, pady=25)

        # --- HEADER ---
        head = ttk.Frame(main)
        head.pack(fill="x", pady=(0, 25))
        
        logo_path = get_image_path("istituto_stampa_s_r_l__logo-removebg-preview.png")
        if logo_path:
            try:
                img = Image.open(logo_path)
                img.thumbnail((220, 90), Image.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
                lbl = ttk.Label(head, image=self.logo_image, background="#e0e0e0") 
                lbl.pack(side="left", padx=(0, 20))
            except: pass
        
        titles = ttk.Frame(head)
        titles.pack(side="left", fill="both")
        ttk.Label(titles, text="Schedulatore del Taglio", style="Title.TLabel").pack(anchor="w", pady=(10,0))

        # --- PARAMETRI ---
        p_card = self.create_card(main, "Parametri Algoritmo")
        p_card.pack(fill="x", pady=(0, 15))
        
        def on_slider_move(val):
            rounded_val = round(float(val), 1)
            self.alfa_val.set(rounded_val)
            self.alfa_str.set(f"{rounded_val:.1f}")

        def on_text_change(*args):
            try:
                val = float(self.alfa_str.get())
                if 0.0 <= val <= 1.0: self.alfa_val.set(val) 
            except ValueError: pass

        self.alfa_str.trace_add("write", on_text_change)

        # Riga 1
        row1 = ttk.Frame(p_card, style="Card.TFrame")
        row1.pack(fill="x", pady=5)
        
        ttk.Label(row1, text="α (LS):", style="Card.TLabel", width=12).pack(side="left")
        scale = ttk.Scale(row1, from_=0.0, to=1.0, variable=self.alfa_val, orient="horizontal", style="Horizontal.TScale", length=250, command=on_slider_move)
        scale.pack(side="left", padx=10, pady = 6)
        entry_alfa = ttk.Entry(row1, textvariable=self.alfa_str, width=6, justify="center", font=(FONT_FAMILY, FONT_SIZE_BASE + 1))
        entry_alfa.pack(side="left")
        
        # Riga 2
        row2 = ttk.Frame(p_card, style="Card.TFrame")
        row2.pack(fill="x", pady=(10, 5))

        ttk.Label(row2, text="β (GRASP):", style="Card.TLabel", width=12).pack(side="left")
        ttk.Entry(row2, textvariable=self.beta_val, width=12, justify="center", font=(FONT_FAMILY, FONT_SIZE_BASE)).pack(side="left", padx=(10, 30))
        
        ttk.Label(row2, text="Iterazioni:", style="Card.TLabel").pack(side="left")
        ttk.Entry(row2, textvariable=self.iter_val, width=12, justify="center", font=(FONT_FAMILY, FONT_SIZE_BASE) ).pack(side="left", padx=10)

        # --- FILE INPUTS ---
        f_card = self.create_card(main, "Input Dati")
        f_card.pack(fill="x", pady=(0, 15))
        f_card.columnconfigure(1, weight=1)
        
        files = [
            ("📁 Commesse", self.file_commesse, "Commesse"), 
            ("⚙️ Macchine", self.file_macchine, "Macchine"), 
            ("🚚 Veicoli", self.file_veicoli, "Veicoli")
        ]
        
        for i, (lbl, var, t) in enumerate(files):
            ttk.Label(f_card, text=lbl, style="Card.TLabel").grid(row=i, column=0, sticky="w", pady=10)
            entry = ttk.Entry(f_card, textvariable=var, font=(FONT_FAMILY, FONT_SIZE_BASE + 1))
            entry.grid(row=i, column=1, sticky="ew", padx=15, pady=10)
            ttk.Button(f_card, text="Sfoglia", style="Secondary.TButton", command=lambda x=var, y=t: self.select_file(x, y)).grid(row=i, column=2, pady=10)

        # --- AZIONI ---
        act = ttk.Frame(main)
        act.pack(fill="x", pady=(0, 15))
        
        self.start_btn = ttk.Button(act, text="AVVIA SCHEDULAZIONE", style="Primary.TButton", command=self.start_main_script)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # RIAPRI GRAFICO
        ttk.Button(act, text="APRI GRAFICO", style="Primary.TButton", command=self.reload_graph).pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ttk.Button(act, text="APRI OUTPUT", style="Primary.TButton", command=self.open_output_folder).pack(side="left", fill="x", expand=True)

        # --- CONSOLE ---
        out_card = self.create_card(main)
        out_card.pack(fill="both", expand=True)
        
        self.p_bar = ttk.Progressbar(out_card, mode="indeterminate", style="Horizontal.TProgressbar")
        self.status = ttk.Label(out_card, text="Sistema pronto.", style="Card.TLabel", font=(FONT_FAMILY, 9, "italic"))
        self.status.pack(anchor="w", pady=(0,5))
        
        t_frame = ttk.Frame(out_card)
        t_frame.pack(fill="both", expand=True)
        
        self.out_txt = tk.Text(t_frame, height=10, 
                               font=("Consolas", FONT_SIZE_BASE), 
                               bg="#101010", fg="#cccccc",
                               insertbackground="white", relief="flat",
                               padx=10, pady=10)
        
        sb = ttk.Scrollbar(t_frame, command=self.out_txt.yview)
        self.out_txt.configure(yscrollcommand=sb.set)
        
        self.out_txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def select_file(self, var, tipo):
        f = filedialog.askopenfilename(title=f"Seleziona {tipo}", filetypes=[("Excel", "*.xlsx *.xls")])
        if f: var.set(f)

    def start_main_script(self):
        self.start_btn.config(state="disabled")
        self.p_bar.pack(fill="x", pady=(0, 10), before=self.status)
        self.p_bar.start(10)
        self.status.config(text="Esecuzione algoritmo in corso...", foreground=COLOR_ACCENT)
        self.out_txt.delete(1.0, tk.END)
        self.out_txt.insert(tk.END, "> Avvio processo...\n")
        threading.Thread(target=self._run_thread, daemon=True).start()

    def _run_thread(self):
        try:
            env = os.environ.copy()
            env.update({
                'FILE_COMMESSE': self.file_commesse.get(),
                'FILE_MACCHINE': self.file_macchine.get(),
                'FILE_VEICOLI': self.file_veicoli.get(),
                'PARAM_ALFA': str(self.alfa_val.get()),
                'PARAM_BETA': self.beta_val.get(),
                'PARAM_ITER': self.iter_val.get()
            })
            
            p = subprocess.Popen([sys.executable, get_main_script_path()], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                 text=True, bufsize=1, universal_newlines=True, 
                                 env=env)
            
            for line in p.stdout:
                self.root.after(0, lambda l=line: self.out_txt.insert(tk.END, l) or self.out_txt.see(tk.END))
            
            # Quando il processo finisce (dopo aver chiuso il grafico), chiamiamo _reset_ui
            stderr_out = p.stderr.read()
            self.root.after(0, lambda: self._reset_ui(p.poll(), stderr_out))
            
        except Exception as e:
            self.root.after(0, lambda: self._reset_ui(1, str(e)))

    def _reset_ui(self, code, err):
        """Ripristina l'UI dopo che il Main (e il Grafico) sono stati chiusi"""
        self.p_bar.stop()
        self.p_bar.pack_forget()
        self.start_btn.config(state="normal")
        
        if code == 0:
            self.status.config(text="Completato con successo.", foreground=COLOR_SUCCESS)
            self.out_txt.insert(tk.END, "\n=== PROCESSO TERMINATO ===\n")
            messagebox.showinfo("Fatto", "Schedulazione completata!")
        else:
            self.status.config(text="Processo terminato (Verificare output).", foreground="#e67e22")
            if err:
                self.out_txt.insert(tk.END, f"\n[NOTE/ERRORI]:\n{err}")
            messagebox.showinfo("Info", "Il processo è terminato.")

    def open_output_folder(self):
        paths = [os.path.join(os.getcwd(), "Dati_output"), os.path.join(os.getcwd(), "PS-VRP", "Dati_output")]
        path_to_open = paths[0]
        for p in paths:
            if os.path.exists(p):
                path_to_open = p
                break
        if not os.path.exists(path_to_open):
            try: os.makedirs(path_to_open)
            except: pass
        try:
            if sys.platform == "win32": os.startfile(path_to_open)
            else: subprocess.run(["xdg-open", path_to_open])
        except Exception as e:
            messagebox.showerror("Errore", str(e))

        
    # --- NUOVA FUNZIONE PER RIAPRIRE IL GRAFICO ---
    def reload_graph(self):
        """Legge il file pickle e riapre il grafico Matplotlib interattivo"""
        
        # Cerca il file .pkl nei percorsi standard
        path_1 = os.path.join(os.getcwd(), "Dati_output", "grafico_schedulazione.pkl")
        path_2 = os.path.join(os.getcwd(), "PS-VRP", "Dati_output", "grafico_schedulazione.pkl")
        
        target_path = None
        if os.path.exists(path_1): target_path = path_1
        elif os.path.exists(path_2): target_path = path_2
        
        if not target_path:
            messagebox.showwarning("File non trovato", "Nessun dato di grafico salvato trovato.\nEsegui prima una schedulazione.")
            return

        try:
            if solver:
                # Carica i dati grezzi
                with open(target_path, "rb") as f:
                    data = pickle.load(f)
                
                print("Riapertura grafico da file salvato...")
                # Lancia il grafico (bloccherà la GUI finché aperto, ma è immediato)
                solver.grafico_schedulazione(data)
            else:
                messagebox.showerror("Errore", "Modulo 'solver' non importato correttamente.")
                
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aprire il grafico:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    app = App(root)
    root.mainloop()