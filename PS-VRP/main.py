#from commessa import Commessa
#from macchina import Macchina
#from veicolo import Veicolo
import read_excel
import solver
import output
from copy import deepcopy
import time
#from datetime import timedelta
#from datetime import datetime
from colorama import Fore, Style, init

##INPUT(s) [Macchine, Commesse, Veicoli (Vettori)]
file_macchine_excel="PS-VRP/Dati_input/Estrazione macchine 4.xlsx"
file_commesse_excel="PS-VRP/Dati_input/Estrazione commesse 4.xlsx"
file_veicoli_excel="PS-VRP/Dati_input/Estrazione veicoli 4.xlsx"

##ELABORAZIONI SU INPUT(s)
lista_macchine=read_excel.read_excel_macchine(file_macchine_excel) #Lista base oggetti macchina
read_excel.read_attrezzaggio_macchine(file_macchine_excel,lista_macchine)
inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione
lista_commesse=read_excel.read_excel_commesse(file_commesse_excel,inizio_schedulazione) #Lista base oggetti commessa
read_excel.read_compatibilita(file_commesse_excel,lista_commesse) #aggiungo le compatibilita commessa-macchina alle commesse della lista passata come parametro(lista con tutte le commesse)
lista_veicoli=read_excel.read_excel_veicoli(file_veicoli_excel) #Lista base oggetti veicolo
lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
#for commessa in lista_commesse:
#    print(f'Commessa: {commessa.id_commessa}, Compatibilità: {commessa.compatibilita}')#print(f'Lista macchine {lista_macchine}, Lista veicoli {lista_veicoli}, Lista_commesse {lista_commesse}')

init(autoreset=True)  # Ripristina i colori dopo ogni print

## EURISTICO COSTRUTTIVO
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}EURISTICO COSTRUTTIVO".center(40))
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}\n")
print(f"{Fore.GREEN}{Style.BRIGHT}COMMESSE SENZA CAMPI MANCANTI (LETTE CORRETTAMENTE): {len(lista_commesse)}")

start_time_eur = time.time()

commesse_da_schedulare, commesse_filtro_zone, commesse_filtro_veicoli, commesse_scartate = solver.filtro_commesse(lista_commesse, lista_veicoli)
schedulazione3, f_obj3, causa_fallimento, lista_macchine = solver.euristico_costruttivo(commesse_da_schedulare, lista_macchine, lista_veicoli, commesse_scartate)
output.write_output_soluzione_euristica(schedulazione3, "PS-VRP/OUTPUT_TEST/euristico_costruttivo.xlsx")
print(f'Fallimenti euristico costruttivo {len(causa_fallimento)}; Filtrate per zone {len(commesse_filtro_zone)}; Filtrate per veicoli {len(commesse_filtro_veicoli)}')
commesse_non_schedulate = causa_fallimento | commesse_filtro_zone | commesse_filtro_veicoli #| commesse_oltre_data (in caso d'uso, da reinserire eventualmente anche come output della chiamata al solver)

print(f"\n{Fore.RED}{Style.BRIGHT}COMMESSE NON SCHEDULATE (su veicoli): {len(commesse_non_schedulate)}")
print(f"{Fore.RED}Dettaglio motivi: {commesse_non_schedulate}")
print(f"\n{Fore.YELLOW}Funzione obiettivo euristico: {f_obj3} minuti di setup\n")

end_time_eur = time.time()
tot_time_eur = end_time_eur - start_time_eur

solver.grafico_schedulazione(schedulazione3)

## DEEPCOPIES PER RICERCHE LOCALI
lista_veicoli_copy = deepcopy(lista_veicoli)
lista_macchine_copy = deepcopy(lista_macchine)
lista_commesse_copy = deepcopy(lista_commesse)
lista_veicoli_copy1 = deepcopy(lista_veicoli)
lista_macchine_copy1 = deepcopy(lista_macchine)
lista_commesse_copy1 = deepcopy(lista_commesse)
lista_veicoli_copy2 = deepcopy(lista_veicoli)
#for macchina in lista_macchine:
#    print(f'La macchina {macchina.nome_macchina} ha {len(macchina.lista_commesse_processate)} commesse processate')
lista_macchine_copy2 = deepcopy(lista_macchine)
lista_commesse_copy2 = deepcopy(lista_commesse)

## RICERCHE LOCALI
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}RICERCHE LOCALI".center(40))
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}\n")

# M2M
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS1 (Insert inter-macchina)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start1 = time.time()
soluzione1, f1, contatoreLS1 = solver.move_2_macchine(lista_macchine_copy2, lista_veicoli_copy2, f_obj3, schedulazione3)
print(f"{Fore.YELLOW}Funzione obiettivo LS1: {f1} minuti di setup")
print(f"Mosse LS1: {contatoreLS1}")
output.write_output_soluzione_euristica(soluzione1, "PS-VRP/OUTPUT_TEST/insert_inter.xlsx")
tot1 = time.time() - start1
solver.grafico_schedulazione(soluzione1)  # TEMP

# M
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS2 (Insert intra-macchina)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_move = time.time()
soluzione2, f2, contatoreLS2 = solver.move_no_delta(lista_macchine_copy1, lista_veicoli_copy1, f_obj3, schedulazione3)
soluzione_move = [b for a in soluzione2 for b in a]
print(f"{Fore.YELLOW}Funzione obiettivo LS2: {f2} minuti di setup")
print(f"Mosse LS2: {contatoreLS2}")
output.write_output_soluzione_euristica(soluzione_move, "PS-VRP/OUTPUT_TEST/insert_intra.xlsx")
tot2 = time.time() - start_time_move
solver.grafico_schedulazione(soluzione_move)  # TEMP

# S
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS3 (Swap intra-macchina)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_swap = time.time()
soluzione3, f3, contatoreLS3 = solver.swap_no_delta(lista_macchine_copy, lista_veicoli_copy, f_obj3, schedulazione3)
soluzione_swap = [b for a in soluzione3 for b in a]
print(f"{Fore.YELLOW}Funzione obiettivo LS3: {f3} minuti di setup")
print(f"Mosse LS3: {contatoreLS3}")
output.write_output_soluzione_euristica(soluzione_swap, "PS-VRP/OUTPUT_TEST/swap_intra.xlsx")
tot3 = time.time() - start_time_swap
solver.grafico_schedulazione(soluzione_swap)  # TEMP

# SEQUENZA PARZIALE
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}G+LS1+LS2 (sequenza parziale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_tot = time.time()
soluzione4, f4, contatoreLS2 = solver.move_no_delta(lista_macchine_copy2, lista_veicoli_copy2, f1, soluzione1)
print(f'Mosse LS1+LS2: {contatoreLS1+contatoreLS2}')
soluzione_move = [b for a in soluzione4 for b in a]
print(f"{Fore.YELLOW}Funzione obiettivo LS1+LS2: {f4} minuti di setup")

# SEQUENZA COMPLETA
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}G+LS1+LS2+LS3 (sequenza finale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
soluzione5, f5, contatoreLS3 = solver.swap_no_delta(lista_macchine_copy2, lista_veicoli_copy2, f4, soluzione_move)
print(f'Mosse LS1+LS2+LS3: {contatoreLS1+contatoreLS2+contatoreLS3}')
soluzione_swap = [b for a in soluzione5 for b in a]
print(f"{Fore.YELLOW}Funzione obiettivo LS1+LS2+LS3: {f5} minuti di setup")
output.write_output_soluzione_euristica(soluzione_swap, "PS-VRP/OUTPUT_TEST/sequenza.xlsx")
tot_tot = time.time() - start_time_tot

## STAMPE FINALI
print(f"{Fore.MAGENTA}{Style.BRIGHT}\n{'='*40}")
print(f"{Fore.MAGENTA}{Style.BRIGHT}RISULTATI FINALI".center(40))
print(f"{Fore.MAGENTA}{Style.BRIGHT}{'='*40}\n")

print(f"{Fore.GREEN}COMMESSE LETTE CORRETTAMENTE: {len(lista_commesse)}")
print(f"{Fore.GREEN}COMMESSE POST FILTRO ZONE E FILTRO VEICOLI (Interne a zona aperta): {len(commesse_da_schedulare)}")
print(f"{Fore.GREEN}COMMESSE SCARTATE (RELEGATE A TERZO CICLO): {len(commesse_scartate)}")
print(f"{Fore.GREEN}COMMESSE CORRETTAMENTE SCHEDULATE SU MACCHINA: {len(schedulazione3)}\n")

print(f"{Fore.BLUE}TEMPO Greedy: {tot_time_eur:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy + LS1: {tot_time_eur + tot1:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy + LS2: {tot_time_eur + tot2:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy + LS3: {tot_time_eur + tot3:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy + LS1+LS2+LS3: {tot_time_eur + tot1 + tot_tot:.2f}s")

solver.grafico_schedulazione(soluzione_swap)  # Soluzione finale