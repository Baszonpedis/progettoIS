
from commessa import Commessa
from datetime import datetime
from datetime import timedelta
import pandas as pd

class Macchina():
    def __init__(self,nome_macchina,disponibilita,tempo_setup_medio,velocita_taglio_media,bobina_foglio,setup_cambio_albero,setup_coltelli_fisso,setup_cambio_coltelli,tempo_carico_bobina,tempo_avvio_taglio,tempo_scarico_bobina,tempo_confezionamento,data_ora_disponibilita,data_inizio_schedulazione):
        self.nome_macchina=nome_macchina
        self.disponibilita=disponibilita
        self.tempo_setup_medio=tempo_setup_medio
        self.velocita_taglio_media=velocita_taglio_media
        self.bobina_foglio=bobina_foglio
        self.attrezzaggio=None
        self.lista_commesse_processate=[]
        self.data_ora_disponibilita=data_ora_disponibilita
        self.data_inizio_schedulazione=data_inizio_schedulazione

        m_1=int((data_ora_disponibilita - data_inizio_schedulazione).total_seconds() / 60) #differenza in minuti tra il lunedi della settimana e il primo giorno di disponibilita della macchina
        m_2=m_1 // 1440  # 1440 minuti totali in 24 ore (giorni trascorsi tra data_inizio_schedulazione e data_ora_disponibilita)
        m_3=m_1 // 10080  # 10080 minuti totali in 7 giorni (numero di settimane trascorse tra data_inizio_schedulazione e data_ora_disponibilita)
        gg_lavorativi = 5
        h_lavorative = 8 #ore lavorative in una giornata
        m_lavorativi = round(h_lavorative * 60) #minuti lavorativi 480 al giorno
        self._minuti_fine_ultima_lavorazione = max(m_1 - 2 * m_lavorativi * m_2 - 2 * m_lavorativi * m_3, 0) #minuti lavorativi che separano l'inizio della schedulazione con la prima disponibilita della macchina

        self.setup_cambio_albero = setup_cambio_albero
        self.setup_coltelli_fisso = setup_coltelli_fisso
        self.setup_cambio_coltelli = setup_cambio_coltelli
        self.tempo_carico_bobina = tempo_carico_bobina
        self.tempo_avvio_taglio = tempo_avvio_taglio
        self.tempo_scarico_bobina = tempo_scarico_bobina
        self.tempo_confezionamento = tempo_confezionamento
        #self.numero_tubi_utilizzati = nr_tubi_utilizzati
        #self.contatore_tubi= nr_tubi_utilizzati // 40
        #self.minuti_processamenti=[self._minuti_fine_ultima_lavorazione]
        #self.minuti_processamenti=self._minuti_fine_ultima_lavorazione
        self.ultima_lavorazione=self._minuti_fine_ultima_lavorazione

    def calcolo_setup(self,commessa1:Commessa,commessa2:Commessa):
        """
        :param commessa1: oggetto commessa che è stato lavorato sulla macchina
        :param commessa2: oggetto commessa che si vuole provare a lavorare sulla macchina
        :return: tempo di setup sulla macchina per passare dalla commessa1 alla commessa2
        """
        #se bobina e bobina così se bobina e foglio ERR, se foglio e foglio altra cosa
        t_coltelli=30 #si ipotizza un tempo per montare/smontare un singolo coltello (30 minuti)
        t_tubo=50 #si considera un tempo per cambiare il tubo (50 minuti)
        tempo_coltelli=abs(commessa1.numero_coltelli-commessa2.numero_coltelli)*t_coltelli #tempo necessario a cambiare i coltelli
        if commessa1.diametro_tubo!=commessa2.diametro_tubo:
            tempo_tubo=t_tubo #se il tubo tra le due commesse è diverso è necessario cambiarlo
        else:
            tempo_tubo=0 #se il tubo è uguale il tempo è zero
        tempo_setup=tempo_coltelli+tempo_tubo #calcolo il tempo totale di setup
        #if commessa2.id_commessa==242655:
            #print('sei qui ', self.nome_macchina)
            #print(commessa1.numero_coltelli)
            #print(commessa2.numero_coltelli)
            #print(tempo_coltelli)
        return tempo_setup #ritorno il tempo totale di setup

    def inizializza_lista_commesse(self):
        """
        funzione che serve per inserire una commessa fittizzia all'inizio della schedulazione di una macchina.
        il numero di coltelli e il diametro del tubo sono quelli dell'ultima commessa schedulata
        """
        if str(self.bobina_foglio).lower()=='bobina':
            commessa_dummy=Commessa(-1,pd.to_datetime('03/07/2024'),pd.to_datetime('03/07/2024'),-1,0,0,-1,None,1,1,self.attrezzaggio['diametro_tubo'],self.data_inizio_schedulazione,'') #commessa fittizia che viene inserita su ogni macchina
            commessa_dummy.numero_coltelli=self.attrezzaggio['numero_coltelli']
            #print(self.nome_macchina,' ',self.attrezzaggio['numero_coltelli'],' ',self.attrezzaggio['diametro_tubo'])
            self.lista_commesse_processate.append(commessa_dummy) #si aggiunge la commessa alla lista delle commesse processate dalla macchina
        else:
            commessa_dummy = Commessa(-1, pd.to_datetime('03/07/2024'), pd.to_datetime('03/07/2024'), -1, 0, 0, -1,None, 1, 0, 0, self.data_inizio_schedulazione,'')
            self.lista_commesse_processate.append(commessa_dummy)

    def converti_minuti_in_giorni(self):
        gg_lavorativi= 5
        h_lavorative=8
        # converte i minuti di lavorazione in data espressa in gg-mm-aaaa h-m-s
        numero_settimana = self._minuti_fine_ultima_lavorazione // round(h_lavorative*gg_lavorativi*60)
        numero_minuti = self._minuti_fine_ultima_lavorazione % round(h_lavorative*60)
        numero_giorni = self._minuti_fine_ultima_lavorazione // round(h_lavorative*60)
        return timedelta(minutes=numero_minuti) + timedelta(days=numero_giorni + numero_settimana * 2)

    def calcolo_tempi_setup(self, commessa1:Commessa, commessa2:Commessa):
        """
        :param commessa1: oggetto commessa che è stato lavorato sulla macchina
        :param commessa2: oggetto commessa che si vuole provare a lavorare sulla macchina
        :return: tempo di setup sulla macchina per passare dalla commessa1 alla commessa2
        """
        tempo_setup = 0  # inizializzo il tempo di setup a zero
        if str(self.bobina_foglio).lower()=='bobina': #macchine taglio a bobina
            if commessa1.diametro_tubo!=commessa2.diametro_tubo: # se il diametro del tubo tra le due commesse è diverso inserisco un tempo di setup
                tempo_setup+=self.setup_cambio_albero
            tempo_setup+=self.setup_coltelli_fisso
            differenza_coltelli=abs((commessa1.numero_coltelli-2)-(commessa2.numero_coltelli-2))
            tempo_setup+=(differenza_coltelli*self.setup_cambio_coltelli)
            tempo_setup+=self.tempo_avvio_taglio
            #if commessa2.kg_da_tagliare>=500 and (self.nome_macchina=='H7' or self.nome_macchina=='R5' or or self.nome_macchina=='R5'):
            #    tempo_setup+=7
            tempo_setup+=self.tempo_carico_bobina
            tempo_setup+=self.tempo_scarico_bobina
            tempo_setup+=self.tempo_confezionamento
            #self.numero_tubi_utilizzati+=1
            #if self.numero_tubi_utilizzati // 40 > self.contatore_tubi:
            #    self.contatore_tubi+=1
            #    tempo_setup+=2
            #if commessa2.materiale=='alluminio':
                #tempo_setup+=10
        if str(self.bobina_foglio).lower()=='foglio': #macchine taglio a foglio
            tempo_setup=0
        return tempo_setup