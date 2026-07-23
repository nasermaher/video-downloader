# -*- mode: python ; coding: utf-8 -*-
# ملف تحزيم PyInstaller لبرنامج تحميل الفيديوهات.
# التشغيل: pyinstaller main.spec
# الناتج: dist/YoutubeDownloader.exe (ملف واحد مستقل)
#
# ملاحظة مهمة: لو عايز البرنامج المجمّع يشتغل من غير ما يحتاج تثبيت ffmpeg على جهاز
# المستخدم، حمّل نسخة ffmpeg.exe الثابتة (static build) وحطها في نفس مجلد الـ exe
# الناتج (جوه dist/) بعد التحزيم مباشرة. core/paths.py بيدور عليها هناك تلقائيًا.

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YoutubeDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
