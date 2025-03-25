import math
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import pandas as pd
from commessa import Commessa
from macchina import Macchina
from veicolo import Veicolo
import macchina
import random
from copy import deepcopy

def Selezione_commesse(lista_commesse:list,lista_veicoli:list):
    """
    :param lista_commesse: lista di oggetti commessa contenete tutte le commesse
    :param lista_veicoli: lista di oggetti veicolo contenente tutti i veicoli
    :return: lista di commesse ordinate sulla base di alcuni criteri
    """
    lista_commesse_ordinate=[] #lista inizialmente vuota che conterrà tutte le commesse da schedulare ordinate secondo un dato criterio (priorità cliente)
    lista_veicoli_disponibili=[veicolo for veicolo in lista_veicoli if veicolo.disponibilita==1] #lista che contiene i veicoli disponibili (veicoli filtrati per disponibilità)
    zone_aperte=set([veicolo.zone_coperte for veicolo in lista_veicoli_disponibili]) #set contenete tutte le zone aperte (una lista può contenere duplicati, mentre un set ha elementi unici)
    commesse_da_tagliare=[]
    for commessa in lista_commesse:
        intersezione=set(commessa.zona_cliente).intersection(zone_aperte) #calcolo l'intersezione tra l'insieme delle zone della commessa e le zone aperte
        if intersezione: #se l'intersezione contiene elementi (è diversa dall'insieme vuoto)
            commesse_da_tagliare.append(commessa) #aggiungo alla lista la commessa
    #commesse_da_tagliare=sorted(list(set(commesse_da_tagliare)),key=lambda commessa:commessa.priorita_cliente,reverse=True) # ordino la lista sulla base della priorita
    commesse_da_tagliare.sort(key=lambda commessa:commessa.priorita_cliente , reverse=True) # ordino la lista sulla base della priorita
    commesse_tot=len(commesse_da_tagliare)
    commesse_assegnate=0 #variabile contatore
    for commessa in commesse_da_tagliare:
        veicolo_assegnato=None #inizialmente il veicolo assegnato non esiste
        capacita_massima=-math.inf #capacità massima inizializzata a valore meno infinito
        for veicolo in lista_veicoli_disponibili:
            if veicolo.zone_coperte in commessa.zona_cliente and veicolo.capacita>capacita_massima and veicolo.capacita>=commessa.kg_da_tagliare: #cerco di assegnare la commessa al veicolo più scarico (quello con capacità residua maggiore)
                capacita_massima=veicolo.capacita-commessa.kg_da_tagliare
                veicolo_assegnato=veicolo
        if veicolo_assegnato!=None: #se riesco a trovare un veicolo in cui inserire la commessa
            commessa.veicolo=veicolo_assegnato.nome #assegno la commessa al veicolo
            veicolo_assegnato.capacita-=commessa.kg_da_tagliare #decremento la capacità residua di un valore pari al peso della commessa
            commesse_assegnate+=1 #vado ad aumentare il contatore ogni volta che riesco ad assegnare una commessa
            lista_commesse_ordinate.append(commessa) #aggiungo la commessa alla lista delle commesse
    #print(f"commesse totali {commesse_tot}, commesse assegnate {commesse_assegnate}")
    return lista_commesse_ordinate

def aggiungi_minuti(minuti,data):
    """
    :param minuti: minuti da aggiungere ad una data
    :param data: data di riferimento
    :return: data + minuti da aggiungere
    """
    # la funzione aggiunge un tot di minuti ad una certa data
    data_copy=data #creo all'interno della funzione una copia della data per non modificare la data originale
    gg_lavorativi=5
    h_lavorative=8
    numero_settimana = minuti // round(gg_lavorativi*h_lavorative*60)
    numero_minuti = minuti % round(h_lavorative*60)
    numero_giorni = minuti // round(h_lavorative*60)
    # si moltiplica numero_settimana * 2 per aggiungere 2 giorni per ogni settimana trascorsa (sabato e domenica)
    return data_copy + timedelta(days = numero_giorni + numero_settimana * 2, minutes = numero_minuti)

def trova_macchina_migliore(commessa: Commessa, lista_macchine: list):
    macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
    tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
    tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
    tempo_minimo_processamento=math.inf
    for macchina in lista_macchine:  # cerco tra le macchine
        if macchina.disponibilita == 1 and commessa.compatibilita[macchina.nome_macchina] == 1 and commessa._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
            tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
            tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
            tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
            tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
            if tempo_fine_lavorazione < tempo_minimo_completamento:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                tempo_minimo_setup = tempo_setup
                tempo_minimo_processamento = tempo_processamento
                macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
    if macchina_schedula!=None:
        return macchina_schedula, tempo_minimo_setup, tempo_minimo_processamento, tempo_minimo_completamento
    else:
        return None, 0, 0, 0

def trova_macchina_migliore_obbligo_lavorazione(commessa: Commessa, lista_macchine: list):
    macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
    tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
    tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
    tempo_minimo_processamento=math.inf
    for macchina in lista_macchine:  # cerco tra le macchine
        if macchina.disponibilita == 1 and commessa.compatibilita[macchina.nome_macchina] == 1:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
            tempo_inizio_taglio = max(macchina._minuti_fine_ultima_lavorazione,commessa._minuti_release_date)
            tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
            tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
            tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
            if tempo_fine_lavorazione < tempo_minimo_completamento:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                tempo_minimo_setup = tempo_setup
                tempo_minimo_processamento = tempo_processamento
                macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
    if macchina_schedula!=None:
        return macchina_schedula, tempo_minimo_setup, tempo_minimo_processamento, tempo_minimo_completamento
    else:
        return None, 0, 0, 0


def aggiorna_schedulazione(commessa: Commessa ,macchina: Macchina, tempo_setup, tempo_processamento, inizio_schedulazione ,schedulazione: list, lista_commesse_non_schedulate:list):
    if commessa in lista_commesse_non_schedulate:
        minuti_inizio_lavorazione=max(macchina._minuti_fine_ultima_lavorazione,commessa._minuti_release_date)
    else:
        minuti_inizio_lavorazione = macchina._minuti_fine_ultima_lavorazione
    schedulazione.append({"commessa": commessa.id_commessa,
                          "macchina": macchina.nome_macchina,
                          "minuti setup": tempo_setup,
                          "minuti processamento":tempo_processamento,
                          "inizio_setup": aggiungi_minuti(minuti_inizio_lavorazione,inizio_schedulazione),
                          "fine_setup": aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup,inizio_schedulazione),
                          "inizio_lavorazione": aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup,inizio_schedulazione),
                          "fine_lavorazione": aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup + tempo_processamento,inizio_schedulazione),
                          "mt da tagliare": commessa.metri_da_tagliare,
                          "taglio": commessa.tipologia_taglio,
                          "macchine compatibili": [machine for machine, value in commessa.compatibilita.items() if value == 1],
                          "nr coltelli": commessa.numero_coltelli,
                          "diametro_tubo": commessa.diametro_tubo,
                          "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
    if commessa in lista_commesse_non_schedulate:
        macchina._minuti_fine_ultima_lavorazione = max(macchina._minuti_fine_ultima_lavorazione,commessa._minuti_release_date)+(tempo_setup + tempo_processamento)
    else:
        macchina._minuti_fine_ultima_lavorazione += (tempo_setup+tempo_processamento)
    macchina.lista_commesse_processate.append(commessa)  # aggiungo la commessa alla macchina che eseguirà la lavorazione

def Euristico(lista_macchine: list, lista_commesse: list):
    f_obj = 0  # funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione = []  # è una lista che conterrà tutte le schedulazioni
    lista_macchine = sorted(lista_macchine, key=lambda macchina: macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i)  # inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_commesse_non_schedulate = []
    for commessa in lista_commesse:
        for commessa_non_schedulata in lista_commesse_non_schedulate:
            macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = trova_macchina_migliore(commessa_non_schedulata, lista_macchine)
            if macchina_schedula!=None:
                f_obj += commessa_non_schedulata.priorita_cliente * (tempo_minimo_completamento)
                aggiorna_schedulazione(commessa_non_schedulata, macchina_schedula,tempo_setup, tempo_processamento, inizio_schedulazione, schedulazione,lista_commesse_non_schedulate)
                # macchina_schedula.numero_tubi_utilizzati+=1
                lista_commesse_non_schedulate.remove(commessa_non_schedulata)
        macchina_schedula,tempo_setup,tempo_processamento,tempo_minimo_completamento=trova_macchina_migliore(commessa,lista_macchine)
        if macchina_schedula!=None:
            f_obj+=commessa.priorita_cliente * (tempo_minimo_completamento)
            aggiorna_schedulazione(commessa,macchina_schedula,tempo_setup,tempo_processamento,inizio_schedulazione,schedulazione,lista_commesse_non_schedulate)
            #macchina_schedula.numero_tubi_utilizzati+=1
        else:
            lista_commesse_non_schedulate.append(commessa)
    # ordina le commesse non schedulate per release date
    for commessa_non_schedulata in lista_commesse_non_schedulate:
        macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = trova_macchina_migliore_obbligo_lavorazione(commessa_non_schedulata, lista_macchine)
        if macchina_schedula != None:
            f_obj+=commessa_non_schedulata.priorita_cliente * (tempo_minimo_completamento)
            aggiorna_schedulazione(commessa_non_schedulata, macchina_schedula, tempo_setup, tempo_processamento,inizio_schedulazione, schedulazione,lista_commesse_non_schedulate)
            #macchina_schedula.numero_tubi_utilizzati+=1
            lista_commesse_non_schedulate.remove(commessa_non_schedulata)
    return schedulazione,f_obj

def grafico_schedulazione(schedulazione):
    """
    :param schedulazione: lista di dizionari che contiene le informazioni relative ad una schedulazione
    :return: plot del grafico relativo alla schedulazione
    """
    macchine = list(set(schedula["macchina"] for schedula in schedulazione))  # Prendo i nomi unici delle macchine dal dizionario tramite il set
    macchine.sort(reverse = True)
    asse_x_setup = []  # Inizializzo l'asse delle x relativo al setup
    asse_y_setup = []  # Inizializzo l'asse delle y relativo al setup
    asse_x_lavorazione = []  # Inizializzo l'asse delle x relativo alla lavorazione
    asse_y_lavorazione = []  # Inizializzo l'asse delle y relativo alla lavorazione
    identificativi_commesse = []  # Inizializzo la lista degli identificativi delle commesse

    # Assegna un colore univoco a ogni veicolo
    veicoli = list(set(schedula["veicolo"] for schedula in schedulazione))
    colori = list(mcolors.TABLEAU_COLORS.values())  # Usa i colori della palette 'TABLEAU_COLORS'
    colori_veicoli = {veicolo: colori[i % len(colori)] for i, veicolo in enumerate(veicoli)}

    for schedula in schedulazione:  # Per ogni schedula nella lista vado a riempire le liste
        asse_x_setup.append((schedula["inizio_setup"], schedula["fine_setup"]))
        asse_y_setup.append(macchine.index(schedula["macchina"]))
        asse_x_lavorazione.append((schedula["inizio_lavorazione"], schedula["fine_lavorazione"]))
        asse_y_lavorazione.append(macchine.index(schedula["macchina"]))
        identificativi_commesse.append(schedula["commessa"])

    # Plot delle barre dei setup
    for i in range(len(asse_x_setup)):
        plt.barh(y=asse_y_setup[i], width=asse_x_setup[i][1] - asse_x_setup[i][0], left=asse_x_setup[i][0], height=0.5,
                 color='red', edgecolor='black')

    # Plot delle barre di lavorazione
    for i in range(len(asse_x_lavorazione)):
        veicolo = next(
            schedula["veicolo"] for schedula in schedulazione if schedula["commessa"] == identificativi_commesse[i])
        colore = colori_veicoli[veicolo]
        plt.barh(y=asse_y_lavorazione[i], width=asse_x_lavorazione[i][1] - asse_x_lavorazione[i][0],
                 left=asse_x_lavorazione[i][0], height=0.5, color=colore, edgecolor='black')
        plt.text(x=asse_x_lavorazione[i][0] + (asse_x_lavorazione[i][1] - asse_x_lavorazione[i][0]) / 2,
                 y=asse_y_lavorazione[i], s=identificativi_commesse[i], ha='center', va='center', color='black')

    plt.yticks(range(len(macchine)), macchine)  # Per ogni macchina, mette il suo nome sull'asse y
    inizi = [schedula["inizio_setup"] for schedula in schedulazione] + [schedula["inizio_lavorazione"] for schedula in
                                                                        schedulazione]  # Lista contenente tutti gli istanti di inizio lavorazione
    fine = [schedula["fine_setup"] for schedula in schedulazione] + [schedula["fine_lavorazione"] for schedula in
                                                                     schedulazione]  # Lista contenente tutti gli istanti di fine lavorazione
    plt.xticks(ticks=inizi + fine,labels=[time.strftime('%Y-%m-%d %H:%M:%S') for time in inizi] + [time.strftime('%Y-%m-%d %H:%M:%S') for time in fine], rotation=90)
    plt.xlim(min(inizi + fine),
             max(inizi + fine))  # Imposta la lunghezza dell'asse x uguale all'istante in cui si conclude l'ultima lavorazione in modo da visualizzare correttamente il grafico
    plt.gca().set_ylim(-0.5, len(macchine) - 0.5)
    plt.gcf().autofmt_xdate()  # Serve per visualizzare meglio il grafico
    plt.xlabel('Tempo')  # Titolo asse x
    plt.ylabel('Macchina')  # Titolo asse y
    plt.title('Schedulazione')  # Titolo del grafico

    # Creazione della legenda
    handles = [mpatches.Patch(color=colore, label=f't taglio commessa associata al veicolo {veicolo}') for veicolo, colore in colori_veicoli.items()]
    handles.append(mpatches.Patch(color='red', label='t setup'))
    plt.legend(handles=handles, title="Legenda")
    plt.savefig("Dati_output\schedulazione.jpg")
    plt.show()  # Mostra il grafico

def data_partenza_veicoli(lista_commesse:list,lista_veicoli:list):
    lista_commesse.sort(key=lambda commessa:(-commessa.priorita_cliente,commessa.due_date.timestamp())) # ordino la lista sulla base della priorita e successivamente sulla due date
    for veicolo in lista_veicoli:
        lista_filtrata=[commessa for commessa in lista_commesse if veicolo.zone_coperte in commessa.zona_cliente] #lista che contiene solo le commesse ammissibili per il veicolo
        if len(lista_filtrata)>0: #se ho almeno una commessa nella lista
            data_partenza=lista_filtrata[0].due_date #calcolo la data di partenza come la data di quella più urgente
            oggi=datetime.now() #data di oggi
            if oggi>=data_partenza: #se la commessa più urgente ha una data nel passato rispetto ad oggi
                data_partenza=oggi+timedelta(days=2) #aggiungo 2 giorni alla data di oggi
            else:
                differenza=data_partenza-oggi
                if differenza.days>365:
                    data_partenza = oggi + timedelta(days=7)
            #veicolo.set_data_partenza(lista_filtrata[0].due_date) #la data di partenza del veicolo diventa la due date delle commessa più ravvicinata della zona
            veicolo.set_data_partenza(data_partenza) #la data di partenza del veicolo diventa la due date delle commessa più ravvicinata della zona


def Euristico1(lista_macchine: list, lista_commesse: list, lista_veicoli:list):
    data_partenza_veicoli(lista_commesse,lista_veicoli)
    lista_commesse.sort(key=lambda commessa:(-commessa.priorita_cliente,commessa.due_date.timestamp())) # ordino la lista sulla base della priorita
    f_obj = 0  # funzione obiettivo (somma pesata dei tempi di setup)
    schedulazione = []  # è una lista che conterrà tutte le schedulazioni
    lista_macchine = sorted(lista_macchine, key=lambda macchina: macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i)  # inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_commesse_non_schedulate = []
    for commessa in lista_commesse:
        for commessa_non_schedulata in lista_commesse_non_schedulate:
            macchina_schedula, veicolo_selezionato, tempo_setup, tempo_processamento, tempo_minimo_completamento,minuti_inizio_lavorazione = trova_macchina_setup_minimo(commessa_non_schedulata, lista_macchine, lista_veicoli ,inizio_schedulazione)
            if macchina_schedula!=None and veicolo_selezionato!=None:
                f_obj += tempo_setup
                aggiorna_schedulazione1(commessa_non_schedulata, macchina_schedula,tempo_setup, tempo_processamento, inizio_schedulazione, schedulazione,minuti_inizio_lavorazione)
                # macchina_schedula.numero_tubi_utilizzati+=1
                lista_commesse_non_schedulate.remove(commessa_non_schedulata)
        macchina_schedula,veicolo_selezionato,tempo_setup,tempo_processamento,tempo_minimo_completamento,minuti_inizio_lavorazione=trova_macchina_setup_minimo_obbligo_lavorazione(commessa, lista_macchine, lista_veicoli ,inizio_schedulazione)
        if macchina_schedula!=None and veicolo_selezionato!=None:
            f_obj+=tempo_setup
            aggiorna_schedulazione1(commessa,macchina_schedula,tempo_setup,tempo_processamento,inizio_schedulazione,schedulazione,minuti_inizio_lavorazione)
            #macchina_schedula.numero_tubi_utilizzati+=1
        else:
            lista_commesse_non_schedulate.append(commessa)
    # ordina le commesse non schedulate per release date
    for commessa_non_schedulata in lista_commesse_non_schedulate:
        macchina_schedula, veicolo_selezionato,tempo_setup, tempo_processamento, tempo_minimo_completamento, minuti_inizio_lavorazione = trova_macchina_setup_minimo(commessa_non_schedulata, lista_macchine, lista_veicoli ,inizio_schedulazione)
        if macchina_schedula!= None and veicolo_selezionato!=None:
            f_obj+=tempo_setup
            aggiorna_schedulazione1(commessa_non_schedulata, macchina_schedula, tempo_setup, tempo_processamento,inizio_schedulazione, schedulazione,minuti_inizio_lavorazione)
            #macchina_schedula.numero_tubi_utilizzati+=1
            lista_commesse_non_schedulate.remove(commessa_non_schedulata)
    return schedulazione,f_obj

def trova_macchina_setup_minimo(commessa: Commessa, lista_macchine:list, lista_veicoli:list, inizio_schedulazione):
    macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
    tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
    tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
    tempo_minimo_processamento = math.inf
    veicolo_selezionato=None
    minuti_inizio=None
    for macchina in lista_macchine:  # cerco tra le macchine
        if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1 and commessa._minuti_release_date<=macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
            tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
            tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
            tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
            tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
            data_fine_lavorazione=aggiungi_minuti(tempo_fine_lavorazione,inizio_schedulazione)
            veicoli_feasible=[veicolo for veicolo in lista_veicoli if (veicolo.zone_coperte in commessa.zona_cliente and veicolo.disponibilita==1)]
            for veicolo in veicoli_feasible:
                if data_fine_lavorazione<=veicolo.data_partenza and veicolo.capacita>=commessa.kg_da_tagliare:
                    if tempo_setup < tempo_minimo_setup: #data_fine_lavorazione<=commessa.due:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                        minuti_inizio=tempo_inizio_taglio
                        tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                        tempo_minimo_setup = tempo_setup
                        tempo_minimo_processamento = tempo_processamento
                        veicolo_selezionato=veicolo
                        macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
    if macchina_schedula!= None and veicolo_selezionato!=None:
        commessa.veicolo=veicolo_selezionato.nome
        veicolo_selezionato.capacita-=commessa.kg_da_tagliare
        return macchina_schedula, veicolo_selezionato,tempo_minimo_setup, tempo_minimo_processamento, tempo_minimo_completamento, minuti_inizio
    else:
        return None, None, 0, 0, 0 , None

def trova_macchina_setup_minimo_obbligo_lavorazione(commessa: Commessa, lista_macchine:list, lista_veicoli:list, inizio_schedulazione):
    macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
    tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
    tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
    tempo_minimo_processamento = math.inf
    veicolo_selezionato=None
    minuti_inizio=None
    for macchina in lista_macchine:  # cerco tra le macchine
        if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1: # and commessa._minuti_release_date<=macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
            tempo_inizio_taglio = max(macchina._minuti_fine_ultima_lavorazione,commessa._minuti_release_date)
            tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
            tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
            tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
            data_fine_lavorazione=aggiungi_minuti(tempo_fine_lavorazione,inizio_schedulazione)
            veicoli_feasible=[veicolo for veicolo in lista_veicoli if (veicolo.zone_coperte in commessa.zona_cliente and veicolo.disponibilita==1)]
            for veicolo in veicoli_feasible:
                if data_fine_lavorazione<=veicolo.data_partenza and veicolo.capacita>=commessa.kg_da_tagliare:
                    if tempo_setup < tempo_minimo_setup: #data_fine_lavorazione<=commessa.due:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                        minuti_inizio=tempo_inizio_taglio
                        tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                        tempo_minimo_setup = tempo_setup
                        tempo_minimo_processamento = tempo_processamento
                        veicolo_selezionato=veicolo
                        macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
    if macchina_schedula!= None and veicolo_selezionato!=None:
        commessa.veicolo=veicolo_selezionato.nome
        veicolo_selezionato.capacita-=commessa.kg_da_tagliare
        return macchina_schedula, veicolo_selezionato,tempo_minimo_setup, tempo_minimo_processamento, tempo_minimo_completamento, minuti_inizio
    else:
        return None, None, 0, 0, 0, None

def aggiorna_schedulazione1(commessa: Commessa ,macchina: Macchina, tempo_setup, tempo_processamento, inizio_schedulazione ,schedulazione: list, minuti_inizio_lavorazione):
    schedulazione.append({"commessa": commessa.id_commessa,
                          "macchina": macchina.nome_macchina,
                          "minuti setup": tempo_setup,
                          "minuti processamento":tempo_processamento,
                          "inizio_setup": aggiungi_minuti(minuti_inizio_lavorazione,inizio_schedulazione),
                          "fine_setup": aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup,inizio_schedulazione),
                          "inizio_lavorazione": aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup,inizio_schedulazione),
                          "fine_lavorazione": aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup + tempo_processamento,inizio_schedulazione),
                          "mt da tagliare": commessa.metri_da_tagliare,
                          "taglio": commessa.tipologia_taglio,
                          "macchine compatibili": [machine for machine, value in commessa.compatibilita.items() if value == 1],
                          "nr coltelli": commessa.numero_coltelli,
                          "diametro_tubo": commessa.diametro_tubo,
                          "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula

    macchina._minuti_fine_ultima_lavorazione = minuti_inizio_lavorazione+tempo_setup+tempo_processamento
    macchina.lista_commesse_processate.append(commessa)  # aggiungo la commessa alla macchina che eseguirà la lavorazione

def filtro_commesse(lista_commesse:list,lista_veicoli):
    data_partenza_veicoli(lista_commesse,lista_veicoli)
    lista_veicoli_disponibili = [veicolo for veicolo in lista_veicoli if veicolo.disponibilita == 1]  # lista che contiene i veicoli disponibili (veicoli filtrati per disponibilità)
    zone_aperte = set([veicolo.zone_coperte for veicolo in lista_veicoli_disponibili])  # set contenete tutte le zone aperte (una lista può contenere duplicati, mentre un set ha elementi unici)
    commesse_da_tagliare = []
    for commessa in lista_commesse:
        intersezione = set(commessa.zona_cliente).intersection(zone_aperte)  # calcolo l'intersezione tra l'insieme delle zone della commessa e le zone aperte
        if intersezione:  # se l'intersezione contiene elementi (è diversa dall'insieme vuoto)
            commesse_da_tagliare.append(commessa)  # aggiungo alla lista la commessa
    commesse_da_schedulare=[]
    for commessa in commesse_da_tagliare:
        for veicolo in lista_veicoli_disponibili:
            if veicolo.zone_coperte in commessa.zona_cliente and commessa.due_date<=veicolo.data_partenza:
                commesse_da_schedulare.append(commessa)
    #print(len(lista_commesse),len(commesse_da_schedulare))
    return commesse_da_schedulare

def Euristico2(lista_commesse:list, lista_macchine:list, lista_veicoli:list):
    data_partenza_veicoli(lista_commesse, lista_veicoli)
    lista_commesse.sort(key=lambda commessa:(commessa.due_date.timestamp(),-commessa.priorita_cliente)) # ordino la lista sulla base della priorita
    f_obj = 0  # funzione obiettivo (somma pesata dei tempi di setup)
    schedulazione = []  # è una lista che conterrà tutte le schedulazioni
    #lista_macchine = sorted(lista_macchine, key=lambda macchina: macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i)  # inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine
    while len(lista_commesse)>0 and len(lista_macchine)>0:
        schedulazione_eseguita=False
        lista_macchine=sorted(lista_macchine,key=lambda macchina: macchina._minuti_fine_ultima_lavorazione)
        macchina=lista_macchine[0]
        commessa_selezionata, veicolo_selezionato, tempo_setup, tempo_processamento, tempo_minimo_completamento, minuti_inizio_lavorazione= trova_commessa_tempo_setup_minimo(macchina,lista_commesse,lista_veicoli,inizio_schedulazione)
        if commessa_selezionata!=None and veicolo_selezionato!=None:
            f_obj+=tempo_setup
            #macchina.minuti_processamenti.append(macchina._minuti_fine_ultima_lavorazione)
            aggiorna_schedulazione1(commessa_selezionata,macchina,tempo_setup,tempo_processamento,inizio_schedulazione,schedulazione,minuti_inizio_lavorazione)
            lista_commesse.remove(commessa_selezionata)
            #macchina.minuti_processamenti.append(macchina._minuti_fine_ultima_lavorazione)
            schedulazione_eseguita=True
        if not schedulazione_eseguita:
            #print(f'elimino macchina {macchina.nome_macchina}')
            lista_macchine.remove(macchina)
    return schedulazione,f_obj

def trova_commessa_tempo_setup_minimo(macchina: Macchina, lista_commesse:list, lista_veicoli:list, inizio_schedulazione):
    commessa_selezionata = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
    tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
    tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
    tempo_minimo_processamento = math.inf
    veicolo_selezionato = None
    minuti_inizio = None
    for commessa in lista_commesse:
        if macchina.disponibilita == 1 and commessa.compatibilita[macchina.nome_macchina] == 1 and commessa._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:
            tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
            tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
            tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
            tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
            data_fine_lavorazione = aggiungi_minuti(tempo_fine_lavorazione, inizio_schedulazione)
            veicoli_feasible = [veicolo for veicolo in lista_veicoli if (veicolo.zone_coperte in commessa.zona_cliente and veicolo.disponibilita == 1)]
            for veicolo in veicoli_feasible:
                if data_fine_lavorazione <= veicolo.data_partenza and veicolo.capacita >= commessa.kg_da_tagliare:
                    if tempo_setup < tempo_minimo_setup:
                        minuti_inizio = tempo_inizio_taglio
                        tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                        tempo_minimo_setup = tempo_setup
                        tempo_minimo_processamento = tempo_processamento
                        veicolo_selezionato = veicolo
                        commessa_selezionata = commessa
    if commessa_selezionata != None and veicolo_selezionato != None:
        commessa_selezionata.veicolo = veicolo_selezionato.nome
        veicolo_selezionato.capacita -= commessa_selezionata.kg_da_tagliare
        return commessa_selezionata, veicolo_selezionato, tempo_minimo_setup, tempo_minimo_processamento, tempo_minimo_completamento, minuti_inizio
    else:
        return None, None, 0, 0, 0, None

def swap(lista_macchine: list, lista_veicoli:list, f_obj,schedulazione: list):
    """
    :param lista_macchine: lista contenente oggetti macchina
    :param lista_veicoli: lista contenente oggetti veicolo
    :param f_obj: funzione obiettivo ottenuta con l'euristico greedy
    :param schedulazione: schedulazione ottenuta con l'euristico greedy
    :return: schedulazione ottenuta applicando ricerca locale swap intra macchina
    """
    partenze = {veicolo.nome: veicolo.data_partenza for veicolo in lista_veicoli} #dizionario in cui ad ogni veicolo viene associata la sua data di partenza
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione #data in cui inizia la schedulazione
    f_best = f_obj #funzione obiettivo
    eps = 0.00001 #parametro per stabilire se il delta è conveniente
    soluzione_swap=[] #lista contenente tutte le schedule
    for macchina in lista_macchine: #per ogni macchina
        print(macchina.nome_macchina)
        macchina_schedula=[s for s in schedulazione if s['macchina']==macchina.nome_macchina] #vado a prendere tutte le schedule ad essa associate
        schedula=deepcopy(macchina.lista_commesse_processate) #copia profonda della lista di commesse schedulate
        print(schedula)
        #ultima_lavorazione=macchina.ultima_lavorazione #copia del parametro che indica i minuti a partire dai quali una macchina è disponibile
        improved = True #variabile booleana che indica se è stato trovato un miglioramento
        if len(schedula)>=3: #se ho sufficienti elementi nella lista per effettuare uno swap
            while improved: #finchè trovo miglioramenti continuo
                improved=False #imposto subito la variabile boolena a False, così se non trovo miglioramenti esco dal ciclo
                #scorro tutte le possibili coppie i,j di commesse schedulate sulla macchina evitando coppie con elementi identici
                for i in range(1,len(schedula)-1):
                    for j in range(i+1,len(schedula)):
                        #for vvv in schedula:
                            #print(vvv.id_commessa)
                        ultima_lavorazione = macchina.ultima_lavorazione #imposto la variabile al tempo in cui la macchina diventa disponibile per la prima volta
                        veicolo_i = schedula[i].veicolo #prendo il veicolo associato alla commessa i
                        veicolo_j = schedula[j].veicolo #prendo il veicolo associato alla commessa j
                        #effettuo il calcolo del delta
                        #print(i,j)
                        if i+1<j and j+1<len(schedula): #commesse non consecutive con j non in ultima posizione
                            #print('if1')
                            delta=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i+1])+\
                                  macchina.calcolo_tempi_setup(schedula[j-1],schedula[i])+macchina.calcolo_tempi_setup(schedula[i],schedula[j+1])+ \
                                  -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[i+1])+ \
                                  -macchina.calcolo_tempi_setup(schedula[j-1],schedula[j])-macchina.calcolo_tempi_setup(schedula[j],schedula[j+1])

                        if i+1==j and j+1<len(schedula): #commesse consecutive con j non in ultima posizione
                            #print('if2')
                            delta=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i])+\
                                  macchina.calcolo_tempi_setup(schedula[i],schedula[j+1])-macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])+\
                                  -macchina.calcolo_tempi_setup(schedula[i],schedula[j])-macchina.calcolo_tempi_setup(schedula[j],schedula[j+1])

                        if i+1<j and j+1==len(schedula): #commesse non consecutive con j in ultima posizione
                            #print('if3')
                            delta=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i+1])+\
                                  macchina.calcolo_tempi_setup(schedula[j-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[j-1],schedula[j])+\
                                  -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[i+1])

                        if i+1==j and j+1==len(schedula): #commesse consecutive con j in ultima posizione
                            #print('if4')
                            delta=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i])+\
                                  -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[j])

                        #print(delta)
                        if delta<-eps: #se la swap è migliorativo
                            s=[] #imposto nuova schedula inizialmente vuota
                            comm_i=schedula[i] #commessa i
                            comm_j=schedula[j] #commessa j
                            #eseguo temporaneamente lo swap
                            schedula[i]=schedula[j]
                            schedula[j]=comm_i
                            for k in range(1,len(schedula)): #vado a ricostruire la soluzione e la schedula
                                tempo_setup_commessa=macchina.calcolo_tempi_setup(schedula[k-1],schedula[k])
                                tempo_processamento_commessa=schedula[k].metri_da_tagliare/macchina.velocita_taglio_media
                                return_schedulazione(schedula[k],macchina,tempo_setup_commessa,tempo_processamento_commessa,ultima_lavorazione,inizio_schedulazione,s)
                                ultima_lavorazione=ultima_lavorazione+tempo_setup_commessa+tempo_processamento_commessa
                            if partenze[veicolo_i]>=s[j-1]['fine_lavorazione'] and partenze[veicolo_j]>=s[i-1]['fine_lavorazione']: #faccio il check sulle date di partenza dei veicoli
                                #print(veicolo_i,s[j-1]['commessa'],' ',veicolo_j,s[i-1]['commessa'])
                            #if partenze[veicolo_i]>=s[j]['fine_lavorazione'] and partenze[veicolo_j]>=s[i]['fine_lavorazione']: #faccio il check sulle date di partenza dei veicoli
                                #print(veicolo_i,s[j]['commessa'],' ',veicolo_j,s[i]['commessa'])
                                improved=True #miglioramento trovato
                                f_best+=delta #aggiorno funzione obiettivo
                                print(f'scambio {schedula[i].id_commessa} con {schedula[j].id_commessa} con delta={delta} su {macchina.nome_macchina}')
                                macchina_schedula=s #aggiorno le schedule associate alla macchina
                                #for vvv in schedula:
                                    #print(vvv.id_commessa)
                                #break
                            else:
                                print('scambio non feasible')
                                #se lo swap non è ammissibile torno indietro annullando lo scambio
                                schedula[i]=comm_i
                                schedula[j]=comm_j
                        if improved:
                            break
                    if improved:
                        break
                #if improved:
                    #break
            soluzione_swap.append(macchina_schedula) #aggiungo la schedula della macchina alla lista delle schedule
        else:
            soluzione_swap.append(macchina_schedula) #aggiungo la schedula della macchina alla lista delle schedule
    return soluzione_swap,f_best

def return_schedulazione(commessa: Commessa, macchina:Macchina, minuti_setup, minuti_processamento, minuti_fine_ultima_commessa, inizio_schedulazione, schedulazione):
    id=commessa.id_commessa
    macchina_lavorazione=macchina.nome_macchina
    tempo_setup=minuti_setup
    tempo_processamento=minuti_processamento
    data_inizio_setup=aggiungi_minuti(minuti_fine_ultima_commessa,inizio_schedulazione)
    data_fine_setup=aggiungi_minuti(minuti_fine_ultima_commessa+minuti_setup,inizio_schedulazione)
    data_inizio_lavorazione=aggiungi_minuti(minuti_fine_ultima_commessa+minuti_setup,inizio_schedulazione)
    data_fine_lavorazione=aggiungi_minuti(minuti_fine_ultima_commessa+minuti_setup+minuti_processamento,inizio_schedulazione)
    metri_da_tagliare=commessa.metri_da_tagliare
    tipo_taglio=commessa.tipologia_taglio
    macchine_compatibili=[machine for machine, value in commessa.compatibilita.items() if value == 1]
    n_coltelli=commessa.numero_coltelli
    d_tubo=commessa.diametro_tubo
    camion=commessa.veicolo
    schedulazione.append({"commessa": id,
                          "macchina": macchina_lavorazione,
                          "minuti setup": tempo_setup,
                          "minuti processamento":tempo_processamento,
                          "inizio_setup": data_inizio_setup,
                          "fine_setup": data_fine_setup,
                          "inizio_lavorazione": data_inizio_lavorazione,
                          "fine_lavorazione": data_fine_lavorazione,
                          "mt da tagliare": metri_da_tagliare,
                          "taglio": tipo_taglio,
                          "macchine compatibili": macchine_compatibili,
                          "nr coltelli": n_coltelli,
                          "diametro_tubo": d_tubo,
                          "veicolo": camion})
