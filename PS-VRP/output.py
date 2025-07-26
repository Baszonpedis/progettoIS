
import openpyxl as pyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
import pandas as pd

campi_risultati_euristico=['commessa','macchina','minuti setup','minuti processamento','inizio setup','fine setup','inizio lavorazione','fine lavorazione','mt da tagliare','taglio','macchine compatibili','numero coltelli','diametro tubo','veicolo', 'tassativita', 'veicolo tassativo', 'due date (non indicativa)', 'ritardo', 'priorita']

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
    ws1.column_dimensions['A'].width=15 #si settano le dimensioni delle colonne
    ws1.column_dimensions['B'].width=15
    ws1.column_dimensions['C'].width=20
    ws1.column_dimensions['D'].width=20
    ws1.column_dimensions['E'].width=50
    ws1.column_dimensions['F'].width=50
    ws1.column_dimensions['G'].width=50
    ws1.column_dimensions['H'].width=50
    ws1.column_dimensions['I'].width=15
    ws1.column_dimensions['J'].width=15
    ws1.column_dimensions['K'].width=90
    ws1.column_dimensions['L'].width=15
    ws1.column_dimensions['M'].width=15
    ws1.column_dimensions['N'].width=15
    ws1.column_dimensions['O'].width=15
    ws1.column_dimensions['P'].width=15
    ws1.column_dimensions['Q'].width=20 #si settano le dimensioni delle colonne



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
    campi_risultati_ridotti = ['commessa', 'macchina', 'inizio_setup', 'inizio_lavorazione', 'tassativita']

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
    campi_risultati_ridotti = ['commessa', 'macchina', 'inizio_setup', 'inizio_lavorazione']

    # Larghezza colonne di base
    larghezze = [15, 15, 22, 22]  # Ho allargato un po' anche le date

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

def write_error_output(df,nome_file):
    """
    :param df: dataframe contenente tutte le commesse e tutti i campi
    :param nome_file: percorso che indica dove salvare il file e con che nome
    :return: file excel in cui vado a fare la print delle commesse e i relativi campi vuoti
    """
    wb=pyxl.Workbook()  #inizializzo il file
    ws1=wb.active #si prende il foglio attivo
    ws1.title='Error' #si rinomina il titolo del foglio
    nomi_colonne=list(df.columns)
    ws1.append(nomi_colonne) #vado ad inserire il nome delle colonne
    ws1.column_dimensions['A'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['B'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['C'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['D'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['E'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['F'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['G'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['H'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['I'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['J'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['K'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['L'].width =30  # si settano le dimensioni delle colonne
    ws1.column_dimensions['M'].width =35  # si settano le dimensioni delle colonne
    start_row=2 #inizializzo la riga in cui andrò a printare. si parte dalla seconda in quanto la prima è occupata dai titoli
    start_column=1 #inizializzo le colonne in cui andrò a printare si parte dalla prima e si andrà avanti fino all'ultimo campo

    commesse_campi_vuoti=list(df[df.isnull().any(axis=1)].index)
    #print(f'COMMESSE CON CAMPO MANCANTE: ', len(commesse_campi_vuoti))
    fill=PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    for riga in commesse_campi_vuoti:
        ws1.cell(row=riga+2,column=1).fill=fill

    df=df.fillna('CAMPO VUOTO')
    for index, row in df.iterrows():
        indici_valori=enumerate(row)
        ws1.cell(row=start_row,column=start_column,value=df['commessa'][index])  # assegno il valore in questione alla cella
        for indice,valore in indici_valori:
            if valore=='CAMPO VUOTO':
                ws1.cell(row=start_row,column=indice+1,value=valore)  # assegno il valore in questione alla cella
        start_row+=1
    wb.save(nome_file) #salvo il file excel con il nome che passo come parametro

def write_veicoli_error_output(df, nome_file):
    wb = pyxl.Workbook()
    ws1 = wb.active
    ws1.title = 'Errori Veicoli'
    
    # Titoli colonne
    nomi_colonne = list(df.columns)
    ws1.append(nomi_colonne)
    
    # Imposta larghezza colonne dinamicamente
    for i, col in enumerate(nomi_colonne, start=1):
        ws1.column_dimensions[chr(64 + i)].width = 30
    
    fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    start_row = 2
    df = df.fillna("CAMPO VUOTO")
    
    for index, row in df.iterrows():
        for col_index, value in enumerate(row):
            cell = ws1.cell(row=start_row, column=col_index + 1, value=value)
            if value == "CAMPO VUOTO":
                cell.fill = fill
        start_row += 1
    
    wb.save(nome_file)

def write_tassative_error_output(df, nome_file):
    wb = pyxl.Workbook()
    ws1 = wb.active
    ws1.title = 'Problemi Tassative (i.e. tassative con release date troppo lontana)'
    
    # Titoli colonne
    nomi_colonne = list(df.columns)
    ws1.append(nomi_colonne)
    
    # Imposta larghezza colonne dinamicamente
    for i, col in enumerate(nomi_colonne, start=1):
        ws1.column_dimensions[chr(64 + i)].width = 30
    
    fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    
    start_row = 2
    df = df.fillna("CAMPO VUOTO")
    
    for index, row in df.iterrows():
        for col_index, value in enumerate(row):
            cell = ws1.cell(row=start_row, column=col_index + 1, value=value)
            if value == "CAMPO VUOTO":
                cell.fill = fill
        start_row += 1
    
    wb.save(nome_file)
