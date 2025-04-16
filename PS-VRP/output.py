
import openpyxl as pyxl
from openpyxl.styles import PatternFill
import pandas as pd

campi_risultati_euristico=['commessa','macchina','minuti setup','minuti processamento','inizio setup','fine setup','inizio lavorazione','fine lavorazione','mt da tagliare','taglio','macchine compatibili','numero coltelli','diametro tubo','veicolo']

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
    ws1.column_dimensions['B'].width=15 #si settano le dimensioni delle colonne
    ws1.column_dimensions['C'].width=20 #si settano le dimensioni delle colonne
    ws1.column_dimensions['D'].width=20 #si settano le dimensioni delle colonne
    ws1.column_dimensions['E'].width=50 #si settano le dimensioni delle colonne
    ws1.column_dimensions['F'].width=50 #si settano le dimensioni delle colonne
    ws1.column_dimensions['G'].width=50 #si settano le dimensioni delle colonne
    ws1.column_dimensions['H'].width=50 #si settano le dimensioni delle colonne
    ws1.column_dimensions['I'].width=15 #si settano le dimensioni delle colonne
    ws1.column_dimensions['J'].width=15 #si settano le dimensioni delle colonne
    ws1.column_dimensions['K'].width=100 #si settano le dimensioni delle colonne
    ws1.column_dimensions['L'].width=15 #si settano le dimensioni delle colonne
    ws1.column_dimensions['M'].width=15 #si settano le dimensioni delle colonne
    ws1.column_dimensions['N'].width=15 #si settano le dimensioni delle colonne
    ws1.column_dimensions['O'].width=15 #si settano le dimensioni delle colonne

    start_row=2 #inizializzo la riga in cui andrò a printare. si parte dalla seconda in quanto la prima è occupata dai titoli
    start_column=1 #inizializzo le colonne in cui andrò a printare si parte dalla prima e si andrà avanti fino all'ultimo campo
    for schedula in schedulazione: #per ogni dizionario nella lista
        for chiave,valore in schedula.items(): #vado a prendere tutti i valori all'interno del dizionario
            if chiave=='macchine compatibili':
                valore.sort()
                valore=" ;".join(valore)
            if type(valore)==pd.Timestamp: #se sto considerando un campo contenente una data pandas devo convertirla
                valore=valore.strftime("%Y-%m-%d %H:%M:%S") #converto in data (giorno-mese-anno)
            ws1.cell(row=start_row,column=start_column,value=valore) #assegno il valore in questione alla cella
            start_column+=1 #se non sono finiti i campi avanzo di una colonna
        start_row+=1 #quando sono finiti i campi passo alla riga successiva
        start_column=1 #quando sono finiti i campi riparto dalla prima colonna
    wb.save(nome_file) #salvo il file excel con il nome che passo come parametro

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
    print(f'COMMESSE CON CAMPO MANCANTE: ', len(commesse_campi_vuoti))
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

