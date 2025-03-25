
class Commessa():
    def __init__(self,id_commessa,release_date,due_date,priorita_cliente,metri_da_tagliare,kg_da_tagliare,zona_cliente,tipologia_taglio,fascia_iniziale,fascia_finale,diametro_tubo,data_inizio_schedulazione,materiale):
        self.id_commessa=id_commessa
        self.release_date=release_date
        self.due_date=due_date
        self.priorita_cliente=priorita_cliente
        self.metri_da_tagliare=metri_da_tagliare
        self.kg_da_tagliare=kg_da_tagliare
        self.zona_cliente=zona_cliente
        self.compatibilita=None #matrice compatibilita commessa-macchina. inizialmente viene messo None per poi rimpiazzarlo con un dizionario
        self.tipologia_taglio=tipologia_taglio
        self.fascia_iniziale=fascia_iniziale
        self.fascia_finale=fascia_finale
        self.numero_coltelli=self.calcolo_nr_coltelli() #round per intero più vicino se un campo è vuoto mettere media coltelli
        self.diametro_tubo=diametro_tubo
        self.veicolo=None #veicolo a cui la commessa viene associata (veicolo che si occuperà della delivery)
        self.data_inizio_schedulazione=data_inizio_schedulazione

        m_1 = int((release_date - data_inizio_schedulazione).total_seconds() / 60)  # differenza in minuti tra il lunedi della settimana e il primo giorno di disponibilita della macchina
        m_2 = m_1 // 1440  # 1440 minuti totali in 24 ore (giorni trascorsi tra data_inizio_schedulazione e data_ora_disponibilita)
        m_3 = m_1 // 10080  # 10080 minuti totali in 7 giorni (numero di settimane trascorse tra data_inizio_schedulazione e data_ora_disponibilita)
        gg_lavorativi = 5
        h_lavorative = 8  # ore lavorative in una giornata
        m_lavorativi = round(h_lavorative * 60)  # minuti lavorativi 480 al giorno
        self._minuti_release_date = max(m_1 - 2 * m_lavorativi * m_2 - 2 * m_lavorativi * m_3, 0)  # minuti lavorativi che separano l'inizio della schedulazione con la prima disponibilita della macchina

        self.materiale=materiale

    def calcolo_nr_coltelli(self):
        if str(self.tipologia_taglio).lower()=='bobina':
            return int(self.fascia_iniziale/self.fascia_finale)+1
        else:
            return 0


