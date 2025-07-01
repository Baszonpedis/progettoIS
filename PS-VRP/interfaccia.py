import sys
import subprocess
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QSlider, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMovie

a = 1  # Default α

class SchedulerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedulatore Produzione & Logistica")
        self.setStyleSheet("background-color: #1E3A8A; color: white; font-size: 14px;")
        self.setFixedSize(400, 500)

        layout = QVBoxLayout()

        # Importa
        self.import_button = QPushButton("📂 Importa estrazione")
        self.import_button.clicked.connect(self.import_files)
        layout.addWidget(self.import_button)

        # Slider alpha
        self.alpha_label = QLabel(f"α = {a}")
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setMinimum(0)
        self.alpha_slider.setMaximum(100)
        self.alpha_slider.setValue(100)
        self.alpha_slider.valueChanged.connect(self.update_alpha)
        layout.addWidget(self.alpha_label)
        layout.addWidget(self.alpha_slider)

        # Avvia main.py
        self.run_button = QPushButton("🚀 Avvia Schedulazione")
        self.run_button.clicked.connect(self.run_main)
        layout.addWidget(self.run_button)

        # Loader gif
        self.loading_label = QLabel("")
        self.loading_movie = QMovie("spinner.gif")  # Inserisci una gif spinner!
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)

        # Visualizza Avvisi
        self.alert_button = QPushButton("⚠️ Visualizza Avvisi")
        self.alert_button.clicked.connect(self.open_alerts)
        layout.addWidget(self.alert_button)

        # Visualizza Gantt
        self.gantt_button = QPushButton("📊 Visualizza Gantt")
        self.gantt_button.clicked.connect(self.show_gantt)
        layout.addWidget(self.gantt_button)

        # Visualizza Soluzione
        self.solution_button = QPushButton("📁 Visualizza Soluzione")
        self.solution_button.clicked.connect(self.open_solution)
        layout.addWidget(self.solution_button)

        self.setLayout(layout)

    def import_files(self):
        QMessageBox.information(self, "Importa", "Input importati correttamente!")

    def update_alpha(self, value):
        global a
        a = value / 100
        self.alpha_label.setText(f"α = {a:.2f}")

    def run_main(self):
        self.loading_label.setVisible(True)
        self.loading_movie.start()
        try:
            subprocess.run(["python", "main.py"], check=True)
            QMessageBox.information(self, "Completato", "Schedulazione completata.")
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Errore", "Errore durante l'esecuzione di main.py")
        self.loading_movie.stop()
        self.loading_label.setVisible(False)

    def open_alerts(self):
        os.startfile("PS-VRP/Dati_output/errori_veicoli.xlsx")
        os.startfile("PS-VRP/Dati_output/errori_lettura.xlsx")
        os.startfile("PS-VRP/Dati_output/errori_compatibilità.xlsx")

    def show_gantt(self):
        from main import grafico_schedulazione  # Assumendo che funzioni!
        from main import soluzione_finale
        import pickle  # O carica da file
        # schedulazione = carica schedulazione
        grafico_schedulazione(soluzione_finale)  # Passa la schedulazione giusta!

    def open_solution(self):
        os.startfile("PS-VRP/Dati_output/sequenza_post.xlsx")


app = QApplication(sys.argv)
window = SchedulerGUI()
window.show()
sys.exit(app.exec())