# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# --- LISTA FILE DA INCLUDERE ---
added_files = [
    ('Dati_input', 'Dati_input'),
    ('main.py', '.'),
    ('solver.py', '.'),
    ('read_excel.py', '.'),
    ('output.py', '.'),
    ('veicolo.py', '.'),
    ('commessa.py', '.'),
    ('macchina.py', '.'),
    ('istituto_stampa_s_r_l__logo.png', '.'), 
    ('istituto_stampa_s_r_l__logo-removebg-preview.png', '.')
]

a = Analysis(
    ['interfaccia.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['pandas', 'openpyxl', 'matplotlib', 'PIL', 'colorama', 'babel.numbers', 'matplotlib.backends.backend_tkagg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Schedulatore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # --- QUESTA E' LA RIGA PER L'ICONA DELL'EXE ---
    # Assicurati che il file PNG sia nella stessa cartella di questo file .spec!
    icon='istituto_stampa_s_r_l__logo.png' 
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Schedulatore',
)