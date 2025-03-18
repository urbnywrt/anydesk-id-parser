import os
import shutil
import time
import psutil
import subprocess

# ANSI escape codes for text color and formatting
RESET = '\033[0m'
BOLD = '\033[1m'
RED = '\033[91m'       # Для повторяющихся цифр
GREEN = '\033[92m'     # Для возрастающих последовательностей
YELLOW = '\033[93m'    # Для убывающих последовательностей
BLUE = '\033[94m'      # Для палиндромов
MAGENTA = '\033[95m'   # Для специальных чисел (228, 1488, 322)

def find_ad_anynet_id(file_path):
    """Ищет строку ad.anynet.id в файле."""
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('ad.anynet.id='):
                    return line.strip()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return None

def get_file_content(file_path):
    """Читает содержимое файла."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return ""

def is_beautiful_id(id_str):
    """Определяет, является ли ID 'красивым'."""
    # Проверка на повторяющиеся цифры (например, 1111)
    for i in range(len(id_str) - 3):
        if id_str[i] == id_str[i+1] == id_str[i+2] == id_str[i+3]:
            # Находим все вхождения повторяющейся цифры
            repeated_digit = id_str[i]
            part = ''
            j = i
            while j < len(id_str) and id_str[j] == repeated_digit:
                part += id_str[j]
                j += 1
            return {'type': 'repeated', 'part': part}
    
    # Проверка на возрастающую последовательность (например, 1234)
    if ''.join(sorted(id_str)) == id_str and len(set(id_str)) == len(id_str):
        return {'type': 'ascending', 'part': id_str}
    
    # Проверка на убывающую последовательность (например, 4321)
    if ''.join(sorted(id_str, reverse=True)) == id_str and len(set(id_str)) == len(id_str):
        return {'type': 'descending', 'part': id_str}
    
    # Проверка на палиндром (симметричные числа, например, 1221)
    if id_str == id_str[::-1]:
        return {'type': 'palindrome', 'part': id_str}
    
    # Проверка на наличие чисел 228, 1488, 322
    special_numbers = ['228', '1488', '322']
    for number in special_numbers:
        if number in id_str:
            return {'type': 'special_number', 'part': number}
    
    # Временно закомментировано условие про короткие ID
    # if len(id_str) <= 9:
    #     return {'type': 'short', 'part': id_str}
    
    return None

def parse_profiles(profiles_dir):
    """Парсит профили и ищет 'красивые' ID."""
    profiles = {}
    beautiful_profiles = {}

    # Проверяем, существует ли директория
    if not os.path.exists(profiles_dir):
        print(f"Profiles directory '{profiles_dir}' does not exist!")
        return profiles, beautiful_profiles

    # Проверяем содержимое директории
    dir_contents = os.listdir(profiles_dir)
    if not dir_contents:
        print(f"Profiles directory '{profiles_dir}' is empty!")
        return profiles, beautiful_profiles

    print(f"Contents of profiles directory: {dir_contents}")

    for profile_name in dir_contents:
        profile_path = os.path.join(profiles_dir, profile_name)
        if not os.path.isdir(profile_path):
            print(f"Skipping non-directory item: {profile_name}")
            continue

        # Учитываем новую структуру: profiles/ADx/AnyDesk/system.conf
        anydesk_dir = os.path.join(profile_path, "AnyDesk")
        system_conf_path = os.path.join(anydesk_dir, "system.conf")

        if not os.path.exists(system_conf_path):
            print(f"system.conf not found in profile: {profile_name}")
            continue

        print(f"Parsing profile: {profile_name}")
        ad_anynet_id = find_ad_anynet_id(system_conf_path)
        if ad_anynet_id:
            id_value = ad_anynet_id.split('=')[1]
            profiles[profile_name] = {
                'id': id_value,
                'config_path': system_conf_path
            }
            beauty_info = is_beautiful_id(id_value)
            if beauty_info:
                beautiful_profiles[profile_name] = {'id': id_value, 'beauty_info': beauty_info}
        else:
            print(f"No ad.anynet.id found in system.conf for profile: {profile_name}")

    return profiles, beautiful_profiles


def highlight_beautiful_id(id_str, beauty_info):
    """Подсвечивает 'красивую' часть ID."""
    part = beauty_info['part']
    type_ = beauty_info['type']

    highlighted_id = id_str

    if type_ == 'repeated':
        # Находим все вхождения повторяющейся части и подсвечиваем их красным
        start_index = 0
        while True:
            start_index = highlighted_id.find(part, start_index)
            if start_index == -1:
                break
            end_index = start_index + len(part)
            highlighted_part = RED + BOLD + part + RESET
            highlighted_id = highlighted_id[:start_index] + highlighted_part + highlighted_id[end_index:]
            start_index += len(highlighted_part)  # Учитываем длину подсвеченной части

    elif type_ == 'ascending':
        # Подсвечиваем возрастающие последовательности зеленым
        start_index = highlighted_id.find(part)
        if start_index != -1:
            end_index = start_index + len(part)
            highlighted_part = GREEN + BOLD + part + RESET
            highlighted_id = highlighted_id[:start_index] + highlighted_part + highlighted_id[end_index:]

    elif type_ == 'descending':
        # Подсвечиваем убывающие последовательности желтым
        start_index = highlighted_id.find(part)
        if start_index != -1:
            end_index = start_index + len(part)
            highlighted_part = YELLOW + BOLD + part + RESET
            highlighted_id = highlighted_id[:start_index] + highlighted_part + highlighted_id[end_index:]

    elif type_ == 'palindrome':
        # Подсвечиваем палиндромы синим
        start_index = highlighted_id.find(part)
        if start_index != -1:
            end_index = start_index + len(part)
            highlighted_part = BLUE + BOLD + part + RESET
            highlighted_id = highlighted_id[:start_index] + highlighted_part + highlighted_id[end_index:]

    elif type_ == 'special_number':
        # Подсвечиваем специальные числа магентой
        start_index = highlighted_id.find(part)
        if start_index != -1:
            end_index = start_index + len(part)
            highlighted_part = MAGENTA + BOLD + part + RESET
            highlighted_id = highlighted_id[:start_index] + highlighted_part + highlighted_id[end_index:]

    return highlighted_id

def kill_process(process_name):
    """Убивает процесс по имени."""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                proc.kill()
    except Exception as e:
        pass  # Игнорируем ошибки при завершении процесса

def generate_profiles(output_dir, anydesk_exe_path, num_ids, timeout_seconds):
    """Генерирует профили AnyDesk."""
    appdata_dir = os.getenv('APPDATA')
    anydesk_config_dir = os.path.join(appdata_dir, "AnyDesk")

    # Определяем следующий доступный номер профиля
    existing_profiles = [name for name in os.listdir(output_dir) if name.startswith("AD") and name[2:].isdigit()]
    next_profile_number = max([int(name[2:]) for name in existing_profiles], default=0) + 1

    # Прогресс-бар
    print("Generating profiles:")
    for i in range(next_profile_number, next_profile_number + num_ids):
        progress = int((i - next_profile_number + 1) / num_ids * 100)
        bar = f"[{'#' * (progress // 2):<50}] {progress}%"
        print(f"\r{bar}", end="")

        profile_name = f"AD{i}"
        profile_dir = os.path.join(output_dir, profile_name)
        anydesk_subdir = os.path.join(profile_dir, "AnyDesk")
        os.makedirs(anydesk_subdir, exist_ok=True)

        # Убиваем процесс AnyDesk
        kill_process("AnyDesk.exe")

        # Запускаем AnyDesk
        subprocess.Popen([anydesk_exe_path], shell=True)
        time.sleep(timeout_seconds)

        # Копируем конфигурацию с обработкой ошибок
        try:
            if os.path.exists(anydesk_config_dir):
                shutil.copytree(anydesk_config_dir, anydesk_subdir, dirs_exist_ok=True)
        except Exception as e:
            pass
            #print(f"\nError copying files for profile {profile_name}: {e}")

        # Убиваем процесс AnyDesk снова
        kill_process("AnyDesk.exe")
        if os.path.exists(anydesk_config_dir):
            shutil.rmtree(anydesk_config_dir, ignore_errors=True)

    print("\nAll profiles generated successfully!")

def apply_profile(profiles_dir, profile_name):
    """Копирует конфигурацию профиля в папку AnyDesk пользователя и запускает AnyDesk."""
    appdata_dir = os.getenv('APPDATA')
    anydesk_config_dir = os.path.join(appdata_dir, "AnyDesk")

    # Удаляем текущую конфигурацию AnyDesk
    if os.path.exists(anydesk_config_dir):
        shutil.rmtree(anydesk_config_dir, ignore_errors=True)

    # Находим путь к конфигурации выбранного профиля
    profile_path = os.path.join(profiles_dir, profile_name)
    anydesk_subdir = os.path.join(profile_path, "AnyDesk")

    if not os.path.exists(anydesk_subdir):
        print(f"Profile '{profile_name}' does not exist or is invalid!")
        return

    # Копируем конфигурацию профиля в папку AnyDesk
    try:
        shutil.copytree(anydesk_subdir, anydesk_config_dir, dirs_exist_ok=True)
        print(f"Profile '{profile_name}' applied successfully!")
    except Exception as e:
        print(f"Error applying profile '{profile_name}': {e}")
        return

    # Запускаем AnyDesk
    anydesk_exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AnyDesk.exe")
    if not os.path.exists(anydesk_exe_path):
        print(f"Error: AnyDesk.exe not found at {anydesk_exe_path}")
        return

    subprocess.Popen([anydesk_exe_path], shell=True)
    print("AnyDesk started with the selected profile.")

def main_menu():
    # Определяем директорию для профилей
    script_dir = os.path.dirname(os.path.abspath(__file__))
    profiles_dir = os.path.join(script_dir, "profiles")
    os.makedirs(profiles_dir, exist_ok=True)

    # Путь к AnyDesk.exe по умолчанию
    default_anydesk_path = os.path.join(script_dir, "AnyDesk.exe")

    # Парсим профили один раз для использования в меню
    profiles, beautiful_profiles = parse_profiles(profiles_dir)

    while True:
        print("\nMain Menu:")
        print("1. Parse Profiles")
        print("2. Generate Profiles")
        print("3. View Beautiful IDs")
        print("4. Get Configuration by ID")
        print("5. Apply Profile to AnyDesk")
        print("6. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            profiles, beautiful_profiles = parse_profiles(profiles_dir)
            print("Profiles parsed successfully!")
            print("Found IDs:")
            for profile_name, profile_data in profiles.items():
                print(f"{profile_name}: {profile_data['id']}")

        elif choice == '2':
            anydesk_exe_path = input(f"Enter the path to AnyDesk.exe (default: {default_anydesk_path}): ").strip()
            if not anydesk_exe_path:
                anydesk_exe_path = default_anydesk_path  # Используем путь по умолчанию

            num_ids = int(input("Enter the number of IDs to generate: "))
            timeout_seconds = int(input("Enter timeout duration (in seconds): "))

            generate_profiles(profiles_dir, anydesk_exe_path, num_ids, timeout_seconds)
            print("Profiles generated successfully!")

            # Обновляем список профилей после генерации
            profiles, beautiful_profiles = parse_profiles(profiles_dir)
            print("Updated Found IDs:")
            for profile_name, profile_data in profiles.items():
                print(f"{profile_name}: {profile_data['id']}")

        elif choice == '3':
            print("\nBeautiful IDs:")
            if beautiful_profiles:
                for profile_name, data in beautiful_profiles.items():
                    id_str = data['id']
                    beauty_info = data['beauty_info']
                    highlighted_id = highlight_beautiful_id(id_str, beauty_info)
                    print(f"{profile_name}: {highlighted_id}")
            else:
                print("No beautiful IDs found.")

        elif choice == '4':
            user_input = input("Enter ID to get configuration (or 'exit' to cancel): ")
            if user_input.lower() == 'exit':
                continue

            found = False
            for profile_name, profile_data in profiles.items():
                if profile_data['id'] == user_input:
                    print(f"Configuration for profile {profile_name}:")
                    config_content = get_file_content(profile_data['config_path'])
                    print(config_content)
                    found = True
                    break
            
            if not found:
                print("ID not found.")

        elif choice == '5':
            profile_name = input("Enter the profile name to apply (e.g., AD1): ")
            apply_profile(profiles_dir, profile_name)

        elif choice == '6':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()