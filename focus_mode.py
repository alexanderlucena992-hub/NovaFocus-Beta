import os
import time
import subprocess
import json
import urllib.request
from datetime import datetime, timedelta

# Configuration
WATCH_PATH = "."
IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".gemini"}
ACTIVITY_THRESHOLD = 3  # Regresamos a los 3 cambios para mayor control
WINDOW_SECONDS = 60     
POLL_INTERVAL = 2       

class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class SystemDND:
    # Processes to "freeze" during focus mode
    TARGET_PROCESSES = ["slack", "thunderbird", "geary", "evolution", "mailspring", "discord"]

    @staticmethod
    def set_enabled(enabled):
        try:
            # 1. Toggle GNOME notifications
            val = "false" if enabled else "true"
            subprocess.run([
                "gsettings", "set", "org.gnome.desktop.notifications", 
                "show-banners", val
            ], check=False)

            # 2. Freeze/Thaw applications
            signal = "-STOP" if enabled else "-CONT"
            for proc in SystemDND.TARGET_PROCESSES:
                subprocess.run(["pkill", signal, "-x", proc], check=False, stderr=subprocess.DEVNULL)
            
            return True
        except Exception as e:
            return False

class ActivityMonitor:
    def __init__(self, path):
        self.path = path
        self.last_mtimes = {}
        self.activity_log = []
        self.is_focusing = False
        
    def scan(self):
        changes = 0
        current_time = time.time()
        for root, dirs, files in os.walk(self.path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(filepath)
                    if filepath in self.last_mtimes:
                        if mtime > self.last_mtimes[filepath]:
                            changes += 1
                            self.activity_log.append(current_time)
                    self.last_mtimes[filepath] = mtime
                except OSError:
                    continue
        return changes

    def get_activity_score(self):
        cutoff = time.time() - WINDOW_SECONDS
        self.activity_log = [t for t in self.activity_log if t > cutoff]
        return len(self.activity_log)

    def update_status(self):
        score = self.get_activity_score()
        should_focus = score >= ACTIVITY_THRESHOLD
        
        if should_focus != self.is_focusing:
            self.is_focusing = should_focus
            self.trigger_dnd(should_focus)
            return True
        return False

    def trigger_dnd(self, enabled):
        SystemDND.set_enabled(enabled)
        status = f"{Color.BOLD}{Color.PURPLE}ON (Apps Frozen){Color.END}" if enabled else f"{Color.YELLOW}OFF (Apps Restored){Color.END}"
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Focus Mode: {status}")

# Translations
STRINGS = {
    "es": {
        "title": "--- Focus Mode para Código ---",
        "monitoring": "Vigilando",
        "threshold": "Umbral: {0} cambios en {1}s",
        "active": "ENFOQUE ACTIVO",
        "idle": "ESPERANDO",
        "activity": "Actividad",
        "on": "ENCENDIDO (Apps Congeladas)",
        "off": "APAGADO (Apps Restauradas)",
        "stopping": "Deteniendo Focus Mode...",
        "restored": "Notificaciones restauradas.",
        "select": "Selecciona idioma / Select language:\n1. Español\n2. English\n> "
    },
    "en": {
        "title": "--- Focus Mode for Code ---",
        "monitoring": "Monitoring",
        "threshold": "Threshold: {0} changes / {1}s",
        "active": "FOCUS ACTIVE",
        "idle": "WAITING",
        "activity": "Activity",
        "on": "ON (Apps Frozen)",
        "off": "OFF (Apps Restored)",
        "stopping": "Stopping Focus Mode...",
        "restored": "Notifications restored.",
        "select": "Selecciona idioma / Select language:\n1. Español\n2. English\n> "
    }
}

def select_language():
    choice = input(STRINGS["es"]["select"]).strip()
    return "en" if choice == "2" else "es"

def main():
    lang_code = select_language()
    lang = STRINGS[lang_code]
    
    monitor = ActivityMonitor(WATCH_PATH)
    print(f"\n{Color.BOLD}{Color.PURPLE}==============================")
    print(f"   MADE BY NOVAVOLPERS INC")
    print(f"=============================={Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{lang['title']}{Color.END}")
    print(f"{lang['monitoring']}: {os.path.abspath(WATCH_PATH)}")
    print(lang['threshold'].format(ACTIVITY_THRESHOLD, WINDOW_SECONDS))
    print("----------------------------")
    
    monitor.scan()
    
    try:
        while True:
            monitor.scan()
            
            # Custom trigger logic for localization
            score = monitor.get_activity_score()
            should_focus = score >= ACTIVITY_THRESHOLD
            
            if should_focus != monitor.is_focusing:
                monitor.is_focusing = should_focus
                SystemDND.set_enabled(should_focus)
                status = lang['on'] if should_focus else lang['off']
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Focus Mode: {Color.BOLD}{Color.PURPLE if should_focus else Color.YELLOW}{status}{Color.END}")
            
            bar_length = 20
            filled_length = min(int(bar_length * score / ACTIVITY_THRESHOLD), bar_length)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            
            status_color = Color.PURPLE if monitor.is_focusing else Color.CYAN
            status_text = lang['active'] if monitor.is_focusing else lang['idle']
            
            print(f"\r{status_color}{status_text}{Color.END} | {lang['activity']}: [{bar}] ({score}/{ACTIVITY_THRESHOLD})  ", end="", flush=True)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}--- {lang['stopping']} ---{Color.END}")
        if monitor.is_focusing:
            SystemDND.set_enabled(False)
        print(f"{Color.GREEN}{lang['restored']}{Color.END}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
