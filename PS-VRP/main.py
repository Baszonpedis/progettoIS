
from commessa import Commessa
from macchina import Macchina
from veicolo import Veicolo
import read_excel
import solver
import output
from copy import deepcopy
import time
from datetime import timedelta
from datetime import datetime

file_macchine_excel="INPUT_TEST\MACCHINE12.xlsx" # metto il nome del file all'interno di una variabile
file_commesse_excel="INPUT_TEST\COMMESSE_200.xlsx" # metto il nome del file all'interno di una variabile
lista_macchine=read_excel.read_excel_macchine(file_macchine_excel) # creo una lista di oggetti macchina
read_excel.read_attrezzaggio_macchine(file_macchine_excel,lista_macchine)
inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione
lista_commesse=read_excel.read_excel_commesse(file_commesse_excel,inizio_schedulazione) # creo una lista di oggetti commessa
read_excel.read_compatibilita(file_commesse_excel,lista_commesse) #aggiungo le compatibilita commessa-macchina alle commesse della lista passata come parametro(lista con tutte le commesse)
lista_veicoli=read_excel.read_excel_veicoli("INPUT_TEST\VEICOLI5.xlsx")
lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)

start_time_eur = time.time()
print()
print('EURISTICO COSTRUTTIVO')
commesse_filtrate=solver.filtro_commesse(lista_commesse,lista_veicoli)
numero_commesse_filtrate=len(commesse_filtrate)
schedulazione3,f_obj3=solver.Euristico_Costruttivo(commesse_filtrate,lista_macchine,lista_veicoli)
#output.write_output_soluzione_euristica(schedulazione3,"Dati_output\euristico_risultati_euristico3.xlsx")
output.write_output_soluzione_euristica(schedulazione3,"OUTPUT_TEST\euristico_1.xlsx")
print(f'funzione obiettivo euristico {f_obj3}')
end_time_eur = time.time()
tot_time_eur= end_time_eur-start_time_eur

print()

lista_veicoli_copy=deepcopy(lista_veicoli)
lista_macchine_copy=deepcopy(lista_macchine)
lista_commesse_copy=deepcopy(lista_commesse)
lista_veicoli_copy1=deepcopy(lista_veicoli)
lista_macchine_copy1=deepcopy(lista_macchine)
lista_commesse_copy1=deepcopy(lista_commesse)
lista_veicoli_copy2=deepcopy(lista_veicoli)
lista_macchine_copy2=deepcopy(lista_macchine)
lista_commesse_copy2=deepcopy(lista_commesse)

start1=time.time()
print('Move 2 macchine')
soluzione1,f1=solver.move_2_macchine(lista_macchine_copy2,lista_veicoli_copy2,f_obj3,schedulazione3)
print(f'funzione obiettivo move {f1}')
output.write_output_soluzione_euristica(soluzione1,"OUTPUT_TEST\euristico_2.xlsx")
end1=time.time()
tot1=end1-start1

print()

start_time_move=time.time()
print('Move')
soluzione2,f2=solver.move_no_delta(lista_macchine_copy1,lista_veicoli_copy1,f_obj3,schedulazione3)
soluzione_move=[]
for a in soluzione2:
    for b in a:
        soluzione_move.append(b)
print(f'funzione obiettivo move {f2}')
output.write_output_soluzione_euristica(soluzione_move,"OUTPUT_TEST\euristico_3.xlsx")
end_time_move=time.time()
tot2 = end_time_move-start_time_move
print()

start_time_swap=time.time()
print('Swap')
soluzione3,f3=solver.swap_no_delta(lista_macchine_copy,lista_veicoli_copy,f_obj3,schedulazione3)
soluzione_swap=[]
for a in soluzione3:
    for b in a:
        soluzione_swap.append(b)
print(f'funzione obiettivo swap {f3}')
output.write_output_soluzione_euristica(soluzione_swap,"OUTPUT_TEST\euristico_4.xlsx")
end_time_swap=time.time()
tot3= end_time_swap-start_time_swap

print()

start_time_tot=time.time()
print('sequenza Move')
soluzione4,f4=solver.move_no_delta(lista_macchine_copy2,lista_veicoli_copy2,f1,soluzione1)
soluzione_move=[]
for a in soluzione4:
    for b in a:
        soluzione_move.append(b)
print(f'funzione obiettivo move {f4}')
#output.write_output_soluzione_euristica(soluzione_move,"OUTPUT_TEST\euristico_5.xlsx")
print()
print('sequenza Swap')
soluzione5,f5=solver.swap_no_delta(lista_macchine_copy2,lista_veicoli_copy2,f4,soluzione_move)
soluzione_swap=[]
for a in soluzione5:
    for b in a:
        soluzione_swap.append(b)
print(f'funzione obiettivo swap {f5}')
output.write_output_soluzione_euristica(soluzione_swap,"OUTPUT_TEST\euristico_5.xlsx")
end_time_tot=time.time()
tot_tot = end_time_move-start_time_move



print()
print('COMMESSE INIZIALI:',len(lista_commesse))
print('COMMESSE FILTRATE:',numero_commesse_filtrate)
print('COMMESSE SCHEDULATE:',len(schedulazione3))



print()

print('TEMPO Greedy:',tot_time_eur)
print('TEMPO Greedy + LS1:',tot_time_eur+tot1) #move2
print('TEMPO Greedy + LS2:',tot_time_eur+tot2) #move
print('TEMPO Greedy + LS3:',tot_time_eur+tot3) #swap
print('TEMPO Greedy + LS1 + LS2 + LS3:',tot_time_eur+tot1+tot_tot) #tutti







