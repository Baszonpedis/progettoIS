import os
import read_excel
import solver
import output
from copy import deepcopy
import time
from colorama import Fore, Style, init
import math
import pandas as pd

##INPUT(s) [Macchine, Commesse, Veicoli (Vettori)]
#print(os.getcwd())
if os.path.basename(os.getcwd()) == "PS-VRP": ##PER PC ISTITUTO STAMPA
    file_macchine_excel= os.getcwd() + '/Dati_input/Scheda_Macchine_Taglio.xlsx'
    file_commesse_excel= os.getcwd() + '/Dati_input/Commesse_da_tagliare.xlsx'
    file_veicoli_excel= os.getcwd() + '/Dati_input/vettori.xlsx'
elif os.path.basename(os.getcwd()) == "progettoIS": ##PER DEBUGGING
    file_macchine_excel= os.getcwd() + '/PS-VRP/Dati_input/Scheda_Macchine_Taglio.xlsx'
    file_commesse_excel= os.getcwd() + '/PS-VRP//Dati_input/Commesse_da_tagliare.xlsx'
    file_veicoli_excel= os.getcwd() + '/PS-VRP//Dati_input/vettori.xlsx'
else:
    print("ERRORE - file di input non localizzati correttamente")
#a = 0.5 #parametro "a" per decidere la migliore ricerca locale nei due stadi di ricerca locale
#NB: questo NON è alfa; alfa è nel solver

##ELABORAZIONI SU INPUT(s)
lista_macchine=read_excel.read_excel_macchine(file_macchine_excel) #Lista base oggetti macchina
read_excel.read_attrezzaggio_macchine(file_macchine_excel,lista_macchine)
inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione
lista_commesse=read_excel.read_excel_commesse(file_commesse_excel,inizio_schedulazione) #Lista base oggetti commessa
incompatibili = read_excel.read_compatibilita(file_commesse_excel,lista_commesse) #aggiungo le compatibilita commessa-macchina alle commesse della lista passata come parametro(lista con tutte le commesse); estraggo le eventuali incompatibili con ogni macchina
lista_veicoli=read_excel.read_excel_veicoli(file_veicoli_excel) #Lista base oggetti veicolo
lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)

init(autoreset=True)  # Ripristina i colori dopo ogni print

commesse_da_schedulare, dizionario_filtri, commesse_scartate = solver.filtro_commesse(lista_commesse, lista_veicoli)
lista_commesse_tassative = [c for c in commesse_da_schedulare if c.tassativita == "X"]
df_errati, lista_commesse_tassative, commesse_da_schedulare, commesse_veicoli_errati = solver.associa_veicoli_tassativi(lista_commesse_tassative, commesse_da_schedulare, lista_veicoli)

if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_veicoli_error_output(df_errati, os.getcwd() +'/Dati_output/errori_veicoli.xlsx')
elif os.path.basename(os.getcwd()) == "progettoIS":
    output.write_veicoli_error_output(df_errati, os.getcwd() +'/PS-VRP/Dati_output/errori_veicoli.xlsx')


##EURISTICO DI BASE
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}EURISTICO COSTRUTTIVO (G1+G2)".center(40))
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}\n")
print(f"{Fore.GREEN}{Style.BRIGHT}COMMESSE LETTE CORRETTAMENTE (NO CAMPI MANCANTI, ALMENO UNA COMPATIBILITA' MACCHINA): {len(lista_commesse)}")
print(f"{Fore.GREEN}{Style.BRIGHT}COMMESSE ESCLUSE PER INCOMPATIBILITA' CON TUTTE LE MACCHINE: {len(incompatibili)}")

start_time_eur = time.time()

schedulazione3, f_obj3, causa_fallimento, lista_macchine, commesse_residue, f_obj3_ritardo, f_obj3_ritardo_pesato = solver.euristico_costruttivo(commesse_da_schedulare, lista_macchine, lista_veicoli)
#output.write_output_soluzione_euristica(schedulazione3, os.getcwd() + '/Dati_output/euristico_costruttivo.xlsx')
print(f'SCARTATI DAL PRIMO EURISTICO - Direttamente al Gruppo tre: {len(dizionario_filtri)}')
print(f'INPUT AL PRIMO EURISTICO: {len(lista_commesse) - len(dizionario_filtri)}')
print(f'FALLIMENTI PRIMO EURISTICO: {len(causa_fallimento)}')
print(f'ASSEGNATI PRIMO EURISTICO: {len(lista_commesse) - len(dizionario_filtri) - len(causa_fallimento)}')
commesse_non_schedulate = causa_fallimento | dizionario_filtri | commesse_veicoli_errati #| commesse_oltre_data (in caso d'uso, da reinserire eventualmente anche come output della chiamata al solver)

print(f"\n{Fore.RED}{Style.BRIGHT}COMMESSE NON SCHEDULATE AL PRIMO EURISTICO (su veicoli): {len(commesse_non_schedulate)}")
print(f"{Fore.RED}Dettaglio motivi: {commesse_non_schedulate}")
print(f"\n{Fore.YELLOW}Funzione obiettivo euristico (setup): {f_obj3} minuti di setup")
print(f"{Fore.YELLOW}Funzione obiettivo euristico (consegna): {-f_obj3_ritardo} ore di ritardo\n")

end_time_eur = time.time()
tot_time_eur = end_time_eur - start_time_eur

#solver.grafico_schedulazione(schedulazione3)

## DEEPCOPIES PER RICERCHE LOCALI (prima fase)
lista_macchine_copy = deepcopy(lista_macchine)
lista_macchine_copy1 = deepcopy(lista_macchine)
lista_macchine_copy2 = deepcopy(lista_macchine)

## RICERCHE LOCALI (su primo euristico)
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}RICERCHE LOCALI".center(40))
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}\n")

# M2M
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS1 (Insert inter-macchina)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

start1 = time.time()
soluzione1, f1, contatoreLS1, f1_ritardo, ritardo_pesato_1 = solver.insert_inter_macchina(lista_macchine_copy, f_obj3)
#print(f1)
print(f"{Fore.YELLOW}Risultato LS1 (setup): ottenuto {f1-f_obj3} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS1 (consegna): ottenuto {-f1_ritardo + f_obj3_ritardo} ore di ritardo")
print(f"Mosse LS1: {contatoreLS1}")
#output.write_output_soluzione_euristica(soluzione1, os.getcwd() +'/Dati_output/insert_inter.xlsx')
tot1 = time.time() - start1
#solver.grafico_schedulazione(soluzione1)

#lista_macchine_copy10 = lista_macchine_copy.copy()
#print("ID macchine in copia shallow (lista_macchine_copy10):", [id(m) for m in lista_macchine_copy10])

# M
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS2 (Insert intra-macchina)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

start_time_move = time.time()
soluzione2, f2, contatoreLS2, f2_ritardo, ritardo_pesato_2 = solver.insert_intra(lista_macchine_copy1, f_obj3)
#soluzione_move = [b for a in soluzione2 for b in a]
#print(f2)
print(f"{Fore.YELLOW}Risultato LS2 (setup): ottenuto {f2-f_obj3} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS2 (consegna): ottenuto {-f2_ritardo+f_obj3_ritardo} ore di ritardo")
print(f"Mosse LS2: {contatoreLS2}")
#output.write_output_soluzione_euristica(soluzione2, os.getcwd() + '/Dati_output/insert_intra.xlsx')
tot2 = time.time() - start_time_move
#solver.grafico_schedulazione(soluzione2)

# S
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS3 (Swap intra-macchina)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

start_time_swap = time.time()
soluzione3, f3, contatoreLS3, f3_ritardo, ritardo_pesato_3 = solver.swap_intra(lista_macchine_copy2, f_obj3)
#print(f3)
#soluzione_swap = [b for a in soluzione3 for b in a]
print(f"{Fore.YELLOW}Risultato LS3 (setup): ottenuto {f3-f_obj3} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS3 (consegna): ottenuto {-f3_ritardo+f_obj3_ritardo} ore di ritardo")
print(f"Mosse LS3: {contatoreLS3}")
#output.write_output_soluzione_euristica(soluzione3, os.getcwd() + '/Dati_output/swap_intra.xlsx')
tot3 = time.time() - start_time_swap

# SEQUENZA PARZIALE
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}G+LS1+LS2 (sequenza parziale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_tot = time.time()
soluzione4, f4, contatoreLS2, f4_ritardo, ritardo_pesato_4 = solver.insert_intra(lista_macchine_copy, f1)
print(f'Mosse LS1+LS2: {contatoreLS1+contatoreLS2}')
#soluzione_parziale = [b for a in soluzione4 for b in a]
#print(f4)
#print(-f4_ritardo)
#output.write_output_soluzione_euristica(soluzione4, os.getcwd() + '/Dati_output/sequenza_parziale.xlsx')
print(f"{Fore.YELLOW}Risultato LS1+LS2 (setup): ottenuto {f4-f1} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS1+LS2 (consegna): {-f4_ritardo+f1_ritardo} ore di ritardo")

# SEQUENZA COMPLETA
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}G+LS1+LS2+LS3 (sequenza finale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
soluzione5, f5, contatoreLS3, f5_ritardo, ritardo_pesato_5 = solver.swap_intra(lista_macchine_copy, f4)
print(f'Mosse LS1+LS2+LS3: {contatoreLS1+contatoreLS2+contatoreLS3}')
#soluzione_sequenza = [b for a in soluzione5 for b in a]
#print(f5_ritardo)
#print(f4_ritardo)
print(f"{Fore.YELLOW}Risultato LS1+LS2+LS3 (setup): ottenuto {f5-f4} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS1+LS2+LS3 (consegna): ottenuto {-f5_ritardo+f4_ritardo} ore di ritardo")
#output.write_output_soluzione_euristica(soluzione5, os.getcwd() + '/Dati_output/sequenza.xlsx')
tot_tot = time.time() - start_time_tot
#print(f5)
print(f"{Fore.YELLOW}RISPARMIO SEQUENZA (setup): ottenuto {f5-f_obj3} minuti di setup")
print(f"{Fore.YELLOW}RISPARMIO SEQUENZA (consegna): ottenuto {-f5_ritardo+f_obj3_ritardo} ore di ritardo")

# EURISTICO NUOVO (gruppo3)
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}EURISTICO COSTRUTTIVO (G3)".center(40))
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
ritardo5 = -f5_ritardo.total_seconds()/3600 
ritardo2 = -f2_ritardo.total_seconds()/3600
ritardo3 = -f3_ritardo.total_seconds()/3600

#if (a*f5+(1-a)*ritardo5) < (a*f2+(1-a)*ritardo2) and (a*f5+(1-a)*ritardo5) < (a*f3+(1-a)*ritardo3):
#print(f'SOLUZIONE MIGLIORE PER BETA = {a} -> SEQUENZA')
fprimo = f5
fritardoprimo = f5_ritardo
ritardo_pesato_primo = ritardo_pesato_5
macchine_post = lista_macchine_copy
soluzionebest = soluzione5
"""elif (a*f5+(1-a)*ritardo5) < (a*f2+(1-a)*ritardo2) and (a*f5+(1-a)*ritardo5) > (a*f3+(1-a)*ritardo3):
    print(f'SOLUZIONE MIGLIORE PER BETA = {a} -> SWAP INTRA')
    fprimo = f3
    fritardoprimo = f3_ritardo
    ritardo_pesato_primo = ritardo_pesato_3
    macchine_post = lista_macchine_copy2
    soluzionebest = soluzione3
else:
    print(f'SOLUZIONE MIGLIORE PER ALFA = {a} -> INSERT INTRA')
    fprimo = f2
    fritardoprimo = f2_ritardo
    ritardo_pesato_primo = ritardo_pesato_2
    macchine_post = lista_macchine_copy1
    soluzionebest = soluzione1"""

start_time_post = time.time()
soluzionepost, fpost, fpost_ritardo, ritardo_post_pesato = solver.euristico_post(soluzionebest, commesse_residue, macchine_post, commesse_scartate, fprimo, fritardoprimo, ritardo_pesato_primo)
print(f"{Fore.YELLOW}Funzione obiettivo (LS[G1+G2]+G3) (setup): {fpost} minuti di setup")
print(f"{Fore.YELLOW}Funzione obiettivo (LS[G1+G2]+G3) (consegna): {-fpost_ritardo} ore di ritardo")
#output.write_output_soluzione_euristica(soluzionepost, os.getcwd() + '/Dati_output/euristico_post.xlsx')
#solver.grafico_schedulazione(soluzionepost)
post_time = time.time() - start_time_post

## DEEPCOPIES PER RICERCHE LOCALI (seconda fase)
lista_macchine_copy3 = deepcopy(macchine_post)
lista_macchine_copy4 = deepcopy(macchine_post)
lista_macchine_copy5 = deepcopy(macchine_post)


## RICERCHE LOCALI (su secondo euristico)

# M2M - Bis
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}LS1[G3] (Insert inter-macchina)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

start1_post = time.time()
soluzione1post, f1post, contatoreLS1post, f1_ritardo_post, ritardo_post_pesato_1 = solver.insert_inter_macchina(lista_macchine_copy3, fpost)
#print(f1post)
print(f"{Fore.YELLOW}Risultato LS1[LS[G1+G2]+G3] (setup): ottenuto {f1post-fpost} minuti di setup")
#print(f1_ritardo_post)
print(f"{Fore.YELLOW}Risultato LS1[LS[G1+G2]+G3] (consegna): ottenuto {-f1_ritardo_post + fpost_ritardo} ore di ritardo")
print(f"Mosse LS1 - post: {contatoreLS1post}")
#output.write_output_soluzione_euristica(soluzione1post, os.getcwd() + '/Dati_output/insert_inter_post.xlsx')
tot1_post = time.time() - start1_post

# INSERT-INTRA - Bis
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Insert Intra Bis")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_tot_post = time.time()
soluzione2post, f2post, contatoreLS2post, f2_ritardo_post, ritardo_post_pesato_2 = solver.insert_intra(lista_macchine_copy4, fpost)
print(f'Mosse LS1+LS2 - post: {contatoreLS2post}')
#soluzione_move_post = [b for a in soluzione2post for b in a]
#solver.grafico_schedulazione(soluzione2post)
#output.write_output_soluzione_euristica(soluzione2post, os.getcwd() + '/Dati_output/insert_intra_post.xlsx')
print(f"{Fore.YELLOW}Risultato LS2[LS[G1+G2]+G3] (setup): ottenuto {f2post-fpost} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS2[LS[G1+G2]+G3] (consegna): ottenuto {-f2_ritardo_post+fpost_ritardo} ore di ritardo")

# SWAP-INTRA - Bis
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Swap Intra Bis")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_tot_post = time.time()
soluzione3post, f3post, contatoreLS3post, f3_ritardo_post, ritardo_post_pesato_3 = solver.swap_intra(lista_macchine_copy5, fpost)
print(f'Mosse LS1+LS2 - post: {contatoreLS3post}')
#soluzione_swap_post = [b for a in soluzione3post for b in a]
#solver.grafico_schedulazione(soluzione_swap_post)
#output.write_output_soluzione_euristica(soluzione3post, os.getcwd() + '/Dati_output/swap_intra_post.xlsx')
print(f"{Fore.YELLOW}Risultato LS3[LS[G1+G2]+G3] (setup): ottenuto {f3post-fpost} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS3[LS[G1+G2]+G3] (consegna): ottenuto {-f3_ritardo_post+fpost_ritardo} ore di ritardo")

# SEQUENZA PARZIALE
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}LS1+LS2[LS[G1+G2]+G3] (sequenza parziale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_tot_post = time.time()
soluzione4post, f4post, contatoreLS2post, f4_ritardo_post, ritardo_post_pesato_4 = solver.insert_intra(lista_macchine_copy3, f1post)
print(f'Mosse LS1+LS2 - post: {contatoreLS1post+contatoreLS2post}')
#soluzione_move_post = [b for a in soluzione4post for b in a]
#solver.grafico_schedulazione(soluzione4post)
print(f4_ritardo_post)
print(f1_ritardo_post)
print(f'f4 {f4post}, f1 {f1post}')
#output.write_output_soluzione_euristica(soluzione4post, os.getcwd() + '/Dati_output/sequenza_parziale_post.xlsx')
print(f"{Fore.YELLOW}Risultato LS1+LS2[LS[G1+G2]+G3] (setup): ottenuto {f4post-f1post} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS1+LS2[LS[G1+G2]+G3] (consegna): ottenuto {-f4_ritardo_post+f1_ritardo_post} ore di ritardo")

# APPIATTIMENTO SOLUZIONE4POST PER RENDERLA LEGGIBILE ALLO SWAP FINALE
#schedulazione_flat = [job_dict 
#                      for sched_macchina in soluzione4post 
#                      for job_dict in sched_macchina]

# SEQUENZA COMPLETA
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}LS[LS[G1+G2]+G3] (sequenza finale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
soluzione5post, f5post, contatoreLS3post, f5_ritardo_post, ritardo_post_pesato_5 = solver.swap_intra(lista_macchine_copy3, f4post)
print(f5post)
print(f4post)
print(f'Mosse LS1+LS2+LS3 - post: {contatoreLS1post+contatoreLS2post+contatoreLS3post}')
#soluzione_sequenza_post = [b for a in soluzione5post for b in a]
print(f"{Fore.YELLOW}Risultato LS[LS[G1+G2]+G3] (setup): ottenuto {f5post-f4post} minuti di setup")
print(f'f5 {f5_ritardo_post}, f4 {f4_ritardo_post}')
print(f"{Fore.YELLOW}Risultato LS[LS[G1+G2]+G3] (consegna): ottenuto {-f5_ritardo_post+f4_ritardo_post} ore di ritardo")

if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_soluzione_euristica(soluzione5post, os.getcwd() + '/Dati_output/output.xlsx')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_soluzione_euristica(soluzione5post, os.getcwd() + '/PS-VRP/Dati_output/output.xlsx')
if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_ridotto(soluzione5post, os.getcwd() + '/Dati_output/output_ridotto.xlsx')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_ridotto(soluzione5post, os.getcwd() + '/PS-VRP/Dati_output/output_ridotto.xlsx')
if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_ridotto_txt(soluzione5post, os.getcwd() + '/Dati_output/output_ridotto.txt')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_ridotto_txt(soluzione5post, os.getcwd() + '/PS-VRP/Dati_output/output_ridotto.txt')
tot_tot_post = time.time() - start_time_tot_post

ritardo1 = -f1_ritardo_post.total_seconds()/3600
ritardo2 = -f2_ritardo_post.total_seconds()/3600
ritardo3 = -f3_ritardo_post.total_seconds()/3600
#print(a*f1post+(1-a)*f1_ritardo_post.total_seconds()/3600)
#print(a*f1post)
#print((1-a))
#print(f1_ritardo_post.total_seconds()/3600)

#if (a*f5post+(1-a)*ritardo5) < (a*f2post+(1-a)*ritardo2) and (a*f5post+(1-a)*ritardo5) < (a*f3post+(1-a)*ritardo3):
#print(f'SOLUZIONE MIGLIORE PER ALFA = {a} -> SEQUENZA')
fprimopost = f5post
fritardoprimopost = f5_ritardo_post
ritardo_pesato_post_primo = ritardo_post_pesato_5
soluzionefinale = soluzione5post
"""elif (a*f5+(1-a)*ritardo5) < (a*f2post+(1-a)*ritardo2) and (a*f5post+(1-a)*ritardo5) > (a*f3post+(1-a)*ritardo3):
    print(f'SOLUZIONE MIGLIORE PER ALFA = {a} -> SWAP INTRA')
    fprimopost = f3post
    fritardoprimopost = f3_ritardo_post
    ritardo_pesato_post_primo = ritardo_post_pesato_3
    soluzionefinale = soluzione3post
else:
    print(f'SOLUZIONE MIGLIORE PER ALFA = {a} -> INSERT INTRA')
    fprimopost = f2post
    fritardoprimopost = f2_ritardo_post
    ritardo_pesato_post_primo = ritardo_post_pesato_2
    soluzionefinale = soluzione2post"""

## STAMPE FINALI
print(f"{Fore.MAGENTA}{Style.BRIGHT}\n{'='*40}")
print(f"{Fore.MAGENTA}{Style.BRIGHT}RISULTATI FINALI".center(40))
print(f"{Fore.MAGENTA}{Style.BRIGHT}{'='*40}\n")

print(f"{Fore.YELLOW}RISULTATO FINALE (SETUP): {fprimopost} minuti di setup\n")
print(f"{Fore.YELLOW}RISULTATO FINALE (CONSEGNE): {-fritardoprimopost} ore di ritardo\n")
print(f"{Fore.YELLOW}RISULTATO FINALE (CONSEGNE): {-ritardo_pesato_post_primo} ore di ritardo pesato\n")
print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (entrambe le ricerche locali) (SETUP): {fprimopost - fpost + fprimo - f_obj3} minuti di setup")
print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (entrambe le ricerche locali) (CONSEGNE): {-fritardoprimopost+fpost_ritardo -fritardoprimo + f_obj3_ritardo} ore di ritardo\n")
print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (entrambe le ricerche locali) (CONSEGNE): {-ritardo_pesato_post_primo+ritardo_post_pesato - ritardo_pesato_primo + f_obj3_ritardo_pesato} ore di ritardo pesato\n")
print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (sole seconde ricerche locali) (SETUP): {fprimopost - fpost} minuti di setup")
print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (sole seconde ricerche locali) (CONSEGNE): {-fritardoprimopost+fpost_ritardo} ore di ritardo")

print(f"{Fore.GREEN}COMMESSE LETTE CORRETTAMENTE: {len(lista_commesse)}")
print(f"{Fore.GREEN}COMMESSE ESCLUSE PER ERRORE NELL'ESTRAZIONE VEICOLI: {len(commesse_veicoli_errati)}")
print(f"{Fore.GREEN}COMMESSE POST FILTRO ZONE E FILTRO VEICOLI (Interne a zona aperta + tassative): {len(commesse_da_schedulare)}")
print(f"{Fore.GREEN}COMMESSE SCARTATE (RELEGATE A TERZO CICLO): {len(commesse_scartate+commesse_residue)}")
print(f"{Fore.GREEN}COMMESSE CORRETTAMENTE SCHEDULATE SU MACCHINA: {len(soluzionefinale)}\n")

print(f"{Fore.BLUE}TEMPO Greedy (G1+G2): {tot_time_eur:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS1: {tot_time_eur + tot1:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS2: {tot_time_eur + tot2:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS3: {tot_time_eur + tot3:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS1: {tot_time_eur + tot1:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS1+LS2+LS3: {tot_time_eur + tot1 + tot_tot:.2f}s")

print(f"{Fore.BLUE}TEMPO Greedy (G3): {post_time:.2f}s")
print(f"{Fore.BLUE}TEMPO Greedy (G3) + LS: {post_time + tot1_post:.2f}s")

##GRASP
alfa = 0.9 #NB: modifica anche l'altro
iterazioni = 5
fbest = fprimopost
fobest = alfa*fprimopost-0.5*((1-alfa)*ritardo_pesato_post_primo.total_seconds()/3600)
fritardobest = fritardoprimopost
fritardopesatobest = ritardo_pesato_post_primo
soluzionebest = soluzionefinale

for _ in range(iterazioni):
    #NB: gli input sono ricalcolati a ogni iterazione; non è ottimale ma è per evitare problemi con le due strutture dati utilizzate
    lista_macchine=read_excel.read_excel_macchine(file_macchine_excel) #Lista base oggetti macchina
    read_excel.read_attrezzaggio_macchine(file_macchine_excel,lista_macchine)
    inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione
    lista_commesse=read_excel.read_excel_commesse(file_commesse_excel,inizio_schedulazione) #Lista base oggetti commessa
    incompatibili = read_excel.read_compatibilita(file_commesse_excel,lista_commesse) #aggiungo le compatibilita commessa-macchina alle commesse della lista passata come parametro(lista con tutte le commesse); estraggo le eventuali incompatibili con ogni macchina
    lista_veicoli=read_excel.read_excel_veicoli(file_veicoli_excel) #Lista base oggetti veicolo
    lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)
    ## EURISTICO COSTRUTTIVO
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}EURISTICO COSTRUTTIVO (G1+G2)".center(40))
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}\n")
    print(f"{Fore.GREEN}{Style.BRIGHT}COMMESSE LETTE CORRETTAMENTE (NO CAMPI MANCANTI, ALMENO UNA COMPATIBILITA' MACCHINA): {len(lista_commesse)}")
    print(f"{Fore.GREEN}{Style.BRIGHT}COMMESSE ESCLUSE PER INCOMPATIBILITA' CON TUTTE LE MACCHINE: {len(incompatibili)}")

    start_time_eur = time.time()

    schedulazione3, f_obj3, causa_fallimento, lista_macchine, commesse_residue, f_obj3_ritardo, f_obj3_ritardo_pesato = solver.euristico_costruttivo(commesse_da_schedulare, lista_macchine, lista_veicoli)
    #output.write_output_soluzione_euristica(schedulazione3, os.getcwd() + '/Dati_output/euristico_costruttivo.xlsx')
    print(f'SCARTATI DAL PRIMO EURISTICO - Direttamente al Gruppo tre: {len(dizionario_filtri)}')
    print(f'INPUT AL PRIMO EURISTICO: {len(lista_commesse) - len(dizionario_filtri)}')
    print(f'FALLIMENTI PRIMO EURISTICO: {len(causa_fallimento)}')
    print(f'ASSEGNATI PRIMO EURISTICO: {len(lista_commesse) - len(dizionario_filtri) - len(causa_fallimento)}')
    commesse_non_schedulate = causa_fallimento | dizionario_filtri | commesse_veicoli_errati #| commesse_oltre_data (in caso d'uso, da reinserire eventualmente anche come output della chiamata al solver)

    print(f"\n{Fore.RED}{Style.BRIGHT}COMMESSE NON SCHEDULATE AL PRIMO EURISTICO (su veicoli): {len(commesse_non_schedulate)}")
    print(f"{Fore.RED}Dettaglio motivi: {commesse_non_schedulate}")
    print(f"\n{Fore.YELLOW}Funzione obiettivo euristico (setup): {f_obj3} minuti di setup")
    print(f"{Fore.YELLOW}Funzione obiettivo euristico (consegna): {-f_obj3_ritardo} ore di ritardo\n")

    end_time_eur = time.time()
    tot_time_eur = end_time_eur - start_time_eur

    #solver.grafico_schedulazione(schedulazione3)

    ## DEEPCOPIES PER RICERCHE LOCALI (prima fase)
    lista_macchine_copy = deepcopy(lista_macchine)
    lista_macchine_copy1 = deepcopy(lista_macchine)
    lista_macchine_copy2 = deepcopy(lista_macchine)

    ## RICERCHE LOCALI (su primo euristico)
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}RICERCHE LOCALI".center(40))
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}\n")

    # M2M
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS1 (Insert inter-macchina)")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

    start1 = time.time()
    soluzione1, f1, contatoreLS1, f1_ritardo, ritardo_pesato_1 = solver.insert_inter_macchina(lista_macchine_copy, f_obj3)
    #print(f1)
    print(f"{Fore.YELLOW}Risultato LS1 (setup): ottenuto {f1-f_obj3} minuti di setup")
    print(f"{Fore.YELLOW}Risultato LS1 (consegna): ottenuto {-f1_ritardo + f_obj3_ritardo} ore di ritardo")
    print(f"Mosse LS1: {contatoreLS1}")
    #output.write_output_soluzione_euristica(soluzione1, os.getcwd() +'/Dati_output/insert_inter.xlsx')
    tot1 = time.time() - start1
    #solver.grafico_schedulazione(soluzione1)

    #lista_macchine_copy10 = lista_macchine_copy.copy()
    #print("ID macchine in copia shallow (lista_macchine_copy10):", [id(m) for m in lista_macchine_copy10])

    # M
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS2 (Insert intra-macchina)")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

    start_time_move = time.time()
    soluzione2, f2, contatoreLS2, f2_ritardo, ritardo_pesato_2 = solver.insert_intra(lista_macchine_copy1, f_obj3)
    #soluzione_move = [b for a in soluzione2 for b in a]
    #print(f2)
    print(f"{Fore.YELLOW}Risultato LS2 (setup): ottenuto {f2-f_obj3} minuti di setup")
    print(f"{Fore.YELLOW}Risultato LS2 (consegna): ottenuto {-f2_ritardo+f_obj3_ritardo} ore di ritardo")
    print(f"Mosse LS2: {contatoreLS2}")
    #output.write_output_soluzione_euristica(soluzione2, os.getcwd() + '/Dati_output/insert_intra.xlsx')
    tot2 = time.time() - start_time_move
    #solver.grafico_schedulazione(soluzione2)

    # S
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS3 (Swap intra-macchina)")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

    start_time_swap = time.time()
    soluzione3, f3, contatoreLS3, f3_ritardo, ritardo_pesato_3 = solver.swap_intra(lista_macchine_copy2, f_obj3)
    #print(f3)
    #soluzione_swap = [b for a in soluzione3 for b in a]
    print(f"{Fore.YELLOW}Risultato LS3 (setup): ottenuto {f3-f_obj3} minuti di setup")
    print(f"{Fore.YELLOW}Risultato LS3 (consegna): ottenuto {-f3_ritardo+f_obj3_ritardo} ore di ritardo")
    print(f"Mosse LS3: {contatoreLS3}")
    #output.write_output_soluzione_euristica(soluzione3, os.getcwd() + '/Dati_output/swap_intra.xlsx')
    tot3 = time.time() - start_time_swap

    # SEQUENZA PARZIALE
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}G+LS1+LS2 (sequenza parziale)")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    start_time_tot = time.time()
    soluzione4, f4, contatoreLS2, f4_ritardo, ritardo_pesato_4 = solver.insert_intra(lista_macchine_copy, f1)
    print(f'Mosse LS1+LS2: {contatoreLS1+contatoreLS2}')
    #soluzione_parziale = [b for a in soluzione4 for b in a]
    #print(f4)
    #print(-f4_ritardo)
    #output.write_output_soluzione_euristica(soluzione4, os.getcwd() + '/Dati_output/sequenza_parziale.xlsx')
    print(f"{Fore.YELLOW}Risultato LS1+LS2 (setup): ottenuto {f4-f1} minuti di setup")
    print(f"{Fore.YELLOW}Risultato LS1+LS2 (consegna): {-f4_ritardo+f1_ritardo} ore di ritardo")

    # SEQUENZA COMPLETA
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}G+LS1+LS2+LS3 (sequenza finale)")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    soluzione5, f5, contatoreLS3, f5_ritardo, ritardo_pesato_5 = solver.swap_intra(lista_macchine_copy, f4)
    print(f'Mosse LS1+LS2+LS3: {contatoreLS1+contatoreLS2+contatoreLS3}')
    #soluzione_sequenza = [b for a in soluzione5 for b in a]
    #print(f5_ritardo)
    #print(f4_ritardo)
    print(f"{Fore.YELLOW}Risultato LS1+LS2+LS3 (setup): ottenuto {f5-f4} minuti di setup")
    print(f"{Fore.YELLOW}Risultato LS1+LS2+LS3 (consegna): ottenuto {-f5_ritardo+f4_ritardo} ore di ritardo")
    #output.write_output_soluzione_euristica(soluzione5, os.getcwd() + '/Dati_output/sequenza.xlsx')
    tot_tot = time.time() - start_time_tot
    #print(f5)
    print(f"{Fore.YELLOW}RISPARMIO SEQUENZA (setup): ottenuto {f5-f_obj3} minuti di setup")
    print(f"{Fore.YELLOW}RISPARMIO SEQUENZA (consegna): ottenuto {-f5_ritardo+f_obj3_ritardo} ore di ritardo")

    # EURISTICO NUOVO (gruppo3)
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}EURISTICO COSTRUTTIVO (G3)".center(40))
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
    ritardo5 = -f5_ritardo.total_seconds()/3600 
    ritardo2 = -f2_ritardo.total_seconds()/3600
    ritardo3 = -f3_ritardo.total_seconds()/3600

    #if (a*f5+(1-a)*ritardo5) < (a*f2+(1-a)*ritardo2) and (a*f5+(1-a)*ritardo5) < (a*f3+(1-a)*ritardo3):
    #print(f'SOLUZIONE MIGLIORE PER BETA = {a} -> SEQUENZA')
    fprimo = f5
    fritardoprimo = f5_ritardo
    ritardo_pesato_primo = ritardo_pesato_5
    macchine_post = lista_macchine_copy
    soluzionebest = soluzione5
    """elif (a*f5+(1-a)*ritardo5) < (a*f2+(1-a)*ritardo2) and (a*f5+(1-a)*ritardo5) > (a*f3+(1-a)*ritardo3):
        print(f'SOLUZIONE MIGLIORE PER BETA = {a} -> SWAP INTRA')
        fprimo = f3
        fritardoprimo = f3_ritardo
        ritardo_pesato_primo = ritardo_pesato_3
        macchine_post = lista_macchine_copy2
        soluzionebest = soluzione3
    else:
        print(f'SOLUZIONE MIGLIORE PER ALFA = {a} -> INSERT INTRA')
        fprimo = f2
        fritardoprimo = f2_ritardo
        ritardo_pesato_primo = ritardo_pesato_2
        macchine_post = lista_macchine_copy1
        soluzionebest = soluzione1"""

    start_time_post = time.time()
    soluzionepost, fpost, fpost_ritardo, ritardo_post_pesato = solver.euristico_post(soluzionebest, commesse_residue, macchine_post, commesse_scartate, fprimo, fritardoprimo, ritardo_pesato_primo)
    print(f"{Fore.YELLOW}Funzione obiettivo (LS[G1+G2]+G3) (setup): {fpost} minuti di setup")
    print(f"{Fore.YELLOW}Funzione obiettivo (LS[G1+G2]+G3) (consegna): {-fpost_ritardo} ore di ritardo")
    #output.write_output_soluzione_euristica(soluzionepost, os.getcwd() + '/Dati_output/euristico_post.xlsx')
    #solver.grafico_schedulazione(soluzionepost)
    post_time = time.time() - start_time_post

    ## DEEPCOPIES PER RICERCHE LOCALI (seconda fase)
    lista_macchine_copy3 = deepcopy(macchine_post)
    lista_macchine_copy4 = deepcopy(macchine_post)
    lista_macchine_copy5 = deepcopy(macchine_post)


    ## RICERCHE LOCALI (su secondo euristico)

    # M2M - Bis
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}LS1[G3] (Insert inter-macchina)")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

    start1_post = time.time()
    soluzione1post, f1post, contatoreLS1post, f1_ritardo_post, ritardo_post_pesato_1 = solver.insert_inter_macchina(lista_macchine_copy3, fpost)
    #print(f1post)
    print(f"{Fore.YELLOW}Risultato LS1[LS[G1+G2]+G3] (setup): ottenuto {f1post-fpost} minuti di setup")
    #print(f1_ritardo_post)
    print(f"{Fore.YELLOW}Risultato LS1[LS[G1+G2]+G3] (consegna): ottenuto {-f1_ritardo_post + fpost_ritardo} ore di ritardo")
    print(f"Mosse LS1 - post: {contatoreLS1post}")
    #output.write_output_soluzione_euristica(soluzione1post, os.getcwd() + '/Dati_output/insert_inter_post.xlsx')
    tot1_post = time.time() - start1_post

    # INSERT-INTRA - Bis
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Insert Intra Bis")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    start_time_tot_post = time.time()
    soluzione2post, f2post, contatoreLS2post, f2_ritardo_post, ritardo_post_pesato_2 = solver.insert_intra(lista_macchine_copy4, fpost)
    print(f'Mosse LS1+LS2 - post: {contatoreLS2post}')
    #soluzione_move_post = [b for a in soluzione2post for b in a]
    #solver.grafico_schedulazione(soluzione2post)
    #output.write_output_soluzione_euristica(soluzione2post, os.getcwd() + '/Dati_output/insert_intra_post.xlsx')
    print(f"{Fore.YELLOW}Risultato LS2[LS[G1+G2]+G3] (setup): ottenuto {f2post-fpost} minuti di setup")
    print(f"{Fore.YELLOW}Risultato LS2[LS[G1+G2]+G3] (consegna): ottenuto {-f2_ritardo_post+fpost_ritardo} ore di ritardo")

    # SWAP-INTRA - Bis
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Swap Intra Bis")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    start_time_tot_post = time.time()
    soluzione3post, f3post, contatoreLS3post, f3_ritardo_post, ritardo_post_pesato_3 = solver.swap_intra(lista_macchine_copy5, fpost)
    print(f'Mosse LS1+LS2 - post: {contatoreLS3post}')
    #soluzione_swap_post = [b for a in soluzione3post for b in a]
    #solver.grafico_schedulazione(soluzione_swap_post)
    #output.write_output_soluzione_euristica(soluzione3post, os.getcwd() + '/Dati_output/swap_intra_post.xlsx')
    print(f"{Fore.YELLOW}Risultato LS3[LS[G1+G2]+G3] (setup): ottenuto {f3post-fpost} minuti di setup")
    print(f"{Fore.YELLOW}Risultato LS3[LS[G1+G2]+G3] (consegna): ottenuto {-f3_ritardo_post+fpost_ritardo} ore di ritardo")

    # SEQUENZA PARZIALE
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}LS1+LS2[LS[G1+G2]+G3] (sequenza parziale)")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    start_time_tot_post = time.time()
    soluzione4post, f4post, contatoreLS2post, f4_ritardo_post, ritardo_post_pesato_4 = solver.insert_intra(lista_macchine_copy3, f1post)
    print(f'Mosse LS1+LS2 - post: {contatoreLS1post+contatoreLS2post}')
    #soluzione_move_post = [b for a in soluzione4post for b in a]
    #solver.grafico_schedulazione(soluzione4post)
    print(f4_ritardo_post)
    print(f1_ritardo_post)
    print(f'f4 {f4post}, f1 {f1post}')
    #output.write_output_soluzione_euristica(soluzione4post, os.getcwd() + '/Dati_output/sequenza_parziale_post.xlsx')
    print(f"{Fore.YELLOW}Risultato LS1+LS2[LS[G1+G2]+G3] (setup): ottenuto {f4post-f1post} minuti di setup")
    print(f"{Fore.YELLOW}Risultato LS1+LS2[LS[G1+G2]+G3] (consegna): ottenuto {-f4_ritardo_post+f1_ritardo_post} ore di ritardo")

    # APPIATTIMENTO SOLUZIONE4POST PER RENDERLA LEGGIBILE ALLO SWAP FINALE
    #schedulazione_flat = [job_dict 
    #                      for sched_macchina in soluzione4post 
    #                      for job_dict in sched_macchina]

    # SEQUENZA COMPLETA
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    print(f"{Fore.CYAN}{Style.BRIGHT}LS[LS[G1+G2]+G3] (sequenza finale)")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
    soluzione5post, f5post, contatoreLS3post, f5_ritardo_post, ritardo_post_pesato_5 = solver.swap_intra(lista_macchine_copy3, f4post)

    tot_tot_post = time.time() - start_time_tot_post

    ritardo1 = -f1_ritardo_post.total_seconds()/3600
    ritardo2 = -f2_ritardo_post.total_seconds()/3600
    ritardo3 = -f3_ritardo_post.total_seconds()/3600

    fprimopost = f5post
    fritardoprimopost = f5_ritardo_post
    ritardo_pesato_post_primo = ritardo_post_pesato_5
    soluzionefinale = soluzione5post

    ## STAMPE FINALI
    print(f"{Fore.MAGENTA}{Style.BRIGHT}\n{'='*40}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}RISULTATI FINALI".center(40))
    print(f"{Fore.MAGENTA}{Style.BRIGHT}{'='*40}\n")

    print(f"{Fore.YELLOW}RISULTATO FINALE (SETUP): {fprimopost} minuti di setup\n")
    print(f"{Fore.YELLOW}RISULTATO FINALE (CONSEGNE): {-fritardoprimopost} ore di ritardo\n")
    print(f"{Fore.YELLOW}RISULTATO FINALE (CONSEGNE): {-ritardo_pesato_post_primo} ore di ritardo pesato\n")
    print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (entrambe le ricerche locali) (SETUP): {fprimopost - fpost + fprimo - f_obj3} minuti di setup")
    print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (entrambe le ricerche locali) (CONSEGNE): {-fritardoprimopost+fpost_ritardo -fritardoprimo + f_obj3_ritardo} ore di ritardo\n")
    print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (entrambe le ricerche locali) (CONSEGNE): {-ritardo_pesato_post_primo+ritardo_post_pesato - ritardo_pesato_primo + f_obj3_ritardo_pesato} ore di ritardo pesato\n")
    print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (sole seconde ricerche locali) (SETUP): {fprimopost - fpost} minuti di setup")
    print(f"{Fore.YELLOW}RISPARMIO CUMULATIVO (sole seconde ricerche locali) (CONSEGNE): {-fritardoprimopost+fpost_ritardo} ore di ritardo")

    print(f"{Fore.GREEN}COMMESSE LETTE CORRETTAMENTE: {len(lista_commesse)}")
    print(f"{Fore.GREEN}COMMESSE ESCLUSE PER ERRORE NELL'ESTRAZIONE VEICOLI: {len(commesse_veicoli_errati)}")
    print(f"{Fore.GREEN}COMMESSE POST FILTRO ZONE E FILTRO VEICOLI (Interne a zona aperta + tassative): {len(commesse_da_schedulare)}")
    print(f"{Fore.GREEN}COMMESSE SCARTATE (RELEGATE A TERZO CICLO): {len(commesse_scartate+commesse_residue)}")
    print(f"{Fore.GREEN}COMMESSE CORRETTAMENTE SCHEDULATE SU MACCHINA: {len(soluzionefinale)}\n")

    print(f"{Fore.BLUE}TEMPO Greedy (G1+G2): {tot_time_eur:.2f}s")
    print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS1: {tot_time_eur + tot1:.2f}s")
    print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS2: {tot_time_eur + tot2:.2f}s")
    print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS3: {tot_time_eur + tot3:.2f}s")
    print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS1: {tot_time_eur + tot1:.2f}s")
    print(f"{Fore.BLUE}TEMPO Greedy (G1+G2) + LS1+LS2+LS3: {tot_time_eur + tot1 + tot_tot:.2f}s")

    print(f"{Fore.BLUE}TEMPO Greedy (G3): {post_time:.2f}s")
    print(f"{Fore.BLUE}TEMPO Greedy (G3) + LS: {post_time + tot1_post:.2f}s")
    #print(f"{Fore.BLUE}TEMPO Greedy (G3) + LS1+LS2+LS3 post: {post_time + tot1 + tot_tot_post:.2f}s")

    fo = alfa*fprimopost-0.5*((1-alfa)*ritardo_pesato_post_primo.total_seconds()/3600)

    if fo < fobest:
        print(fo,fobest,fprimopost,ritardo_pesato_post_primo,fbest,fritardopesatobest)
        fbest = fprimopost
        soluzionebest = soluzionefinale
        fritardobest = fritardoprimopost
        fritardopesatobest = ritardo_pesato_post_primo

print(f"{Fore.YELLOW}SETUP (BEST SOLUTION): {fbest:.2f}s")
print(f"{Fore.YELLOW}RITARDO (BEST SOLUTION): {-fritardobest}s")
print(f"{Fore.YELLOW}RITARDO PESATO (BEST SOLUTION): {-fritardopesatobest}s")

if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_soluzione_euristica(soluzionebest, os.getcwd() + '/Dati_output/best.xlsx')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_soluzione_euristica(soluzionebest, os.getcwd() + '/PS-VRP/Dati_output/best.xlsx')
if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_ridotto(soluzionebest, os.getcwd() + '/Dati_output/best_ridotto.xlsx')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_ridotto(soluzionebest, os.getcwd() + '/PS-VRP/Dati_output/best_ridotto.xlsx')
if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_ridotto_txt(soluzionebest, os.getcwd() + '/Dati_output/best_ridotto.txt')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_ridotto_txt(soluzionebest, os.getcwd() + '/PS-VRP/Dati_output/best_ridotto.txt')
solver.grafico_schedulazione(soluzionebest)  # Soluzione finale totale