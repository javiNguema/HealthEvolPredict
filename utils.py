import sys
import os
import platform
import subprocess

def resource_path(relative_path):
    """
    Get absolute path to resource.
    Works in development and in PyInstaller bundle.
    """

    if getattr(sys, 'frozen', False):
        # Running inside PyInstaller bundle
        base_path = sys._MEIPASS # type: ignore
    else:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)



def kill_ollama_process() -> None:
    """
    Identifies and terminates any active local Ollama engine instances
    running on the host system upon application exit.
    """
    sys_os = platform.system()
    
    try:
        if sys_os == "Darwin":  # macOS
            print("Terminando instancias locales de Ollama en macOS...")
            # Kill the background CLI engine process
            subprocess.run(["pkill", "-f", "ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Kill the desktop app process if running
            subprocess.run(["pkill", "-f", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif sys_os == "Windows":
            print("Terminando instancias locales de Ollama en Windows...")
            # Forcefully terminate the task running the Ollama engine executable
            subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    except Exception as e:
        print(f"Aviso: No se pudo cerrar Ollama automáticamente: {e}")