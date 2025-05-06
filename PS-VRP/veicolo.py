
class Veicolo():
    def __init__(self,nome,data_partenza,zone_coperte,capacita):
        self.nome=nome
        #self.disponibilita=disponibilita
        self.capacita=capacita
        self.zone_coperte=zone_coperte
        self.data_partenza=data_partenza

    def set_data_partenza(self,data):
        self.data_partenza=data
        '''funzione per inizializzare set e get
            vado a fare sort delle commesse per priorità e due date
            poi schedulo minimizzando i setup'''