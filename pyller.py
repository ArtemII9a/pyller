# ------------
# std imports
# -----------
import os
import winreg
import ctypes
from enum import Enum
from pathlib import Path
from uuid import uuid4 

# ------------
# Custom types
# ------------
class Scope(Enum):
    USER = 1
    SYSTEM = 2

class UserIsNotAnAdminError(Exception): pass

# ----------------
# Global constants
# ----------------
HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x1A
REGISTRY_VALUE = 'Path'


# --------------------
# Fuctions definitions
# --------------------
def broadcast_env_change():
    ctypes.windll.user32.SendMessageW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        'Environment'
    )


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


def is_valid_dir(path: Path):
    if not path.exists():
        return 'Path does not exist.\n\n'
    
    if not path.is_dir():
        return 'Path is not a directory.\n\n'
    
    tmp = path / f'.tmp_{uuid4().hex}'

    try:
        with open(tmp, 'w') as file:
            file.write('tmp')
    except OSError as error:
        return f'Could not create a tmp file in the specified directory: {error}\n\n'
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass

    return None


def get_path_from_input(message: str):
    while True:
        raw_path: str = input(f"{message}\n").strip()
        path: Path = Path(raw_path)

        error: str | None = is_valid_dir(path)

        if not error:
            return path
        
        print(error)


def get_int_input(message: str):
    answer: str = input(f'{message}\n').strip()
    try:
        return int(answer)
    except ValueError:
        print('Invalid input.\n\n')
        return




def get_scope_from_input(message: str):
    while True:
        answer: int | None = get_int_input(message)

        if answer is None:
            continue
        elif answer == 1:
            return Scope.USER
        elif answer == 2:
            return Scope.SYSTEM
        else:
            print('Invalid option.\n\n')


def backup_as_txt(registry: str):
    while True:
        make_a_backup: int | None = get_int_input('Make a backup of the registry?\n1. Yes.\n2. No.\n')

        if make_a_backup is None:
            continue
        elif make_a_backup == 2:
            return
        elif make_a_backup == 1:
            backup_dir = get_path_from_input('Please provide a path for the backup file.\n')
            backup = backup_dir / f'path_registry_backup_{uuid4().hex}.txt'

            with open(backup, mode='w') as file:
                file.write(registry)

            print(f'{backup} has been successfully created.\n\n')
            return
        else:
            continue


def get_registry_key_user():
    access = winreg.KEY_READ | winreg.KEY_SET_VALUE
    root: int = winreg.HKEY_CURRENT_USER
    subkey = r'Environment'
    return (access, root, subkey)


def get_registry_key_system():
    access = winreg.KEY_READ | winreg.KEY_SET_VALUE
    access |= winreg.KEY_WOW64_64KEY
    root = winreg.HKEY_LOCAL_MACHINE
    subkey = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    return (access, root, subkey)


def add_to_path_registry(entry: Path, scope: Scope = Scope.USER):
    if scope == Scope.USER:
        access, root, subkey = get_registry_key_user()
    elif scope == Scope.SYSTEM and is_admin():
        access, root, subkey = get_registry_key_system()
    else:
        print('User has no admin privileges to update system registry.\n\n')
        return


    with winreg.OpenKey(root, subkey, 0, access) as key:
        try:
            path_registry, registry_type_id = winreg.QueryValueEx(key, REGISTRY_VALUE)
        except FileNotFoundError:
            print('PATH variable has not been found. Creating one...\n\n')
            path_registry = ''
            registry_type_id = winreg.REG_EXPAND_SZ

        backup_as_txt(path_registry)

        if not path_registry:
            updated_path = entry 
        
        if path_registry.endswith(';'):
            updated_path = rf'{path_registry}{entry}'
        else:
            updated_path = rf'{path_registry};{entry}'

        winreg.SetValueEx(key, REGISTRY_VALUE, 0, registry_type_id, updated_path)

        broadcast_env_change()
    
    print('The registry has been successfully updated.\n\n')

def remove_from_path_registry(entry: Path, scope: Scope):
    # TODO write code to remove an entry from a registry 
    pass


# TODO add normalization and deduplication


def main():

    try:
        while True:
            entry = get_path_from_input('Enter a path to add to a registry:\n')
            scope = get_scope_from_input('Choose the PATH registry:\n1. User.\n2. System.\n')

            add_to_path_registry(entry, scope)
    except KeyboardInterrupt:
        print('A keyboard interrupt signal has been recieved. Terminating the program...\n')

    
if __name__ == '__main__':
    main()