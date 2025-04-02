Contenuti:
- commessa.py (classe commessa)
- macchina.py (classe macchina)
- veicolo.py (classe veicolo)
- output.py (per l'output)
- read_excel.py (per l'input - testing)
- read_excel - originale.py (per l'input - originale)
- main.py (modificato)
- solver.py (solver - testing)
- solver - originale.py (solver - originale)
- Dati_input (dati reali?)
- Dati_ouput
- INPUT_TEST (input ad hoc)
- OUTPUT_TEST

Per il funzionamento del main sono chiamate solamente le funzioni
- filtro_commesse (da solver.py)
- euristico_costruttivo (da solver.py)
  - inizializza_lista_commesse (da macchina.py)
  - aggiungi_minuti (da solver.py)
  - aggiorna_schedulazione1 (da solver.py)
- move_2_macchine (da solver.py)
  - return_schedulazione (da solver.py) [**]
  - move_inter_macchina (da solver.py)
- calcolo_tempi_setup
- move_no_delta (da solver.py)
  - [**]
- swap_no_delta (da solver.py)
  - [**]
- write_output_soluzione_euristica (da output.py)
