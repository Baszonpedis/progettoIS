import openpyxl as pyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows
import numpy as np

campi_risultati_euristico=['commessa','macchina', 'data fine stampa', 'minuti setup','minuti processamento','inizio setup','fine setup','inizio lavorazione','fine lavorazione','mt da tagliare','taglio','macchine compatibili','numero coltelli','diametro tubo','veicolo', 'tassativita', 'veicolo tassativo', 'due date (non indicativa)', 'ritardo', 'priorita']

def write_output_soluzione_euristica(schedulazione,nome_file):
    """
    :param schedulazione: lista di dizionari che contengono le informazioni sulle schedule
    :param nome_file: percorso che indica dove salvare il file e con che nome
    :return: file excel in cui vado a fare la print delle informazioni relative alla schedulazione
    """
    wb=pyxl.Workbook() #inizializzo il file
    ws1=wb.active #si prende il foglio attivo
    ws1.title='Schedulazione' #si rinomina il titolo del foglio
    ws1.append(campi_risultati_euristico) #vado ad inserire il nome delle colonne
    ws1.column_dimensions['A'].width=10 #si settano le dimensioni delle colonne
    ws1.column_dimensions['B'].width=10
    ws1.column_dimensions['C'].width=15
    ws1.column_dimensions['D'].width=15
    ws1.column_dimensions['E'].width=15
    ws1.column_dimensions['F'].width=25
    ws1.column_dimensions['G'].width=25
    ws1.column_dimensions['H'].width=25
    ws1.column_dimensions['I'].width=15
    ws1.column_dimensions['J'].width=15
    ws1.column_dimensions['K'].width=15
    ws1.column_dimensions['L'].width=50
    ws1.column_dimensions['M'].width=15
    ws1.column_dimensions['N'].width=15
    ws1.column_dimensions['O'].width=10
    ws1.column_dimensions['P'].width=10
    ws1.column_dimensions['Q'].width=15
    ws1.column_dimensions['R'].width=15

    start_row=2 #inizializzo la riga in cui andrò a printare. si parte dalla seconda in quanto la prima è occupata dai titoli
    start_column=1 #inizializzo le colonne in cui andrò a printare si parte dalla prima e si andrà avanti fino all'ultimo campo
    for schedula in schedulazione: #per ogni dizionario nella lista
        for chiave,valore in schedula.items(): #vado a prendere tutti i valori all'interno del dizionario
            if chiave=='macchine compatibili':
                valore.sort()
                valore=" ;".join(valore)
            if type(valore)==pd.Timestamp: #se sto considerando un campo contenente una data pandas devo convertirla
                valore=valore.strftime("%d-%m-%Y %H:%M:%S") #converto in data (giorno-mese-anno)
            if chiave=='veicolo' and valore != None and not isinstance(valore, str):
                valore = valore.nome
            ws1.cell(row=start_row,column=start_column,value=valore) #assegno il valore in questione alla cella
            start_column+=1 #se non sono finiti i campi avanzo di una colonna
        start_row+=1 #quando sono finiti i campi passo alla riga successiva
        start_column=1 #quando sono finiti i campi riparto dalla prima colonna
    wb.save(nome_file) #salvo il file excel con il nome che passo come parametro

def write_output_ridotto(schedulazione,nome_file):
    """
    :param schedulazione: lista di dizionari con info sulla schedulazione
    :param nome_file: percorso file excel
    :return: file excel abbellito
    """
    campi_risultati_ridotti = ['commessa', 'macchina', 'inizio_setup', 'inizio_lavorazione', 'tassativita', 'priorita']

    # Colori pastello tenui (HEX)
    colori_pastello = [
        'CCE5FF',  # azzurro chiaro
        'D5E8D4',  # verde pallido
        'FCE5CD',  # arancio chiarissimo
        'EAD1DC',  # rosa tenue
        'FFF2CC',  # giallo chiaro
        'D9D2E9',  # lilla chiaro
        'E2EFDA',  # verde menta
        'F4CCCC',  # rosato
    ]

    # Costruisci mappa macchina → colore
    macchine = list({schedula['macchina'] for schedula in schedulazione})
    macchina_colori = {
        macchina: colori_pastello[i % len(colori_pastello)] for i, macchina in enumerate(macchine)
    }

    # Workbook e foglio
    wb = pyxl.Workbook()
    ws = wb.active
    ws.title = 'Schedulazione'

    # Stili base
    bold_font = Font(bold=True)
    center_align = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Scrivi intestazioni
    for idx, campo in enumerate(campi_risultati_ridotti, start=1):
        cell = ws.cell(row=1, column=idx, value=campo)
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = thin_border

    # Scrivi dati con colore
    for row_idx, schedula in enumerate(schedulazione, start=2):
        macchina = schedula.get('macchina')
        colore = macchina_colori.get(macchina, 'FFFFFF')
        fill = PatternFill(start_color=colore, end_color=colore, fill_type='solid')

        for col_idx, chiave in enumerate(campi_risultati_ridotti, start=1):
            valore = schedula.get(chiave, '')
            if isinstance(valore, pd.Timestamp):
                valore = valore.strftime("%d-%m-%Y %H:%M:%S")
            cell = ws.cell(row=row_idx, column=col_idx, value=valore)
            cell.alignment = center_align
            cell.border = thin_border
            cell.fill = fill

    # Colonne larghezza base
    col_widths = [15, 15, 22, 22]
    for idx, width in zip(range(1, len(campi_risultati_ridotti) + 1), col_widths):
        ws.column_dimensions[pyxl.utils.get_column_letter(idx)].width = width

    # Congela intestazione
    ws.freeze_panes = 'A2'

    # Salva file
    wb.save(nome_file)

def write_output_ridotto_txt(schedulazione, nome_file):
    """
    Salva la schedulazione in un .txt formattato a tabella leggibile
    """
    campi_risultati_ridotti = ['commessa', 'macchina', 'inizio_setup', 'inizio_lavorazione', 'tassativita', 'priorita']

    # Larghezza colonne di base
    larghezze = [15, 15, 22, 22]

    with open(nome_file, 'w', encoding='utf-8') as f:
        # Linea intestazione
        intestazione = ''
        for i, (campo, larghezza) in enumerate(zip(campi_risultati_ridotti, larghezze)):
            intestazione += f"{campo:<{larghezza}}"
            # Aggiungi separazione extra solo tra terza e quarta colonna
            if i == 2:
                intestazione += '   '  # 3 spazi extra
        f.write(intestazione + '\n')

        # Riga di separazione
        separatore = ''
        for i, larghezza in enumerate(larghezze):
            separatore += '-' * larghezza
            if i == 2:
                separatore += '   '
        f.write(separatore + '\n')

        # Dati
        for schedula in schedulazione:
            riga = ''
            for i, (chiave, larghezza) in enumerate(zip(campi_risultati_ridotti, larghezze)):
                valore = schedula.get(chiave, '')
                if isinstance(valore, pd.Timestamp):
                    valore = valore.strftime("%d-%m-%Y %H:%M:%S")
                riga += f"{str(valore):<{larghezza}}"
                if i == 2:
                    riga += '   '
            f.write(riga + '\n')

def write_output_commesse_veicoli(schedulazione, nome_file):
    """
    :param schedulazione: lista di dizionari con info sulla schedulazione
    :param nome_file: percorso file excel
    :return: file excel abbellito
    """
    campi_risultati_ridotti = ['commessa', 'veicolo']

    # Colori pastello tenui (HEX)
    colori_pastello = [
        'CCE5FF',  # azzurro chiaro
        'D5E8D4',  # verde pallido
        'FCE5CD',  # arancio chiarissimo
        'EAD1DC',  # rosa tenue
        'FFF2CC',  # giallo chiaro
        'D9D2E9',  # lilla chiaro
        'E2EFDA',  # verde menta
        'F4CCCC',  # rosato
    ]

    colore_nessun_veicolo = 'EEEEEE'  # grigio chiaro

    # Costruisci mappa veicolo → colore
    veicoli = [
        schedula['veicolo'].nome if schedula['veicolo'] is not None else None
        for schedula in schedulazione
    ]
    veicolo_colori = {}
    for i, veicolo in enumerate(veicoli):
        if veicolo is None:
            veicolo_colori[None] = colore_nessun_veicolo
        else:
            veicolo_colori[veicolo] = colori_pastello[i % len(colori_pastello)]

    # Workbook e foglio
    wb = pyxl.Workbook()
    ws = wb.active
    ws.title = 'Schedulazione'

    # Stili base
    bold_font = Font(bold=True)
    center_align = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Scrivi intestazioni
    for idx, campo in enumerate(campi_risultati_ridotti, start=1):
        cell = ws.cell(row=1, column=idx, value=campo)
        cell.font = bold_font
        cell.alignment = center_align
        cell.border = thin_border

    # Scrivi dati con colore
    for row_idx, schedula in enumerate(schedulazione, start=2):
        veicolo_obj = schedula.get('veicolo')
        veicolo_nome = veicolo_obj.nome if veicolo_obj is not None else None

        colore = veicolo_colori.get(veicolo_nome, colore_nessun_veicolo)
        fill = PatternFill(start_color=colore, end_color=colore, fill_type='solid')

        for col_idx, chiave in enumerate(campi_risultati_ridotti, start=1):
            valore = schedula.get(chiave, '')

            if chiave == 'veicolo':
                valore = veicolo_nome if veicolo_nome is not None else '—'

            cell = ws.cell(row=row_idx, column=col_idx, value=valore)
            cell.alignment = center_align
            cell.border = thin_border
        cell.fill = fill

    # Colonne larghezza base
    col_widths = [15, 15]
    for idx, width in zip(range(1, len(campi_risultati_ridotti) + 1), col_widths):
        ws.column_dimensions[pyxl.utils.get_column_letter(idx)].width = width

    # Congela intestazione
    ws.freeze_panes = 'A2'

    # Salva file
    wb.save(nome_file)

def _append_sheet_to_workbook(df, nome_file, nome_foglio):
    """Funzione helper interna per gestire l'apertura/creazione del file e l'aggiunta del foglio"""
    try:
        wb = pyxl.load_workbook(nome_file)
    except FileNotFoundError:
        wb = pyxl.Workbook()
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
            
    # Se il foglio esiste già, lo rimuoviamo per sovrascriverlo
    if nome_foglio in wb.sheetnames:
        wb.remove(wb[nome_foglio])
        
    ws = wb.create_sheet(title=nome_foglio)
    
    # Scrittura Intestazioni
    ws.append(list(df.columns))
    
    # Scrittura Dati
    for r in dataframe_to_rows(df, index=False, header=False):
        ws.append(r)
        
    # Larghezza colonne (base)
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 25
        
    wb.save(nome_file)

def write_error_output(df, nome_file):
    """
    Filtra il dataframe per trovare righe con campi critici vuoti,
    le scrive nel file unico ed evidenzia in GIALLO le celle specifiche mancanti.
    """
    nome_foglio = 'Problemi Lettura Excel'

    # 1. Definizione campi opzionali (da NON evidenziare se vuoti)
    campi_opzionali = [
        'Commesse::CODICE DI ZONA', 
        'flag tassativo taglio per schedulatore', 
        'id spedizione'
    ]
    
    # 2. Logica di FILTRO (identica a prima)
    # Creiamo una copia per controllo e riempiamo i campi opzionali
    df_check = df.copy()
    for col in campi_opzionali:
        if col in df_check.columns:
            # Usiamo un valore fittizio che non sia NaN
            df_check[col] = df_check[col].replace({np.nan: 'IGNORE_ME', None: 'IGNORE_ME'})
            
    # Troviamo le righe che hanno ancora dei NaN veri nei campi obbligatori
    righe_con_errori_mask = df_check.isnull().any(axis=1)
    
    # Selezioniamo dal DF originale solo le righe problematiche
    df_output = df[righe_con_errori_mask].copy()
    
    if df_output.empty:
        print("Nessun errore critico di lettura rilevato (fogli puliti).")
        return

    # 3. Gestione Workbook (Apertura/Creazione file unico)
    # Nota: Non usiamo _append_sheet_to_workbook qui perché ci serve controllo sulle celle
    try:
        wb = pyxl.load_workbook(nome_file)
    except FileNotFoundError:
        wb = pyxl.Workbook()
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
            
    if nome_foglio in wb.sheetnames:
        wb.remove(wb[nome_foglio])
        
    ws = wb.create_sheet(title=nome_foglio)

    # Definizione stile (Giallo)
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

    # 4. Scrittura Intestazioni
    headers = list(df_output.columns)
    for col_idx, header_name in enumerate(headers, start=1):
        ws.cell(row=1, column=col_idx, value=header_name)

    # 5. Scrittura Dati ed EVIDENZIAZIONE
    # Iteriamo sulle righe del DF filtrato (partiamo dalla riga Excel 2)
    for r_idx, (index_originale, row_series) in enumerate(df_output.iterrows(), start=2):
        # Iteriamo sulle colonne
        for c_idx, col_name in enumerate(headers, start=1):
            valore_originale = row_series[col_name]
            
            # Scriviamo il valore nella cella (se è nan pandas, mettiamo stringa vuota o lasciamo None)
            valore_da_scrivere = valore_originale
            if pd.isna(valore_originale):
                 valore_da_scrivere = None # Lascia la cella Excel vuota

            cell = ws.cell(row=r_idx, column=c_idx, value=valore_da_scrivere)

            # LOGICA DI EVIDENZIAZIONE:
            # Se il valore originale era nullo E la colonna NON è tra quelle opzionali
            if pd.isna(valore_originale) and col_name not in campi_opzionali:
                cell.fill = yellow_fill

    # 6. Impostazione larghezza colonne (estetica)
    for i in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 25

    wb.save(nome_file)

def write_incompatibili_error_output(df, nome_file):
    """Nuova funzione per le incompatibilità (usata da read_compatibilita)"""
    _append_sheet_to_workbook(df, nome_file, 'Incompatibilità')

def error_commesse_in_veicoli_errati(df, nome_file):
    """Per commesse associate a veicoli errati (i.e. non in estrazione)"""
    _append_sheet_to_workbook(df, nome_file, 'Commesse su veicoli errati')

def write_veicoli_error_output(df, nome_file):
    """ Per veicoli errati (i.e. non in estrazione)"""
    _append_sheet_to_workbook(df, nome_file, 'Veicoli errati')