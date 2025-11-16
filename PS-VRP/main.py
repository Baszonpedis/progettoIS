import os
import sys
import read_excel
import solver
from solver import alfa
import output
from copy import deepcopy
import time
from colorama import Fore, Style, init
import pandas as pd

start_time_schedulazione = time.time()

##INPUT(s) [Macchine, Commesse, Veicoli (Vettori)]
if __name__ == "__main__":
    print("=== AVVIO MAIN.PY ===")
    
    # Leggi dalle variabili d'ambiente (passate dalla GUI)
    file_commesse_excel = os.getenv('FILE_COMMESSE')
    file_veicoli_excel = os.getenv('FILE_VEICOLI')
    file_macchine_excel = os.getenv('FILE_MACCHINE')
    alfa_str = os.getenv('PARAM_ALFA')
    beta_str = os.getenv('PARAM_BETA')
    iter_str = os.getenv('PARAM_ITER')
    
    print(f"File Commesse da GUI: {file_commesse_excel}")
    print(f"File Veicoli da GUI: {file_veicoli_excel}")
    print(f"File Macchine da GUI: {file_macchine_excel}")
    print(f"Parametro Alfa: {alfa_str}")
    print(f"Parametro Beta: {beta_str}")
    print(f"Numero di iterazioni: {iter_str}")
    
    # Converti i parametri numerici
    try:
        alfa = float(alfa_str) if alfa_str else 0.7  # Default
        beta = float(beta_str) if beta_str else 0.2  # Default
        iter = int(iter_str) if iter_str else 5 #Default; int per poter essere essere correttamente usato nella funzione range()
        print(f"Parametri convertiti - Alfa: {alfa}, Beta: {beta}")
    except (ValueError, TypeError):
        print("ERRORE: Parametri Alfa o Beta o Iter non validi.", file=sys.stderr)
        sys.exit(1)
    
    # Se i file non sono specificati via environment, usa la logica di fallback
    if not all([file_commesse_excel, file_veicoli_excel, file_macchine_excel]):
        print("File non specificati via GUI, uso percorsi default...")
        
        current_dir_name = os.path.basename(os.getcwd())
        print(f"Directory corrente: {current_dir_name}")
        
        if current_dir_name == "PS-VRP":
            file_macchine_excel = os.getcwd() + '/Dati_input/Scheda_Macchine_Taglio.xlsx'
            file_commesse_excel = os.getcwd() + '/Dati_input/Commesse_da_tagliare.xlsx'
            file_veicoli_excel = os.getcwd() + '/Dati_input/vettori.xlsx'
            print("Usando percorsi per PC ISTITUTO STAMPA")
            
        elif current_dir_name == "progettoIS":
            file_macchine_excel = os.getcwd() + '/PS-VRP/Dati_input/Scheda_Macchine_Taglio.xlsx'
            file_commesse_excel = os.getcwd() + '/PS-VRP/Dati_input/Commesse_da_tagliare.xlsx'
            file_veicoli_excel = os.getcwd() + '/PS-VRP/Dati_input/vettori.xlsx'
            print("Usando percorsi per DEBUGGING")
            
        else:
            print("ERRORE - file di input non localizzati correttamente o variabili d'ambiente mancanti.", file=sys.stderr)
            sys.exit(1)
    
    # Verifica che tutti i file esistano
    files_to_check = {
        'Commesse': file_commesse_excel,
        'Veicoli': file_veicoli_excel,
        'Macchine': file_macchine_excel
    }
    
    for nome, percorso in files_to_check.items():
        if not os.path.exists(percorso):
            print(f"ERRORE: File {nome} non trovato: {percorso}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"[OK] File {nome} trovato: {os.path.basename(percorso)}")
    
    print("\n=== INIZIO SCHEDULAZIONE ===")

#NB: Il valore divid (fondamentale per il calcolo di fobest) è invece impostato manualmente qui
#NB2: Idem il valore multip (altro fondamentale per il calcolo di fobest)
divid = 10
multip = 1000

##ELABORAZIONI SU INPUT(s)
lista_macchine=read_excel.read_excel_macchine(file_macchine_excel) #Lista base oggetti macchina
read_excel.read_attrezzaggio_macchine(file_macchine_excel,lista_macchine)
inizio_schedulazione=lista_macchine[0].data_inizio_schedulazione
lista_commesse=read_excel.read_excel_commesse(file_commesse_excel,inizio_schedulazione) #Lista base oggetti commessa
schedulabili = len(lista_commesse)
incompatibili = read_excel.read_compatibilita(file_commesse_excel,lista_commesse) #aggiungo le compatibilita commessa-macchina alle commesse della lista passata come parametro(lista con tutte le commesse); estraggo le eventuali incompatibili con ogni macchina
lista_veicoli=read_excel.read_excel_veicoli(file_veicoli_excel) #Lista base oggetti veicolo
lista_macchine=sorted(lista_macchine,key=lambda macchina:macchina.nome_macchina)

init(autoreset=True)  # Ripristina i colori dopo ogni print

commesse_da_schedulare, dizionario_filtri, commesse_scartate = solver.filtro_commesse(lista_commesse, lista_veicoli)
lista_commesse_tassative = [c for c in commesse_da_schedulare if c.tassativita == "X"]
df_errati, lista_commesse_tassative, commesse_da_schedulare, commesse_veicoli_errati = solver.associa_veicoli_tassativi(lista_commesse_tassative, commesse_da_schedulare, lista_veicoli)

if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_veicoli_error_output(df_errati, os.getcwd() +'/Dati_output/Problemi_veicoli.xlsx')
elif os.path.basename(os.getcwd()) == "progettoIS":
    output.write_veicoli_error_output(df_errati, os.getcwd() +'/PS-VRP/Dati_output/Problemi_veicoli.xlsx')


##EURISTICO DI BASE
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}EURISTICO COSTRUTTIVO (G1+G2)".center(40))
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}\n")
print(f"{Fore.GREEN}{Style.BRIGHT}COMMESSE LETTE CORRETTAMENTE (NO CAMPI MANCANTI, ALMENO UNA COMPATIBILITA' MACCHINA): {len(lista_commesse)}")
#print(f"{Fore.GREEN}{Style.BRIGHT}COMMESSE ESCLUSE PER INCOMPATIBILITA' CON TUTTE LE MACCHINE: {len(incompatibili)}")

start_time_eur = time.time()

schedulazione3, f_obj3, causa_fallimento, lista_macchine, commesse_residue, f_obj3_ritardo, f_obj3_ritardo_pesato, df_tass = solver.euristico_costruttivo(commesse_da_schedulare, lista_macchine, lista_veicoli)
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
lista_veicoli_copy = deepcopy(lista_veicoli)
lista_veicoli_copy1 = deepcopy(lista_veicoli)
lista_veicoli_copy2 = deepcopy(lista_veicoli)

## RICERCHE LOCALI (su primo euristico)
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}RICERCHE LOCALI".center(40))
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}\n")

# M2M
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}Greedy + LS1 (Insert inter-macchina)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")

start1 = time.time()
soluzione1, f1, contatoreLS1, f1_ritardo, ritardo_pesato_1 = solver.insert_inter_macchina(lista_macchine_copy, f_obj3, lista_veicoli_copy)
#print(f1)
print(f"{Fore.YELLOW}Risultato LS1 (setup): ottenuto {f1-f_obj3} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS1 (consegna): ottenuto {-f1_ritardo + f_obj3_ritardo} ore di ritardo")
print(f"Mosse LS1: {contatoreLS1}")
#output.write_output_soluzione_euristica(soluzione1, os.getcwd() +'/Dati_output/insert_inter.xlsx')
tot1 = time.time() - start1
#solver.grafico_schedulazione(soluzione1)

# INSERT INTRA (Sequenza Parziale)
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}G+LS1+LS2 (sequenza parziale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_tot = time.time()
soluzione4, f4, contatoreLS2, f4_ritardo, ritardo_pesato_4 = solver.insert_intra(lista_macchine_copy, f1, lista_veicoli_copy)
print(f'Mosse LS1+LS2: {contatoreLS1+contatoreLS2}')
#soluzione_parziale = [b for a in soluzione4 for b in a]
#print(f4)
#print(-f4_ritardo)
#output.write_output_soluzione_euristica(soluzione4, os.getcwd() + '/Dati_output/sequenza_parziale.xlsx')
print(f"{Fore.YELLOW}Risultato LS1+LS2 (setup): ottenuto {f4-f1} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS1+LS2 (consegna): {-f4_ritardo+f1_ritardo} ore di ritardo")

# INSERT INTER (Sequenza Finale)
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}G+LS1+LS2+LS3 (sequenza finale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
soluzione5, f5, contatoreLS3, f5_ritardo, ritardo_pesato_5 = solver.swap_intra(lista_macchine_copy, f4, lista_veicoli_copy)
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

#Soluzione finale primo euristico
fprimo = f5
fritardoprimo = f5_ritardo
ritardo_pesato_primo = ritardo_pesato_5
macchine_post = lista_macchine_copy
#veicoli_post = lista_veicoli_copy
soluzionebasepost = soluzione5

# EURISTICO NUOVO (gruppo3)
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}EURISTICO COSTRUTTIVO (G3)".center(40))
print(f"{Fore.CYAN}{Style.BRIGHT}{'='*40}")
ritardo5 = -f5_ritardo.total_seconds()/3600 
#ritardo2 = -f2_ritardo.total_seconds()/3600
#ritardo3 = -f3_ritardo.total_seconds()/3600

start_time_post = time.time()
soluzionepost, fpost, fpost_ritardo, ritardo_post_pesato, commesse_fallite = solver.euristico_post(soluzionebasepost, commesse_residue, macchine_post, commesse_scartate, fprimo, fritardoprimo, ritardo_pesato_primo)
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
soluzione1post, f1post, contatoreLS1post, f1_ritardo_post, ritardo_post_pesato_1 = solver.insert_inter_macchina(lista_macchine_copy3, fpost, lista_veicoli)
#print(f1post)
print(f"{Fore.YELLOW}Risultato LS1[LS[G1+G2]+G3] (setup): ottenuto {f1post-fpost} minuti di setup")
#print(f1_ritardo_post)
print(f"{Fore.YELLOW}Risultato LS1[LS[G1+G2]+G3] (consegna): ottenuto {-f1_ritardo_post + fpost_ritardo} ore di ritardo")
print(f"Mosse LS1 - post: {contatoreLS1post}")
#output.write_output_soluzione_euristica(soluzione1post, os.getcwd() + '/Dati_output/insert_inter_post.xlsx')
tot1_post = time.time() - start1_post

# SEQUENZA PARZIALE
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}LS1+LS2[LS[G1+G2]+G3] (sequenza parziale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
start_time_tot_post = time.time()
soluzione4post, f4post, contatoreLS2post, f4_ritardo_post, ritardo_post_pesato_4 = solver.insert_intra(lista_macchine_copy3, f1post, lista_veicoli)
print(f'Mosse LS1+LS2 - post: {contatoreLS1post+contatoreLS2post}')
#solver.grafico_schedulazione(soluzione4post)
print(f'f4 {f4post}, f1 {f1post}')
#output.write_output_soluzione_euristica(soluzione4post, os.getcwd() + '/Dati_output/sequenza_parziale_post.xlsx')
print(f"{Fore.YELLOW}Risultato LS1+LS2[LS[G1+G2]+G3] (setup): ottenuto {f4post-f1post} minuti di setup")
print(f"{Fore.YELLOW}Risultato LS1+LS2[LS[G1+G2]+G3] (consegna): ottenuto {-f4_ritardo_post+f1_ritardo_post} ore di ritardo")

# SEQUENZA COMPLETA
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
print(f"{Fore.CYAN}{Style.BRIGHT}LS[LS[G1+G2]+G3] (sequenza finale)")
print(f"{Fore.CYAN}{Style.BRIGHT}{'-'*40}")
soluzione5post, f5post, contatoreLS3post, f5_ritardo_post, ritardo_post_pesato_5 = solver.swap_intra(lista_macchine_copy3, f4post, lista_veicoli)
print(f'Mosse LS1+LS2+LS3 - post: {contatoreLS1post+contatoreLS2post+contatoreLS3post}')
#soluzione_sequenza_post = [b for a in soluzione5post for b in a]
print(f"{Fore.YELLOW}Risultato LS[LS[G1+G2]+G3] (setup): ottenuto {f5post-f4post} minuti di setup")
print(f'f5 {f5_ritardo_post}, f4 {f4_ritardo_post}')
print(f"{Fore.YELLOW}Risultato LS[LS[G1+G2]+G3] (consegna): ottenuto {-f5_ritardo_post+f4_ritardo_post} ore di ritardo")

#Output di errore - commesse con veicolo errato e pertanto escluse (ERRORE NON RISOLUBILE DAL CODICE)
commesse_in_5post = {c['commessa'] for c in soluzione5post}
df = pd.DataFrame([
    {
        'id': c
    }
    for c in commesse_veicoli_errati
])

#Output di errore - commesse non schedulate (problemi release date)
df2 = pd.DataFrame([
    {
        'id': c.id_commessa,
        'release_date': c.release_date,
        'tassativita': c.tassativita
    }
    for c in commesse_fallite
])

#L'output di errore legato ai veicoli in sé è precedente (presso "elaborazione input(s)")
if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_tassative_error_output(df,os.getcwd() + '/Dati_output/Problemi_schedulazione_commesse.xlsx', 'Veicolo')
    output.write_tassative_error_output(df2,os.getcwd() + '/Dati_output/Problemi_schedulazione_commesse.xlsx', 'Release Date (RD)')
    output.write_tassative_error_output(df_tass,os.getcwd() + '/Dati_output/Problemi_schedulazione_commesse.xlsx', 'RD Tassative')
elif os.path.basename(os.getcwd()) == "progettoIS":
    output.write_tassative_error_output(df,os.getcwd() + '/PS-VRP/Dati_output/Problemi_schedulazione_commesse.xlsx', 'Veicolo')
    output.write_tassative_error_output(df2,os.getcwd() + '/PS-VRP/Dati_output/Problemi_schedulazione_commesse.xlsx', 'Release Date (RD)')
    output.write_tassative_error_output(df_tass,os.getcwd() + '/PS-VRP/Dati_output/Problemi_schedulazione_commesse.xlsx', 'RD Tassative')

ritardo1 = -f1_ritardo_post.total_seconds()/3600

#Soluzione finale secondo euristico
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
print(f"{Fore.YELLOW}SCHEDULATE FINALI: {len(soluzionefinale)}")

##GRASP
#iter = 1 #Definito prima o dal GUI

#Impostazione migliore soluzione per il GRASP; parametri divid e multip definiti in precedenza
fbest = fprimopost
print(fprimopost, ritardo_pesato_post_primo.total_seconds()/3600)
fobest = alfa*fprimopost -((1-alfa)*(ritardo_pesato_post_primo.total_seconds()/3600)/divid) + multip*(-len(soluzionefinale) + schedulabili)
fritardobest = fritardoprimopost
fritardopesatobest = ritardo_pesato_post_primo
soluzionebest = soluzionefinale
veicoli_best = deepcopy(lista_veicoli)

for _ in range(iter):
    print("\n" + "="*24)
    print(f"|||ITERAZIONE: {_} / {iter}|||")
    print("="*24 + "\n")

    #NB: gli input sono ricalcolati a ogni iterazione; non è ottimale ma è per evitare problemi con le due strutture dati utilizzate
    #NB2: questo si dimostra particolarmente conveniente nella nuova logica di veicoli
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

    ## EURISTICO COSTRUTTIVO
    start_time_eur = time.time()
    schedulazione3, f_obj3, causa_fallimento, lista_macchine, commesse_residue, f_obj3_ritardo, f_obj3_ritardo_pesato, df_tass = solver.euristico_costruttivo(commesse_da_schedulare, lista_macchine, lista_veicoli)
    #output.write_output_soluzione_euristica(schedulazione3, os.getcwd() + '/Dati_output/euristico_costruttivo.xlsx')
    commesse_non_schedulate = causa_fallimento | dizionario_filtri | commesse_veicoli_errati #| commesse_oltre_data (in caso d'uso, da reinserire eventualmente anche come output della chiamata al solver)
    end_time_eur = time.time()
    tot_time_eur = end_time_eur - start_time_eur

    ## DEEPCOPIES PER RICERCHE LOCALI (prima fase)
    lista_macchine_copy = deepcopy(lista_macchine)
    lista_macchine_copy1 = deepcopy(lista_macchine)
    lista_macchine_copy2 = deepcopy(lista_macchine)

    ## RICERCHE LOCALI (su primo euristico)
    start1 = time.time()
    soluzione1, f1, contatoreLS1, f1_ritardo, ritardo_pesato_1 = solver.insert_inter_macchina(lista_macchine_copy, f_obj3, lista_veicoli)
    #output.write_output_soluzione_euristica(soluzione1, os.getcwd() +'/Dati_output/insert_inter.xlsx')
    tot1 = time.time() - start1

    # SEQUENZA PARZIALE
    start_time_tot = time.time()
    soluzione4, f4, contatoreLS2, f4_ritardo, ritardo_pesato_4 = solver.insert_intra(lista_macchine_copy, f1, lista_veicoli)
    #output.write_output_soluzione_euristica(soluzione4, os.getcwd() + '/Dati_output/sequenza_parziale.xlsx')

    # SEQUENZA COMPLETA
    soluzione5, f5, contatoreLS3, f5_ritardo, ritardo_pesato_5 = solver.swap_intra(lista_macchine_copy, f4, lista_veicoli)
    #output.write_output_soluzione_euristica(soluzione5, os.getcwd() + '/Dati_output/sequenza.xlsx')
    tot_tot = time.time() - start_time_tot

    #Soluzione finale primo euristico
    fprimo = f5
    fritardoprimo = f5_ritardo
    ritardo_pesato_primo = ritardo_pesato_5
    macchine_post = lista_macchine_copy
    soluzionebasepost = soluzione5

    # EURISTICO NUOVO (gruppo3)
    ritardo5 = -f5_ritardo.total_seconds()/3600 

    start_time_post = time.time()
    soluzionepost, fpost, fpost_ritardo, ritardo_post_pesato, commesse_fallite = solver.euristico_post(soluzionebasepost, commesse_residue, macchine_post, commesse_scartate, fprimo, fritardoprimo, ritardo_pesato_primo)
    #output.write_output_soluzione_euristica(soluzionepost, os.getcwd() + '/PS-VRP/Dati_output/euristico_post.xlsx')
    #solver.grafico_schedulazione(soluzionepost)
    post_time = time.time() - start_time_post

    ## DEEPCOPIES PER RICERCHE LOCALI (seconda fase)
    lista_macchine_copy3 = deepcopy(macchine_post)
    lista_macchine_copy4 = deepcopy(macchine_post)
    lista_macchine_copy5 = deepcopy(macchine_post)


    ## RICERCHE LOCALI (su secondo euristico)

    # M2M - Bis
    start1_post = time.time()
    soluzione1post, f1post, contatoreLS1post, f1_ritardo_post, ritardo_post_pesato_1 = solver.insert_inter_macchina(lista_macchine_copy3, fpost, lista_veicoli)
    #output.write_output_soluzione_euristica(soluzione1post, os.getcwd() + '/Dati_output/insert_inter_post.xlsx')
    tot1_post = time.time() - start1_post

    # SEQUENZA PARZIALE
    start_time_tot_post = time.time()
    soluzione4post, f4post, contatoreLS2post, f4_ritardo_post, ritardo_post_pesato_4 = solver.insert_intra(lista_macchine_copy3, f1post, lista_veicoli)

    # SEQUENZA COMPLETA
    soluzione5post, f5post, contatoreLS3post, f5_ritardo_post, ritardo_post_pesato_5 = solver.swap_intra(lista_macchine_copy3, f4post, lista_veicoli)
    tot_tot_post = time.time() - start_time_tot_post
    ritardo1 = -f1_ritardo_post.total_seconds()/3600

    #Soluzione finale secondo euristico
    fprimopost = f5post
    fritardoprimopost = f5_ritardo_post
    ritardo_pesato_post_primo = ritardo_post_pesato_5
    soluzionefinale = soluzione5post

    ## STAMPE FINALI
    fo = alfa*fprimopost -((1-alfa)*(ritardo_pesato_post_primo.total_seconds()/3600)/divid) + multip*(-len(soluzionefinale) + schedulabili)
    print(fprimopost, ritardo_pesato_post_primo.total_seconds()/3600)
    print(fo, fobest)

    if fo < fobest and len(soluzionefinale) >= len(soluzionebest):
        print(len(soluzionefinale), len(soluzionebest))
        print(fo,fobest,fprimopost,ritardo_pesato_post_primo,fbest,fritardopesatobest)
        fbest = fprimopost #aggiornamento funzione obiettivo solo setup
        fritardobest = fritardoprimopost #aggiornamento funzione obiettivo solo ritardo non pesato
        fritardopesatobest = ritardo_pesato_post_primo #aggiornamento funzione obiettivo solo ritardo pesato
        fobest = fo #aggiornamento funzione obiettivo setup+ritardi pesati
        soluzionebest = soluzionefinale #aggiornamento soluzione
        veicoli_best = deepcopy(lista_veicoli)

        #Output di errore 1 - veicoli problematici
            #write_output a seguito

        #Output di errore 2 - commesse con veicoli errati
        df = pd.DataFrame([
            {
                'id': c
            }
            for c in commesse_veicoli_errati
        ])

        #Output di errore 3 - commesse non schedulate (problemi release date euristico finale)
        df2 = pd.DataFrame([
            {
                'id': c.id_commessa,
                'release_date': c.release_date,
                'tassativita': c.tassativita
            }
            for c in commesse_fallite
        ])

        #Output di errore 4 - tassative non schedulate come tali (problemi release date euristico ciclo 1)
            #write_output a seguito

        if os.path.basename(os.getcwd()) == "PS-VRP":
            output.write_veicoli_error_output(df_errati, os.getcwd() +'/Dati_output/Problemi_veicoli.xlsx')
            output.write_tassative_error_output(df,os.getcwd() + '/Dati_output/Problemi_schedulazione_commesse.xlsx', 'Veicolo')
            output.write_tassative_error_output(df2,os.getcwd() + '/Dati_output/Problemi_schedulazione_commesse.xlsx', 'Release Date (RD)')
            output.write_tassative_error_output(df_tass,os.getcwd() + '/Dati_output/Problemi_schedulazione_commesse.xlsx', 'RD Tassative')

        elif os.path.basename(os.getcwd()) == "progettoIS":
            output.write_veicoli_error_output(df_errati, os.getcwd() +'/PS-VRP/Dati_output/Problemi_veicoli.xlsx')
            output.write_tassative_error_output(df,os.getcwd() + '/PS-VRP/Dati_output/Problemi_schedulazione_commesse.xlsx', 'Veicolo')
            output.write_tassative_error_output(df2,os.getcwd() + '/PS-VRP/Dati_output/Problemi_schedulazione_commesse.xlsx', 'Release Date (RD)')
            output.write_tassative_error_output(df_tass,os.getcwd() + '/PS-VRP/Dati_output/Problemi_schedulazione_commesse.xlsx', 'RD Tassative')


print(f"{Fore.YELLOW}SETUP (BEST SOLUTION): {fbest:.2f}s")
print(f"{Fore.YELLOW}RITARDO (BEST SOLUTION): {-fritardobest} ore")
print(f"{Fore.YELLOW}RITARDO PESATO (BEST SOLUTION): {-fritardopesatobest} ore")
print(f"{Fore.YELLOW}SCHEDULAZIONI FINALI: {len(soluzionebest)}")

if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_soluzione_euristica(soluzionebest, os.getcwd() + '/Dati_output/schedulazione.xlsx')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_soluzione_euristica(soluzionebest, os.getcwd() + '/PS-VRP/Dati_output/schedulazione.xlsx')
if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_ridotto(soluzionebest, os.getcwd() + '/Dati_output/schedulazione_ridotta.xlsx')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_ridotto(soluzionebest, os.getcwd() + '/PS-VRP/Dati_output/schedulazione_ridotta.xlsx')
if os.path.basename(os.getcwd()) == "PS-VRP":
    output.write_output_ridotto_txt(soluzionebest, os.getcwd() + '/Dati_output/schedulazione_ridotta.txt')
if os.path.basename(os.getcwd()) == "progettoIS":
    output.write_output_ridotto_txt(soluzionebest, os.getcwd() + '/PS-VRP/Dati_output/schedulazione_ridotta.txt')

end_time_schedulazione = time.time()

seconds = end_time_schedulazione - start_time_schedulazione
minutes, secs = divmod(round(seconds), 60)
print(f"La schedulazione ha impiegato: {minutes}:{secs:02d} minuti")  # formato x:yz

solver.grafico_schedulazione(soluzionebest)  #Graficazione finale