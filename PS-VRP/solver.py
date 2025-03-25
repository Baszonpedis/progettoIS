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

def data_partenza_veicoli(lista_commesse:list,lista_veicoli:list):
    lista_commesse.sort(key=lambda commessa:(-commessa.priorita_cliente,commessa.due_date.timestamp())) # ordino la lista sulla base della priorita e successivamente sulla due date
    for veicolo in lista_veicoli:
        lista_filtrata=[commessa for commessa in lista_commesse if veicolo.zone_coperte in commessa.zona_cliente] #lista che contiene solo le commesse ammissibili per il veicolo
        if len(lista_filtrata)>0: #se ho almeno una commessa nella lista
            data_partenza=lista_filtrata[0].due_date #calcolo la data di partenza come la data di quella più urgente
            oggi=datetime.now() #data di oggi
            oggi=datetime.strptime("2024-09-11","%Y-%m-%d")
            if oggi>=data_partenza: #se la commessa più urgente ha una data nel passato rispetto ad oggi
                data_partenza=oggi+timedelta(days=2) #aggiungo 2 giorni alla data di oggi
            else:
                differenza=data_partenza-oggi
                if differenza.days>365:
                    data_partenza = oggi + timedelta(days=7)
            #veicolo.set_data_partenza(lista_filtrata[0].due_date) #la data di partenza del veicolo diventa la due date delle commessa più ravvicinata della zona
            veicolo.set_data_partenza(data_partenza) #la data di partenza del veicolo diventa la due date delle commessa più ravvicinata della zona

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
            #if veicolo.zone_coperte in commessa.zona_cliente and commessa.due_date>=veicolo.data_partenza:#commessa.due_date<=veicolo.data_partenza:
            if veicolo.zone_coperte in commessa.zona_cliente and commessa.release_date<veicolo.data_partenza:#commessa.due_date<=veicolo.data_partenza:
                #if commessa not in commesse_da_schedulare:
                commesse_da_schedulare.append(commessa)
                break
    #print(len(lista_commesse),len(commesse_da_schedulare))
    return commesse_da_schedulare

def swap(lista_macchine: list, lista_veicoli:list, f_obj,schedulazione: list):
    """
    :param lista_macchine: lista contenente oggetti macchina
    :param lista_veicoli: lista contenente oggetti veicolo
    :param f_obj: funzione obiettivo ottenuta con l'euristico greedy
    :param schedulazione: schedulazione ottenuta con l'euristico greedy
    :return: schedulazione ottenuta applicando ricerca locale swap intra macchina
    """
    contatore=0
    partenze = {veicolo.nome: veicolo.data_partenza for veicolo in lista_veicoli} #dizionario in cui ad ogni veicolo viene associata la sua data di partenza
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione #data in cui inizia la schedulazione
    f_best = f_obj #funzione obiettivo
    eps = 0.00001 #parametro per stabilire se il delta è conveniente
    soluzione_swap=[] #lista contenente tutte le schedule
    for macchina in lista_macchine: #per ogni macchina
        macchina_schedula=[s for s in schedulazione if s['macchina']==macchina.nome_macchina] #vado a prendere tutte le schedule ad essa associate
        schedula=macchina.lista_commesse_processate #copia della lista di commesse schedulate
        #schedula=deepcopy(macchina.lista_commesse_processate) #copia profonda della lista di commesse schedulate
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
                            check=True
                            for k in range(1,len(schedula)): #vado a ricostruire la soluzione e la schedula
                                tempo_setup_commessa=macchina.calcolo_tempi_setup(schedula[k-1],schedula[k])
                                tempo_processamento_commessa=schedula[k].metri_da_tagliare/macchina.velocita_taglio_media
                                return_schedulazione(schedula[k],macchina,tempo_setup_commessa,tempo_processamento_commessa,ultima_lavorazione,inizio_schedulazione,s)
                                if s[-1]['fine_lavorazione']<schedula[k].release_date or s[-1]['fine_lavorazione']>partenze[schedula[k].veicolo]:
                                    check=False
                                ultima_lavorazione=ultima_lavorazione+tempo_setup_commessa+tempo_processamento_commessa
                            if check:
                            #if partenze[veicolo_i]>=s[j-1]['fine_lavorazione'] and partenze[veicolo_j]>=s[i-1]['fine_lavorazione'] and check: #faccio il check sulle date di partenza dei veicoli
                                #print(veicolo_i,s[j-1]['commessa'],' ',veicolo_j,s[i-1]['commessa'])
                            #if partenze[veicolo_i]>=s[j]['fine_lavorazione'] and partenze[veicolo_j]>=s[i]['fine_lavorazione']: #faccio il check sulle date di partenza dei veicoli
                                #print(veicolo_i,s[j]['commessa'],' ',veicolo_j,s[i]['commessa'])
                                improved=True #miglioramento trovato
                                f_best+=delta #aggiorno funzione obiettivo
                                #print(f'scambio {schedula[i].id_commessa} con {schedula[j].id_commessa} con delta={delta} su {macchina.nome_macchina}')
                                macchina_schedula=s #aggiorno le schedule associate alla macchina
                                #for vvv in schedula:
                                    #print(vvv.id_commessa)
                                #break
                                contatore+=1
                            else:
                                #print('scambio non feasible')
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
    print('Swap eseguiti =',contatore)
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

def euristico_costruttivo(lista_commesse:list, lista_macchine:list, lista_veicoli:list):
    #data_partenza_veicoli(lista_commesse,lista_veicoli)
    lista_commesse.sort(key=lambda commessa: (commessa.due_date.timestamp(), commessa.priorita_cliente))
    f_obj = 0  # funzione obiettivo (somma pesata dei tempi di setup)
    schedulazione = []  # è una lista che conterrà tutte le schedulazioni
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i)  # inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine
    while len(lista_commesse)>0 and len(lista_macchine)>0:
        schedulazione_eseguita=False
        lista_macchine=sorted(lista_macchine,key=lambda macchina: macchina._minuti_fine_ultima_lavorazione)
        macchina=lista_macchine[0]
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
                        commessa.veicolo=veicolo.nome
                        veicolo.capacita-=commessa.kg_da_tagliare
                        schedulazione_eseguita=True
                        f_obj+=tempo_setup
                        aggiorna_schedulazione1(commessa,macchina,tempo_setup,tempo_processamento,inizio_schedulazione,schedulazione,macchina._minuti_fine_ultima_lavorazione)
                        lista_commesse.remove(commessa)
                        #print(macchina.nome_macchina,commessa.id_commessa,veicolo.nome)
                    if schedulazione_eseguita:
                        break
                #if schedulazione_eseguita:
                    #break
            if schedulazione_eseguita:
                break
        if not schedulazione_eseguita:
            lista_macchine.remove(macchina)
    return schedulazione, f_obj

def move_no_delta(lista_macchine: list, lista_veicoli:list, f_obj,schedulazione: list):
    """
    :param lista_macchine: lista contenente oggetti macchina
    :param lista_veicoli: lista contenente oggetti veicolo
    :param f_obj: funzione obiettivo ottenuta con l'euristico greedy
    :param schedulazione: schedulazione ottenuta con l'euristico greedy
    :return: schedulazione ottenuta applicando ricerca locale swap intra macchina
    """
    contatore=0
    partenze = {veicolo.nome: veicolo.data_partenza for veicolo in lista_veicoli} #dizionario in cui ad ogni veicolo viene associata la sua data di partenza
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione #data in cui inizia la schedulazione
    f_best = f_obj #funzione obiettivo
    eps = 0.00001 #parametro per stabilire se il delta è conveniente
    soluzione_move=[] #lista contenente tutte le schedule
    for macchina in lista_macchine: #per ogni macchina
        macchina_schedula=[s for s in schedulazione if s['macchina']==macchina.nome_macchina] #vado a prendere tutte le schedule ad essa associate
        #schedula=deepcopy(macchina.lista_commesse_processate) #copia profonda della lista di commesse schedulate

        schedula=macchina.lista_commesse_processate #copia profonda della lista di commesse schedulate
        #ultima_lavorazione=macchina.ultima_lavorazione #copia del parametro che indica i minuti a partire dai quali una macchina è disponibile
        improved = True #variabile booleana che indica se è stato trovato un miglioramento

        f_macchina=sum(s['minuti setup'] for s in macchina_schedula)
        #print('inizio', f_macchina)
        if len(schedula)>=3: #se ho sufficienti elementi nella lista per effettuare uno swap
            while improved: #finchè trovo miglioramenti continuo
                improved=False #imposto subito la variabile boolena a False, così se non trovo miglioramenti esco dal ciclo
                for i in range(1,len(schedula)): #scorro tutti i possibili job
                    for j in range(1,len(schedula)): #scorro tutte le possibili posizioni
                        if i!=j:
                            delta=math.inf
                            ultima_lavorazione = macchina.ultima_lavorazione #imposto la variabile al tempo in cui la macchina diventa disponibile per la prima volta
                            veicolo_i = schedula[i].veicolo #prendo il veicolo associato alla commessa i
                            #effettuo il calcolo del delta
                            """
                            a=0
                            if i+1<len(schedula) and j+1<len(schedula) and i+1!=j and i-1!=j and j-1!=i and j+1!=i:
                                a=1
                                delta=macchina.calcolo_tempi_setup(schedula[i-1],schedula[i+1])+macchina.calcolo_tempi_setup(schedula[j-1],schedula[i])+\
                                      macchina.calcolo_tempi_setup(schedula[i],schedula[j]) +\
                                      -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[i+1])+ \
                                      -macchina.calcolo_tempi_setup(schedula[j-1],schedula[j])

                            if i+1==len(schedula) and j+1<len(schedula):
                                #print('if2')
                                a=2
                                delta=macchina.calcolo_tempi_setup(schedula[j-1],schedula[i])+macchina.calcolo_tempi_setup(schedula[i],schedula[j])+\
                                      -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[j-1],schedula[j])

                            if i+1<len(schedula) and j+1==len(schedula) : #commesse non consecutive con j in ultima posizione
                                #print('if3')
                                a=3
                                delta=macchina.calcolo_tempi_setup(schedula[i-1],schedula[i+1])+macchina.calcolo_tempi_setup(schedula[j],schedula[i])+\
                                      -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[i+1])



                            #print(delta)
                            #for s1 in schedula:
                                #print(s1.id_commessa)
                            """

                            if True: #delta<-eps: #se la swap è migliorativo
                                #print('a=',a,'i=',i,'j=',j,'len=',len(schedula), macchina.nome_macchina)
                                s=[] #imposto nuova schedula inizialmente vuota
                                comm_i=schedula[i] #commessa i
                                #eseguo temporaneamente il move
                                #for vvv in schedula:
                                    #print(vvv.id_commessa)
                                copia=deepcopy(schedula)
                                schedula.remove(comm_i)
                                schedula.insert(j,comm_i)
                                #schedula.remove(comm_i)
                                #if j>i and j-1!=i and j<len(schedula):# and j-1!=1:
                                #    j-=1
                                #schedula.insert(j,comm_i)
                                #for s1 in schedula:
                                    #print(s1.id_commessa)
                                #schedula[i]=schedula[j]
                                #schedula[j]=comm_i
                                F=0
                                check=True
                                for k in range(1,len(schedula)): #vado a ricostruire la soluzione e la schedula
                                    tempo_setup_commessa=macchina.calcolo_tempi_setup(schedula[k-1],schedula[k])
                                    F+=tempo_setup_commessa
                                    tempo_processamento_commessa=schedula[k].metri_da_tagliare/macchina.velocita_taglio_media
                                    return_schedulazione(schedula[k],macchina,tempo_setup_commessa,tempo_processamento_commessa,ultima_lavorazione,inizio_schedulazione,s)
                                    # if s[-1]['fine_lavorazione']<schedula[k].release_date:
                                    if s[-1]['fine_lavorazione'] < schedula[k].release_date or s[-1]['fine_lavorazione'] > partenze[schedula[k].veicolo]:
                                        check=False
                                    ultima_lavorazione=ultima_lavorazione+tempo_setup_commessa+tempo_processamento_commessa
                                #print('fine', F)
                                if check and F < f_macchina:
                                #if partenze[veicolo_i]>=s[j-1]['fine_lavorazione'] and check and F<f_macchina: #faccio il check sulle date di partenza dei veicoli
                                    delta=F-f_macchina
                                    f_macchina = F
                                    improved=True #miglioramento trovato
                                    f_best+=delta #aggiorno funzione obiettivo
                                    #print(f'metto commessa {comm_i.id_commessa} con delta={delta} in posizione {j} su macchina {macchina.nome_macchina}')
                                    macchina_schedula=s #aggiorno le schedule associate alla macchina
                                    #for vvv in schedula:
                                        #print(vvv.id_commessa)
                                    #break
                                    contatore+=1
                                    #print(delta, comm_i.id_commessa,'j-->', j,'i-->', i , len(schedula))

                                    #print(delta, comm_i.id_commessa, j)
                                else:
                                    #print('scambio non feasible')
                                    #se lo swap non è ammissibile torno indietro annullando lo scambio
                                    #schedula=copia
                                    schedula.remove(comm_i)
                                    schedula.insert(i,comm_i)
                            if improved:
                                break
                    if improved:
                        break
                #if improved:
                    #break
            soluzione_move.append(macchina_schedula) #aggiungo la schedula della macchina alla lista delle schedule
        else:
            soluzione_move.append(macchina_schedula) #aggiungo la schedula della macchina alla lista delle schedule
    print('Mosse eseguite =',contatore)
    return soluzione_move,f_best

def swap_no_delta(lista_macchine: list, lista_veicoli:list, f_obj,schedulazione: list):
    """
    :param lista_macchine: lista contenente oggetti macchina
    :param lista_veicoli: lista contenente oggetti veicolo
    :param f_obj: funzione obiettivo ottenuta con l'euristico greedy
    :param schedulazione: schedulazione ottenuta con l'euristico greedy
    :return: schedulazione ottenuta applicando ricerca locale swap intra macchina
    """
    contatore=0
    partenze = {veicolo.nome: veicolo.data_partenza for veicolo in lista_veicoli} #dizionario in cui ad ogni veicolo viene associata la sua data di partenza
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione #data in cui inizia la schedulazione
    f_best = f_obj #funzione obiettivo
    eps = 0.00001 #parametro per stabilire se il delta è conveniente
    soluzione_swap=[] #lista contenente tutte le schedule

    for macchina in lista_macchine: #per ogni macchina
        macchina_schedula=[s for s in schedulazione if s['macchina']==macchina.nome_macchina] #vado a prendere tutte le schedule ad essa associate
        schedula=macchina.lista_commesse_processate #copia profonda della lista di commesse schedulate
        f_macchina = sum(s['minuti setup'] for s in macchina_schedula)

        #schedula=deepcopy(macchina.lista_commesse_processate) #copia profonda della lista di commesse schedulate
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
                        """
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
                        """
                        #print(delta)
                        if True:#delta<-eps: #se la swap è migliorativo
                            s=[] #imposto nuova schedula inizialmente vuota
                            comm_i=schedula[i] #commessa i
                            comm_j=schedula[j] #commessa j
                            #eseguo temporaneamente lo swap
                            schedula[i]=schedula[j]
                            schedula[j]=comm_i
                            check=True
                            F=0
                            for k in range(1,len(schedula)): #vado a ricostruire la soluzione e la schedula
                                tempo_setup_commessa=macchina.calcolo_tempi_setup(schedula[k-1],schedula[k])
                                F+=tempo_setup_commessa
                                tempo_processamento_commessa=schedula[k].metri_da_tagliare/macchina.velocita_taglio_media
                                return_schedulazione(schedula[k],macchina,tempo_setup_commessa,tempo_processamento_commessa,ultima_lavorazione,inizio_schedulazione,s)
                                if s[-1]['fine_lavorazione']<schedula[k].release_date or s[-1]['fine_lavorazione']>partenze[schedula[k].veicolo]:
                                    check=False
                                ultima_lavorazione=ultima_lavorazione+tempo_setup_commessa+tempo_processamento_commessa
                            if check and F<f_macchina:
                            #if partenze[veicolo_i]>=s[j-1]['fine_lavorazione'] and partenze[veicolo_j]>=s[i-1]['fine_lavorazione'] and check: #faccio il check sulle date di partenza dei veicoli
                                #print(veicolo_i,s[j-1]['commessa'],' ',veicolo_j,s[i-1]['commessa'])
                            #if partenze[veicolo_i]>=s[j]['fine_lavorazione'] and partenze[veicolo_j]>=s[i]['fine_lavorazione']: #faccio il check sulle date di partenza dei veicoli
                                #print(veicolo_i,s[j]['commessa'],' ',veicolo_j,s[i]['commessa'])
                                improved=True #miglioramento trovato
                                delta = F - f_macchina
                                f_macchina = F
                                f_best+=delta #aggiorno funzione obiettivo
                                #print(f'scambio {schedula[i].id_commessa} con {schedula[j].id_commessa} con delta={delta} su {macchina.nome_macchina}')
                                macchina_schedula=s #aggiorno le schedule associate alla macchina
                                #for vvv in schedula:
                                    #print(vvv.id_commessa)
                                #break
                                contatore+=1
                            else:
                                #print('scambio non feasible')
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
    print('Swap eseguiti =',contatore)
    return soluzione_swap,f_best

def move_2_macchine(lista_macchine: list, lista_veicoli:list, f_obj,schedulazione: list):
    partenze = {veicolo.nome: veicolo.data_partenza for veicolo in lista_veicoli}  # dizionario in cui ad ogni veicolo viene associata la sua data di partenza
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # data in cui inizia la schedulazione
    f_best = f_obj  # funzione obiettivo
    soluzione_move = []  # lista contenente tutte le schedule
    contatore=0
    for m1 in range(len(lista_macchine)):
        for m2 in range(len(lista_macchine)):
            #print(lista_macchine[m1].nome_macchina,len(lista_macchine[m1].lista_commesse_processate))
            #print(lista_macchine[m2].nome_macchina,len(lista_macchine[m2].lista_commesse_processate))
            if m1!=m2 and len(lista_macchine[m1].lista_commesse_processate)>2 and len(lista_macchine[m2].lista_commesse_processate)>2:
                schedula1,schedula2,f_best,contatore=move_inter_macchina(lista_macchine[m1],lista_macchine[m2],partenze,contatore,inizio_schedulazione,f_best)
                lista_macchine[m1].lista_commesse_processate=schedula1
                lista_macchine[m2].lista_commesse_processate=schedula2
                #print('nuove dim')
                #print(lista_macchine[m1].nome_macchina,len(lista_macchine[m1].lista_commesse_processate))
                #print(lista_macchine[m2].nome_macchina,len(lista_macchine[m2].lista_commesse_processate))
    print('Mosse =',contatore)
    for m in lista_macchine:
        if len(m.lista_commesse_processate)>1:
            ultima_lavorazione=m.ultima_lavorazione
            for pos in range(1,len(m.lista_commesse_processate)):
                tempo_setup_commessa=m.calcolo_tempi_setup(m.lista_commesse_processate[pos-1],m.lista_commesse_processate[pos])
                tempo_processamento_commessa=m.lista_commesse_processate[pos].metri_da_tagliare/m.velocita_taglio_media
                return_schedulazione(m.lista_commesse_processate[pos],m, tempo_setup_commessa, tempo_processamento_commessa,ultima_lavorazione,inizio_schedulazione,soluzione_move)
                ultima_lavorazione = ultima_lavorazione + tempo_setup_commessa + tempo_processamento_commessa
    return soluzione_move,f_best

def move_inter_macchina(macchina1:Macchina,macchina2:Macchina,partenze:dict,contatore:int,inizio_schedulazione,f_best):
    #macchina1_schedula=[s for s in schedulazione if s['macchina']==macchina1.nome_macchina] #vado a prendere tutte le schedule ad essa associate
    #macchina2_schedula=[s for s in schedulazione if s['macchina']==macchina2.nome_macchina] #vado a prendere tutte le schedule ad essa associate
    schedula1=macchina1.lista_commesse_processate #copia profonda della lista di commesse schedulate
    schedula2=macchina2.lista_commesse_processate #copia profonda della lista di commesse schedulate
    eps = 0.00001  # parametro per stabilire se il delta è conveniente
    improved = True #variabile booleana che indica se è stato trovato un miglioramento
    while improved:  # finchè trovo miglioramenti continuo
        improved = False  # imposto subito la variabile boolena a False, così se non trovo miglioramenti esco dal ciclo
        for i in range(1, len(schedula1)):
            for j in range(1, len(schedula2)):
                commessa = schedula1[i]
                if commessa.compatibilita[macchina2.nome_macchina]==1:
                    posizione = j
                    ultima_lavorazione1=macchina1.ultima_lavorazione
                    ultima_lavorazione2=macchina2.ultima_lavorazione
                    if i+1<len(schedula1) and j+1<len(schedula2):
                        delta=-macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i])-macchina1.calcolo_tempi_setup(schedula1[i],schedula1[i+1])+\
                              -macchina2.calcolo_tempi_setup(schedula2[j-1],schedula2[j])+\
                              +macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i+1])+\
                              +macchina2.calcolo_tempi_setup(schedula2[j-1],schedula1[i])+macchina2.calcolo_tempi_setup(schedula1[i],schedula2[j])

                    if i+1==len(schedula1) and j+1<len(schedula2):
                        delta=-macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i])+\
                              -macchina2.calcolo_tempi_setup(schedula2[j-1],schedula2[j])+\
                              +macchina2.calcolo_tempi_setup(schedula2[j-1],schedula1[i])+macchina2.calcolo_tempi_setup(schedula1[i],schedula2[j])

                    if i+1==len(schedula1) and j+1==len(schedula2):
                        delta=-macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i])+ \
                              +macchina2.calcolo_tempi_setup(schedula2[j],schedula1[i]) #[j-1][i]

                    if i+1<len(schedula1) and j+1==len(schedula2):
                        delta=-macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i])-macchina1.calcolo_tempi_setup(schedula1[i],schedula1[i+1])+\
                              +macchina1.calcolo_tempi_setup(schedula1[i-1],schedula1[i+1])+\
                              +macchina2.calcolo_tempi_setup(schedula2[j],schedula1[i])

                    if delta<-eps:
                        s1=[]
                        s2=[]
                        copia1=deepcopy(schedula1)
                        copia2=deepcopy(schedula2)
                        schedula1.remove(commessa)
                        if j + 1 == len(schedula2):
                            schedula2.append(commessa)
                        else:
                            schedula2.insert(posizione, commessa)
                        #schedula2.insert(posizione,commessa)
                        check1=True
                        for k in range(1,len(schedula1)): #vado a ricostruire la soluzione e la schedula
                            tempo_setup_commessa=macchina1.calcolo_tempi_setup(schedula1[k-1],schedula1[k])
                            tempo_processamento_commessa=schedula1[k].metri_da_tagliare/macchina1.velocita_taglio_media
                            return_schedulazione(schedula1[k],macchina1,tempo_setup_commessa,tempo_processamento_commessa,ultima_lavorazione1,inizio_schedulazione,s1)
                            if s1[-1]['fine_lavorazione'] < schedula1[k].release_date or s1[-1]['fine_lavorazione'] > partenze[schedula1[k].veicolo]:
                                check1=False
                            ultima_lavorazione1=ultima_lavorazione1+tempo_setup_commessa+tempo_processamento_commessa
                        check2 = True
                        for k in range(1, len(schedula2)):  # vado a ricostruire la soluzione e la schedula
                            tempo_setup_commessa=macchina2.calcolo_tempi_setup(schedula2[k - 1], schedula2[k])
                            tempo_processamento_commessa = schedula2[k].metri_da_tagliare / macchina2.velocita_taglio_media
                            return_schedulazione(schedula2[k], macchina2, tempo_setup_commessa,tempo_processamento_commessa, ultima_lavorazione2, inizio_schedulazione,s2)
                            if s2[-1]['fine_lavorazione'] < schedula2[k].release_date or s2[-1]['fine_lavorazione'] > partenze[schedula2[k].veicolo]:
                                check2 = False
                            ultima_lavorazione2=ultima_lavorazione2+tempo_setup_commessa+tempo_processamento_commessa
                        if check1 and check2: #faccio il check sulle date di partenza dei veicoli
                            improved=True #miglioramento trovato
                            f_best+=delta #aggiorno funzione obiettivo
                            #print(f'metto {commessa.id_commessa} dalla posizione {i} su macchina {macchina1.nome_macchina} in posizione {posizione} su macchina {macchina2.nome_macchina} con delta={delta}')

                            #macchina_schedula1=s1 #aggiorno le schedule associate alla macchina
                            #macchina_schedula2=s2
                            contatore+=1
                        else:
                            schedula1=copia1
                            schedula2=copia2
                if improved:
                    break
            if improved:
                break
    return schedula1,schedula2,f_best,contatore

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
    #plt.xticks(ticks=inizi + fine,labels=[time.strftime('%Y-%m-%d %H:%M:%S') for time in inizi] + [time.strftime('%Y-%m-%d %H:%M:%S') for time in fine], rotation=90)
    '''La linea sopra serve per mostrare gli orari precisi, ma si tratta di un'informazione troppo granulare'''
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
    plt.savefig("PS-VRP\Dati_output\schedulazione.jpg")
    plt.show()  # Mostra il grafico

    # Spostare legenda
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()  # Adjust layout to prevent overlapping