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
        else: #se l'id tassativo punta ad un veicolo fuori dalla mappa veicolo (e dunque fuori dall'estrazione)
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
    f_obj_ritardo_pesato = timedelta(days = 0) #Idem ma con ritardi pesati
    schedulazione = []  #Lista di dizionari (le singole schedulazioni)

    #Inizializzazione macchine
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i)  # inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_macchine2 = lista_macchine.copy()

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
                f_obj_ritardo_pesato+=commessa.ritardo/commessa.priorita_cliente
                lista_commesse_tassative.remove(commessa)
            if schedulazione_eseguita:
                #print(f'La commessa {commessa.id_commessa} è associata al veicolo {commessa.veicolo} //////////')
                break
        if not schedulazione_eseguita:
            lista_macchine.remove(macchina)

    #Si ricostituisce la lista delle macchine per il prossimo ciclo  
    lista_macchine = lista_macchine2.copy()

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
                    tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
                    tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                    tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                    tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                    data_fine_lavorazione = aggiungi_minuti(tempo_fine_lavorazione, inizio_schedulazione)
                    if data_fine_lavorazione <= veicolo.data_partenza and veicolo.capacita >= commessa.kg_da_tagliare:
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
                f_obj_ritardo_pesato+=commessa.ritardo/commessa.priorita_cliente
                causa_fallimento.pop(commessa.id_commessa, None) #rimuovo la commessa da quelle non schedulate; potrebbe succedere che alcune non siano schedulate subito ma in seguito sì
                break
        if not schedulazione_eseguita:
            lista_macchine.remove(macchina)

    commesse_residue = [c for c in commesse_da_schedulare]

    #Si ricostituisce la lista delle macchine per future chiamate
    lista_macchine = lista_macchine2.copy()

    #for i in lista_macchine:
    #    print(i.nome_macchina)
    #    for j in i.lista_commesse_processate:
    #        print(j.id_commessa)
    
    #for i in schedulazione:
    #    print(i['commessa'],i['macchina'])

    return schedulazione, f_obj, causa_fallimento, lista_macchine, commesse_residue, f_obj_ritardo, f_obj_ritardo_pesato

##EURISTICO POST (Greedy 2)
def euristico_post(soluzione, commesse_residue:list, lista_macchine:list, commesse_scartate: list, f_obj_base, f_obj_ritardo, f_obj_ritardo_pesato):
    
    commesse_da_schedulare = commesse_residue + commesse_scartate #Tutte quelle non schedulate per vari motivi nel secondo ciclo + le scartate dal filtro

    f_obj = f_obj_base  #Funzione obiettivo (somma pesata dei tempi di setup)
    fpost_ritardo = f_obj_ritardo
    fpost_ritardo_pesato = f_obj_ritardo_pesato
    soluzionepost = soluzione #si parte con la schedulazione già effettuata (euristico + ricerche locali)
    lista_macchine2 = lista_macchine.copy()

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
                fpost_ritardo_pesato+=commessa.ritardo/commessa.priorita_cliente
                commesse_da_schedulare.remove(commessa)
            if schedulazione_eseguita:
                break
        if not schedulazione_eseguita:
            lista_macchine.remove(macchina)

    #for i in lista_macchine:
    #    print(i.nome_macchina)
    #    for j in i.lista_commesse_processate:
    #        print(j.id_commessa)

    #Si ricostituisce la lista delle macchine per future chiamate
    lista_macchine = lista_macchine2.copy()

    #for i in lista_macchine:
    #    print(i.nome_macchina)
    #    for j in i.lista_commesse_processate:
    #        print(j.id_commessa)
    return soluzionepost, f_obj, fpost_ritardo, fpost_ritardo_pesato

##INSERT INTER-MACCHINA (Ricerca locale 1)
def insert_inter_macchina(lista_macchine: list, f_obj):
    #for m in lista_macchine:
    #    seen = set()
    #    for c in m.lista_commesse_processate:
    #        if c.id_commessa in seen:
    #            print(f"[DUPLICATE in machine {m.nome_macchina}]: {c.id_commessa}")
    #        seen.add(c.id_commessa)
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # data in cui inizia la schedulazione
    f_best = f_obj  # funzione obiettivo
    schedulazione = []  # lista contenente tutte le schedule
    contatoreLS1=0 # contatore mosse insert
    #ritardo_totale_ore = timedelta(days = 0)
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
                aggiorna_schedulazione(m.lista_commesse_processate[pos], m, tempo_setup_commessa, tempo_processamento_commessa, inizio_schedulazione, schedulazione, ultima_lavorazione,1)
                ultima_lavorazione = ultima_lavorazione + tempo_setup_commessa + tempo_processamento_commessa
                #print(f'In posizione {pos} sulla macchina {m.nome_macchina} si ha la commessa {m.lista_commesse_processate[pos].id_commessa}, che aggiunge un ritardo di ben {int(m.lista_commesse_processate[pos].ritardo.total_seconds() / 3600)}')
    ritardo_cumul = timedelta(days = 0)
    ritardo_cumul_pesato = timedelta(days = 0)
    for commessa in schedulazione:
        ritardo_cumul += commessa['ritardo']
        ritardo_cumul_pesato += commessa['ritardo'] / commessa['priorita']
        #print(ritardo_cumul)
    print(f'Ritardo cumulativo: {-ritardo_cumul}')

    #for i in lista_macchine:
    #    print(i.nome_macchina)
    #    for j in i.lista_commesse_processate:
    #        print(j.id_commessa)
    
    #for i in schedulazione:
    #    print(i['commessa'],i['macchina'])

    return schedulazione,f_best,contatoreLS1,ritardo_cumul,ritardo_cumul_pesato

#Usato da insert_inter_macchina (Ricerca locale 1 - utility)
def insert_inter_macchina_utility(macchina1:Macchina,macchina2:Macchina,contatore:int,inizio_schedulazione,f_best):
    #for i in macchina1.lista_commesse_processate:
    #    print(i.id_commessa)
    schedula1=macchina1.lista_commesse_processate #copia della lista di commesse schedulate
    schedula2=macchina2.lista_commesse_processate #copia della lista di commesse schedulate
    eps = 0.00001  # parametro per stabilire se il delta è conveniente
    improved=False
    #risparmio_tot = 0
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
                delta_ritardo_print = timedelta(days = 0)
                s1=[]
                s2=[]
                copia1 = deepcopy(schedula1)
                copia2 = deepcopy(schedula2)
                check1 = True
                check2 = True

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
                    check1 = check_LS(check1, s1[-1], schedula1[k]) #check validità schedula 1

                for k in range(1, len(schedula2)):  # vado a ricostruire la soluzione e la schedula
                    tempo_setup_commessa=macchina2.calcolo_tempi_setup(schedula2[k - 1], schedula2[k]) #ricostruzione 2
                    tempo_processamento_commessa = schedula2[k].metri_da_tagliare / macchina2.velocita_taglio_media
                    return_schedulazione(schedula2[k], macchina2, tempo_setup_commessa,tempo_processamento_commessa, ultima_lavorazione2, inizio_schedulazione,s2,0)
                    #print(f'la commessa {schedula2[k].id_commessa} ha ritardo {schedula2[k].ritardo}')
                    ultima_lavorazione2=ultima_lavorazione2+tempo_setup_commessa+tempo_processamento_commessa
                    check2 = check_LS(check2, s2[-1], schedula2[k]) #check validità schedula 2

                for entry in s1:
                    new_h = entry['ritardo mossa'].total_seconds()/3600
                    old_h = entry['ritardo'].total_seconds()/3600
                    delta_ritardo += timedelta(hours=(-new_h +old_h)) / entry['priorita']
                    delta_ritardo_print+= timedelta(hours=(-new_h +old_h))
                for entry in s2:
                    new_h = entry['ritardo mossa'].total_seconds()/3600
                    old_h = entry['ritardo'].total_seconds()/3600
                    delta_ritardo += timedelta(hours=(-new_h +old_h)) / entry['priorita']
                    delta_ritardo_print+= timedelta(hours=(-new_h +old_h))

                ##CONDIZIONE DI MIGLIORAMENTO
                delta = math.inf
                delta = calcolo_delta(delta_setup,delta_ritardo) #calcolo della funzione obiettivo della ricerca locale
                if delta < -eps and check1 and check2:
                    #print(f'\n---------------------------')
                    #print(f'Macchine: {macchina1.nome_macchina}, {macchina2.nome_macchina}; Commessa mossa: {commessa.id_commessa}')
                    #print(f'Ritardo non pesato cumulato: {delta_ritardo_print}; Ritardo pesato (delta_ritardo): {delta_ritardo}')
                    #print(f'Tempo di setup (delta_setup): {delta_setup}')
                    #print(f'Funzione risultante: alfa({delta_setup})*(1-alfa)({delta_ritardo.total_seconds()/3600})')
                    #Aggiornamento necessario pena la desincronizzazione tra lista_commesse_processate e la soluzione
                    for entry in s1:
                        for comm in macchina1.lista_commesse_processate:
                            if comm.id_commessa == entry['commessa']:
                                comm.ritardo = entry['ritardo mossa']
                    for entry in s2:
                        for comm in macchina2.lista_commesse_processate:
                            if comm.id_commessa == entry['commessa']:
                                comm.ritardo = entry['ritardo mossa']
                    #for entry in s1:
                        #new_t = entry['ritardo mossa']
                        #old_t = entry['ritardo']
                        #pri   = entry['priorita']
                        #risparmio_tot += (old_t.total_seconds()/3600 - new_t.total_seconds()/3600) / pri
                        #entry['ritardo'] = entry['ritardo mossa']
                       # for commessa in schedula1:
                      #      if commessa.id_commessa == entry['commessa']:
                     #           commessa.ritardo = entry['ritardo']
                    #for entry in s2:
                        #new_t = entry['ritardo mossa']
                        #old_t = entry['ritardo']
                        #pri   = entry['priorita']
                       # entry['ritardo'] = entry['ritardo mossa']
                        #risparmio_tot += (old_t.total_seconds()/3600 - new_t.total_seconds()/3600) / pri
                      #  for commessa in schedula2:
                     #       if commessa.id_commessa == entry['commessa']:
                    #            commessa.ritardo = entry['ritardo']
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
def insert_intra(lista_macchine: list, f_obj):
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
        schedula = macchina.lista_commesse_processate
        improved = True

        if len(schedula) >= 3:
            while improved:
                improved = False
                # Calcolo una volta per tutta la configurazione corrente il setup totale
                setup_corrente = total_setup(schedula, macchina)

                for i in range(1, len(schedula)):
                    if improved:
                        break
                    for j in range(1, len(schedula)):
                        if i == j:
                            continue

                        schedula_copy = deepcopy(schedula)
                        # Calcolo delta_setup ricostruendo la sequenza
                        comm_i = schedula.pop(i)
                        if j > i:
                            schedula.insert(j - 1, comm_i)
                        else:
                            schedula.insert(j, comm_i)

                        new_setup = total_setup(schedula, macchina)
                        delta_setup = new_setup - setup_corrente

                        # Calcolo delta_ritardo mantenendo il tuo approccio originale
                        delta_ritardo = timedelta(days=0)
                        delta_ritardo_print= timedelta(days=0)
                        s = []
                        ultima_lavorazione = macchina.ultima_lavorazione
                        check = True

                        # Ricostruisco soluzione per calcolare i ritardi di “candidate_seq”
                        for k in range(1, len(schedula)):
                            tempo_setup_commessa = macchina.calcolo_tempi_setup(schedula[k - 1], schedula[k])
                            tempo_processamento_commessa = schedula[k].metri_da_tagliare / macchina.velocita_taglio_media
                            return_schedulazione(
                                schedula[k],
                                macchina,
                                tempo_setup_commessa,
                                tempo_processamento_commessa,
                                ultima_lavorazione,
                                inizio_schedulazione,
                                s,
                                0
                            )
                            ultima_lavorazione += tempo_setup_commessa + tempo_processamento_commessa
                            check_LS(check, s[-1], schedula[k])

                        for k in range(1, len(s)):
                            delta_ritardo += (-s[k]['ritardo mossa'] + s[k]['ritardo']) / s[k]['priorita']
                            delta_ritardo_print += (-s[k]['ritardo mossa'] + s[k]['ritardo']) 

                        # CONDIZIONE DI MIGLIORAMENTO
                        delta = calcolo_delta(delta_setup, delta_ritardo)
                        if delta < -eps and check:
                            #print(f'\n---------------------------')
                            #print(f'Macchina: {macchina.nome_macchina}')
                            #print(f'Ritardo non pesato cumulato: {delta_ritardo_print}; Ritardo pesato (delta_ritardo): {delta_ritardo}')
                            #print(f'Tempo di setup (delta_setup): {delta_setup}')
                            #print(f'Funzione risultante: alfa({delta_setup})*(1-alfa)({delta_ritardo.total_seconds()/3600})')
                            f_best += delta_setup
                            contatoreLS2 += 1
                            macchina.lista_commesse_processate = schedula
                            improved = True
                            break
                        else:
                            schedula = schedula_copy
                    if improved:
                        break
                if improved:
                    break

    for m in lista_macchine:
        if len(m.lista_commesse_processate)>1:
            ultima_lavorazione=m.ultima_lavorazione
            for pos in range(1,len(m.lista_commesse_processate)):
                tempo_setup_commessa=m.calcolo_tempi_setup(m.lista_commesse_processate[pos-1],m.lista_commesse_processate[pos])
                tempo_processamento_commessa=m.lista_commesse_processate[pos].metri_da_tagliare/m.velocita_taglio_media
                #ritardo_totale_ore += int(m.lista_commesse_processate[pos].ritardo.total_seconds() / 3600)
                aggiorna_schedulazione(m.lista_commesse_processate[pos], m, tempo_setup_commessa, tempo_processamento_commessa, inizio_schedulazione, soluzione_move, ultima_lavorazione,1)
                ultima_lavorazione = ultima_lavorazione + tempo_setup_commessa + tempo_processamento_commessa

    ritardo_cumul = timedelta(days = 0)
    ritardo_cumul_pesato = timedelta(days = 0)
    for commessa in soluzione_move:
        ritardo_cumul += commessa['ritardo']
        ritardo_cumul_pesato += commessa['ritardo'] / commessa['priorita']
        #print(ritardo_cumul)
    print(f'Ritardo cumulativo: {-ritardo_cumul}')

    #for i in lista_macchine:
    #    print(i.nome_macchina)
    #    for j in i.lista_commesse_processate:
    #        print(j.id_commessa)
    
    #for i in soluzione_move:
    #    print(i['commessa'],i['macchina'])

    return soluzione_move, f_best, contatoreLS2, ritardo_cumul, ritardo_cumul_pesato

##SWAP INTRA-MACCHINA (Ricerca locale 3)
def swap_intra(lista_macchine, f_obj):
    """
    :param lista_macchine: lista contenente oggetti macchina
    :param lista_veicoli: lista contenente oggetti veicolo
    :param f_obj: funzione obiettivo ottenuta con l'euristico greedy
    :param schedulazione: schedulazione ottenuta con l'euristico greedy
    :return: schedulazione ottenuta applicando ricerca locale swap intra macchina
    """
    contatoreLS3 = 0  # numero di swap eseguiti
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione
    f_best = f_obj
    eps = 0.00001
    soluzione_swap = []

    # Funzione di supporto per calcolare il setup totale di una sequenza di job
    def total_setup(seq, macchina_obj):
        tot = 0.0
        for kk in range(1, len(seq)):
            tot += macchina_obj.calcolo_tempi_setup(seq[kk - 1], seq[kk])
        return tot

    for macchina in lista_macchine:
        #macchina_schedula = [s for s in schedulazione if s['macchina'] == macchina.nome_macchina]
        schedula_original = macchina.lista_commesse_processate
        schedula = deepcopy(schedula_original)
        improved = True

        if len(schedula) >= 3:
            while improved:
                improved = False
                #Calcolo una volta per tutta la configurazione corrente il setup totale
                setup_corrente = total_setup(schedula, macchina)

                #Scorro tutte le possibili coppie i,j di commesse schedulate sulla macchina evitando coppie identiche
                for i in range(1, len(schedula) - 1):
                    for j in range(i + 1, len(schedula)):
                        # Creo una copia candidati di "schedula" e applico lo swap
                        schedula_copy = schedula.copy()
                        schedula[i], schedula[j] = schedula[j], schedula[i]

                        # Calcolo delta_setup: differenza tra setup nuovo e setup corrente
                        new_setup = total_setup(schedula, macchina)
                        delta_setup = new_setup - setup_corrente

                        # CALCOLO delta_ritardo usando lo stesso approccio di insert
                        delta_ritardo = timedelta(days=0)
                        delta_ritardo_print = timedelta(days=0) #corrisponde al delta ritardo "vero" senza peso
                        s = []
                        ultima_lavorazione = macchina.ultima_lavorazione
                        check = True

                        # Ricostruisco soluzione per calcolare i ritardi della schedula
                        for k in range(1, len(schedula)):
                            tempo_setup_commessa = macchina.calcolo_tempi_setup(schedula[k - 1], schedula[k])
                            tempo_processamento_commessa = schedula[k].metri_da_tagliare / macchina.velocita_taglio_media
                            return_schedulazione(
                                schedula[k],
                                macchina,
                                tempo_setup_commessa,
                                tempo_processamento_commessa,
                                ultima_lavorazione,
                                inizio_schedulazione,
                                s,
                                0
                            )
                            ultima_lavorazione += tempo_setup_commessa + tempo_processamento_commessa
                            check_LS(check,s[-1],schedula[k])

                        for k in range(1, len(s)):
                            delta_ritardo += (-s[k]['ritardo mossa'] + s[k]['ritardo']) / s[k]['priorita']
                            delta_ritardo_print += (-s[k]['ritardo mossa'] + s[k]['ritardo'])

                        # CONDIZIONE DI MIGLIORAMENTO (ed eventuali aggiornamenti)
                        delta = calcolo_delta(delta_setup, delta_ritardo)
                        if delta < -eps and check:
                            #print(f'\n---------------------------')
                            #print(f'Macchina: {macchina.nome_macchina}')
                            #print(f'Ritardo non pesato cumulato: {delta_ritardo_print}; Ritardo pesato (delta_ritardo): {delta_ritardo}')
                            #print(f'Tempo di setup (delta_setup): {delta_setup}')
                            #print(f'Funzione risultante: alfa({delta_setup})*(1-alfa)({delta_ritardo.total_seconds()/3600})')
                            f_best += delta_setup
                            macchina.lista_commesse_processate = schedula
                            contatoreLS3 += 1
                            improved = True
                            break
                        else:
                            schedula = schedula_copy
                    if improved:
                        break
                if improved:
                    break
    
    for m in lista_macchine:
        if len(m.lista_commesse_processate)>1:
            ultima_lavorazione=m.ultima_lavorazione
            for pos in range(1,len(m.lista_commesse_processate)):
                tempo_setup_commessa=m.calcolo_tempi_setup(m.lista_commesse_processate[pos-1],m.lista_commesse_processate[pos])
                tempo_processamento_commessa=m.lista_commesse_processate[pos].metri_da_tagliare/m.velocita_taglio_media
                #ritardo_totale_ore += int(m.lista_commesse_processate[pos].ritardo.total_seconds() / 3600)
                aggiorna_schedulazione(m.lista_commesse_processate[pos], m, tempo_setup_commessa, tempo_processamento_commessa, inizio_schedulazione, soluzione_swap, ultima_lavorazione,1)
                ultima_lavorazione = ultima_lavorazione + tempo_setup_commessa + tempo_processamento_commessa

    ritardo_cumul = timedelta(days = 0)
    ritardo_cumul_pesato = timedelta(days = 0)
    for commessa in soluzione_swap:
        ritardo_cumul += commessa['ritardo']
        ritardo_cumul_pesato += commessa['ritardo'] / commessa['priorita']
        #print(ritardo_cumul)
    print(f'Ritardo cumulativo: {-ritardo_cumul}')

    #for i in lista_macchine:
    #    print(i.nome_macchina)
    #    for j in i.lista_commesse_processate:
    #        print(j.id_commessa)
    
    #for i in soluzione_swap:
    #    print(i['commessa'],i['macchina'])

    return soluzione_swap, f_best, contatoreLS3, ritardo_cumul, ritardo_cumul_pesato

#Funzione utility per fare i check di validità nelle varie ricerche locali
def check_LS(check, commessa1, commessa):
    '''
    commessa - commessa memorizzata come oggetto di una classe
    commessa1 - stessa commessa memorizzata come dizionario di una lista
    '''
    if commessa.tassativita == "X": #tassative
        if 0 in commessa.zona_cliente: #tassative esterne
            if commessa1["inizio_lavorazione"] < commessa.release_date:
                check = False
            if commessa.ritardo / commessa.priorita_cliente > commessa1["ritardo mossa"] / commessa1["priorita"]:
                check = False
        else: #tassative interne
            if commessa1["inizio_lavorazione"] < commessa.release_date:
                check = False
            if commessa.ritardo / commessa.priorita_cliente > commessa1["ritardo mossa"] / commessa1["priorita"]:
                check = False
    else: #non tassative
        if commessa1["inizio_lavorazione"] < commessa.release_date:
            check = False
        #if commessa.ritardo > commessa1["ritardo mossa"]:
        #    check = False
    #print(f'tassative: {counter_tass}, tassative interne: {counter_tass_int}, tassative esterne: {counter_tass_ext}, altre: {counter_aliud}')
    return check

#Funzione utility per il calcolo del delta migliorativo per le varie ricerche locali, combinando linearmente delta_ritardo (pesato e cumulativo) con delta_setup (cumulativo) in funzione del parametro alfa
def calcolo_delta(delta_setup,delta_ritardo):
    alfa = 0 #parametro variante tra zero ed uno; zero minimizza i ritardi (proporzionalmente a priorità cliente), uno minimizza i setup
    delta_ritardo = delta_ritardo.total_seconds()/3600
    delta = alfa*delta_setup+(1-alfa)*delta_ritardo
    return delta
        
#GRAFICAZIONE
#import mplcursors
"""def grafico_schedulazione(schedulazione):
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
    plt.show()"""

#Graficazione alternativa
import matplotlib.pyplot as plt
from matplotlib.text import Annotation
from datetime import timedelta
import matplotlib.colors as mcolors
import matplotlib.dates as mdates

def desatura(colore, luminanza=0.7):
    #Restituisce un grigio uniforme di luminanza specificata.
    return (luminanza, luminanza, luminanza)

def split_intervallo(inizio, fine, blocchi_np):
    segments = []
    cursor = inizio
    while cursor < fine:
        # check se siamo in NP
        in_np = next(((s,e) for (s,e) in blocchi_np if s <= cursor < e), None)
        if in_np:
            end_np = min(in_np[1], fine)
            segments.append((cursor, end_np, 'np'))
            cursor = end_np
        else:
            # trova prossimo start NP
            next_np_start = min([s for (s,e) in blocchi_np if s > cursor] + [fine])
            end_p = min(next_np_start, fine)
            segments.append((cursor, end_p, 'p'))
            cursor = end_p
    return segments

def grafico_schedulazione(schedulazione):
    macchine = list({s["macchina"] for s in schedulazione})
    macchine.sort(reverse=True)

    veicoli = list({s["veicolo"] for s in schedulazione})
    green_shades = ['#006400']
    colori_veicoli = {}
    gi = 0
    for v in veicoli:
        colori_veicoli[v] = '#d9b904' if v is None else green_shades[gi % len(green_shades)]
        if v is not None: gi += 1

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = []
    schedula_by_bar = {}

    # timeline
    inizi = [s["inizio_setup"] for s in schedulazione] + [s["inizio_lavorazione"] for s in schedulazione]
    fine  = [s["fine_setup"]  for s in schedulazione] + [s["fine_lavorazione"]  for s in schedulazione]
    t0 = min(inizi)
    t1 = max(fine)

    # calcolo blocchi non produzione (15:00→07:00 + weekend)
    blocchi_np = []
    ct = t0.replace(hour=0, minute=0, second=0, microsecond=0)
    while ct < t1:
        wd = ct.weekday()
        if wd == 4:  # venerdì
            s = ct + timedelta(hours=15)
            e = (ct + timedelta(days=3)).replace(hour=7)
            if s < t1 and e > t0: blocchi_np.append((max(s, t0), min(e, t1)))
            ct += timedelta(days=3)
        else:
            s = ct + timedelta(hours=15)
            e = (ct + timedelta(days=1)).replace(hour=7)
            if s < t1 and e > t0: blocchi_np.append((max(s, t0), min(e, t1)))
            ct += timedelta(days=1)

    # calcola durata utile per setup (senza NP)
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

    # disegno effettivo
    for s in schedulazione:
        y = macchine.index(s["macchina"])

        # --- SETUP (rosso / grigio) ---
        for start, end, tipo in split_intervallo(s["inizio_setup"], s["fine_setup"], blocchi_np):
            durata = end - start
            colore = 'red' if tipo=='p' else desatura('red', 0.7)
            bar = ax.barh(y, durata, left=start, height=0.5, color=colore, edgecolor='black')[0]
            bars.append(bar)
            # tooltip
            schedula_by_bar[bar] = {
                'type': 'setup',
                'data': s,
                'durata_netto': calcola_durata_netto(s["inizio_setup"], s["fine_setup"], blocchi_np)
            }

        # --- LAVORAZIONE (giallo/verde / grigio) ---
        base_col = colori_veicoli[s["veicolo"]]
        for start, end, tipo in split_intervallo(s["inizio_lavorazione"], s["fine_lavorazione"], blocchi_np):
            durata = end - start
            colore = base_col if tipo=='p' else desatura(base_col, 0.8)
            bar = ax.barh(y, durata, left=start, height=0.5, color=colore, edgecolor='black')[0]
            bars.append(bar)
            schedula_by_bar[bar] = {
                'type': 'lavorazione',
                'data': s
            }

    # etichette e formato
    ax.set_yticks(range(len(macchine)))
    ax.set_yticklabels(macchine)
    ax.set_xlim(t0, t1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.set_ylim(-0.5, len(macchine)-0.5)
    fig.autofmt_xdate()
    ax.set_xlabel('Tempo')
    ax.set_ylabel('Macchina')
    ax.set_title('Schedulazione con fasce di non produzione desaturate')

    # tooltip come prima
    tooltip = Annotation('', xy=(0,0), xytext=(15,15), textcoords='offset points',
                         bbox=dict(boxstyle="round", fc="w", ec="k"),
                         arrowprops=dict(arrowstyle="->"))
    tooltip.set_visible(False)
    ax.add_artist(tooltip)

    def on_motion(event):
        vis = False
        for bar in bars:
            contains, _ = bar.contains(event)
            if contains:
                info = schedula_by_bar[bar]
                s = info['data']
                tooltip.xy = (event.xdata, event.ydata)
                if info['type']=='setup':
                    testo = (f"TEMPO DI SETUP\n"
                             f"Commessa: {s['commessa']}\n"
                             f"Durata utile: {info['durata_netto']}")
                else:
                    veicolo = s["veicolo"]
                    nome = veicolo.nome if veicolo is not None else "Senza veicolo"
                    testo = f"Commessa: {s['commessa']}\nVeicolo: {nome}"
                tooltip.set_text(testo)
                tooltip.set_visible(True)
                vis = True
                break
        if not vis:
            tooltip.set_visible(False)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_motion)

    plt.tight_layout()
    plt.show()

"""import matplotlib.pyplot as plt
from matplotlib.text import Annotation
from datetime import datetime, timedelta

def grafico_schedulazione(schedulazione):
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

    inizi = [s["inizio_setup"] for s in schedulazione] + [s["inizio_lavorazione"] for s in schedulazione]
    fine = [s["fine_setup"] for s in schedulazione] + [s["fine_lavorazione"] for s in schedulazione]
    inizio_timeline = min(inizi)
    fine_timeline = max(fine)

    # Calcola intervalli non produttivi
    intervalli_non_produzione = []
    current_time = inizio_timeline.replace(hour=0, minute=0, second=0, microsecond=0)
    while current_time < fine_timeline:
        weekday = current_time.weekday()

        if weekday == 4:  # Venerdì
            weekend_start = current_time + timedelta(hours=15)
            weekend_end = (current_time + timedelta(days=3)).replace(hour=7)

            start = max(weekend_start, inizio_timeline)
            end = min(weekend_end, fine_timeline)
            if start < end:
                intervalli_non_produzione.append((start, end))

            current_time += timedelta(days=3)
        else:
            np_start = current_time + timedelta(hours=15)
            np_end = (current_time + timedelta(days=1)).replace(hour=7)

            start = max(np_start, inizio_timeline)
            end = min(np_end, fine_timeline)
            if start < end:
                intervalli_non_produzione.append((start, end))

            current_time += timedelta(days=1)

    # Funzione per mappare i tempi produttivi
    def crea_mappa_tempo(inizio, fine, blocchi_np):
        mappa = {}
        tempo_corrente = inizio
        tempo_asse = 0

        blocchi_np = sorted(blocchi_np)

        while tempo_corrente < fine:
            in_np = False
            for np_start, np_end in blocchi_np:
                if np_start <= tempo_corrente < np_end:
                    in_np = True
                    tempo_corrente = np_end  # Salta il blocco NP
                    break
            if not in_np:
                mappa[tempo_corrente] = tempo_asse
                tempo_corrente += timedelta(minutes=1)
                tempo_asse += 1  # ogni minuto è un'unità asse
        return mappa

    def trasforma_tempo(dt, mappa_tempo):
        dt_rounded = dt.replace(second=0, microsecond=0)
        return mappa_tempo.get(dt_rounded, None)

    mappa_tempo = crea_mappa_tempo(inizio_timeline, fine_timeline, intervalli_non_produzione)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = []
    schedula_by_bar = {}

    for s in schedulazione:
        y = macchine.index(s["macchina"])

        # Setup
        start_setup = trasforma_tempo(s["inizio_setup"], mappa_tempo)
        end_setup = trasforma_tempo(s["fine_setup"], mappa_tempo)
        if start_setup is None or end_setup is None:
            continue  # salta se fuori range
        durata_setup = end_setup - start_setup

        setup_bar = ax.barh(y, durata_setup, left=start_setup, height=0.5, color='red', edgecolor='black')[0]
        bars.append(setup_bar)
        schedula_by_bar[setup_bar] = {
            'type': 'setup',
            'data': s
        }

        # Lavorazione
        start_lav = trasforma_tempo(s["inizio_lavorazione"], mappa_tempo)
        end_lav = trasforma_tempo(s["fine_lavorazione"], mappa_tempo)
        if start_lav is None or end_lav is None:
            continue
        durata_lav = end_lav - start_lav

        colore = colori_veicoli[s["veicolo"]]
        lav_bar = ax.barh(y, durata_lav, left=start_lav, height=0.5, color=colore, edgecolor='black')[0]
        bars.append(lav_bar)
        schedula_by_bar[lav_bar] = {
            'type': 'lavorazione',
            'data': s
        }

    ax.set_yticks(range(len(macchine)))
    ax.set_yticklabels(macchine)

    # Calcola tick asse X
    ticks = []
    labels = []
    tick_set = set()
    for dt, pos in sorted(mappa_tempo.items()):
        if dt.hour == 8 and dt.minute == 0 and pos not in tick_set:  # Solo 8:00
            ticks.append(pos)
            labels.append(dt.strftime('%d-%m %H:%M'))
            tick_set.add(pos)

    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, rotation=45)

    ax.set_xlabel('Tempo (produttivo)')
    ax.set_ylabel('Macchina')
    ax.set_title('Schedulazione (tempi non produttivi rimossi)')
    plt.tight_layout()
    plt.show()"""