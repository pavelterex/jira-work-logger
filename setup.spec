# -*- mode: python -*-

block_cipher = None

data_files = [
    ('jira_work_logger\\gui\\misc', 'gui\\misc'),
	('README.md', '.'),
	('jira_work_logger\\config.yaml', '.')
]

a = Analysis(['jira_work_logger\\runner.py'],
             pathex=['jira_work_logger'],
             datas=data_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=['.\\use_lib_hook.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Jira Work Logger',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='jira_work_logger\\gui\\misc\\clock-icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Jira Work Logger')
