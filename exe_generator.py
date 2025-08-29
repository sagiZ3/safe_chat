import os, shutil, subprocess

files = ["main.py","server.py","client.py","gui.py","protocol.py", "logging_config.py"]
out_dir = "runnable_files"
os.makedirs(out_dir, exist_ok=True)

for f in files:
    subprocess.run(["pyinstaller","--onefile",f,"--distpath",out_dir])

for x in ["build","__pycache__"] + [f.replace(".py",".spec") for f in files]:
    if os.path.exists(x):
        shutil.rmtree(x) if os.path.isdir(x) else os.remove(x)
