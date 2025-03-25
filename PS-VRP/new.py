
import math
from datetime import datetime,timedelta
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from commessa import Commessa
from macchina import Macchina
from veicolo import Veicolo
import macchina


def Euristico(lista_macchine:list,lista_commesse:list):
    """
    :param lista_macchine: lista di oggetti macchina contenente tutti le macchine
    :param lista_commesse: lista di oggetti commessa contenente tutte le commesse
    :return: lista di dizionari contenenti una soluzione euristica
    """
    for i in lista_macchine:
        Macchina.inizializza_lista_commesse(i) #inizializzo ogni macchina con una commessa dummy

    schedulazione=[] #è una lista che conterrà tutte le schedulazioni
    for commessa in lista_commesse:
        macchina_schedula=None  #è la macchina che schedulerà la commessa in questione. inizialmente è inizializzata a None
        tempo_minimo_completamento=datetime(9999, 12, 31)#commessa.due_date  #metto come tempo di minimo completamento la due date della commessa
        for macchina in lista_macchine: #cerco tra le macchine
            if macchina.disponibilita==1 and commessa.compatibilita[macchina.nome_macchina]==1:#and macchina.bobina_foglio==commessa.tipologia_taglio and commessa.compatibilita[macchina.nome_macchina]==1: #controllo se la macchina è disponibile, se esegue la corretta tipologia di taglio e se la commessa è compatibile con la macchina
                tempo_processamento=commessa.metri_da_tagliare/macchina.velocita_taglio_media  #calcolo il tempo necessario per processare la commessa che è dato dai metri da tagliare/velocita taglio (tempo=spazio/velocita)
                tempo_setup=macchina.calcolo_setup(macchina.lista_commesse_processate[-1],commessa)  #calcolo il tempo di setup come il tempo necessario a passare dall'ultima lavorazione alla lavorazione in questione
                tempo_fine_lavorazione=max(commessa.release_date,macchina.data_ora_disponibilita)+timedelta(minutes=tempo_processamento)+timedelta(minutes=tempo_setup) #calcolo quale sarebbe il tempo di fine lavorazione
                if tempo_fine_lavorazione<tempo_minimo_completamento: #con questa condizione trovo la macchina che completa la lavorazione della commessa nell'istante minore possibile
                    tempo_minimo_completamento=tempo_fine_lavorazione #assegno al tempo di completamento uguale al tempo di fine lavorazione
                    macchina_schedula=macchina #la variabile inizialmente settata a None assume il valore della macchina
        if macchina_schedula!=None: #se sono riuscito ad assegnare la commessa ad una macchina aggiorno la sua disponibilita e eseguo la print
            print(macchina_schedula.nome_macchina, '-->', commessa.id_commessa)
            schedulazione.append({"macchina": macchina_schedula.nome_macchina,"commessa": commessa.id_commessa,"inizio_setup":max(macchina_schedula.data_ora_disponibilita,commessa.release_date),"fine_setup":max(macchina_schedula.data_ora_disponibilita,commessa.release_date)+timedelta(minutes=tempo_setup),"inizio_lavorazione":max(macchina_schedula.data_ora_disponibilita,commessa.release_date)+timedelta(minutes=tempo_setup),"fine_lavorazione":tempo_minimo_completamento,"veicolo":0})  # dizionario che contiene le informazioni sulla schedula
            macchina_schedula.data_ora_disponibilita = tempo_minimo_completamento  # aggiorno la disponibilita della macchina che ha effettuato la lavorazione
            macchina_schedula.lista_commesse_processate.append(commessa) #aggiungo la commessa alla macchina che eseguirà la lavorazione
    return schedulazione #lista di dizionari che contiene le informazioni relative ad una schedulazione