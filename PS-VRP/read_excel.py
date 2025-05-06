
import pandas as pd
from macchina import Macchina
from commessa import Commessa
from veicolo import Veicolo
from datetime import datetime
from datetime import timedelta
import output
import warnings

#CAMPI DI LETTURA DEI FILE DI INPUT
campi_input_macchine=['Nome macchina','disponibilita','setup','velocità media','tipologia taglio','dt ultima lavorazione','ora ultima lavorazione','tempo setup cambio alberi','tempo setup prima fila coltelli','tempo setup coltelli','tempo carico bobina','tempo avvio taglio','tempo scarico bobina','tempo confezionamento sacchetti']
campi_attrezzaggio=['numero file ult lavoro','diam tubo ult lavoro']
campi_input_commesse=['commessa','data fine stampa per schedulatore','stato stampa calc','Commesse::DATA CONSEGNA','Commesse::Priorita cliente','qta da tagliare metri per schedulatore','qta da tagliare per schedulatore','Commesse::CODICE DI ZONA','Anagrafica incarti::tipologia taglio','Commesse::FASCIA','Commesse::FASCIA UTILE','Commesse::Diam int tubo','compatibilità macchine taglio::check dati','Commesse::categoria materiale', 'Commesse::tassativita', 'Commesse::id_tassativo']
campi_compatibilita=campi_input_commesse+['compatibilità macchine taglio::compat macc taglio 1','compatibilità macchine taglio::compat macc taglio 2','compatibilità macchine taglio::compat macc taglio 3','compatibilità macchine taglio::compat macc taglio 4','compatibilità macchine taglio::compat macc taglio 5','compatibilità macchine taglio::compat macc taglio 6','compatibilità macchine taglio::compat macc taglio 7','compatibilità macchine taglio::compat macc taglio 8','compatibilità macchine taglio::compat macc taglio 9','compatibilità macchine taglio::compat macc taglio 10','compatibilità macchine taglio::compat macc taglio 11','compatibilità macchine taglio::compat macc taglio 12','compatibilità macchine taglio::compat macc taglio 13','compatibilità macchine taglio::compat macc taglio 14','compatibilità macchine taglio::compat macc taglio 15','compatibilità macchine taglio::compat macc taglio 16','compatibilità macchine taglio::compat macc taglio 17']
#campi_veicoli=['Nome veicolo','Data e ora disponibilita','Disponibilita','Capacita','Zone coperte']
campi_veicoli=['id sped', 'dt sped', 'zona spedizione', 'spedizioni condivise::kg_rimanenti']

def read_excel_macchine(nome_file):
    """
    :param nome_file: nome del file da leggere relativo alle macchine
    :return: lista di oggetti macchina
    """
    warnings.simplefilter("ignore") #ignorare i warning fastidiosi pandas
    df=pd.read_excel(nome_file,0,skiprows=0,usecols=campi_input_macchine) #creazione di un dataframe con i dati di input. usecols permette di usare i nomi delle colonne che passo come parametro
    colonne_setup=['tempo setup cambio alberi','tempo setup prima fila coltelli','tempo setup coltelli','tempo carico bobina','tempo avvio taglio','tempo scarico bobina','tempo confezionamento sacchetti']
    for col in colonne_setup:
        df.loc[df['tipologia taglio'] == 'FOGLIO', col] = df.loc[df['tipologia taglio'] == 'FOGLIO', col].fillna(0)
    lista_macchine=[] #lista di macchine inizialmente vuota
    df.loc[~df['Nome macchina'].str.startswith('BIMEC'),'Nome macchina'] = df['Nome macchina'].str.split().str[0] #per tutte le macchine il cui nome non inizia con BIMEC, tengo solo la sottostringa del nome
    df.loc[df['Nome macchina'].str.contains('H7'),'Nome macchina'] = df['Nome macchina'].str.split('_').str[0] #per H7 prendo solo la sottostringa con il suo nome
    
    #VERIFICA DEL DTYPE DELLA COLONNA
    if pd.api.types.is_timedelta64_dtype(df['ora ultima lavorazione']):
        #Conversione timedelta diretta
        df['ora ultima lavorazione'] = df['ora ultima lavorazione'].apply(lambda x: (pd.Timestamp("1900-01-01") + x).time())
    else:
        #Conversione stringa a datetime ed estrazione time
        df['ora ultima lavorazione'] = pd.to_datetime(df['ora ultima lavorazione'], format='%H:%M:%S', errors='coerce').dt.time

    df['ora ultima lavorazione']=pd.to_datetime(df['ora ultima lavorazione'], format='%H:%M:%S').dt.time
    df['Data e ora disponibilita'] = df.apply(lambda row: pd.Timestamp.combine(row['dt ultima lavorazione'], row['ora ultima lavorazione']), axis=1)
    df=df.drop(columns=['dt ultima lavorazione','ora ultima lavorazione'])
    file=df.loc[df['disponibilita']==1]
    file=file.sort_values('Data e ora disponibilita') # Considera tutte le date di ultima lavorazione delle macchine e le ordina
    d=file.iat[0,12]  # .iat ritorna un elemento in una posizione particolare di un dataframe d e' la prima data di ultima lavorazione, in altre parole, in posizione 0,13 troviamo la prima (indice 0) macchina disponibile (dato che erano state ordinate per 'data ultima lavorazione') e con indice di colonna = 5 andiamo a prendere il valore di tale data
    days_ahead=d.weekday()  # days_ahead e' il giorno della settimana corrispondente alla data d, espresso in int (0 = lunedì, 6 = domenica)
    data_inizio_schedulazione=d-timedelta(days_ahead)  # Timedelta può essere usato per sottrarre un tot di giorni ad una certa data, in questo caso d. Sottraendo days_ahead ad una data qualunque si può risalire al primo lunedì antecedente alla data d.
    #print(f'timedelta {timedelta(days_ahead)}')
    df['data_inizio_schedulazione'] = data_inizio_schedulazione.replace(hour=7, minute=0,second=0)  # Aggiungiamo la colonna 'data_inizio_lavorazione' al dataframe file_macchine. L'ora di inizio schedulazione viene impostata alle 7 della mattina
    for (i,f) in df.iterrows():  # iterrows() ritorna una pd.Series per ogni riga nel dataframe, "i" prende l'indice e "f" è la riga/pd.Series
        lista_macchine.append(Macchina(*f)) #aggiungo alla lista la macchina
        #if lista_macchine[i].disponibilita==1: #per il momento imposto la data a mano (data del giorno in cui si è fatta l'estrazione)
        #    lista_macchine[i].data_ora_disponibilita=datetime.strptime('03/07/2024','%d/%m/%Y').replace(hour=8, minute=0) #se la macchina è disponibile, diventa disponibile dal momento in cui eseguo il run, quindi datetime.today()
    return lista_macchine

def read_attrezzaggio_macchine(nome_file,lista_macchine):
    """
    :param nome_file: nome del file da leggere relativo all'attrezzaggio iniziale delle macchine
    :param lista_macchine: lista di oggetti Macchina a cui andare ad aggiungere gli attrezzaggi
    :return: nulla da ritornare in quanto la lista esiste già
    """
    df=pd.read_excel(nome_file, 0, skiprows=0, usecols=campi_attrezzaggio) #lettura pandas del file input
    df=df.replace('?',0)
    df['diam tubo ult lavoro']=df['diam tubo ult lavoro'].fillna(int(0)) #riempio i campi nan con 0
    df['numero file ult lavoro']=df['numero file ult lavoro'].fillna(int(0)) #riempio i campi nan con -1
    for (i,f) in df.iterrows(): #itero lungo le righe del df (la i indica l'indice della riga; da notare che vi è corrispondenza tra la i del df pandas e la i della macchina)
        lista_macchine[i].attrezzaggio={'numero_coltelli':df['numero file ult lavoro'][i],
                                        'diametro_tubo':df['diam tubo ult lavoro'][i]}

def read_excel_commesse(nome_file,inizio_schedulazione):
    """
    :param nome_file: nome del file da leggere relativo alle commesse
    :return: lista di oggetti macchina
    """
    #rimuoviamo tutte le commesse con campi vuoti e andiamo a stampare un file con tutte le commesse eliminate e il motivo
    #warnings.simplefilter("ignore") #ignorare i warning fastidiosi pandas
    df=pd.read_excel(nome_file,0, skiprows=0,usecols=campi_input_commesse)  # creazione di un dataframe con i dati di input. usecols permette di usare i nomi delle colonne che passo come parametro
    colonne_commesse_foglio=['Commesse::FASCIA','Commesse::Diam int tubo']
    for col in colonne_commesse_foglio:
        df.loc[df['Anagrafica incarti::tipologia taglio'] == 'foglio', col] = df.loc[df['Anagrafica incarti::tipologia taglio'] == 'foglio', col].fillna(0)
    output.write_error_output(df,"PS-VRP\Dati_output\error_read_file.xlsx")

    #Campi riempiti per evitare che vengano rimossi dal .dropna (campi "facoltativi")
    df['Commesse::CODICE DI ZONA'] = df['Commesse::CODICE DI ZONA'].fillna(0)
    df['Commesse::tassativita'] = df['Commesse::tassativita'].fillna(0)
    df['Commesse::id_tassativo'] = df['Commesse::id_tassativo'].fillna(0)

    df = df.dropna()
    lista_commesse=[] #lista commesse inizialmente vuota
    df=df[~df['compatibilità macchine taglio::check dati'].str.startswith('ERR')] #elimino tutte le righe del df che presentano errori nell'estrazione filemaker
    df=df.drop(columns=['compatibilità macchine taglio::check dati']) #elimino la colonna dopo averla utilizzata per filtrare le commesse
    df=df.reset_index(drop=True)
    df['Release date']=pd.to_datetime(df['data fine stampa per schedulatore']).apply(lambda x: x.replace(hour=14, minute=0, second=0))
    if df['Commesse::CODICE DI ZONA'] is not int:
        df['Commesse::CODICE DI ZONA'] = df['Commesse::CODICE DI ZONA'].apply(lambda x: [int(num) for num in str(x).split(' / ')])
    df['data_inizio_schedulazione']=inizio_schedulazione
    #print(df['data_inizio_schedulazione'])
    ordine_colonne_df=['commessa','Release date','Commesse::DATA CONSEGNA',
                        'Commesse::Priorita cliente', 'qta da tagliare metri per schedulatore',
                        'qta da tagliare per schedulatore', 'Commesse::CODICE DI ZONA',
                        'Anagrafica incarti::tipologia taglio','Commesse::FASCIA UTILE','Commesse::FASCIA',
                        'Commesse::Diam int tubo','data_inizio_schedulazione','Commesse::categoria materiale', 'Commesse::tassativita', 'Commesse::id_tassativo'] #stabilisco il nuovo ordine delle colonne del df
    df=df[ordine_colonne_df] #assegno il nuovo ordine di colonne
    for (_,f) in df.iterrows():  # iterrows() ritorna una pd.Series per ogni riga nel dataframe, "_" prende l'indice (usato quando non mi importa il valore di tale indice) e "f" è la riga/pd.Series
        lista_commesse.append(Commessa(*f))
    return lista_commesse

def read_compatibilita(nome_file,lista_commesse):
    """
    :param nome_file: nome del file da leggere relativo alle compatibilita commessa-macchina
    :param lista_commesse: lista di oggetti Commessa a cui andare ad aggiungere le compatibilita con le macchine
    :return: nulla da ritornare in quanto la lista esiste gia
    """
    df=pd.read_excel(nome_file, 0, skiprows=0, usecols=campi_compatibilita) #lettura del df con pandas
    colonne_commesse_foglio = ['Commesse::FASCIA', 'Commesse::Diam int tubo']
    for col in colonne_commesse_foglio:
        df.loc[df['Anagrafica incarti::tipologia taglio'] == 'foglio', col] = df.loc[df['Anagrafica incarti::tipologia taglio'] == 'foglio', col].fillna(0)
    
    #Campi riempiti per evitare che vengano rimossi dal .dropna (campi "facoltativi")
    df['Commesse::CODICE DI ZONA'] = df['Commesse::CODICE DI ZONA'].fillna(0)
    df['Commesse::tassativita'] = df['Commesse::tassativita'].fillna(0)
    df['Commesse::id_tassativo'] = df['Commesse::id_tassativo'].fillna(0)

    df=df.dropna()
    df=df[~df['compatibilità macchine taglio::check dati'].str.startswith('ERR')]
    df=df.drop(columns=campi_input_commesse)
    #df=df.drop(columns=['compatibilità macchine taglio::check dati'])
    df=df.reset_index(drop=True)
    macchine=['R10','R12','BIMEC 2','BIMEC 5','CASON','R3','BIMEC 4','R9','R6','H7','R5','BIMEC 3','T9','T2','T3','T8','T1'] #nomi delle macchine inseriti a mano nell'ordine corretto (ordine del file estratto da filemaker)
    vecchie_colonne=list(df.columns) #vecchi nomi delle colonne del df pandas che andrò a sostituire con i nuovi nomi
    nuove_colonne={vecchie_colonne[i]:macchine[i] for i in range(len(vecchie_colonne))} #creo un dizionario in cui le chiavi sono i nomi delle vecchie colonne e i valori sono i nomi delle nuove colonne
    df=df.rename(columns=nuove_colonne) #rinomino le colonne del df pandas
    pattern_ok = r'^OK.*$' #pattern che inizia con OK
    pattern_err = r'^ERR.*$' #pattern che inizia con ERR
    df[macchine]=df[macchine].replace({pattern_ok: 1, pattern_err: 0}, regex=True).astype(int) #dove c'è OK metto 1, dove c'è ERR metto 0
    for (i,f) in df.iterrows(): #itero lungo le righe del df (la i indica l'indice della riga; da notare che vi è corrispondenza tra la i del df pandas e la i della commessa)
        lista_commesse[i].compatibilita=dict(f) #assegno all'attributo compatibilita un dizionario con chiave=nome della macchina e valore=0/1 a seconda che la commessa non possa/possa essere schedulata sulla macchina

def read_excel_veicoli(nome_file):
    """
    :param nome_file: nome del file da leggere relativo ai veicoli disponibili
    :return: ritorna una lista di oggetti veicolo
    """
    df=pd.read_excel(nome_file, 0, skiprows=0, usecols=campi_veicoli)
    lista_veicoli=[] #creo una lista di veicoli inizialmente vuota
    for (_,f) in df.iterrows():  # iterrows() ritorna una pd.Series per ogni riga nel dataframe, "_" prende l'indice (usato quando non mi importa il valore di tale indice) e "f" è la riga/pd.Series
        lista_veicoli.append(Veicolo(*f))
    return lista_veicoli