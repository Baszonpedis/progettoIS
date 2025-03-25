
class Veicolo():
    def __init__(self,nome,data_disponibilita,disponibilita,capacita,zone_coperte):
        self.nome=nome
        self.data_disponibilita=data_disponibilita
        self.disponibilita=disponibilita
        self.capacita=capacita
        self.zone_coperte=zone_coperte
        self.data_partenza=None

    def set_data_partenza(self,data):
        self.data_partenza=data
        '''funzione per inizializzare set e get
            vado a fare sort delle commesse per priorità e due date
            poi schedulo minimizzando i setup'''