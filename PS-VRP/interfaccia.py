import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import sys
from PIL import Image, ImageTk # Importa Pillow per gestire le immagini (se non l'hai, installalo con pip install Pillow)

def get_base_path():
    """Ottiene il percorso base corretto per PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Siamo in un bundle PyInstaller
        return sys._MEIPASS
    else:
        # Esecuzione normale Python
        return os.path.dirname(os.path.abspath(__file__))

# Funzione per ottenere il percorso dell'immagine
def get_image_path(image_name):
    base_path = get_base_path()
    # Controlla prima nella root, poi in una sottocartella 'assets' o 'images'
    possible_paths = [
        os.path.join(base_path, image_name),
        os.path.join(base_path, "assets", image_name),
        os.path.join(base_path, "images", image_name)
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None # Ritorna None se l'immagine non viene trovata

def get_main_script_path():
    """Trova il percorso corretto di main.py"""
    base_path = get_base_path()
    
    # Prova diversi percorsi possibili
    possible_paths = [
        os.path.join(base_path, "main.py"),
        os.path.join(os.path.dirname(base_path), "main.py"),
        "main.py"  # Se è nel PATH o nella directory corrente
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Se non troviamo main.py, proviamo a eseguirlo direttamente
    # (utile se è stato incluso nel bundle o è nel PATH)
    return "main.py"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Schedulatore del taglio")
        self.root.geometry("800x750") # Aumenta larghezza per il layout affiancato
        self.root.resizable(True, True)

        # --- IMPOSTA L'ICONA DELLA FINESTRA E DELLA BARRA DELLE APPLICAZIONI ---
        icon_path_ico = get_image_path("istituto_stampa_s_r_l__logo.ico") # Preferito per Windows
        icon_path_png = get_image_path("istituto_stampa_s_r_l__logo.png") # Alternativa per PNG/GIF

        if icon_path_ico:
            try:
                self.root.iconbitmap(icon_path_ico)
            except tk.TclError:
                print(f"Attenzione: Impossibile caricare l'icona ICO da {icon_path_ico}. Proverò con PNG.")
                if icon_path_png:
                    try:
                        photo = tk.PhotoImage(file=icon_path_png)
                        self.root.iconphoto(True, photo)
                    except tk.TclError:
                        print(f"Attenzione: Impossibile caricare l'icona PNG da {icon_path_png}.")
                else:
                    print("Nessun file icona ICO o PNG trovato per la finestra.")
        elif icon_path_png:
            try:
                photo = tk.PhotoImage(file=icon_path_png)
                self.root.iconphoto(True, photo)
            except tk.TclError:
                print(f"Attenzione: Impossibile caricare l'icona PNG da {icon_path_png}.")
        else:
            print("Nessun file icona (ICO o PNG) trovato per la finestra.")

        # Variabili per i file
        self.file_commesse = tk.StringVar()
        self.file_veicoli = tk.StringVar()
        self.file_macchine = tk.StringVar()
        
        # Parametri solver
        self.alfa_val = tk.DoubleVar(value=0.7)
        self.beta_val = tk.StringVar(value="0.2")
        self.iter_val = tk.StringVar(value="10")

        self.setup_ui()

    def setup_ui(self):
        # Frame principale con scrollbar se necessario
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- HEADER CON LOGO E PARAMETRI AFFIANCATI ---
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 15))

        # Frame sinistro per il logo
        logo_frame = ttk.Frame(header_frame)
        logo_frame.pack(side="left", anchor="nw")

        # Carica e mostra il logo
        logo_path = get_image_path("istituto_stampa_s_r_l__logo-removebg-preview.png")
        self.logo_image = None
        self.logo_label = None

        if logo_path:
            try:
                img = Image.open(logo_path)
                # Ridimensiona il logo mantenendo le proporzioni originali
                # Impostiamo un'altezza massima di 120px e calcoliamo la larghezza proporzionale
                original_width, original_height = img.size
                max_height = 120
                aspect_ratio = original_width / original_height
                new_height = min(max_height, original_height)
                new_width = int(new_height * aspect_ratio)
                
                img = img.resize((new_width, new_height), Image.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
                self.logo_label = ttk.Label(logo_frame, image=self.logo_image)
                self.logo_label.pack()
            except FileNotFoundError:
                messagebox.showerror("Errore Logo", f"Immagine del logo non trovata: {logo_path}")
            except Exception as e:
                messagebox.showerror("Errore Logo", f"Impossibile caricare l'immagine del logo: {e}")
        else:
            print("Nessun file logo interno ('logo_grande.png') trovato.")

        # Frame destro per i parametri di configurazione
        params_frame = ttk.LabelFrame(header_frame, text="Parametri di Configurazione", padding=15)
        params_frame.pack(side="right", fill="both", expand=True, padx=(20, 0))

        # Parametro Alfa con slider
        alfa_frame = ttk.Frame(params_frame)
        alfa_frame.pack(fill="x", pady=(0,8))
        
        ttk.Label(alfa_frame, text="Parametro Alfa:").pack(side="left")
        self.alfa_slider = ttk.Scale(alfa_frame, from_=0.0, to=1.0, orient="horizontal", 
                                   variable=self.alfa_val, length=180)
        self.alfa_slider.pack(side="left", padx=8)
        self.alfa_label = ttk.Label(alfa_frame, text=f"{self.alfa_val.get():.2f}")
        self.alfa_label.pack(side="left", padx=(8,0))
        
        # Aggiorna label quando slider cambia
        self.alfa_val.trace_add("write", self.update_alfa_label)

        # Parametro Beta
        beta_frame = ttk.Frame(params_frame)
        beta_frame.pack(fill="x", pady=(0,8))
        
        ttk.Label(beta_frame, text="Parametro Beta:").pack(side="left")
        beta_entry = ttk.Entry(beta_frame, textvariable=self.beta_val, width=12)
        beta_entry.pack(side="left", padx=(8,0))
        ttk.Label(beta_frame, text="(numero)").pack(side="left", padx=(5,0))

        # Parametro Iter
        iter_frame = ttk.Frame(params_frame)
        iter_frame.pack(fill="x")

        ttk.Label(iter_frame, text="Parametro Iter:").pack(side="left")
        iter_entry = ttk.Entry(iter_frame, textvariable=self.iter_val, width=12)
        iter_entry.pack(side="left", padx=(8,0))
        ttk.Label(iter_frame, text="(numero di iterazioni)").pack(side="left", padx=(5,0))

        # --- FRAME PER LA SELEZIONE DEI FILE ---
        file_frame = ttk.LabelFrame(main_frame, text="Selezionare i file di Input (formato .xlsx)", padding=10)
        file_frame.pack(pady=(0,10), fill="x")

        # Configurazione grid per ridimensionamento
        file_frame.columnconfigure(1, weight=1)

        # File Commesse
        ttk.Label(file_frame, text="Estrazione Commesse:").grid(row=0, column=0, sticky="w", padx=(0,5), pady=3)
        entry_commesse = ttk.Entry(file_frame, textvariable=self.file_commesse)
        entry_commesse.grid(row=0, column=1, sticky="ew", padx=5, pady=3)
        ttk.Button(file_frame, text="Sfoglia", 
                  command=lambda: self.select_file(self.file_commesse, "Commesse")).grid(row=0, column=2, padx=(5,0), pady=3)

        # File Veicoli
        ttk.Label(file_frame, text="Estrazione Veicoli:").grid(row=1, column=0, sticky="w", padx=(0,5), pady=3)
        entry_veicoli = ttk.Entry(file_frame, textvariable=self.file_veicoli)
        entry_veicoli.grid(row=1, column=1, sticky="ew", padx=5, pady=3)
        ttk.Button(file_frame, text="Sfoglia", 
                  command=lambda: self.select_file(self.file_veicoli, "Veicoli")).grid(row=1, column=2, padx=(5,0), pady=3)

        # File Macchine
        ttk.Label(file_frame, text="Estrazione Macchine:").grid(row=2, column=0, sticky="w", padx=(0,5), pady=3)
        entry_macchine = ttk.Entry(file_frame, textvariable=self.file_macchine)
        entry_macchine.grid(row=2, column=1, sticky="ew", padx=5, pady=3)
        ttk.Button(file_frame, text="Sfoglia", 
                  command=lambda: self.select_file(self.file_macchine, "Macchine")).grid(row=2, column=2, padx=(5,0), pady=3)

        # --- FRAME PER I CONTROLLI ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=(0,10), fill="x")

        # Pulsanti
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()

        self.start_button = ttk.Button(button_frame, text="🚀 Avvia schedulazione", 
                                     command=self.start_main_script)
        self.start_button.pack(side="left", padx=(0,10))

        ttk.Button(button_frame, text="📁 Apri cartella Output", 
                  command=self.open_output_folder).pack(side="left")

        # --- PROGRESS FRAME (inizialmente nascosto) ---
        self.progress_frame = ttk.LabelFrame(main_frame, text="Stato schedulazione", padding=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", 
                                          mode="indeterminate", length=400)
        self.progress_bar.pack(pady=(0,5))
        
        self.progress_label = ttk.Label(self.progress_frame, text="In attesa...")
        self.progress_label.pack()

        # --- TEXT WIDGET PER L'OUTPUT CON PIÙ SPAZIO ---
        self.output_frame = ttk.LabelFrame(main_frame, text="Output Elaborazione", padding=5)
        
        # Text widget con scrollbar - altezza aumentata
        text_frame = ttk.Frame(self.output_frame)
        text_frame.pack(fill="both", expand=True)
        
        self.output_text = tk.Text(text_frame, height=15, wrap="word", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        
        self.output_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def update_alfa_label(self, *args):
        """Aggiorna la label del parametro alfa"""
        self.alfa_label.config(text=f"{self.alfa_val.get():.2f}")

    def select_file(self, var, tipo_file):
        """Apre dialog per selezione file Excel"""
        file_path = filedialog.askopenfilename(
            title=f"Seleziona file Excel - {tipo_file}",
            filetypes=[("File Excel", "*.xlsx *.xls"), ("Tutti i file", "*.*")]
        )
        if file_path:
            var.set(file_path)

    def open_output_folder(self):
        """Apre la cartella di output con gestione più flessibile"""
        # Prova diversi percorsi possibili per la cartella di output
        possible_dirs = [
            os.path.join(os.getcwd(), "Dati_output"),
            os.path.join(os.getcwd(), "output"),
            os.path.join(os.getcwd(), "Output"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "Dati_output"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        ]
        
        output_dir = None
        for directory in possible_dirs:
            if os.path.exists(directory):
                output_dir = directory
                break
        
        if output_dir:
            try:
                if sys.platform == "win32":
                    os.startfile(output_dir)
                elif sys.platform == "darwin":
                    subprocess.run(["open", output_dir])
                else:
                    subprocess.run(["xdg-open", output_dir])
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile aprire la cartella: {e}")
        else:
            # Se non trova nessuna cartella esistente, crea "Dati_output"
            default_output = os.path.join(os.getcwd(), "Dati_output")
            try:
                os.makedirs(default_output, exist_ok=True)
                messagebox.showinfo("Info", f"Creata cartella di output:\n{default_output}")
                if sys.platform == "win32":
                    os.startfile(default_output)
                elif sys.platform == "darwin":
                    subprocess.run(["open", default_output])
                else:
                    subprocess.run(["xdg-open", default_output])
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile creare/aprire la cartella di output: {e}")

    def validate_inputs(self):
        """Valida tutti gli input prima dell'elaborazione"""
        errors = []

        # Controlla i file
        files = {
            "Commesse": self.file_commesse.get(),
            "Veicoli": self.file_veicoli.get(),
            "Macchine": self.file_macchine.get()
        }

        for nome, path in files.items():
            if not path:
                errors.append(f"File {nome} non selezionato")
            elif not os.path.exists(path):
                errors.append(f"File {nome} non trovato: {path}")
            elif not path.lower().endswith(('.xlsx', '.xls')):
                errors.append(f"File {nome} deve essere un file Excel (.xlsx o .xls)")

        # Controlla beta
        try:
            beta_val = float(self.beta_val.get())
            if beta_val < 0:
                errors.append("Il parametro Beta deve essere un numero positivo o zero")
        except ValueError:
            errors.append("Il parametro Beta deve essere un numero valido")

        return errors

    def start_main_script(self):
        """Avvia l'elaborazione principale"""
        # Valida gli input
        errors = self.validate_inputs()
        if errors:
            messagebox.showerror("Errori di Input", "\n".join(errors))
            return

        # Prepara l'interfaccia per l'elaborazione
        self.start_button.config(state=tk.DISABLED)
        self.progress_frame.pack(pady=(0,10), fill="x")
        self.progress_bar.start()
        self.progress_label.config(text="Avvio elaborazione...")
        
        # Mostra il frame di output
        self.output_frame.pack(pady=(0,10), fill="both", expand=True)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, "=== Avvio Elaborazione ===\n")

        # Avvia in thread separato
        threading.Thread(target=self._run_main_script_thread, daemon=True).start()

    def _run_main_script_thread(self):
        """Esegue lo script principale in thread separato"""
        try:
            # Prepara i parametri
            commesse_path = self.file_commesse.get()
            veicoli_path = self.file_veicoli.get()
            macchine_path = self.file_macchine.get()
            alfa = self.alfa_val.get()
            beta = float(self.beta_val.get())
            iter = int(self.iter_val.get())

            # Aggiorna il progress
            self.root.after(0, lambda: self.progress_label.config(text="Configurazione parametri..."))
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"File Commesse: {os.path.basename(commesse_path)}\n"))
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"File Veicoli: {os.path.basename(veicoli_path)}\n"))
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"File Macchine: {os.path.basename(macchine_path)}\n"))
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"Alfa: {alfa:.2f}, Beta: {beta}, Iter: {iter}\n\n"))

            # Prepara l'ambiente
            env_vars = os.environ.copy()
            env_vars.update({
                'FILE_COMMESSE': commesse_path,
                'FILE_VEICOLI': veicoli_path,
                'FILE_MACCHINE': macchine_path,
                'PARAM_ALFA': str(alfa),
                'PARAM_BETA': str(beta),
                'PARAM_ITER': str(iter)
            })

            # Trova il percorso di main.py
            main_script_path = get_main_script_path()
            
            self.root.after(0, lambda: self.progress_label.config(text="Esecuzione script principale..."))
            self.root.after(0, lambda: self.output_text.insert(tk.END, f"Esecuzione: {main_script_path}\n\n"))

            # Costruisci il comando
            cmd = [sys.executable, main_script_path]
            
            # Esegui il processo
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env_vars,
                bufsize=1,
                universal_newlines=True
            )

            # Leggi l'output in tempo reale
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.root.after(0, lambda line=output: self.output_text.insert(tk.END, line))
                    self.root.after(0, lambda: self.output_text.see(tk.END))

            # Ottieni il risultato finale
            stderr_output = process.stderr.read()
            return_code = process.poll()

            if return_code == 0:
                self.root.after(0, lambda: self._show_success(stderr_output))
            else:
                self.root.after(0, lambda: self._show_error(return_code, stderr_output))

        except Exception as e:
            self.root.after(0, lambda: self._show_exception(e))

    def _show_success(self, stderr_output):
        """Mostra il risultato di successo"""
        self.progress_label.config(text="✅ Elaborazione completata con successo!")
        self.output_text.insert(tk.END, "\n=== ELABORAZIONE COMPLETATA ===\n")
        
        if stderr_output:
            self.output_text.insert(tk.END, f"Note/Avvisi:\n{stderr_output}\n")
        
        messagebox.showinfo("Completato", "L'elaborazione è stata completata con successo!")
        self._reset_ui()

    def _show_error(self, return_code, stderr_output):
        """Mostra errori di elaborazione"""
        self.progress_label.config(text="❌ Errore durante l'elaborazione")
        self.output_text.insert(tk.END, f"\n=== ERRORE (codice {return_code}) ===\n")
        self.output_text.insert(tk.END, stderr_output)
        
        messagebox.showerror(
            "Errore", 
            f"L'elaborazione è terminata con errore (codice {return_code}).\n\n"
            "Controlla l'output per i dettagli."
        )
        self._reset_ui()

    def _show_exception(self, exception):
        """Mostra eccezioni inaspettate"""
        self.progress_label.config(text="❌ Errore inaspettato")
        self.output_text.insert(tk.END, f"\n=== ERRORE INASPETTATO ===\n{str(exception)}\n")
        
        messagebox.showerror("Errore Inaspettato", f"Si è verificato un errore: {exception}")
        self._reset_ui()

    def _reset_ui(self):
        """Ripristina l'interfaccia utente"""
        self.progress_bar.stop()
        self.start_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()