import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import sys

def get_base_path():
    """Ottiene il percorso base corretto per PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Siamo in un bundle PyInstaller
        return sys._MEIPASS
    else:
        # Esecuzione normale Python
        return os.path.dirname(os.path.abspath(__file__))

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
        self.root.geometry("650x550")
        self.root.resizable(True, True)

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

        # Frame per la selezione dei file
        file_frame = ttk.LabelFrame(main_frame, text="Seleziona File Excel di Input", padding=10)
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

        # Frame per i parametri
        params_frame = ttk.LabelFrame(main_frame, text="Parametri di Configurazione", padding=10)
        params_frame.pack(pady=(0,10), fill="x")

        # Parametro Alfa con slider
        alfa_frame = ttk.Frame(params_frame)
        alfa_frame.pack(fill="x", pady=(0,10))
        
        ttk.Label(alfa_frame, text="Parametro Alfa:").pack(side="left")
        self.alfa_slider = ttk.Scale(alfa_frame, from_=0.0, to=1.0, orient="horizontal", 
                                   variable=self.alfa_val, length=200)
        self.alfa_slider.pack(side="left", padx=10)
        self.alfa_label = ttk.Label(alfa_frame, text=f"{self.alfa_val.get():.2f}")
        self.alfa_label.pack(side="left", padx=(10,0))
        
        # Aggiorna label quando slider cambia
        self.alfa_val.trace_add("write", self.update_alfa_label)

        # Parametro Beta con entry
        beta_frame = ttk.Frame(params_frame)
        beta_frame.pack(fill="x")
        
        ttk.Label(beta_frame, text="Parametro Beta:").pack(side="left")
        beta_entry = ttk.Entry(beta_frame, textvariable=self.beta_val, width=15)
        beta_entry.pack(side="left", padx=(10,0))
        ttk.Label(beta_frame, text="(numero)").pack(side="left", padx=(5,0))

        # Parametro Iter con entry
        iter_frame = ttk.Frame(params_frame)
        iter_frame.pack(fill="x", pady=(10,0))

        ttk.Label(iter_frame, text="Parametro Iter:").pack(side="left")
        iter_entry = ttk.Entry(iter_frame, textvariable=self.iter_val, width=15)
        iter_entry.pack(side="left", padx=(10,0))
        ttk.Label(iter_frame, text="(numero di iterazioni)").pack(side="left", padx=(5,0))

        # Frame per i controlli
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=(0,10), fill="x")

        # Pulsanti
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()

        self.start_button = ttk.Button(button_frame, text="🚀 Avvia Elaborazione", 
                                     command=self.start_main_script)
        self.start_button.pack(side="left", padx=(0,10))

        ttk.Button(button_frame, text="📁 Apri Cartella Output", 
                  command=self.open_output_folder).pack(side="left")

        # Progress frame (inizialmente nascosto)
        self.progress_frame = ttk.LabelFrame(main_frame, text="Stato Elaborazione", padding=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", 
                                          mode="indeterminate", length=400)
        self.progress_bar.pack(pady=(0,5))
        
        self.progress_label = ttk.Label(self.progress_frame, text="In attesa...")
        self.progress_label.pack()

        # Text widget per l'output (inizialmente nascosto)
        self.output_frame = ttk.LabelFrame(main_frame, text="Output Elaborazione", padding=5)
        
        # Text widget con scrollbar
        text_frame = ttk.Frame(self.output_frame)
        text_frame.pack(fill="both", expand=True)
        
        self.output_text = tk.Text(text_frame, height=8, wrap="word")
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
        """Apre la cartella di output"""
        output_dir = os.path.join(os.getcwd(), "Dati_output")
        if os.path.exists(output_dir):
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", output_dir])
            else:
                subprocess.run(["xdg-open", output_dir])
        else:
            messagebox.showinfo("Info", f"Cartella di output non trovata:\n{output_dir}")

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