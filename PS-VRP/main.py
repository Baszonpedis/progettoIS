
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

##INPUT
file_macchine_excel="PS-VRP\INPUT_TEST\MACCHINE12.xlsx" # metto il nome del file all'interno di una variabile
file_commesse_excel="PS-VRP\Dati_input\Commesse_da_tagliare.xlsx" # metto il nome del file all'interno di una variabile
lista_macchine=read_excel.read_excel_macchine(file_macchine_excel) # creo una lista di oggetti macchina
read_excel.read_attrezzaggio_macchine(file_macchine_excel,lista_macchine)
inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione
lista_commesse=read_excel.read_excel_commesse(file_commesse_excel,inizio_schedulazione) # creo una lista di oggetti commessa
read_excel.read_compatibilita(file_commesse_excel,lista_commesse) #aggiungo le compatibilita commessa-macchina alle commesse della lista passata come parametro(lista con tutte le commesse)
lista_veicoli=read_excel.read_excel_veicoli("PS-VRP\INPUT_TEST\VEICOLI9.xlsx")
lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
print(f'Lista macchine {lista_macchine}, Lista veicoli {lista_veicoli}, Lista_commesse {lista_commesse}')

##EURISTICO COSTRUTTIVO
start_time_eur = time.time()
print('\nEURISTICO COSTRUTTIVO')
commesse_filtrate=solver.filtro_commesse(lista_commesse,lista_veicoli)
numero_commesse_filtrate=len(commesse_filtrate)
schedulazione3,f_obj3=solver.euristico_costruttivo(commesse_filtrate,lista_macchine,lista_veicoli)
output.write_output_soluzione_euristica(schedulazione3,"PS-VRP\OUTPUT_TEST\euristico_costruttivo.xlsx")
print(f'Funzione obiettivo euristico {f_obj3}\n')
end_time_eur = time.time()
tot_time_eur= end_time_eur-start_time_eur

##DEEPCOPIES PER RICERCHE LOCALI
lista_veicoli_copy=deepcopy(lista_veicoli)
lista_macchine_copy=deepcopy(lista_macchine)
lista_commesse_copy=deepcopy(lista_commesse)
lista_veicoli_copy1=deepcopy(lista_veicoli)
lista_macchine_copy1=deepcopy(lista_macchine)
lista_commesse_copy1=deepcopy(lista_commesse)
lista_veicoli_copy2=deepcopy(lista_veicoli)
lista_macchine_copy2=deepcopy(lista_macchine)
lista_commesse_copy2=deepcopy(lista_commesse)

##RICERCHE LOCALI
#M2M
start1=time.time()
print('Greedy + LS1 (Insert inter-macchina)')
soluzione1,f1=solver.move_2_macchine(lista_macchine_copy2,lista_veicoli_copy2,f_obj3,schedulazione3)
print(f'Funzione obiettivo LS1 {f1}\n')
output.write_output_soluzione_euristica(soluzione1,"PS-VRP\OUTPUT_TEST\insert_inter.xlsx")
end1=time.time()
tot1=end1-start1
#M
start_time_move=time.time()
print('Greedy + LS2 (Insert intra-macchina)')
soluzione2,f2=solver.move_no_delta(lista_macchine_copy1,lista_veicoli_copy1,f_obj3,schedulazione3)
soluzione_move=[]
for a in soluzione2:
    for b in a:
        soluzione_move.append(b)
print(f'Funzione obiettivo LS2 {f2}\n')
output.write_output_soluzione_euristica(soluzione_move,"PS-VRP\OUTPUT_TEST\insert_intra.xlsx")
end_time_move=time.time()
tot2 = end_time_move-start_time_move
#S
start_time_swap=time.time()
print('Greedy + LS3 (Swap intra-macchina)')
soluzione3,f3=solver.swap_no_delta(lista_macchine_copy,lista_veicoli_copy,f_obj3,schedulazione3)
soluzione_swap=[]
for a in soluzione3:
    for b in a:
        soluzione_swap.append(b)
print(f'Funzione obiettivo LS3 {f3}\n')
output.write_output_soluzione_euristica(soluzione_swap,"PS-VRP\OUTPUT_TEST\swap_intra.xlsx")
end_time_swap=time.time()
tot3= end_time_swap-start_time_swap
#MS
start_time_tot=time.time()
print('G+LS1+LS2 (sequenza parziale)')
soluzione4,f4=solver.move_no_delta(lista_macchine_copy2,lista_veicoli_copy2,f1,soluzione1)
soluzione_move=[]
for a in soluzione4:
    for b in a:
        soluzione_move.append(b)
print(f'Funzione obiettivo LS1+LS2 {f4}\n')
#output.write_output_soluzione_euristica(soluzione_move,"OUTPUT_TEST\euristico_5.xlsx")
#SS
print('G+LS1+LS2+LS3 (sequenza finale)')
soluzione5,f5=solver.swap_no_delta(lista_macchine_copy2,lista_veicoli_copy2,f4,soluzione_move)
soluzione_swap=[]
for a in soluzione5:
    for b in a:
        soluzione_swap.append(b)
print(f'Funzione obiettivo LS1+LS2+LS3 {f5}\n')
output.write_output_soluzione_euristica(soluzione_swap,"PS-VRP\OUTPUT_TEST\sequenza.xlsx")
end_time_tot=time.time()
tot_tot = end_time_move-start_time_move

##STAMPE FINALI
print('COMMESSE INIZIALI:',len(lista_commesse))
print('COMMESSE FILTRATE:',numero_commesse_filtrate)
print('COMMESSE SCHEDULATE:',len(schedulazione3),'\n')
print('TEMPO Greedy:',tot_time_eur)
print('TEMPO Greedy + LS1:',tot_time_eur+tot1) #insert inter
print('TEMPO Greedy + LS2:',tot_time_eur+tot2) #insert intra
print('TEMPO Greedy + LS3:',tot_time_eur+tot3) #swap inter
print('TEMPO Greedy + LS1 + LS2 + LS3:',tot_time_eur+tot1+tot_tot) #in sequenza
solver.grafico_schedulazione(schedulazione3) #euristico
#solver.grafico_schedulazione(soluzione_move) #sequenza pariale (G+LS1+LS2)
solver.grafico_schedulazione(soluzione_swap) #soluzione sequenza finale (G+LS1+LS2+LS3)