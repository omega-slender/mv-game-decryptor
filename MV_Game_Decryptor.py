from concurrent.futures import ThreadPoolExecutor
from Resources.decryptor import MVDecryptor
from colorama import init, Fore, Style
from threading import Lock
from pathlib import Path
import sys, json, shutil

def load_json(file_path):
    try:
        with file_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"- {Fore.RED}{Style.BRIGHT}Error: 'System.json' is empty or has an invalid format")
    except FileNotFoundError:
        print(f"- {Fore.RED}{Style.BRIGHT}Error: File not found {file_path}")
    
    return None

def get_rpgproject_path(script_path):
    resources_path = script_path / 'Resources'
    rpgproject_path = script_path / 'Game.rpgproject'

    if not rpgproject_path.is_file():
        rpgproject_path = resources_path / 'Game.rpgproject'
        if not rpgproject_path.is_file():
            print(f"- {Fore.RED}{Style.BRIGHT}Error: 'Game.rpgproject' file is missing in the 'Resources' folder")
            return None

    return rpgproject_path

def validate_project_files(project_files):
    missing_files = [file for name, file in project_files.items() if not file.is_file() and name != 'rpgproject']
    if missing_files:
        print(f"- {Fore.RED}{Style.BRIGHT}Error: Missing required files: {', '.join(f.name for f in missing_files)}")
        return False
    
    return True

def update_system_file(project_files):
    required_keys = ['hasEncryptedImages', 'hasEncryptedAudio', 'encryptionKey']
    data = load_json(project_files['system'])
    if not data:
        return False

    if any(key not in data for key in required_keys):
        print(f"- {Fore.RED}{Style.BRIGHT}Error: Missing required keys in 'System.json'")
        return False

    if project_files['rpgproject'].is_file() and not data.get('hasEncryptedImages', False) and not data.get('hasEncryptedAudio', False):
        print(f"- {Fore.RED}{Style.BRIGHT}Error: This project is already editable")
        return False

    data.update({'hasEncryptedImages': False, 'hasEncryptedAudio': False})
    try:
        with project_files['system'].open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"- {Fore.CYAN}{Style.BRIGHT}Updated: 'System.json' successfully")
        return True
    except Exception as e:
        print(f"- {Fore.RED}{Style.BRIGHT}Error updating 'System.json': {e}")
        return False

def get_encryption_key(project_files):
    data = load_json(project_files['system'])
    return data.get('encryptionKey') if data else None
    
def decrypt_file(mv_decrypter, file_path, decrypted_count, total_files, lock):
    mv_decrypter.decrypt_file(file_path, True)
    with lock:
        decrypted_count[0] += 1
        print(f"\r- {Fore.CYAN}{Style.BRIGHT}Decrypted: {decrypted_count[0]}/{total_files} edited files", end="")

def decrypt_files(mv_decrypter, files):
    if not files:
        print(f"- {Fore.CYAN}{Style.BRIGHT}Decrypted: No files to decrypt")
        return

    total_files = len(files)
    decrypted_count = [0]
    lock = Lock()
    
    with ThreadPoolExecutor() as executor:
        for file in files:
            executor.submit(decrypt_file, mv_decrypter, file, decrypted_count, total_files, lock)
    
def process_project(project_path):
    try:
        project_path = Path(project_path)
        script_path = Path(__file__).parent

        project_files = {
            'index': project_path / 'index.html',
            'package': project_path / 'package.json',
            'system': project_path / 'data/System.json',
            'rpgproject': project_path / 'Game.rpgproject'
        }

        rpgproject_path = get_rpgproject_path(script_path)
        if not rpgproject_path or not validate_project_files(project_files):
            return

        if not update_system_file(project_files):
            return

        encryption_key = get_encryption_key(project_files)
        if not encryption_key:
            return

        mv_decrypter = MVDecryptor(encryption_key)
        print(f"- {Fore.GREEN}{Style.BRIGHT}Encryption key loaded successfully")
        
        audio_files = list(project_path.rglob('audio/**/*.rpgmvo')) + list(project_path.rglob('audio/**/*.rpgmvm'))
        img_files = list(project_path.rglob('img/**/*.rpgmvp'))
        all_files = audio_files + img_files
        
        decrypt_files(mv_decrypter, all_files)
        shutil.copy(rpgproject_path, project_path)

        line_break = '\n' if all_files else ''
        print(f"{line_break}- {Fore.GREEN}{Style.BRIGHT}Process completed successfully")
        
    except Exception as e:
        print(f"- {Fore.RED}{Style.BRIGHT}Unexpected error: {e}")

if __name__ == "__main__":
    init(autoreset=True)
    print(f"{Fore.BLUE}{Style.BRIGHT}MV GAME DECRYPTOR v1.0")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}By Omega Slender")
    print(f"{Fore.WHITE}{Style.BRIGHT}\nPROCESSES:")

    if len(sys.argv) != 2:
        print(f"- {Fore.RED}{Style.BRIGHT}Error: No project folder specified")
    else:
        project = sys.argv[1]
        project_path = Path(project)

        if project_path.is_file() and project_path.name == 'index.html':
            project_path = project_path.parent
        
        process_project(project_path)

    input(f"{Fore.WHITE}\nPress 'Enter' to close...")