import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import sys

# Funzione fittizia per simulare l'importazione e l'esecuzione di solver.py
# Nel tuo caso, qui importeresti e chiameresti la tua funzione da solver.py
def run_solver_with_params(alfa_valore, beta_valore):
    try:
        # Importa solver.py e chiama la funzione appropriata
        # Esempio:
        # from solver import risolvi
        # risultato = risolvi(alfa_valore, beta_valore)
        
        # Per ora, simuliamo un'operazione
        print(f"Esecuzione di solver.py con alfa={alfa_valore}, beta={beta_valore}")
        import time
        time.sleep(2) # Simula un po' di lavoro
        return f"Solver completato con alfa={alfa_valore}, beta={beta_valore}"
    except Exception as e:
        return f"Errore durante l'esecuzione del solver: {e}"

# Funzione per ottenere il percorso base corretto quando si è in un eseguibile PyInstaller
def get_base_path():
    if getattr(sys, 'frozen', False):
        # We are running in a bundle
        return sys._MEIPASS
    else:
        # We are running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestore Moduli Python")
        self.root.geometry("600x500") # Dimensione iniziale della finestra

        self.file_commesse = tk.StringVar()
        self.file_veicoli = tk.StringVar()
        self.file_macchine = tk.StringVar()
        self.alfa_val = tk.DoubleVar(value=0.5) # Valore iniziale per alfa
        self.beta_val = tk.StringVar(value="10") # Valore iniziale per beta

        self.setup_ui()

    def setup_ui(self):
        # Frame per la selezione dei file
        file_frame = ttk.LabelFrame(self.root, text="Seleziona File Excel")
        file_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(file_frame, text="Estrazione Commesse:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(file_frame, textvariable=self.file_commesse, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Sfoglia", command=lambda: self.select_file(self.file_commesse)).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(file_frame, text="Estrazione Veicoli:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(file_frame, textvariable=self.file_veicoli, width=50).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Sfoglia", command=lambda: self.select_file(self.file_veicoli)).grid(row=1, column=2, padx=5, pady=2)

        ttk.Label(file_frame, text="Estrazione Macchine:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(file_frame, textvariable=self.file_macchine, width=50).grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Sfoglia", command=lambda: self.select_file(self.file_macchine)).grid(row=2, column=2, padx=5, pady=2)

        # Frame per i parametri di solver.py
        params_frame = ttk.LabelFrame(self.root, text="Parametri Solver (solver.py)")
        params_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(params_frame, text="Parametro Alfa:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.alfa_slider = ttk.Scale(params_frame, from_=0.0, to=1.0, orient="horizontal", variable=self.alfa_val, length=200)
        self.alfa_slider.grid(row=0, column=1, padx=5, pady=2)
        self.alfa_label = ttk.Label(params_frame, text=f"{self.alfa_val.get():.2f}")
        self.alfa_label.grid(row=0, column=2, padx=5, pady=2)
        self.alfa_val.trace_add("write", self.update_alfa_label) # Aggiorna la label quando lo slider cambia

        ttk.Label(params_frame, text="Parametro Beta:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(params_frame, textvariable=self.beta_val, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Pulsante per avviare main.py
        self.start_button = ttk.Button(self.root, text="Avvia main.py", command=self.start_main_script)
        self.start_button.pack(pady=20)

        # Loading screen / Progress bar
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.pack(pady=10, padx=10, fill="x")
        self.progress_frame.pack_forget() # Nascondi all'inizio

        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", mode="indeterminate", length=400)
        self.progress_bar.pack(pady=5)
        self.progress_label = ttk.Label(self.progress_frame, text="In esecuzione...")
        self.progress_label.pack(pady=5)

    def update_alfa_label(self, *args):
        self.alfa_label.config(text=f"{self.alfa_val.get():.2f}")

    def select_file(self, var):
        file_path = filedialog.askopenfilename(
            title="Seleziona file Excel",
            filetypes=[("File Excel", "*.xlsx *.xls")]
        )
        if file_path:
            var.set(file_path)

    def start_main_script(self):
        # Disabilita il pulsante e mostra la loading screen
        self.start_button.config(state=tk.DISABLED)
        self.progress_frame.pack(pady=10, padx=10, fill="x")
        self.progress_bar.start()
        self.progress_label.config(text="Avvio script principale...")

        # Avvia lo script in un thread separato per non bloccare la GUI
        threading.Thread(target=self._run_main_script_thread).start()

    def _run_main_script_thread(self):
        try:
            commesse_path = self.file_commesse.get()
            veicoli_path = self.file_veicoli.get()
            macchine_path = self.file_macchine.get()
            alfa = self.alfa_val.get()
            beta = self.beta_val.get()

            if not all([commesse_path, veicoli_path, macchine_path]):
                messagebox.showwarning("Attenzione", "Per favore, seleziona tutti i file Excel.")
                return

            self.progress_label.config(text="Caricamento dati...")

            # --- Qui puoi passare i percorsi dei file e i parametri al tuo main.py ---
            # Modo 1: Tramite variabili d'ambiente (se main.py le legge)
            os.environ['FILE_COMMESSE'] = commesse_path
            os.environ['FILE_VEICOLI'] = veicoli_path
            os.environ['FILE_MACCHINE'] = macchine_path
            os.environ['PARAM_ALFA'] = str(alfa)
            os.environ['PARAM_BETA'] = str(beta)

            # Esegui solver.py con i parametri
            self.progress_label.config(text="Esecuzione solver.py...")
            solver_result = run_solver_with_params(alfa, float(beta)) # Assicurati che beta sia un numero
            print(solver_result) # Stampa il risultato del solver nella console

            # Modo 2: Eseguire main.py come sottoprocesso e passare argomenti
            # Assicurati che main.py sia in grado di accettare questi argomenti
            # main_script_path = os.path.join(get_base_path(), "main.py")
            # cmd = [sys.executable, main_script_path, commesse_path, veicoli_path, macchine_path, str(alfa), str(beta)]
            #
            # process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # stdout, stderr = process.communicate()
            #
            # if process.returncode != 0:
            #     messagebox.showerror("Errore", f"Errore durante l'esecuzione di main.py:\n{stderr}")
            # else:
            #     messagebox.showinfo("Successo", f"main.py completato con successo!\nOutput:\n{stdout}")

            # Modo 3: Importare ed eseguire main.py direttamente (più complesso con parametri)
            # Per importare main.py direttamente, dovresti assicurarti che main.py sia una funzione
            # che accetta i tuoi input come argomenti.

            # Per la dimostrazione, simuleremo l'esecuzione di main.py
            self.progress_label.config(text="Esecuzione main.py (simulato)...")
            import time
            time.sleep(5) # Simula il tempo di esecuzione di main.py
            messagebox.showinfo("Completato", "L'esecuzione di main.py è terminata.")

        except ValueError:
            messagebox.showerror("Errore", "Il parametro Beta deve essere un numero valido.")
        except Exception as e:
            messagebox.showerror("Errore", f"Si è verificato un errore: {e}")
        finally:
            # Riabilita il pulsante e nascondi la loading screen
            self.progress_bar.stop()
            self.progress_frame.pack_forget()
            self.start_button.config(state=tk.NORMAL)
            self.progress_label.config(text="In attesa...")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()