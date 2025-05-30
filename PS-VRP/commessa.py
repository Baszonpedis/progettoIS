#Parametri preliminari
minuti_in_un_giorno = 1440
minuti_in_una_settimana = 10080
ore_di_lavoro = 8
minuti_di_lavoro = ore_di_lavoro * 60

class Commessa():
    def __init__(self,id_commessa,release_date,due_date,priorita_cliente,
                 metri_da_tagliare,kg_da_tagliare,zona_cliente,tipologia_taglio,
                 fascia_iniziale,fascia_finale,diametro_tubo,data_inizio_schedulazione,
                 materiale, tassativita, id_tassativo):
        self.id_commessa=id_commessa
        self.release_date=release_date
        self.due_date=due_date
        self.metri_da_tagliare=metri_da_tagliare
        self.kg_da_tagliare=kg_da_tagliare
        self.zona_cliente=zona_cliente
        self.priorita_cliente=priorita_cliente+1 #+1 per evitare divisioni per zero
        #De-commentare a seguito se serve settare priorita_cliente in base alla zona (prioritizzando così "zona zero")
        # if isinstance(zona_cliente, list): #necessario per come viene letto poi in modo diverso nel codice
        #    self.priorita_cliente = 50 if 0 in zona_cliente else priorita_cliente
        #else:
        #    self.priorita_cliente = 50 if zona_cliente == 0 else priorita_cliente
        self.compatibilita=None #matrice compatibilita commessa-macchina. inizialmente viene messo None per poi rimpiazzarlo con un dizionario
        self.tipologia_taglio=tipologia_taglio
        self.fascia_iniziale=fascia_iniziale
        self.fascia_finale=fascia_finale
        self.numero_coltelli=self.calcolo_nr_coltelli() #round per intero più vicino se un campo è vuoto mettere media coltelli
        self.diametro_tubo=diametro_tubo
        self.veicolo=None #veicolo a cui la commessa viene associata (veicolo che si occuperà della delivery)
        self.data_inizio_schedulazione=data_inizio_schedulazione
        #print(f'Release date di partenza {release_date}, data inizio schedulaz {data_inizio_schedulazione}')
        m_1 = int((release_date - data_inizio_schedulazione).total_seconds() / 60)  # differenza in minuti tra il lunedi della settimana e il primo giorno di disponibilita della macchina
        m_2 = m_1 // minuti_in_un_giorno #(giorni trascorsi tra data_inizio_schedulazione e data_ora_disponibilita)
        m_3 = m_1 // minuti_in_una_settimana  #(numero di settimane trascorse tra data_inizio_schedulazione e data_ora_disponibilita)
        m_lavorativi = round(ore_di_lavoro * 60)  # minuti lavorativi (default: 480/gg)
        self._minuti_release_date = max(m_1 - 2 * m_lavorativi * m_2 - 2 * m_lavorativi * m_3, 0)  # minuti lavorativi che separano l'inizio della schedulazione con la prima disponibilita della macchina
        self.materiale=materiale
        #NUOVI CAMPI IN ITINERE
        self.tassativita=tassativita
        self.id_tassativo=id_tassativo

    def calcolo_nr_coltelli(self):
        if str(self.tipologia_taglio).lower()=='bobina':
            return int(self.fascia_iniziale/self.fascia_finale)+1
        else:
            return 0