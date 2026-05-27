import subprocess
import shutil
import urllib.request
import platform
import os
import time
from typing import Callable

def get_ollama_executable():
    """Returns a permission-safe local absolute path for the Ollama binary."""
    sys_os = platform.system()
    if sys_os == "Darwin":
        # Using a user-owned folder instead of the restricted /usr/local/bin
        return os.path.expanduser("~/.local/bin/ollama")
    elif sys_os == "Windows":
        local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        return os.path.join(local_appdata, "Programs", "Ollama", "ollama.exe")
    return "ollama"

def ensure_ollama_setup(logs: Callable | None = None):
    # Safe logging wrapper fallback to ensure callability without type ignores
    log = logs if logs is not None else lambda message: None

    log(message='Verificando la instalación de Ollama...')
    time.sleep(0.5)
    ollama_path = get_ollama_executable()
    
    # 1. If not found globally or in our safe local path, run the installer
    if not shutil.which("ollama") and not os.path.exists(ollama_path):
        log(message='No se detectó la instalación de Ollama. Instalando dependencias locales...')
        time.sleep(0.5)
        sys_os = platform.system()
        
        if sys_os == "Darwin": # macOS
            try:
                log(message='Descargando Ollama para macOS...')
                time.sleep(0.5)
                url = "https://ollama.com/download/ollama-darwin.zip"
                
                # Fetching via native curl to prevent Python local SSL issuer bugs
                subprocess.run(["curl", "-L", url, "-o", "ollama.zip"], check=True)
                
                log(message="Extrayendo el archivo en la ruta de Aplicaciones...")
                time.sleep(0.5)
                os.system("unzip -o ollama.zip -d /Applications/")
                
                # Create our safe local binary folder inside the user's home directory
                local_bin_dir = os.path.expanduser("~/.local/bin")
                os.makedirs(local_bin_dir, exist_ok=True)
                
                log(message="Creando un enlace simbólico de aplicación local...")
                time.sleep(0.5)
                # Link directly to the user's local space (No 'Permission denied' errors here!)
                os.system(f"ln -sf /Applications/Ollama.app/Contents/Resources/ollama {ollama_path}")
                
                # CRITICAL: Strip the macOS security quarantine attribute so the engine can boot up silently
                log(message="Borrar bits de cuarentena de Gatekeeper en macOS...")
                time.sleep(0.5)
                os.system("xattr -r -d com.apple.quarantine /Applications/Ollama.app")
                
                if os.path.exists("ollama.zip"):
                    os.remove("ollama.zip")
            except Exception as e:
                log(message=f"Error al instalar Ollama automáticamente en Mac: {e}")
                time.sleep(2)
                return
                
        elif sys_os == "Windows":
            try:
                log(message="Descargando Ollama para Windows...")
                time.sleep(0.5)
                url = "https://ollama.com/download/OllamaSetup.exe"
                urllib.request.urlretrieve(url, "OllamaSetup.exe")
                
                log(message="Ejecución en segundo plano del hilo de instalación silenciosa...")
                time.sleep(0.5)
                subprocess.run(["OllamaSetup.exe", "/silent"], check=True)
                if os.path.exists("OllamaSetup.exe"):
                    os.remove("OllamaSetup.exe")
                time.sleep(5)
            except Exception as e:
                log(message=f"Error al instalar Ollama automáticamente en Windows: {e}")
                time.sleep(2)
                return

    # Determine how we are executing the tool
    cmd_executable = ollama_path if os.path.exists(ollama_path) else "ollama"

    is_engine_running = False
    try:
        # Run a fast check to see if the local engine is already active
        subprocess.run([cmd_executable, "list"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        is_engine_running = True
        log(message="El servicio en segundo plano de Ollama ya está activo. Omitiendo el lanzamiento de la aplicación.")
        time.sleep(0.5)
    except Exception:
        # If it fails, the daemon is down and we genuinely need to boot it
        log(message="El servicio en segundo plano de Ollama está fuera de línea.")
        time.sleep(2)

    # Only invoke the OS 'open' command if the engine didn't respond above
    if not is_engine_running:
        sys_os = platform.system()
        if sys_os == "Darwin":
            log(message="Lanzando pipeline de servicio del motor Ollama...")
            time.sleep(0.5)
            subprocess.Popen(["open", "-a", "Ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(4)
        elif sys_os == "Windows":
            # Optional Windows daemon wake-up fallback if needed later
            pass

    # 3. Validation loop: Wait for the local background service to finish initializing (if just launched)
    log(message="Verificando que el servicio en segundo plano del demonio local de Ollama responde...")
    time.sleep(0.5)
    for attempt in range(8):
        try:
            subprocess.run([cmd_executable, "list"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            break
        except Exception:
            if attempt == 7:
                log(message=" Aviso: La instalación de Ollama está completa, pero el motor en segundo plano está fuera de línea. Por favor, haga clic en el ícono de Ollama para iniciarlo manualmente.")
                time.sleep(2)
                return
            log(message="Esperando a que la instancia del servicio en segundo plano de Ollama se monte...")

            time.sleep(3)

    # 4. Pull down the text-to-SQL weights model completely locally
    try:
        log(message='Descargando y configurando parametros para Ollama (qwen2.5-coder:3b)...')
        time.sleep(1)
        subprocess.run([cmd_executable, "pull", "qwen2.5-coder:3b"], check=True)
        log(message='Inicialización de chadbot completada con éxito...')
        time.sleep(1)
    except Exception as e:
        log(message=f'Error al descargar los pesos del modelo desde el servidor: {e}')
        time.sleep(2)