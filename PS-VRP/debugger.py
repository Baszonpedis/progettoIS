from collections import defaultdict

#Per verificare che ci sia consistency tra le strutture dati ad ogni passaggio del main

block_a_text = """
251219 BIMEC 2
251897 BIMEC 4
251752 BIMEC 5
251218 BIMEC 5
251500 BIMEC 5
251565 BIMEC 5
251070 CASON
251773 CASON
251180 CASON
251895 CASON
251780 CASON
252112 R10
252282 R10
251984 R10
251362 R12
251631 R12
251237 R12
252084 R3
251655 R6
251573 R9
251082 T2
"""

# Paste your Block B data as a string [LISTA COMMESSE PROCESSATE (OGGETTI COMMESSA - ATTRIBUTO ID_COMMESSA ASSOCIATI COME ATTRIBUTO LISTA AD OGGETTO MACCHINA)]
block_b_text = """
BIMEC 2
-1
251219
BIMEC 3
-1
BIMEC 4
-1
251897
BIMEC 5
-1
251752
251218
251500
251565
CASON
-1
251070
251773
251180
251895
251780
H7
-1
R10
-1
252112
252282
251984
R12
-1
251362
251631
251237
R3
-1
252084
R5
-1
R6
-1
251655
R9
-1
251573
T1
-1
T2
-1
251082
T3
-1
T8
-1
T9
-1
"""

### Step 1: Parse Block A
id_to_machine = {}
for line in block_a_text.strip().splitlines():
    parts = line.strip().split()
    if len(parts) >= 2:
        id_str, machine = parts[0], " ".join(parts[1:])
        id_to_machine[id_str] = machine

### Step 2: Parse Block B
machine_to_ids = defaultdict(list)
current_machine = None
for line in block_b_text.strip().splitlines():
    line = line.strip()
    if line == "-1":
        continue
    elif not line.isnumeric():
        current_machine = line
    else:
        machine_to_ids[current_machine].append(line)

### Step 3: Check consistency
errors = []

# Forward check (from A to B)
for id_str, machine in id_to_machine.items():
    if id_str not in machine_to_ids[machine]:
        errors.append(f"❌ ID {id_str} assigned to '{machine}' in A but missing from B.")

# Backward check (from B to A)
for machine, ids in machine_to_ids.items():
    for id_str in ids:
        if id_to_machine.get(id_str) != machine:
            errors.append(f"❌ ID {id_str} assigned to '{machine}' in B but maps to '{id_to_machine.get(id_str)}' in A.")

# Final report
if errors:
    print("\n".join(errors))
    print(f"\n🔴 Found {len(errors)} inconsistencies.")
else:
    print("✅ All IDs and machine assignments are consistent between Block A and Block B.")