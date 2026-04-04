import os
import winreg
from enum import Enum
from pathlib import Path
import ctypes


VALUE_NAME: str = 'Path'
HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x1A


class Scope(Enum):
    USER = 1
    SYSTEM = 2

# To appy env changes immediately
def broadcast_env_change():
    ctypes.windll.user32.SendMessageW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        'Environment'
    )

def backup_as_txt(registry: str, backup_dir: str):
        os.makedirs(backup_dir, exist_ok=True)

        # Path structure validaton here

        backup_path = os.path.join(backup_dir, 'path_registry_backup.txt')

        with open(
            file=backup_path, 
            mode='w'
        ) as backup_file:
            try:
                backup_file.write(registry)
            except PermissionError:
                print("Error: You do not have permission to write to this file.")
            except OSError as e:
                print(f"OS error occurred: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


def get_registry_key(scope: Scope):
    access = winreg.KEY_READ | winreg.KEY_SET_VALUE
    root: int = winreg.HKEY_CURRENT_USER
    subkey = r'Environment'

    match scope:
        case Scope.USER:
            pass
        case Scope.SYSTEM:
            access |= winreg.KEY_WOW64_64KEY
            root = winreg.HKEY_LOCAL_MACHINE
            subkey = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
            return (
                access,
                root,
                subkey
            )
        case _:
            print(
                'scope must be either USER or SYSTEM\n',
                'using default option: USER\n'
            )
            pass    

    return (
        access,
        root,
        subkey
    )


def add_to_path_registry(entry: str, backup_dir: str, scope: Scope = Scope.USER):
    access, root, subkey = get_registry_key(scope)
    with winreg.OpenKey(root, subkey, 0, access) as key:
        try:
            path_registry, registry_type_id = winreg.QueryValueEx(key, VALUE_NAME)
        except FileNotFoundError:
            path_registry = ""
            registry_type_id = winreg.REG_EXPAND_SZ

        print(path_registry)
        backup_as_txt(path_registry, backup_dir)

        updated_path: str = rf'{path_registry};{entry}' if path_registry else entry
        winreg.SetValueEx(key, VALUE_NAME, 0, registry_type_id, updated_path)

        broadcast_env_change()
        
        # need to know how it went in the end


def main():
    # here cmd interaction
    # move path validation to a separate function, because it would be handy for entry as well
    # add normalization and deduplication

    entry = r'D:\aaa\helpers'
    scope: Scope = Scope.USER

    print('Please enter a path for the backup file:\n')
    backup_dir = input()

    if (scope == Scope.SYSTEM) and not is_admin():
        print('Current User should have Admin Priveleges to update SYSTEM PATH')
    elif (scope == Scope.SYSTEM) and is_admin():
        add_to_path_registry(entry, backup_dir, scope)
    else:
        add_to_path_registry(entry, backup_dir)

    
if __name__ == '__main__':
    main()