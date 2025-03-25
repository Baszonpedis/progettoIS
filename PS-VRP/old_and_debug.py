
def Euristico(lista_macchine:list,lista_commesse:list):
    """
    :param lista_macchine: lista di oggetti macchina contenente tutti le macchine
    :param lista_commesse: lista di oggetti commessa contenente tutte le commesse
    :return: lista di dizionari contenenti una soluzione euristica
    """
    f_obj=0 #funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione=[] #è una lista che conterrà tutte le schedulazioni
    lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i) #inizializzo ogni macchina con una commessa dummy
    for commessa in lista_commesse:
        macchina_schedula=None  #è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento=datetime(9999, 12, 31)#commessa.due_date  #metto come tempo di minimo completamento la due date della commessa
        tempo_minimo_setup=math.inf
        for macchina in lista_macchine: #cerco tra le macchine
            if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1:#and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_processamento=commessa.metri_da_tagliare/macchina.velocita_taglio_media  #calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup=macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa)  #calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione=max(commessa.release_date,macchina.data_ora_disponibilita)+timedelta(minutes=tempo_processamento)+timedelta(minutes=tempo_setup) #calcolo quale sarebbe il tempo di fine lavorazione
                if tempo_fine_lavorazione<tempo_minimo_completamento: #con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                    tempo_minimo_completamento=tempo_fine_lavorazione #assegno al tempo di completamento uguale al tempo di fine lavorazione
                    tempo_minimo_setup=tempo_setup
                    macchina_schedula=macchina #la variabile inizialmente settata a None assume il valore della macchina
        if macchina_schedula!=None: #se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
            #print(macchina_schedula.nome_macchina, '-->', commessa.id_commessa)
            f_obj+=commessa.priorita_cliente * ((tempo_minimo_completamento-macchina_schedula.data_ora_disponibilita).total_seconds()/60)
            schedulazione.append({"commessa": commessa.id_commessa,
                                  "macchina": macchina_schedula.nome_macchina,
                                  "inizio_setup": max(macchina_schedula.data_ora_disponibilita, commessa.release_date),
                                  "fine_setup": max(macchina_schedula.data_ora_disponibilita,
                                                    commessa.release_date) + timedelta(minutes=tempo_minimo_setup),
                                  "inizio_lavorazione": max(macchina_schedula.data_ora_disponibilita,
                                                            commessa.release_date) + timedelta(minutes=tempo_minimo_setup),
                                  "fine_lavorazione": tempo_minimo_completamento,
                                  "mt da tagliare": commessa.metri_da_tagliare,
                                  "taglio": commessa.tipologia_taglio,
                                  "macchine compatibili": [machine for machine, value in commessa.compatibilita.items()
                                                           if value == 1],
                                  "nr coltelli": commessa.numero_coltelli,
                                  "diametro_tubo": commessa.diametro_tubo,
                                  "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
            macchina_schedula.data_ora_disponibilita = tempo_minimo_completamento  # aggiorno la disponibilita della macchina che ha effettuato la lavorazione
            macchina_schedula.lista_commesse_processate.append(commessa) #aggiungo la commessa alla macchina che eseguirà la lavorazione
    return schedulazione,f_obj #lista di dizionari che contiene le informazioni relative ad una schedulazione

def Euristico1(lista_macchine:list,lista_commesse:list):
    """
    :param lista_macchine: lista di oggetti macchina contenente tutti le macchine
    :param lista_commesse: lista di oggetti commessa contenente tutte le commesse
    :return: lista di dizionari contenenti una soluzione euristica
    """
    f_obj=0 #funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione=[] #è una lista che conterrà tutte le schedulazioni
    lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i) #inizializzo ogni macchina con una commessa dummy
    for commessa in lista_commesse:
        macchina_schedula=None  #è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento=datetime(9999, 12, 31)#commessa.due_date  #metto come tempo di minimo completamento la due date della commessa
        tempo_minimo_setup=math.inf
        for macchina in lista_macchine: #cerco tra le macchine
            if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1:#and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_processamento=commessa.metri_da_tagliare/macchina.velocita_taglio_media  #calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup=macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa)  #calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione=max(commessa.release_date,macchina.data_ora_disponibilita)+timedelta(minutes=tempo_processamento)+timedelta(minutes=tempo_setup) #calcolo quale sarebbe il tempo di fine lavorazione
                if tempo_fine_lavorazione<tempo_minimo_completamento: #con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                    tempo_minimo_completamento=tempo_fine_lavorazione #assegno al tempo di completamento uguale al tempo di fine lavorazione
                    tempo_minimo_setup=tempo_setup
                    macchina_schedula=macchina #la variabile inizialmente settata a None assume il valore della macchina
        if macchina_schedula!=None: #se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
            #print(macchina_schedula.nome_macchina, '-->', commessa.id_commessa)
            f_obj+=commessa.priorita_cliente * ((tempo_minimo_completamento-macchina_schedula.data_ora_disponibilita).total_seconds()/60)
            schedulazione.append({"commessa": commessa.id_commessa,
                                  "macchina": macchina_schedula.nome_macchina,
                                  "inizio_setup": max(macchina_schedula.data_ora_disponibilita, commessa.release_date),
                                  "fine_setup": max(macchina_schedula.data_ora_disponibilita,
                                                    commessa.release_date) + timedelta(minutes=tempo_minimo_setup),
                                  "inizio_lavorazione": max(macchina_schedula.data_ora_disponibilita,
                                                            commessa.release_date) + timedelta(minutes=tempo_minimo_setup),
                                  "fine_lavorazione": tempo_minimo_completamento,
                                  "mt da tagliare": commessa.metri_da_tagliare,
                                  "taglio": commessa.tipologia_taglio,
                                  "macchine compatibili": [machine for machine, value in commessa.compatibilita.items()
                                                           if value == 1],
                                  "nr coltelli": commessa.numero_coltelli,
                                  "diametro_tubo": commessa.diametro_tubo,
                                  "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
            macchina_schedula.data_ora_disponibilita = tempo_minimo_completamento  # aggiorno la disponibilita della macchina che ha effettuato la lavorazione
            macchina_schedula.lista_commesse_processate.append(commessa) #aggiungo la commessa alla macchina che eseguirà la lavorazione
    return schedulazione,f_obj #lista di dizionari che contiene le informazioni relative ad una schedulazione

def Euristico2(lista_macchine:list,lista_commesse:list):
    """
    :param lista_macchine: lista di oggetti macchina contenente tutti le macchine
    :param lista_commesse: lista di oggetti commessa contenente tutte le commesse
    :return: lista di dizionari contenenti una soluzione euristica
    """
    f_obj=0 #funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione=[] #è una lista che conterrà tutte le schedulazioni
    lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i) #inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione
    for commessa in lista_commesse:
        macchina_schedula=None  #è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento=datetime(9999, 12, 31)#commessa.due_date  #metto come tempo di minimo completamento la due date della commessa
        tempo_minimo_setup=math.inf
        for macchina in lista_macchine: #cerco tra le macchine
            if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1:#and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_processamento=commessa.metri_da_tagliare/macchina.velocita_taglio_media  #calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup=macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa)  #calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione=aggiungi_minuti(tempo_processamento+tempo_setup,max(commessa.release_date,macchina.data_ora_disponibilita))
                if tempo_fine_lavorazione<tempo_minimo_completamento: #con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                    tempo_minimo_completamento=tempo_fine_lavorazione #assegno al tempo di completamento uguale al tempo di fine lavorazione
                    tempo_minimo_setup=tempo_setup
                    tempo_minimo_processamento=tempo_processamento
                    macchina_schedula=macchina #la variabile inizialmente settata a None assume il valore della macchina
        if macchina_schedula!=None: #se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
            #print(macchina_schedula.nome_macchina, '-->', commessa.id_commessa)
            f_obj+=commessa.priorita_cliente * ((tempo_minimo_completamento-macchina_schedula.data_ora_disponibilita).total_seconds()/60)
            schedulazione.append({"commessa": commessa.id_commessa,
                                  "macchina": macchina_schedula.nome_macchina,
                                  "inizio_setup": max(macchina_schedula.data_ora_disponibilita,commessa.release_date),
                                  "fine_setup": aggiungi_minuti(tempo_minimo_setup,max(macchina_schedula.data_ora_disponibilita,commessa.release_date)),
                                  "inizio_lavorazione": aggiungi_minuti(tempo_minimo_setup,max(macchina_schedula.data_ora_disponibilita,commessa.release_date)),
                                  "fine_lavorazione": tempo_minimo_completamento,
                                  "mt da tagliare": commessa.metri_da_tagliare,
                                  "taglio": commessa.tipologia_taglio,
                                  "macchine compatibili": [machine for machine, value in commessa.compatibilita.items()
                                                           if value == 1],
                                  "nr coltelli": commessa.numero_coltelli,
                                  "diametro_tubo": commessa.diametro_tubo,
                                  "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
            macchina_schedula.data_ora_disponibilita=tempo_minimo_completamento  # aggiorno la disponibilita della macchina che ha effettuato la lavorazione
            macchina_schedula._minuti_fine_ultima_lavorazione+=(tempo_minimo_setup+tempo_minimo_processamento)
            macchina_schedula.lista_commesse_processate.append(commessa) #aggiungo la commessa alla macchina che eseguirà la lavorazione
    return schedulazione,f_obj #lista di dizionari che contiene le informazioni relative ad una schedulazione


def Euristico5(lista_macchine:list,lista_commesse:list):
    """
    :param lista_macchine: lista di oggetti macchina contenente tutti le macchine
    :param lista_commesse: lista di oggetti commessa contenente tutte le commesse
    :return: lista di dizionari contenenti una soluzione euristica
    """
    f_obj=0 #funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione=[] #è una lista che conterrà tutte le schedulazioni
    lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i) #inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione #è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_commesse_non_schedulate=[]
    for commessa in lista_commesse:

        if len(lista_commesse_non_schedulate)>0:
            for commessa_non_schedulata in lista_commesse_non_schedulate:
                macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
                tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
                tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
                for macchina in lista_macchine:  # cerco tra le macchine
                    if macchina.disponibilita == 1 and commessa_non_schedulata.compatibilita[macchina.nome_macchina] == 1 and commessa_non_schedulata._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                        tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
                        tempo_processamento = commessa_non_schedulata.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                        tempo_setup = macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa_non_schedulata)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                        tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                        if tempo_fine_lavorazione < tempo_minimo_completamento:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                            tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                            tempo_minimo_setup = tempo_setup
                            tempo_minimo_processamento = tempo_processamento
                            macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
                if macchina_schedula != None:  # se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
                    f_obj += commessa.priorita_cliente * (tempo_minimo_completamento)  # -macchina_schedula._minuti_fine_ultima_lavorazione)
                    schedulazione.append({"commessa": commessa_non_schedulata.id_commessa,
                                          "macchina": macchina_schedula.nome_macchina,
                                          "inizio_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione, inizio_schedulazione),
                                          "fine_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup,inizio_schedulazione),
                                          "inizio_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup,inizio_schedulazione),
                                          "fine_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup + tempo_minimo_processamento,inizio_schedulazione),
                                          "mt da tagliare": commessa_non_schedulata.metri_da_tagliare,
                                          "taglio": commessa_non_schedulata.tipologia_taglio,
                                          "macchine compatibili": [machine for machine, value in commessa_non_schedulata.compatibilita.items() if value == 1],
                                          "nr coltelli": commessa_non_schedulata.numero_coltelli,
                                          "diametro_tubo": commessa_non_schedulata.diametro_tubo,
                                          "veicolo": commessa_non_schedulata.veicolo})  # dizionario che contiene le informazioni sulla schedula
                    macchina_schedula._minuti_fine_ultima_lavorazione += (tempo_minimo_setup + tempo_minimo_processamento)
                    macchina_schedula.lista_commesse_processate.append(commessa_non_schedulata)  # aggiungo la commessa alla macchina che eseguirà la lavorazione
                    lista_commesse_non_schedulate.remove(commessa_non_schedulata)

        macchina_schedula=None  #è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento=math.inf #metto come tempo di minimo completamento un tempo molto grande
        tempo_minimo_setup=math.inf #metto come tempo di setup minimo un tempo molto grande
        for macchina in lista_macchine: #cerco tra le macchine
            if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1 and commessa._minuti_release_date<=macchina._minuti_fine_ultima_lavorazione:#and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_inizio_taglio=macchina._minuti_fine_ultima_lavorazione
                tempo_processamento=commessa.metri_da_tagliare/macchina.velocita_taglio_media  #calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup=macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa)  #calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione=tempo_inizio_taglio+tempo_processamento+tempo_setup
                if tempo_fine_lavorazione<tempo_minimo_completamento: #con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                    tempo_minimo_completamento=tempo_fine_lavorazione #assegno al tempo di completamento uguale al tempo di fine lavorazione
                    tempo_minimo_setup=tempo_setup
                    tempo_minimo_processamento=tempo_processamento
                    macchina_schedula=macchina #la variabile inizialmente settata a None assume il valore della macchina
        if macchina_schedula!=None: #se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
            f_obj+=commessa.priorita_cliente*(tempo_minimo_completamento)#-macchina_schedula._minuti_fine_ultima_lavorazione)
            schedulazione.append({"commessa": commessa.id_commessa,
                                  "macchina": macchina_schedula.nome_macchina,
                                  "inizio_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione,inizio_schedulazione),
                                  "fine_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup,inizio_schedulazione),
                                  "inizio_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup,inizio_schedulazione),
                                  "fine_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup+tempo_minimo_processamento,inizio_schedulazione),
                                  "mt da tagliare": commessa.metri_da_tagliare,
                                  "taglio": commessa.tipologia_taglio,
                                  "macchine compatibili": [machine for machine, value in commessa.compatibilita.items()
                                                           if value == 1],
                                  "nr coltelli": commessa.numero_coltelli,
                                  "diametro_tubo": commessa.diametro_tubo,
                                  "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
            macchina_schedula._minuti_fine_ultima_lavorazione+=(tempo_minimo_setup+tempo_minimo_processamento)
            macchina_schedula.lista_commesse_processate.append(commessa) #aggiungo la commessa alla macchina che eseguirà la lavorazione
        else:
            lista_commesse_non_schedulate.append(commessa)

    return schedulazione,f_obj #lista di dizionari che contiene le informazioni relative ad una schedulazione

def macchina_migliore(commessa, lista_macchine, schedulazione, lista_commesse_non_schedulate,inizio_schedulazione):
    macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
    tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
    tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
    for macchina in lista_macchine:  # cerco tra le macchine
        if macchina.disponibilita == 1 and commessa.compatibilita[
            macchina.nome_macchina] == 1 and commessa._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
            tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
            tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
            tempo_setup = macchina.calcolo_setup(macchina.lista_commesse_processate[-1],
                                                 commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
            tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
            if tempo_fine_lavorazione < tempo_minimo_completamento:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                tempo_minimo_setup = tempo_setup
                tempo_minimo_processamento = tempo_processamento
                macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
    if macchina_schedula != None:  # se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
        schedulazione.append({"commessa": commessa.id_commessa,
                              "macchina": macchina_schedula.nome_macchina,
                              "inizio_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione,inizio_schedulazione),
                              "fine_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup,inizio_schedulazione),
                              "inizio_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup,inizio_schedulazione),
                              "fine_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup + tempo_minimo_processamento,inizio_schedulazione),
                              "mt da tagliare": commessa.metri_da_tagliare,
                              "taglio": commessa.tipologia_taglio,
                              "macchine compatibili": [machine for machine, value in commessa.compatibilita.items()
                                                       if value == 1],
                              "nr coltelli": commessa.numero_coltelli,
                              "diametro_tubo": commessa.diametro_tubo,
                              "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
        macchina_schedula._minuti_fine_ultima_lavorazione += (tempo_minimo_setup + tempo_minimo_processamento)
        macchina_schedula.lista_commesse_processate.append(commessa)  # aggiungo la commessa alla macchina che eseguirà la lavorazione
    else:
        lista_commesse_non_schedulate.append(commessa)

def Euristico(lista_macchine:list,lista_commesse:list):
    """
    :param lista_macchine: lista di oggetti macchina contenente tutti le macchine
    :param lista_commesse: lista di oggetti commessa contenente tutte le commesse
    :return: lista di dizionari contenenti una soluzione euristica
    """
    f_obj=0 #funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione=[] #è una lista che conterrà tutte le schedulazioni
    lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i) #inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione #è il primo lunedi disponibile che è uguale per tutte le macchine
    for commessa in lista_commesse:
        #for commes in lista_commesse_non_schedulate
        macchina_schedula=None  #è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento=math.inf #metto come tempo di minimo completamento un tempo molto grande
        tempo_minimo_setup=math.inf #metto come tempo di setup minimo un tempo molto grande
        for macchina in lista_macchine: #cerco tra le macchine
            if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1:#and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_inizio_taglio=macchina._minuti_fine_ultima_lavorazione
                tempo_processamento=commessa.metri_da_tagliare/macchina.velocita_taglio_media  #calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup=macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa)  #calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione=tempo_inizio_taglio+tempo_processamento+tempo_setup
                if tempo_fine_lavorazione<tempo_minimo_completamento: #con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                    tempo_minimo_completamento=tempo_fine_lavorazione #assegno al tempo di completamento uguale al tempo di fine lavorazione
                    tempo_minimo_setup=tempo_setup
                    tempo_minimo_processamento=tempo_processamento
                    macchina_schedula=macchina #la variabile inizialmente settata a None assume il valore della macchina
        if macchina_schedula!=None: #se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
            f_obj+=commessa.priorita_cliente*(tempo_minimo_completamento)#-macchina_schedula._minuti_fine_ultima_lavorazione)
            schedulazione.append({"commessa": commessa.id_commessa,
                                  "macchina": macchina_schedula.nome_macchina,
                                  "inizio_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione,inizio_schedulazione),
                                  "fine_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup,inizio_schedulazione),
                                  "inizio_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup,inizio_schedulazione),
                                  "fine_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup+tempo_minimo_processamento,inizio_schedulazione),
                                  "mt da tagliare": commessa.metri_da_tagliare,
                                  "taglio": commessa.tipologia_taglio,
                                  "macchine compatibili": [machine for machine, value in commessa.compatibilita.items() if value == 1],
                                  "nr coltelli": commessa.numero_coltelli,
                                  "diametro_tubo": commessa.diametro_tubo,
                                  "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
            macchina_schedula._minuti_fine_ultima_lavorazione+=(tempo_minimo_setup+tempo_minimo_processamento)
            macchina_schedula.lista_commesse_processate.append(commessa) #aggiungo la commessa alla macchina che eseguirà la lavorazione
    return schedulazione,f_obj #lista di dizionari che contiene le informazioni relative ad una schedulazione

def Euristico1(lista_macchine:list,lista_commesse:list):
    """
    :param lista_macchine: lista di oggetti macchina contenente tutti le macchine
    :param lista_commesse: lista di oggetti commessa contenente tutte le commesse
    :return: lista di dizionari contenenti una soluzione euristica
    """
    f_obj=0 #funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione=[] #è una lista che conterrà tutte le schedulazioni
    lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i) #inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione #è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_commesse_non_schedulate=[]
    for commessa in lista_commesse:

        if len(lista_commesse_non_schedulate)>0:
            for commessa_non_schedulata in lista_commesse_non_schedulate:
                macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
                tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
                tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
                for macchina in lista_macchine:  # cerco tra le macchine
                    if macchina.disponibilita == 1 and commessa_non_schedulata.compatibilita[macchina.nome_macchina] == 1: #and commessa_non_schedulata._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                        tempo_inizio_taglio = max(macchina._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date)
                        tempo_processamento = commessa_non_schedulata.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                        tempo_setup = macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa_non_schedulata)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                        tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                        if tempo_fine_lavorazione < tempo_minimo_completamento:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                            tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                            tempo_minimo_setup = tempo_setup
                            tempo_minimo_processamento = tempo_processamento
                            macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
                if macchina_schedula != None:  # se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
                    f_obj += commessa_non_schedulata.priorita_cliente * (tempo_minimo_completamento)  # -macchina_schedula._minuti_fine_ultima_lavorazione)
                    schedulazione.append({"commessa": commessa_non_schedulata.id_commessa,
                                          "macchina": macchina_schedula.nome_macchina,
                                          "inizio_setup": aggiungi_minuti(max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date), inizio_schedulazione),
                                          "fine_setup": aggiungi_minuti(max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date) + tempo_minimo_setup,inizio_schedulazione),
                                          "inizio_lavorazione": aggiungi_minuti(max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date) + tempo_minimo_setup,inizio_schedulazione),
                                          "fine_lavorazione": aggiungi_minuti(max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date) + tempo_minimo_setup + tempo_minimo_processamento,inizio_schedulazione),
                                          "mt da tagliare": commessa_non_schedulata.metri_da_tagliare,
                                          "taglio": commessa_non_schedulata.tipologia_taglio,
                                          "macchine compatibili": [machine for machine, value in commessa_non_schedulata.compatibilita.items() if value == 1],
                                          "nr coltelli": commessa_non_schedulata.numero_coltelli,
                                          "diametro_tubo": commessa_non_schedulata.diametro_tubo,
                                          "veicolo": commessa_non_schedulata.veicolo})  # dizionario che contiene le informazioni sulla schedula
                    macchina_schedula._minuti_fine_ultima_lavorazione = max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date)+(tempo_minimo_setup + tempo_minimo_processamento)
                    macchina_schedula.lista_commesse_processate.append(commessa_non_schedulata)  # aggiungo la commessa alla macchina che eseguirà la lavorazione
                    lista_commesse_non_schedulate.remove(commessa_non_schedulata)

        macchina_schedula=None  #è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento=math.inf #metto come tempo di minimo completamento un tempo molto grande
        tempo_minimo_setup=math.inf #metto come tempo di setup minimo un tempo molto grande
        for macchina in lista_macchine: #cerco tra le macchine
            if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1 and commessa._minuti_release_date<=macchina._minuti_fine_ultima_lavorazione:#and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_inizio_taglio=macchina._minuti_fine_ultima_lavorazione
                tempo_processamento=commessa.metri_da_tagliare/macchina.velocita_taglio_media  #calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup=macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa)  #calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione=tempo_inizio_taglio+tempo_processamento+tempo_setup
                if tempo_fine_lavorazione<tempo_minimo_completamento: #con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                    tempo_minimo_completamento=tempo_fine_lavorazione #assegno al tempo di completamento uguale al tempo di fine lavorazione
                    tempo_minimo_setup=tempo_setup
                    tempo_minimo_processamento=tempo_processamento
                    macchina_schedula=macchina #la variabile inizialmente settata a None assume il valore della macchina
        if macchina_schedula!=None: #se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
            f_obj+=commessa.priorita_cliente*(tempo_minimo_completamento)#-macchina_schedula._minuti_fine_ultima_lavorazione)
            schedulazione.append({"commessa": commessa.id_commessa,
                                  "macchina": macchina_schedula.nome_macchina,
                                  "inizio_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione,inizio_schedulazione),
                                  "fine_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup,inizio_schedulazione),
                                  "inizio_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup,inizio_schedulazione),
                                  "fine_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup+tempo_minimo_processamento,inizio_schedulazione),
                                  "mt da tagliare": commessa.metri_da_tagliare,
                                  "taglio": commessa.tipologia_taglio,
                                  "macchine compatibili": [machine for machine, value in commessa.compatibilita.items() if value == 1],
                                  "nr coltelli": commessa.numero_coltelli,
                                  "diametro_tubo": commessa.diametro_tubo,
                                  "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
            macchina_schedula._minuti_fine_ultima_lavorazione+=(tempo_minimo_setup+tempo_minimo_processamento)
            macchina_schedula.lista_commesse_processate.append(commessa) #aggiungo la commessa alla macchina che eseguirà la lavorazione
        else:
            lista_commesse_non_schedulate.append(commessa)
    print(len(lista_commesse_non_schedulate))
    return schedulazione,f_obj #lista di dizionari che contiene le informazioni relative ad una schedulazione

def Euristico2(lista_macchine:list,lista_commesse:list):
    """
    :param lista_macchine: lista di oggetti macchina contenente tutti le macchine
    :param lista_commesse: lista di oggetti commessa contenente tutte le commesse
    :return: lista di dizionari contenenti una soluzione euristica
    """
    f_obj=0 #funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione=[] #è una lista che conterrà tutte le schedulazioni
    lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i) #inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione #è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_commesse_non_schedulate=[]
    for commessa in lista_commesse:

        if len(lista_commesse_non_schedulate)>0:
            for commessa_non_schedulata in lista_commesse_non_schedulate:
                macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
                tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
                tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
                for macchina in lista_macchine:  # cerco tra le macchine
                    if macchina.disponibilita == 1 and commessa_non_schedulata.compatibilita[macchina.nome_macchina] == 1 and commessa_non_schedulata._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                        tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
                        tempo_processamento = commessa_non_schedulata.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                        tempo_setup = macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa_non_schedulata)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                        tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                        if tempo_fine_lavorazione < tempo_minimo_completamento:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                            tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                            tempo_minimo_setup = tempo_setup
                            tempo_minimo_processamento = tempo_processamento
                            macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
                if macchina_schedula != None:  # se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
                    f_obj += commessa_non_schedulata.priorita_cliente * (tempo_minimo_completamento)  # -macchina_schedula._minuti_fine_ultima_lavorazione)
                    schedulazione.append({"commessa": commessa_non_schedulata.id_commessa,
                                          "macchina": macchina_schedula.nome_macchina,
                                          "inizio_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione, inizio_schedulazione),
                                          "fine_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup,inizio_schedulazione),
                                          "inizio_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup,inizio_schedulazione),
                                          "fine_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione + tempo_minimo_setup + tempo_minimo_processamento,inizio_schedulazione),
                                          "mt da tagliare": commessa_non_schedulata.metri_da_tagliare,
                                          "taglio": commessa_non_schedulata.tipologia_taglio,
                                          "macchine compatibili": [machine for machine, value in commessa_non_schedulata.compatibilita.items() if value == 1],
                                          "nr coltelli": commessa_non_schedulata.numero_coltelli,
                                          "diametro_tubo": commessa_non_schedulata.diametro_tubo,
                                          "veicolo": commessa_non_schedulata.veicolo})  # dizionario che contiene le informazioni sulla schedula
                    macchina_schedula._minuti_fine_ultima_lavorazione = macchina_schedula._minuti_fine_ultima_lavorazione+(tempo_minimo_setup + tempo_minimo_processamento)
                    macchina_schedula.lista_commesse_processate.append(commessa_non_schedulata)  # aggiungo la commessa alla macchina che eseguirà la lavorazione
                    lista_commesse_non_schedulate.remove(commessa_non_schedulata)

        macchina_schedula=None  #è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento=math.inf #metto come tempo di minimo completamento un tempo molto grande
        tempo_minimo_setup=math.inf #metto come tempo di setup minimo un tempo molto grande
        for macchina in lista_macchine: #cerco tra le macchine
            if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1 and commessa._minuti_release_date<=macchina._minuti_fine_ultima_lavorazione:#and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_inizio_taglio=macchina._minuti_fine_ultima_lavorazione
                tempo_processamento=commessa.metri_da_tagliare/macchina.velocita_taglio_media  #calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup=macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa)  #calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione=tempo_inizio_taglio+tempo_processamento+tempo_setup
                if tempo_fine_lavorazione<tempo_minimo_completamento: #con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                    tempo_minimo_completamento=tempo_fine_lavorazione #assegno al tempo di completamento uguale al tempo di fine lavorazione
                    tempo_minimo_setup=tempo_setup
                    tempo_minimo_processamento=tempo_processamento
                    macchina_schedula=macchina #la variabile inizialmente settata a None assume il valore della macchina
        if macchina_schedula!=None: #se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
            f_obj+=commessa.priorita_cliente*(tempo_minimo_completamento)#-macchina_schedula._minuti_fine_ultima_lavorazione)
            schedulazione.append({"commessa": commessa.id_commessa,
                                  "macchina": macchina_schedula.nome_macchina,
                                  "inizio_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione,inizio_schedulazione),
                                  "fine_setup": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup,inizio_schedulazione),
                                  "inizio_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup,inizio_schedulazione),
                                  "fine_lavorazione": aggiungi_minuti(macchina_schedula._minuti_fine_ultima_lavorazione+tempo_minimo_setup+tempo_minimo_processamento,inizio_schedulazione),
                                  "mt da tagliare": commessa.metri_da_tagliare,
                                  "taglio": commessa.tipologia_taglio,
                                  "macchine compatibili": [machine for machine, value in commessa.compatibilita.items() if value == 1],
                                  "nr coltelli": commessa.numero_coltelli,
                                  "diametro_tubo": commessa.diametro_tubo,
                                  "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
            macchina_schedula._minuti_fine_ultima_lavorazione+=(tempo_minimo_setup+tempo_minimo_processamento)
            macchina_schedula.lista_commesse_processate.append(commessa) #aggiungo la commessa alla macchina che eseguirà la lavorazione
        else:
            lista_commesse_non_schedulate.append(commessa)

    if len(lista_commesse_non_schedulate) > 0:
        for commessa_non_schedulata in lista_commesse_non_schedulate:
            macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
            tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
            tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
            for macchina in lista_macchine:  # cerco tra le macchine
                if macchina.disponibilita == 1 and commessa_non_schedulata.compatibilita[macchina.nome_macchina] == 1:  # and commessa_non_schedulata._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                    tempo_inizio_taglio = max(macchina._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date)
                    tempo_processamento = commessa_non_schedulata.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                    tempo_setup = macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa_non_schedulata)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                    tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                    if tempo_fine_lavorazione < tempo_minimo_completamento:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                        tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                        tempo_minimo_setup = tempo_setup
                        tempo_minimo_processamento = tempo_processamento
                        macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
            if macchina_schedula != None:  # se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
                f_obj += commessa_non_schedulata.priorita_cliente * (tempo_minimo_completamento)  # -macchina_schedula._minuti_fine_ultima_lavorazione)
                schedulazione.append({"commessa": commessa_non_schedulata.id_commessa,
                                      "macchina": macchina_schedula.nome_macchina,
                                      "inizio_setup": aggiungi_minuti(max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date), inizio_schedulazione),
                                      "fine_setup": aggiungi_minuti(max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date) + tempo_minimo_setup,inizio_schedulazione),
                                      "inizio_lavorazione": aggiungi_minuti(max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date) + tempo_minimo_setup,inizio_schedulazione),
                                      "fine_lavorazione": aggiungi_minuti(max(macchina_schedula._minuti_fine_ultima_lavorazione,commessa_non_schedulata._minuti_release_date) + tempo_minimo_setup + tempo_minimo_processamento,inizio_schedulazione),
                                      "mt da tagliare": commessa_non_schedulata.metri_da_tagliare,
                                      "taglio": commessa_non_schedulata.tipologia_taglio,
                                      "macchine compatibili": [machine for machine, value in commessa_non_schedulata.compatibilita.items() if value == 1],
                                      "nr coltelli": commessa_non_schedulata.numero_coltelli,
                                      "diametro_tubo": commessa_non_schedulata.diametro_tubo,
                                      "veicolo": commessa_non_schedulata.veicolo})  # dizionario che contiene le informazioni sulla schedula
                macchina_schedula._minuti_fine_ultima_lavorazione = max(macchina_schedula._minuti_fine_ultima_lavorazione, commessa_non_schedulata._minuti_release_date) + (tempo_minimo_setup + tempo_minimo_processamento)
                macchina_schedula.lista_commesse_processate.append(commessa_non_schedulata)  # aggiungo la commessa alla macchina che eseguirà la lavorazione
                lista_commesse_non_schedulate.remove(commessa_non_schedulata)

    print(len(lista_commesse_non_schedulate))
    return schedulazione,f_obj #lista di dizionari che contiene le informazioni relative ad una schedulazione


import math
from macchina import Macchina
from solver import aggiorna_schedulazione,trova_macchina_migliore,trova_macchina_migliore_obbligo_lavorazione
import random

############

def greedy_random(lista_macchine: list, lista_commesse: list):
    f_obj = 0  # funzione obiettivo (somma pesata dei completion time --> sum priorita_cliente * tempo_completamento)
    schedulazione = []  # è una lista che conterrà tutte le schedulazioni
    lista_macchine = sorted(lista_macchine, key=lambda macchina: macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i)  # inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_commesse_non_schedulate = []
    random.shuffle(lista_commesse)
    for commessa in lista_commesse:
        for commessa_non_schedulata in lista_commesse_non_schedulate:
            macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = trova_macchina_migliore(
                commessa_non_schedulata, lista_macchine)
            if macchina_schedula != None:
                f_obj += commessa_non_schedulata.priorita_cliente * (tempo_minimo_completamento)
                aggiorna_schedulazione(commessa_non_schedulata, macchina_schedula, tempo_setup, tempo_processamento,inizio_schedulazione, schedulazione, lista_commesse_non_schedulate)
                lista_commesse_non_schedulate.remove(commessa_non_schedulata)
        macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = trova_macchina_migliore(commessa, lista_macchine)
        if macchina_schedula != None:
            f_obj += commessa.priorita_cliente * (tempo_minimo_completamento)
            aggiorna_schedulazione(commessa, macchina_schedula, tempo_setup, tempo_processamento, inizio_schedulazione,schedulazione, lista_commesse_non_schedulate)
        else:
            lista_commesse_non_schedulate.append(commessa)
    for commessa_non_schedulata in lista_commesse_non_schedulate:
        macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = trova_macchina_migliore_obbligo_lavorazione(commessa_non_schedulata, lista_macchine)
        if macchina_schedula != None:
            f_obj += commessa_non_schedulata.priorita_cliente * (tempo_minimo_completamento)
            aggiorna_schedulazione(commessa_non_schedulata, macchina_schedula, tempo_setup, tempo_processamento,inizio_schedulazione, schedulazione, lista_commesse_non_schedulate)
            lista_commesse_non_schedulate.remove(commessa_non_schedulata)
    return schedulazione, f_obj

def multistart(lista_macchine,lista_commesse):
    best_f_obj=math.inf
    best_schedula=None
    for i in range(100):
        lista_macchine_copy = lista_macchine[:]
        lista_commesse_copy = lista_commesse[:]
        schedulazione,f_obj=random_eur(lista_macchine_copy,lista_commesse_copy)
        if f_obj<best_f_obj:
            best_f_obj=f_obj
            best_schedula=schedulazione
    print(f'soluzione MULTISTART={best_f_obj}')


import math
import random


def random_eur(lista_macchine: list, lista_commesse: list, tolleranza=0.05):
    f_obj = 0  # funzione obiettivo
    schedulazione = []  # lista di schedulazioni
    lista_macchine = sorted(lista_macchine, key=lambda macchina: macchina.nome_macchina)

    for macchina in lista_macchine:
        Macchina.inizializza_lista_commesse(macchina)

    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione
    lista_commesse_non_schedulate = []

    for commessa in lista_commesse:
        for commessa_non_schedulata in lista_commesse_non_schedulate:
            macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = trova_macchina_migliore(
                commessa_non_schedulata, lista_macchine)
            if macchina_schedula is not None:
                f_obj += commessa_non_schedulata.priorita_cliente * (tempo_minimo_completamento)
                aggiorna_schedulazione(commessa_non_schedulata, macchina_schedula, tempo_setup, tempo_processamento,
                                       inizio_schedulazione, schedulazione, lista_commesse_non_schedulate)
                lista_commesse_non_schedulate.remove(commessa_non_schedulata)

        # Trova la migliore macchina in termini di tempo di completamento minimo
        macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = trova_macchina_migliore(
            commessa, lista_macchine)

        # Introduciamo una tolleranza sulla scelta della macchina
        if macchina_schedula is not None:
            # Costruiamo una lista di macchine con completamento entro una certa tolleranza
            macchine_candidate = []
            for macchina in lista_macchine:
                if macchina.disponibilita == 1 and commessa.compatibilita[macchina.nome_macchina] == 1:
                    tempo_inizio_taglio = max(macchina._minuti_fine_ultima_lavorazione, commessa._minuti_release_date)
                    tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media
                    tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1], commessa)
                    tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup

                    # Se la macchina è entro la tolleranza, aggiungiamola alla lista
                    if tempo_fine_lavorazione <= tempo_minimo_completamento * (1 + tolleranza):
                        macchine_candidate.append((macchina, tempo_setup, tempo_processamento, tempo_fine_lavorazione))

            # Selezioniamo casualmente tra le macchine candidate
            if macchine_candidate:
                macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = random.choice(
                    macchine_candidate)

            f_obj += commessa.priorita_cliente * tempo_minimo_completamento
            aggiorna_schedulazione(commessa, macchina_schedula, tempo_setup, tempo_processamento, inizio_schedulazione,
                                   schedulazione, lista_commesse_non_schedulate)
        else:
            lista_commesse_non_schedulate.append(commessa)

    # Fase finale per le commesse non schedulate
    for commessa_non_schedulata in lista_commesse_non_schedulate:
        macchina_schedula, tempo_setup, tempo_processamento, tempo_minimo_completamento = trova_macchina_migliore_obbligo_lavorazione(
            commessa_non_schedulata, lista_macchine)

        if macchina_schedula is not None:
            f_obj += commessa_non_schedulata.priorita_cliente * tempo_minimo_completamento
            aggiorna_schedulazione(commessa_non_schedulata, macchina_schedula, tempo_setup, tempo_processamento,
                                   inizio_schedulazione, schedulazione, lista_commesse_non_schedulate)
            lista_commesse_non_schedulate.remove(commessa_non_schedulata)

    return schedulazione, f_obj

def Euristico1000(lista_commesse:list,lista_macchine,lista_veicoli:list):
    data_partenza_veicoli(lista_commesse,lista_veicoli)
    lista_commesse.sort(key=lambda commessa:(-commessa.priorita_cliente,commessa.due_date.timestamp())) # ordino la lista sulla base della priorita
    schedulazione = []  # è una lista che conterrà tutte le schedulazioni
    lista_macchine = sorted(lista_macchine, key=lambda macchina: macchina.nome_macchina)
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i)  # inizializzo ogni macchina con una commessa dummy
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione  # è il primo lunedi disponibile che è uguale per tutte le macchine
    lista_commesse_non_schedulate = []
    for commessa in lista_commesse:
        veicolo_selezionato=None
        macchina_schedula = None  # è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento = math.inf  # metto come tempo di minimo completamento un tempo molto grande
        tempo_minimo_setup = math.inf  # metto come tempo di setup minimo un tempo molto grande
        tempo_minimo_processamento = math.inf
        for macchina in lista_macchine:  # cerco tra le macchine
            if macchina.disponibilita == 1 and commessa.compatibilita[macchina.nome_macchina] == 1 and commessa._minuti_release_date <= macchina._minuti_fine_ultima_lavorazione:  # and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_inizio_taglio = macchina._minuti_fine_ultima_lavorazione
                tempo_processamento = commessa.metri_da_tagliare / macchina.velocita_taglio_media  # calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup = macchina.calcolo_tempi_setup(macchina.lista_commesse_processate[-1],commessa)  # calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione = tempo_inizio_taglio + tempo_processamento + tempo_setup
                data_fine_lavorazione=aggiungi_minuti(tempo_fine_lavorazione,macchina.data_ora_disponibilita)
                veicoli_feasible=[veicolo for veicolo in lista_veicoli if (veicolo.zone_coperte in commessa.zona_cliente and veicolo.data_partenza!=None)]
                for veicolo in veicoli_feasible:
                    if tempo_setup < tempo_minimo_setup and data_fine_lavorazione<=veicolo.data_partenza and veicolo.capacita>=commessa.kg_da_tagliare:  # con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                        tempo_minimo_completamento = tempo_fine_lavorazione  # assegno al tempo di completamento uguale al tempo di fine lavorazione
                        tempo_minimo_setup = tempo_setup
                        tempo_minimo_processamento = tempo_processamento
                        macchina_schedula = macchina  # la variabile inizialmente settata a None assume il valore della macchina
                        veicolo_selezionato=veicolo
        if macchina_schedula != None:
            print(macchina_schedula.nome_macchina)
            #aggiorna_schedulazione(commessa,macchina_schedula,tempo_setup,tempo_processamento,inizio_schedulazione,schedulazione,lista_commesse_non_schedulate)
            schedulazione.append({"commessa": commessa.id_commessa,
                                  "macchina": macchina_schedula.nome_macchina,
                                  "minuti setup": tempo_setup,
                                  "minuti processamento": tempo_processamento,
                                  "inizio_setup": aggiungi_minuti(tempo_inizio_taglio, inizio_schedulazione),
                                  "fine_setup": aggiungi_minuti(tempo_inizio_taglio + tempo_setup,
                                                                inizio_schedulazione),
                                  "inizio_lavorazione": aggiungi_minuti(tempo_inizio_taglio + tempo_setup,
                                                                        inizio_schedulazione),
                                  "fine_lavorazione": aggiungi_minuti(
                                      tempo_inizio_taglio + tempo_setup + tempo_processamento,
                                      inizio_schedulazione),
                                  "mt da tagliare": commessa.metri_da_tagliare,
                                  "taglio": commessa.tipologia_taglio,
                                  "macchine compatibili": [machine for machine, value in commessa.compatibilita.items()
                                                           if value == 1],
                                  "nr coltelli": commessa.numero_coltelli,
                                  "diametro_tubo": commessa.diametro_tubo,
                                  "veicolo": commessa.veicolo})  # dizionario che contiene le informazioni sulla schedula
            veicolo_selezionato.capacita-=commessa.kg_da_tagliare
            commessa.veicolo=veicolo_selezionato.nome
    return schedulazione

def local_search_swap_intra_macchina(lista_commesse:list, lista_macchine:list, lista_veicoli:list, f_obj):
    partenze={veicolo.nome : veicolo.data_partenza for veicolo in lista_veicoli}
    inizio_schedulazione = lista_macchine[0].data_inizio_schedulazione
    f_best=f_obj
    improved=True
    eps=0.000000001
    soluzione=[]
    for macchina in lista_macchine:
        schedula=deepcopy(macchina.lista_commesse_processate)
        #schedula_minuti=deepcopy(macchina.minuti_processamenti)
        minuti_schedula=deepcopy(macchina.minuti_processamenti)
        if len(schedula)>=3:
            while improved:
                improved=False
                for i in range(1,len(schedula)-1):
                    for j in range(i+1,len(schedula)-1):
                        veicolo_i = schedula[i].veicolo
                        veicolo_j = schedula[j].veicolo
                        delta=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])+macchina.calcolo_tempi_setup(schedula[j],schedula[i+1])+\
                              macchina.calcolo_tempi_setup(schedula[j-1],schedula[i])+macchina.calcolo_tempi_setup(schedula[i],schedula[j+1])+ \
                              -macchina.calcolo_tempi_setup(schedula[i-1],schedula[i])-macchina.calcolo_tempi_setup(schedula[i],schedula[i+1])+ \
                              -macchina.calcolo_tempi_setup(schedula[j-1],schedula[j])-macchina.calcolo_tempi_setup(schedula[j],schedula[j+1])
                        if delta>eps:
                            #minuti_schedula=deepcopy(schedula_minuti)
                            comm_i=schedula[i]
                            schedula[i]=schedula[j]
                            schedula[j]=comm_i
                            tempo_inizio_commessa_j=macchina.minuti_processamenti[i-1]
                            tempo_setup_commessa_j_inizio=macchina.calcolo_tempi_setup(schedula[i-1],schedula[j])
                            tempo_processamento_commessa_j=schedula[j].metri_da_tagliare/macchina.velocita_taglio_media
                            minuti_fine_commessa_j=tempo_inizio_commessa_j+tempo_setup_commessa_j_inizio+tempo_processamento_commessa_j
                            minuti_schedula[i]=minuti_fine_commessa_j
                            for k in range(i+1,len(minuti_schedula)):
                                minuti_schedula[k]=minuti_schedula[k-1]+macchina.calcolo_tempi_setup(schedula[k-1],schedula[k])+schedula[k].metri_da_tagliare/macchina.velocita_taglio_media
                            data_fine_i=aggiungi_minuti(minuti_schedula[j],inizio_schedulazione)
                            data_fine_j=aggiungi_minuti(minuti_schedula[i],inizio_schedulazione)
                            if partenze[veicolo_i]>=data_fine_i and partenze[veicolo_j]>=data_fine_j:
                                improved=True
                                f_best+=delta
                                #schedula_minuti=deepcopy(minuti_schedula)
                                print(f'scambio {schedula[i].id_commessa} con {schedula[j].id_commessa} con delta={delta} su {macchina.nome_macchina}')
                                #if improved:
                                    #break
                            else:
                                print('scambio non feasible')
                                schedula=deepcopy(macchina.lista_commesse_processate)
                                minuti_schedula=deepcopy(macchina.minuti_processamenti)
                    #if improved:
                        #break
        date_schedula=minuti_schedula
        commesse_schedula=schedula
        return_schedulazione(commesse_schedula,date_schedula,macchina,inizio_schedulazione)
        soluzione_macchina={macchina.nome_macchina:{'commesse':commesse_schedula,'date':date_schedula}}
        soluzione.append(soluzione_macchina)
        date_schedula=[aggiungi_minuti(minuti_schedula[h],inizio_schedulazione) for h in range(len(minuti_schedula))]
        print(date_schedula)
    return soluzione,f_best
