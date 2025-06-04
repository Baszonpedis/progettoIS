import math
import pandas as pd
from veicolo import Veicolo
from datetime import timedelta
import matplotlib.pyplot as plt
from matplotlib.text import Annotation
from commessa import Commessa
from macchina import Macchina
from copy import deepcopy

##FUNZIONI FONDAMENTALI
#Aggiunge un certo numero di minuti ad una certa data
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

#Associa ad ogni commessa tassativa il proprio veicolo tassativo
def associa_veicoli_tassativi(lista_commesse_tassative, commesse_da_schedulare, lista_veicoli):
    lista_veicoli_errati = []
    commesse_veicoli_errati = {}
    mappa_veicoli = {veicolo.nome: veicolo for veicolo in lista_veicoli} #dizionario oggetti 'veicolo'
    for commessa in lista_commesse_tassative: #ciclo for per assegnazione dei veicoli alle commesse tassative tramite corrispondenza id_tassativo e dizionario mappa_veicoli
        if commessa.id_tassativo in mappa_veicoli:
            commessa.veicolo = mappa_veicoli[commessa.id_tassativo]
        else: #se l'id tassativo punta ad un veicolo fuori dalla mappa veicolo (e dunque furoi dall'estrazione)
            if 0 in commessa.zona_cliente: #veicoli fuori dall'estrazione esterni (comportamento corretto)
                veicolo_non_in_estrazione = Veicolo(str(int(commessa.id_tassativo))+" (esterno)", 0, None, None)
                print(f'Il veicolo {veicolo_non_in_estrazione.nome} non è in estrazione! Aggiunto alla lista')
                lista_veicoli.append(veicolo_non_in_estrazione)
                commessa.veicolo = veicolo_non_in_estrazione
            else: #veicoli fuori dall'estrazione interni (comportamento scorretto)
                veicolo_non_in_estrazione = Veicolo(str(int(commessa.id_tassativo))+" (non in estrazione)", 0, None, None)
                print(f'Il veicolo {veicolo_non_in_estrazione.nome} non è in estrazione! Rimuovo commesse associate')
                #lista_veicoli.append(veicolo_non_in_estrazione)
                commesse_da_schedulare.remove(commessa) #tolgo la commessa dalle schedulande
                commesse_veicoli_errati[commessa.id_commessa] = "Il veicolo associato alla commessa dovrebbe essere in estrazione, ma non c'è" #aggiungo la commessa ad un dizionario da assorbire con gli altri dizionari di errore
                lista_veicoli_errati.append(veicolo_non_in_estrazione) #lista per dataframe per la creazione di un file di errore
    df_errati = pd.DataFrame([{
        'nome': v.nome,
        'peso': v.capacita,
        'zone': v.zone_coperte,
        'partenza': v.data_partenza
    } for v in lista_veicoli_errati])
    return(df_errati, lista_commesse_tassative, commesse_da_schedulare, commesse_veicoli_errati)

#Aggiorna la schedulazione nell'euristico dopo ogni assegnazione
#NB: Funzione modificata con l'inclusione del concetto di ritardo
def aggiorna_schedulazione(commessa: Commessa, macchina: Macchina, tempo_setup, tempo_processamento, inizio_schedulazione, schedulazione: list, minuti_inizio_lavorazione, tipo):
    fine_lavorazione = aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup + tempo_processamento,inizio_schedulazione)
    veicolo = commessa.veicolo
    if commessa.tassativita == "X":
        if 0 in commessa.zona_cliente: #commesse esterne tassative
            commessa.ritardo = min(commessa.due_date - fine_lavorazione, timedelta(days = 0))
        else: #commesse interne tassative correttamente inserite in estrazione
            commessa.ritardo = min(veicolo.data_partenza - fine_lavorazione, timedelta(days = 0))
    elif commessa.veicolo != None: #commesse interne zona aperta
        commessa.ritardo = min(max(veicolo.data_partenza,commessa.due_date) - fine_lavorazione, timedelta(days = 0))
    else: #commesse rimanenti (senza veicolo assegnato / gruppo 3)
        commessa.ritardo = min(commessa.due_date - fine_lavorazione, timedelta(days = 0)) 
        #commessa.ritardo = timedelta(days = 0) #se non si considera il loro ritardo
    schedulazione.append({"commessa": commessa.id_commessa, # dizionario che contiene le informazioni sulla schedula
                          "macchina": macchina.nome_macchina,
                          "minuti setup": tempo_setup,
                          "minuti processamento":tempo_processamento,
                          "inizio_setup": aggiungi_minuti(minuti_inizio_lavorazione,inizio_schedulazione),
                          "fine_setup": aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup,inizio_schedulazione),
                          "inizio_lavorazione": aggiungi_minuti(minuti_inizio_lavorazione + tempo_setup,inizio_schedulazione),
                          "fine_lavorazione": fine_lavorazione,
                          "mt da tagliare": commessa.metri_da_tagliare,
                          "taglio": commessa.tipologia_taglio,
                          "macchine compatibili": [machine for machine, value in commessa.compatibilita.items() if value == 1],
                          "nr coltelli": commessa.numero_coltelli,
                          "diametro_tubo": commessa.diametro_tubo,
                          "veicolo": commessa.veicolo,
                          "tassativita": commessa.tassativita,
                          "id_tassativo": commessa.id_tassativo,
                          "due date": commessa.due_date,
                          "ritardo": commessa.ritardo,
                          "priorita": commessa.priorita_cliente})
    macchina._minuti_fine_ultima_lavorazione = minuti_inizio_lavorazione+tempo_setup+tempo_processamento
    if tipo == 0:
        macchina.lista_commesse_processate.append(commessa)  # aggiungo la commessa alla macchina che eseguirà la lavorazione

#Filtra tutte le commesse lette correttamente in base alle zone aperte ed alle partenze dei veicoli
def filtro_commesse(lista_commesse:list,lista_veicoli):
    #lista_veicoli_disponibili = [veicolo for veicolo in lista_veicoli] #if veicolo.disponibilita == 1]  # lista che contiene i veicoli disponibili (veicoli filtrati per disponibilità)
    zone_aperte = set([veicolo.zone_coperte for veicolo in lista_veicoli])  # set contenente tutte le zone aperte (una lista può contenere duplicati, mentre un set ha elementi unici)
    commesse_da_tagliare = [] #commesse assegnabili in base alle zone
    commesse_da_schedulare = [] #commesse assegnabili in base ai veicoli
    commesse_esterne_non_tassative = [] 
    #commesse_oltre_data = {} #commesse da tagliare non schedulate perché oltre data partenza massima veicolo; formato dizionario per unirlo al resto
    
    for commessa in lista_commesse:
        intersezione = set(commessa.zona_cliente).intersection(zone_aperte)  # calcolo l'intersezione tra l'insieme delle zone della commessa e le zone aperte
        if commessa.tassativita == "X": #or 0 in commessa.zona_cliente:"
            commesse_da_schedulare.append(commessa)
        elif 0 in commessa.zona_cliente:
            commesse_esterne_non_tassative.append(commessa)
        elif intersezione:  # se l'intersezione contiene elementi (è diversa dall'insieme vuoto)
            commesse_da_tagliare.append(commessa)  # aggiungo alla lista la commessa
    for commessa in commesse_da_tagliare:
        for veicolo in lista_veicoli:
            #if veicolo.zone_coperte in commessa.zona_cliente and commessa.due_date>=veicolo.data_partenza:#commessa.due_date<=veicolo.data_partenza:
            if veicolo.zone_coperte in commessa.zona_cliente and commessa.release_date<veicolo.data_partenza:#commessa.due_date<=veicolo.data_partenza:
                commesse_da_schedulare.append(commessa)
                break
    
    #liste per tenere traccia delle commesse scartate da reinserire solo sulle macchine (anche se non schedulabili sui veicoli)
    commesse_zona_chiusa = [c for c in lista_commesse if c not in commesse_da_tagliare and 0 not in c.zona_cliente and c.tassativita != "X"]
    commesse_veicolo_incompatibile = [c for c in commesse_da_tagliare if c not in commesse_da_schedulare]
    commesse_scartate = commesse_zona_chiusa + commesse_veicolo_incompatibile + commesse_esterne_non_tassative

    #dizionari per tenere traccia dei filtraggi e relativi ragioni
    dizionario_filtri = {
        **{commessa.id_commessa: f"La commessa non può essere schedulata in quanto le sue zone {commessa.zona_cliente} non corrispondono alle zone aperte {zone_aperte}" 
        for commessa in commesse_zona_chiusa},
        **{commessa.id_commessa: "La commessa non può essere schedulata in quanto il veicolo non è compatibile"
        for commessa in commesse_veicolo_incompatibile},
        **{commessa.id_commessa: "La commessa non può essere schedulata in quanto è esterna ma non tassativa"
        for commessa in commesse_esterne_non_tassative}
    }
    return commesse_da_schedulare, dizionario_filtri, commesse_scartate

#Serve a ricostruire le soluzioni nelle ricerche locali
#NB: Funzione modificata introducento il concetto di ritardo e ritardomossa
def return_schedulazione(commessa: Commessa, macchina:Macchina, minuti_setup, minuti_processamento, minuti_fine_ultima_commessa, inizio_schedulazione, schedulazione, tipo):
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
    veicolo=commessa.veicolo
    tassativita=commessa.tassativita
    id_tassativo=commessa.id_tassativo
    due_date=commessa.due_date
    ritardo=commessa.ritardo
    veicolo = commessa.veicolo

    #A seguito, si differenzia tra i vari tipi di commesse (in ordine: tassative esterne, tassative interne corrette, tassative interne scorrette, interne zona aperta, altre)
    #Questo a fine di calcolare il "ritardomossa" - ovvero il ritardo associato alla mossa nella soluzione ricostruita
    if commessa.tassativita == "X": #tassative
        if 0 in commessa.zona_cliente: #tassative esterne
            ritardomossa = min(commessa.due_date - data_fine_lavorazione, timedelta(days = 0))
        else: #tassative interne corrette
            ritardomossa = min(veicolo.data_partenza - data_fine_lavorazione, timedelta(days = 0))
    elif veicolo != None: #interne zona aperta
        ritardomossa = min(max(veicolo.data_partenza,commessa.due_date) - data_fine_lavorazione, timedelta(days = 0))
    else: #altre (serve se la funzione dovesse essere mai chiamata anche su commesse solo su macchina, del gruppo 3)
        ritardomossa = min(commessa.due_date - data_fine_lavorazione, timedelta(days = 0))
        #ritardomossa = timedelta(days = 0)
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
                          "veicolo": veicolo,
                          "tassativita": tassativita,
                          "id_tassativo": id_tassativo,
                          "due date": due_date,
                          "ritardo": ritardo,
                          "ritardo mossa": ritardomossa,
                          "priorita": commessa.priorita_cliente})

##EURISTICO COSTRUTTIVO (Greedy)
def euristico_costruttivo(commesse_da_schedulare:list, lista_macchine:list, lista_veicoli:list):

    #INIZIALIZZAZIONI
    causa_fallimento={} #Dizionario con formato "commessa_fallita:motivo"
    lista_commesse_tassative = [c for c in commesse_da_schedulare if c.tassativita == "X"] #Commesse tassative interne ed esterne (i.e. veicolo predeterminato e obbligato)
    commesse_da_schedulare = [c for c in commesse_da_schedulare if c not in lista_commesse_tassative]  #Commesse da schedulare non tassative (i.e.commesse schedulabili su veicolo, ergo filtrate, ma non tassative)
    f_obj = 0  #Funzione obiettivo (somma pesata dei tempi di setup)
    f_obj_ritardo = timedelta(days = 0) #Funzione obiettivo ritardi
    schedulazione = []  #Lista di dizionari (le singole schedulazioni)

    #Inizializzazione macchine
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i)  # inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_macchine2 = []

    #Sorting preliminare al primo ciclo while
    lista_commesse_tassative.sort(key=lambda commessa:(-commessa.priorita_cliente,commessa.due_date.timestamp())) # ordino la lista sulla base della priorita e successivamente della due date

    #PRIMO CICLO WHILE
    #Si assegnano per prime tutte le commesse tassative alle macchine (l'assegnazione al veicolo è fatta dalla funzione apposita)
    while len(lista_commesse_tassative)>0 and len(lista_macchine)>0:
        schedulazione_eseguita=False
        lista_macchine=sorted(lista_macchine,key=lambda macchina: macchina._minuti_fine_ultima_lavorazione)
        macchina=lista_macchine[0]
        for commessa in lista_commesse_tassative:
            if macchina.disponibilita == 1 and commessa.compatibilita[macchina.nome_macchina] == 1 and commessa._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:
                tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
                tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                data_fine_lavorazione = aggiungi_minuti(tempo_fine_lavorazione, inizio_schedulazione)
                schedulazione_eseguita=True
                f_obj+=tempo_setup
                #commessa.veicolo = int(commessa.id_tassativo) #da fare prima dell'aggiornamento
                aggiorna_schedulazione(commessa,macchina,tempo_setup,tempo_processamento,inizio_schedulazione,schedulazione,macchina._minuti_fine_ultima_lavorazione,0)
                f_obj_ritardo+=commessa.ritardo  
                lista_commesse_tassative.remove(commessa)
            if schedulazione_eseguita:
                #print(f'La commessa {commessa.id_commessa} è associata al veicolo {commessa.veicolo} //////////')
                break
        if not schedulazione_eseguita:
            lista_macchine2.append(macchina)
            lista_macchine.remove(macchina)

    #Si ricostituisce la lista delle macchine per il prossimo ciclo  
    lista_macchine = set(lista_macchine2+lista_macchine)
    list(lista_macchine)
    lista_macchine2 = []

    #Sorting preliminare dell'input al secondo ciclo While
    commesse_da_schedulare.sort(key=lambda commessa:(-commessa.priorita_cliente,commessa.due_date.timestamp())) # ordino la lista sulla base della priorita e successivamente della due date

    #SECONDO CICLO WHILE
    #Provo a inserire tutte le commesse interne a zona aperta (su macchine e veicoli)
    while len(commesse_da_schedulare)>0 and len(lista_macchine)>0:
        schedulazione_eseguita=False
        lista_macchine=sorted(lista_macchine,key=lambda macchina: macchina._minuti_fine_ultima_lavorazione)
        macchina=lista_macchine[0]
        for commessa in commesse_da_schedulare:
            if macchina.disponibilita == 1 and commessa.compatibilita[macchina.nome_macchina] == 1 and commessa._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:
                veicoli_feasible = [veicolo for veicolo in lista_veicoli if (veicolo.zone_coperte in commessa.zona_cliente)]
                for veicolo in veicoli_feasible:
                    if data_fine_lavorazione <= veicolo.data_partenza and veicolo.capacita >= commessa.kg_da_tagliare:
                        tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
                        tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                        tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                        tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                        data_fine_lavorazione = aggiungi_minuti(tempo_fine_lavorazione, inizio_schedulazione)
                        commessa.veicolo=veicolo
                        veicolo.capacita-=commessa.kg_da_tagliare
                        schedulazione_eseguita=True
                        f_obj+=tempo_setup
                        aggiorna_schedulazione(commessa,macchina,tempo_setup,tempo_processamento,inizio_schedulazione,schedulazione,macchina._minuti_fine_ultima_lavorazione,0)
                        commesse_da_schedulare.remove(commessa)
                    elif veicolo.capacita < commessa.kg_da_tagliare:
                        causa_fallimento[commessa.id_commessa] = (
                        f'La commessa è troppo grande per il veicolo {veicolo.nome}'
                        )
                    elif veicolo.data_partenza < data_fine_lavorazione:
                        causa_fallimento[commessa.id_commessa] = (
                        f'La commessa non viene schedulata in quanto la lavorazione non finisce in tempo per la partenza veicolo {veicolo.nome}'
                        )
            if schedulazione_eseguita:
                f_obj_ritardo+=commessa.ritardo
                causa_fallimento.pop(commessa.id_commessa, None) #rimuovo la commessa da quelle non schedulate; potrebbe succedere che alcune non siano schedulate subito ma in seguito sì
                break
        if not schedulazione_eseguita:
            lista_macchine2.append(macchina)
            lista_macchine.remove(macchina)

    commesse_residue = [c for c in commesse_da_schedulare]

    #Si ricostituisce la lista delle macchine per future chiamate
    lista_macchine = set(lista_macchine2+lista_macchine)
    lista_macchine = list(lista_macchine)
    ritardo_cumul = timedelta(days = 0)
    return schedulazione, f_obj, causa_fallimento, lista_macchine, commesse_residue, f_obj_ritardo

##EURISTICO POST (Greedy 2)
def euristico_post(soluzione, commesse_residue:list, lista_macchine:list, commesse_scartate: list, f_obj_base, f_obj_ritardo):
    
    commesse_da_schedulare = commesse_residue + commesse_scartate #Tutte quelle non schedulate per vari motivi nel secondo ciclo + le scartate dal filtro

    f_obj = f_obj_base  #Funzione obiettivo (somma pesata dei tempi di setup)
    fpost_ritardo = f_obj_ritardo
    soluzionepost = soluzione #si parte con la schedulazione già effettuata (euristico + ricerche locali)
    lista_macchine2 = []

    #Sorting preliminare dell'input al terzo ciclo While
    commesse_da_schedulare.sort(key=lambda commessa:(-commessa.priorita_cliente,commessa.due_date.timestamp())) # ordino la lista sulla base della priorita e successivamente della due date
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine

    #TERZO CICLO WHILE
    #Inserisco solo sulle macchine tutte le commesse mancanti (Interne zona chiusa, Esterne non tassative)
    while len(commesse_da_schedulare)>0 and len(lista_macchine)>0:
        schedulazione_eseguita=False
        lista_macchine=sorted(lista_macchine,key=lambda macchina: macchina._minuti_fine_ultima_lavorazione)
        macchina=lista_macchine[0]
        for commessa in commesse_da_schedulare:
            if macchina.disponibilita == 1 and commessa.compatibilita[macchina.nome_macchina] == 1 and commessa._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:
                #tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
                tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                #tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                #data_fine_lavorazione = aggiungi_minuti(tempo_fine_lavorazione, inizio_schedulazione)
                schedulazione_eseguita=True
                f_obj+=tempo_setup
                aggiorna_schedulazione(commessa,macchina,tempo_setup,tempo_processamento,inizio_schedulazione,soluzionepost,macchina._minuti_fine_ultima_lavorazione,0)
                fpost_ritardo+=commessa.ritardo
                commesse_da_schedulare.remove(commessa)
            if schedulazione_eseguita:
                break
        if not schedulazione_eseguita:
            lista_macchine2.append(macchina)
            lista_macchine.remove(macchina)

    #Si ricostituisce la lista delle macchine per future chiamate
    lista_macchine = set(lista_macchine2+lista_macchine)
    lista_macchine = list(lista_macchine)

    return soluzionepost, f_obj, fpost_ritardo

##INSERT INTER-MACCHINA (Ricerca locale 1)
def insert_inter_macchina(lista_macchine: list, lista_veicoli:list, f_obj):
    #for m in lista_macchine:
    #    seen = set()
    #    for c in m.lista_commesse_processate:
    #        if c.id_commessa in seen:
    #            print(f"[DUPLICATE in machine {m.nome_macchina}]: {c.id_commessa}")
    #        seen.add(c.id_commessa)
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # data in cui inizia la schedulazione
    f_best = f_obj  # funzione obiettivo
    soluzione_move = []  # lista contenente tutte le schedule
    contatoreLS1=0 # contatore mosse insert
    ritardo_totale_ore = timedelta(days = 0)
    for m1 in range(len(lista_macchine)):
        for m2 in range(len(lista_macchine)):
            #print(lista_macchine[m1].nome_macchina,len(lista_macchine[m1].lista_commesse_processate))
            #print(lista_macchine[m2].nome_macchina,len(lista_macchine[m2].lista_commesse_processate))
            if m1!=m2 and len(lista_macchine[m1].lista_commesse_processate)>2 and len(lista_macchine[m2].lista_commesse_processate)>2:
                schedula1,schedula2,f_best,contatoreLS1=insert_inter_macchina_utility(lista_macchine[m1],lista_macchine[m2],contatoreLS1,inizio_schedulazione,f_best)
                lista_macchine[m1].lista_commesse_processate = schedula1
                lista_macchine[m2].lista_commesse_processate = schedula2
    for m in lista_macchine:
        if len(m.lista_commesse_processate)>1:
            ultima_lavorazione=m.ultima_lavorazione
            for pos in range(1,len(m.lista_commesse_processate)):
                tempo_setup_commessa=m.calcolo_tempi_setup(m.lista_commesse_processate[pos-1],m.lista_commesse_processate[pos])
                tempo_processamento_commessa=m.lista_commesse_processate[pos].metri_da_tagliare/m.velocita_taglio_media
                #ritardo_totale_ore += int(m.lista_commesse_processate[pos].ritardo.total_seconds() / 3600)
                aggiorna_schedulazione(m.lista_commesse_processate[pos], m, tempo_setup_commessa, tempo_processamento_commessa, inizio_schedulazione, soluzione_move, ultima_lavorazione,1)
                ultima_lavorazione = ultima_lavorazione + tempo_setup_commessa + tempo_processamento_commessa
                #print(f'In posizione {pos} sulla macchina {m.nome_macchina} si ha la commessa {m.lista_commesse_processate[pos].id_commessa}, che aggiunge un ritardo di ben {int(m.lista_commesse_processate[pos].ritardo.total_seconds() / 3600)}')
    ritardo_cumul = timedelta(days = 0)
    for commessa in soluzione_move:
        ritardo_cumul += commessa['ritardo']
        print(ritardo_cumul)
    #print(ritardo_cumul)
    return soluzione_move,f_best,contatoreLS1,ritardo_cumul

#Usato da insert_inter_macchina (Ricerca locale 1 - utility)
def insert_inter_macchina_utility(macchina1:Macchina,macchina2:Macchina,contatore:int,inizio_schedulazione,f_best):
    #for i in macchina1.lista_commesse_processate:
    #    print(i.id_commessa)
    schedula1=macchina1.lista_commesse_processate #copia profonda della lista di commesse schedulate
    schedula2=macchina2.lista_commesse_processate #copia profonda della lista di commesse schedulate
    eps = 0.00001  # parametro per stabilire se il delta è conveniente
    improved=False
    risparmio_tot = 0
    for i in range(1, len(schedula1)):
        for j in range(1, len(schedula2)):
            commessa = schedula1[i]
            #commessa2 = schedula2[j]
            #if commessa.tassativita != "X" and commessa2.tassativita != "X"
            if commessa.compatibilita[macchina2.nome_macchina]==1:
                posizione = j
                ultima_lavorazione1=macchina1.ultima_lavorazione
                ultima_lavorazione2=macchina2.ultima_lavorazione
                delta_setup = math.inf

                if i+1<len(schedula1) and j+1<len(schedula2):
                    delta_setup=-macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i])-macchina1.calcolo_tempi_setup(schedula1[i],schedula1[i+1])+\
                        -macchina2.calcolo_tempi_setup(schedula2[j-1],schedula2[j])+\
                        +macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i+1])+\
                        +macchina2.calcolo_tempi_setup(schedula2[j-1],schedula1[i])+macchina2.calcolo_tempi_setup(schedula1[i],schedula2[j])

                if i+1==len(schedula1) and j+1<len(schedula2):
                    delta_setup=-macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i])+\
                        -macchina2.calcolo_tempi_setup(schedula2[j-1],schedula2[j])+\
                        +macchina2.calcolo_tempi_setup(schedula2[j-1],schedula1[i])+macchina2.calcolo_tempi_setup(schedula1[i],schedula2[j])

                if i+1==len(schedula1) and j+1==len(schedula2):
                    delta_setup=-macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i])+ \
                        +macchina2.calcolo_tempi_setup(schedula2[j],schedula1[i])

                if i+1<len(schedula1) and j+1==len(schedula2):
                    delta_setup=-macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i])-macchina1.calcolo_tempi_setup(schedula1[i],schedula1[i+1])+\
                        +macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i+1])+\
                        +macchina2.calcolo_tempi_setup(schedula2[j],schedula1[i])

                #Inizializzazioni
                delta_ritardo = 0
                s1=[]
                s2=[]
                copia1 = schedula1.copy()
                copia2 = schedula2.copy()

                #Effettuo l'insert
                #ids = [c.id_commessa for c in schedula1]
                #if ids.count(commessa.id_commessa) > 1:
                #    print(f"[!!!] DUPLICATE commessa {commessa.id_commessa} in schedula1 before removal!")
                schedula1.remove(commessa)
                if j+1==len(schedula2):
                    schedula2.append(commessa)
                else:
                    schedula2.insert(posizione,commessa)

                #Inizializzazioni
                delta_ritardo = timedelta(days=0)

                #Calcoli post-insert
                for k in range(1, len(schedula1)): #ricostruisco soluzione (da schedula ad s)
                    tempo_setup_commessa=macchina1.calcolo_tempi_setup(schedula1[k-1],schedula1[k])
                    tempo_processamento_commessa=schedula1[k].metri_da_tagliare/macchina1.velocita_taglio_media
                    return_schedulazione(schedula1[k],macchina1,tempo_setup_commessa,tempo_processamento_commessa,ultima_lavorazione1,inizio_schedulazione,s1,0) #ricostruzione 1
                    ultima_lavorazione1=ultima_lavorazione1+tempo_setup_commessa+tempo_processamento_commessa
                    #check1 = check_LS(check1, s1[-1], schedula1[k]) #check validità schedula 1

                for k in range(1, len(schedula2)):  # vado a ricostruire la soluzione e la schedula
                    tempo_setup_commessa=macchina2.calcolo_tempi_setup(schedula2[k - 1], schedula2[k]) #ricostruzione 2
                    tempo_processamento_commessa = schedula2[k].metri_da_tagliare / macchina2.velocita_taglio_media
                    return_schedulazione(schedula2[k], macchina2, tempo_setup_commessa,tempo_processamento_commessa, ultima_lavorazione2, inizio_schedulazione,s2,0)
                    #print(f'la commessa {schedula2[k].id_commessa} ha ritardo {schedula2[k].ritardo}')
                    ultima_lavorazione2=ultima_lavorazione2+tempo_setup_commessa+tempo_processamento_commessa
                    #check2 = check_LS(check2, s2[-1], schedula2[k]) #check validità schedula 2

                for entry in s1:
                    new_h = entry['ritardo mossa'].total_seconds()/3600
                    old_h = entry['ritardo'].total_seconds()/3600
                    delta_ritardo += timedelta(hours=(-new_h +old_h))
                for entry in s2:
                    new_h = entry['ritardo mossa'].total_seconds()/3600
                    old_h = entry['ritardo'].total_seconds()/3600
                    delta_ritardo += timedelta(hours=(-new_h +old_h))

                ##CONDIZIONE DI MIGLIORAMENTO
                delta = math.inf
                delta = calcolo_delta(delta_setup,delta_ritardo) #calcolo della funzione obiettivo della ricerca locale
                if delta < -eps:
                    print(f' AYO, {delta_ritardo}')
                    for entry in s1:
                        new_t = entry['ritardo mossa']
                        old_t = entry['ritardo']
                        pri   = entry['priorita']
                        #risparmio_tot += (old_t.total_seconds()/3600 - new_t.total_seconds()/3600) / pri
                        entry['ritardo'] = entry['ritardo mossa']
                        for commessa in schedula1:
                            if commessa.id_commessa == entry['commessa']:
                                commessa.ritardo = entry['ritardo']
                    for entry in s2:
                        new_t = entry['ritardo mossa']
                        old_t = entry['ritardo']
                        pri   = entry['priorita']
                        entry['ritardo'] = entry['ritardo mossa']
                        #risparmio_tot += (old_t.total_seconds()/3600 - new_t.total_seconds()/3600) / pri
                        for commessa in schedula2:
                            if commessa.id_commessa == entry['commessa']:
                                commessa.ritardo = entry['ritardo']
                                #print(f"aggiornamento ritardo: la commessa {commessa.id_commessa} = {entry['commessa']} ha ora ritardo {entry['ritardo']}")
                    #for k in range(1,len(schedula2)):
                        #print(f'la commessa {schedula2[k].id_commessa} ha ritardo {schedula2[k].ritardo}')
                    improved=True #miglioramento trovato
                    f_best+=delta_setup #aggiorno funzione obiettivo
                    contatore+=1
                else: #se l'insert non è reputato migliorativo in termini di f.o.
                    schedula1=copia1
                    schedula2=copia2
            if improved:
                break
        if improved:
            break
    #risparmio_tot = 0
    return schedula1, schedula2, f_best,contatore

##INSERT INTRA-MACCHINA (Ricerca locale 2)
def insert_intra(lista_macchine: list, lista_veicoli: list, f_obj, schedulazione: list):
    """
    :param lista_macchine: lista contenente oggetti macchina
    :param lista_veicoli: lista contenente oggetti veicolo
    :param f_obj: funzione obiettivo ottenuta con l'euristico greedy
    :param schedulazione: schedulazione ottenuta con l'euristico greedy
    :return: schedulazione ottenuta applicando ricerca locale insert intra macchina
    """
    # INIZIALIZZAZIONI
    contatoreLS2 = 0  # contatore mosse eseguite
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # data in cui inizia la schedulazione
    f_best = f_obj  # funzione obiettivo (dei setup)
    eps = 0.00001  # parametro per stabilire se il delta è conveniente
    soluzione_move = []  # lista contenente tutte le schedule

    # Funzione di supporto per calcolare il setup totale di una sequenza di job
    def total_setup(seq, macchina_obj):
        tot = 0.0
        for kk in range(1, len(seq)):
            tot += macchina_obj.calcolo_tempi_setup(seq[kk - 1], seq[kk])
        return tot

    # CICLO PRINCIPALE
    for macchina in lista_macchine:
        macchina_schedula = [s for s in schedulazione if s['macchina'] == macchina.nome_macchina]
        schedula_original = macchina.lista_commesse_processate
        schedula = deepcopy(schedula_original)
        improved = True

        if len(schedula) >= 3:
            while improved:
                improved = False
                # calcolo una volta per tutta la configurazione corrente il setup totale
                setup_corrente = total_setup(schedula, macchina)

                for i in range(1, len(schedula)):
                    if improved:
                        break
                    for j in range(1, len(schedula)):
                        if i == j:
                            continue

                        # CALCOLO delta_setup ricostruendo la sequenza
                        candidate_seq = schedula[:]
                        comm_i = candidate_seq.pop(i)
                        if j > i:
                            candidate_seq.insert(j - 1, comm_i)
                        else:
                            candidate_seq.insert(j, comm_i)

                        new_setup = total_setup(candidate_seq, macchina)
                        delta_setup = new_setup - setup_corrente

                        # Calcolo delta_ritardo mantenendo il tuo approccio originale
                        delta_ritardo = timedelta(days=0)
                        s = []
                        ultima_lavorazione = macchina.ultima_lavorazione

                        # Ricostruisco soluzione per calcolare i ritardi di “candidate_seq”
                        for k in range(1, len(candidate_seq)):
                            tempo_setup_commessa = macchina.calcolo_tempi_setup(candidate_seq[k - 1], candidate_seq[k])
                            tempo_processamento_commessa = candidate_seq[k].metri_da_tagliare / macchina.velocita_taglio_media
                            return_schedulazione(
                                candidate_seq[k],
                                macchina,
                                tempo_setup_commessa,
                                tempo_processamento_commessa,
                                ultima_lavorazione,
                                inizio_schedulazione,
                                s,
                                0
                            )
                            ultima_lavorazione += tempo_setup_commessa + tempo_processamento_commessa

                        for k in range(1, len(s)):
                            delta_ritardo += (-s[k]['ritardo mossa'] + s[k]['ritardo']) / s[k]['priorita']

                        # CONDIZIONE DI MIGLIORAMENTO
                        delta = calcolo_delta(delta_setup, delta_ritardo)
                        if delta < -eps:
                            # Accetto la mossa: aggiorno i ritardi nella soluzione “s”
                            for k in range(1, len(s)):
                                s[k]['ritardo'] = s[k]['ritardo mossa']

                            f_best += delta_setup
                            macchina_schedula = s[:]
                            contatoreLS2 += 1
                            # aggiornamento di schedula e uscita dai cicli
                            schedula = candidate_seq
                            improved = True
                            break
                        else:
                            # mossa non migliorativa: nessun cambiamento su "schedula"
                            pass

                    if improved:
                        break
                if improved:
                    break
            soluzione_move.append(macchina_schedula)
        else:
            soluzione_move.append(macchina_schedula)

    ritardo_totale_ore = timedelta(days=0)
    for macchina_schedula in soluzione_move:
        for commessa in macchina_schedula:
            ritardo_totale_ore += commessa['ritardo']

    return soluzione_move, f_best, contatoreLS2, ritardo_totale_ore

##SWAP INTRA-MACCHINA (Ricerca locale 3)
def swap_intra(lista_macchine: list, lista_veicoli:list, f_obj,schedulazione: list):
    """
    :param lista_macchine: lista contenente oggetti macchina
    :param lista_veicoli: lista contenente oggetti veicolo
    :param f_obj: funzione obiettivo ottenuta con l'euristico greedy
    :param schedulazione: schedulazione ottenuta con l'euristico greedy
    :return: schedulazione ottenuta applicando ricerca locale swap intra macchina
    """
    contatoreLS3=0 #numero di swap eseguiti
    partenze = {veicolo.nome: veicolo.data_partenza for veicolo in lista_veicoli} #dizionario in cui ad ogni veicolo viene associata la sua data di partenza
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione #data in cui inizia la schedulazione
    f_best = f_obj #funzione obiettivo
    eps = 0.00001 #parametro per stabilire se il delta è conveniente
    soluzione_swap=[] #lista contenente tutte le schedule
    #risparmio_tot = timedelta(days = 0)

    for macchina in lista_macchine: #per ogni macchina
        macchina_schedula=[s for s in schedulazione if s['macchina']==macchina.nome_macchina] #vado a prendere tutte le schedule ad essa associate
        schedula_original=macchina.lista_commesse_processate
        schedula = deepcopy(schedula_original)
        improved = True #variabile booleana che indica se è stato trovato un miglioramento
        if len(schedula)>=3: #se ho sufficienti elementi nella lista per effettuare uno swap
            while improved: #finchè trovo miglioramenti continuo
                improved=False #imposto subito la variabile boolena a False, così se non trovo miglioramenti esco dal ciclo
                #scorro tutte le possibili coppie i,j di commesse schedulate sulla macchina evitando coppie con elementi identici
                for i in range(1,len(schedula)-1):
                    for j in range(i+1,len(schedula)):
                        delta_setup = math.inf
                        ultima_lavorazione = macchina.ultima_lavorazione #imposto la variabile al tempo in cui la macchina diventa disponibile per la prima volta
                        if i+1<j and j+1<len(schedula): #commesse non consecutive con j non in ultima posizione
                            delta_setup=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i+1])+\
                                  macchina.calcolo_tempi_setup(schedula[j-1],schedula[i])+macchina.calcolo_tempi_setup(schedula[i],schedula[j+1])+ \
                                  -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[i+1])+ \
                                  -macchina.calcolo_tempi_setup(schedula[j-1],schedula[j])-macchina.calcolo_tempi_setup(schedula[j],schedula[j+1])

                        if i+1==j and j+1<len(schedula): #commesse consecutive con j non in ultima posizione
                            delta_setup=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i])+\
                                  macchina.calcolo_tempi_setup(schedula[i],schedula[j+1])-macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])+\
                                  -macchina.calcolo_tempi_setup(schedula[i],schedula[j])-macchina.calcolo_tempi_setup(schedula[j],schedula[j+1])

                        if i+1<j and j+1==len(schedula): #commesse non consecutive con j in ultima posizione
                            #print('if3')
                            delta_setup=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i+1])+\
                                  macchina.calcolo_tempi_setup(schedula[j-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[j-1],schedula[j])+\
                                  -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[i+1])

                        if i+1==j and j+1==len(schedula): #commesse consecutive con j in ultima posizione
                            #print('if4')
                            delta_setup=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i])+\
                                  -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[j])
                        
                        #Inizializzazioni
                        delta_ritardo = timedelta(days = 0)
                        s=[] #imposto nuova schedula inizialmente vuota
                        comm_i=schedula[i] #commessa i
                        comm_j=schedula[j] #commessa j
    
                        #Eseguo temporaneamente lo swap
                        schedula[i]=schedula[j]
                        schedula[j]=comm_i

                        #Calcoli post-swap
                        for k in range(1, len(schedula)): #ricostruisco soluzione (da schedula ad s)
                            tempo_setup_commessa = macchina.calcolo_tempi_setup(schedula[k - 1], schedula[k])
                            tempo_processamento_commessa = schedula[k].metri_da_tagliare / macchina.velocita_taglio_media
                            return_schedulazione(schedula[k], macchina, tempo_setup_commessa, tempo_processamento_commessa, ultima_lavorazione, inizio_schedulazione, s,0)
                            ultima_lavorazione += tempo_setup_commessa + tempo_processamento_commessa
                        for k in range(1,len(s)): #calcolo il ritardo totale della mossa
                            delta_ritardo += (-s[k]['ritardo mossa']  +(s[k]['ritardo'])) / s[k]['priorita']
    
                        ##CONDIZIONE DI MIGLIORAMENTO
                        delta = math.inf
                        delta = calcolo_delta(delta_setup,delta_ritardo) #calcolo della funzione obiettivo della ricerca locale
                        if delta < -eps:
                            print(f'ritardo {delta_ritardo}, setup {delta_setup}, delta {delta}, commessa {schedula[i].id_commessa}, priorita {schedula[i].priorita_cliente}')
                            for k in range(1,len(s)): #aggiorno i ritardi per la soluzione ricostruita
                                #risparmio_tot += (s[k]['ritardo'] - s[k]['ritardo mossa'])
                                s[k]['ritardo'] = s[k]['ritardo mossa']
                                #schedula[k].ritardo = s[k]['ritardo']
                            f_best+=delta_setup #aggiorno funzione obiettivo (dei setup)
                            #macchina.lista_commesse_processate = schedula
                            macchina_schedula=s #aggiorno le schedule associate alla macchina
                            contatoreLS3+=1
                            improved = True  
                        else:
                            #se lo swap non è ammissibile torno indietro annullando lo scambio
                            schedula=schedula_original
                    if improved:
                        break
                if improved:
                    break
            soluzione_swap.append(macchina_schedula) #aggiungo la schedula della macchina alla lista delle schedule
        else:
            soluzione_swap.append(macchina_schedula) #aggiungo la schedula della macchina alla lista delle schedule
    ritardo_totale_ore = timedelta(days = 0)
    for macchina_schedula in soluzione_swap:
        for commessa in macchina_schedula:
            ritardo_ore = (commessa['ritardo'])
            ritardo_totale_ore += ritardo_ore
    return soluzione_swap,f_best, contatoreLS3, ritardo_totale_ore

#Nuova funzione utility per fare i check di validità nelle varie ricerche locali
def check_LS(check, commessa1, commessa):
    if commessa.tassativita == "X": #tassative
        if 0 in commessa.zona_cliente: #tassative esterne
            if commessa1["inizio_lavorazione"] < commessa.release_date:
                check = False
            if commessa.ritardo > commessa1["ritardo mossa"]:
                check = False
        else: #tassative interne
            if commessa1["inizio_lavorazione"] < commessa.release_date:
                check = False
            if commessa.ritardo > commessa1["ritardo mossa"]:
                check = False
    else: #non tassative
        if commessa1["inizio_lavorazione"] < commessa.release_date:
            check = False
        if commessa.ritardo > commessa1["ritardo mossa"]:
            check = False
    #print(f'tassative: {counter_tass}, tassative interne: {counter_tass_int}, tassative esterne: {counter_tass_ext}, altre: {counter_aliud}')
    return check

#def calcolo_delta_ritardo(schedula):
#    if schedula.ritardomossa is not None:
#        for k in range(1,len(schedula)):
#            delta_ritardo = (schedula[k].ritardomossa - schedula[k].ritardo)//schedula[k].priorita
#            delta_ritardo_non_pesato = (schedula[k].ritardomossa - schedula[k].ritardo)
#    else:
#        for k in range(1,len(schedula)):
#            delta_ritardo = (schedula[k].ritardo)//schedula[k].priorita
#            delta_ritardo_non_pesato = (schedula[k].ritardomossa - schedula[k].ritardo)
#    return delta_ritardo, delta_ritardo_non_pesato

def calcolo_delta(delta_setup,delta_ritardo):
    alfa = 1 #parametro variante tra zero ed uno; zero minimizza i ritardi (proporzionalmente a priorità cliente), uno minimizza i setup
    delta_ritardo = delta_ritardo.total_seconds()/3600
    delta = alfa*delta_setup+(1-alfa)*delta_ritardo
    return delta
        
#GRAFICAZIONE
#import mplcursors
def grafico_schedulazione(schedulazione):
    """
    :param schedulazione: lista di dizionari che contiene le informazioni relative ad una schedulazione
    :return: plot del grafico relativo alla schedulazione
    """
    macchine = list(set(s["macchina"] for s in schedulazione))
    macchine.sort(reverse=True)

    veicoli = list(set(s["veicolo"] for s in schedulazione))
    green_shades = ['#006400']
    colori_veicoli = {}
    green_index = 0
    for veicolo in veicoli:
        colori_veicoli[veicolo] = '#d9b904' if veicolo is None else green_shades[green_index % len(green_shades)]
        if veicolo is not None:
            green_index += 1

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = []
    schedula_by_bar = {}

    inizi = [s["inizio_setup"] for s in schedulazione] + [s["inizio_lavorazione"] for s in schedulazione]
    fine = [s["fine_setup"] for s in schedulazione] + [s["fine_lavorazione"] for s in schedulazione]
    inizio_timeline = min(inizi)
    fine_timeline = max(fine)

    intervalli_non_produzione = [] #Tutti i giorni dalle 15.00 alle 7.00 + weekend
    current_time = inizio_timeline.replace(hour=0, minute=0, second=0, microsecond=0)
    while current_time < fine_timeline:
        weekday = current_time.weekday()

        if weekday == 4:  # Venerdì
            # Unica fascia di non produzione: 15:00 venerdì → 07:00 lunedì
            weekend_start = current_time + timedelta(hours=15)
            weekend_end = (current_time + timedelta(days=3)).replace(hour=7)

            start = max(weekend_start, inizio_timeline)
            end = min(weekend_end, fine_timeline)

            if start < end:
                intervalli_non_produzione.append((start, end))
                ax.axvspan(start, end, color='dimgray', alpha=0.4, label='Weekend')

            current_time += timedelta(days=3)  # Salta sabato e domenica
        else:
            # Fasce classiche 15:00 → 07:00 del giorno dopo
            np_start = current_time + timedelta(hours=15)
            np_end = (current_time + timedelta(days=1)).replace(hour=7)

            start = max(np_start, inizio_timeline)
            end = min(np_end, fine_timeline)

            if start < end:
                intervalli_non_produzione.append((start, end))
                ax.axvspan(start, end, color='gray', alpha=0.3)

            current_time += timedelta(days=1)

    def calcola_durata_netto(start, end, blocchi_np):
        durata = timedelta(0)
        cursor = start
        while cursor < end:
            prossimo_stop = end
            for np_start, np_end in blocchi_np:
                if cursor < np_start < end:
                    prossimo_stop = min(prossimo_stop, np_start)
                elif np_start <= cursor < np_end:
                    cursor = np_end
                    break
            else:
                durata += prossimo_stop - cursor
                cursor = prossimo_stop
        return durata

    for s in schedulazione:
        y = macchine.index(s["macchina"])

        # Setup
        setup_durata = s["fine_setup"] - s["inizio_setup"]
        setup_bar = ax.barh(y, setup_durata, left=s["inizio_setup"], height=0.5, color='red', edgecolor='black')[0]
        bars.append(setup_bar)
        schedula_by_bar[setup_bar] = {
            'type': 'setup',
            'data': s,
            'durata_netto': calcola_durata_netto(s["inizio_setup"], s["fine_setup"], intervalli_non_produzione)
        }

        # Lavorazione
        colore = colori_veicoli[s["veicolo"]]
        lav_durata = s["fine_lavorazione"] - s["inizio_lavorazione"]
        lav_bar = ax.barh(y, lav_durata, left=s["inizio_lavorazione"], height=0.5, color=colore, edgecolor='black')[0]
        bars.append(lav_bar)
        schedula_by_bar[lav_bar] = {
            'type': 'lavorazione',
            'data': s
        }

    ax.set_yticks(range(len(macchine)))
    ax.set_yticklabels(macchine)
    ax.set_xlim(inizio_timeline, fine_timeline)
    ax.set_ylim(-0.5, len(macchine) - 0.5)
    fig.autofmt_xdate()
    ax.set_xlabel('Tempo')
    ax.set_ylabel('Macchina')
    ax.set_title('Schedulazione')

    tooltip = Annotation('', xy=(0, 0), xytext=(15, 15), textcoords='offset points',
                         bbox=dict(boxstyle="round", fc="w", ec="k"),
                         arrowprops=dict(arrowstyle="->"))
    tooltip.set_visible(False)
    ax.add_artist(tooltip)

    def on_motion(event):
        visibile = False
        for bar in bars:
            contains, _ = bar.contains(event)
            if contains:
                info = schedula_by_bar[bar]
                s = info['data']
                tooltip.xy = (event.xdata, event.ydata)
                if info['type'] == 'setup':
                    testo = f"TEMPO DI SETUP\nCommessa: {s['commessa']}\nDurata utile: {info['durata_netto']}"
                else:
                    veicolo = s["veicolo"]
                    nome_veicolo = veicolo.nome if veicolo is not None else "Senza veicolo"
                    testo = f"Commessa: {s['commessa']}\nVeicolo: {nome_veicolo}"
                tooltip.set_text(testo)
                tooltip.set_visible(True)
                visibile = True
                break
        if not visibile:
            tooltip.set_visible(False)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_motion)

    plt.tight_layout()
    plt.show()