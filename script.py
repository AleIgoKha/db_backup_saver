import subprocess
import os
import json
from dotenv import load_dotenv
from pathlib import Path
from datetime import date, datetime, timedelta


from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
CREDENTIALS_JSON = os.getenv("CREDENTIALS_JSON")


Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# функция для создания дампа базы данных
def dump_postgres():
    today = Path(OUTPUT_DIR) / f"backup_{date.today().isoformat()}.dump"
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD
    
    command = [
        "pg_dump",
        "-h", DB_HOST,
        "-p", str(DB_PORT),
        "-U", DB_USER,
        "-F", "c",
        "-b",
        "-v",
        # "--data-only",
        "-f", str(today),
        DB_NAME
    ]
    
    
    subprocess.run(command, env=env, check=True)
    print(f"Database dumped to {today}")
    return today


# аутентификация с google disc
def authenticate_drive():
    gauth = GoogleAuth()
    
    # если переменная определена, то записываем ее данные в файл
    # если не определена, то 
    if CREDENTIALS_JSON:
        with open("credentials.json", "w") as f:
            f.write(CREDENTIALS_JSON)
    
    gauth.LoadCredentialsFile("credentials.json")
    
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
        
    gauth.SaveCredentialsFile("credentials.json")
    
    return GoogleDrive(gauth)


# функция для загрузки дампа базы данных в папку на google disk
def upload_to_drive(drive, file_path):
    file_drive = drive.CreateFile({'title': file_path.name,
                                   'parents': [{'id': GOOGLE_DRIVE_FOLDER_ID}] })
    file_drive.SetContentFile(str(file_path))
    file_drive.Upload()
    
    
    print(f"Uploaded {file_path} to Google Drive with file ID {file_drive['id']}")


# функция для удаление дампов старше 7 дней
def cleanup_old_backups(drive, folder_id, keep_days=7):
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    
    # List all files in the folder
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    
    for file_drive in file_list:
        # Try to parse the date from the filename: backup_YYYY-MM-DD.dump
        try:
            file_date_str = file_drive['title'].split('_')[1].split('.')[0]
            file_date = datetime.fromisoformat(file_date_str)
        except Exception:
            print(f"Skipping file with unrecognized name: {file_drive['title']}")
            continue
        
        # удаляем если файл старше 7 дней
        if file_date < cutoff_date:
            file_drive.Delete()
            print(f"Deleted old backup: {file_drive['title']}")

    
if __name__ == "__main__":
    dump_file = dump_postgres()
    
    try:
        drive = authenticate_drive()
        upload_to_drive(drive, dump_file)
        cleanup_old_backups(drive, GOOGLE_DRIVE_FOLDER_ID, keep_days=7)
    except Exception as e:
        print(f"Upload failed: {e}")
    finally:
        if dump_file.exists():
            dump_file.unlink()
            print(f"Deleted local backup: {dump_file}")
    
# Текущий дамп базы данных сохраняет исключительно собранные данные
# Все параметры базы данных задаются при помощи моделей связанного с базой приложения
# Для восстановления текущего типа дампа базы данных необходимо ввести команду
# pg_restore -h localhost -U postgres -d test_orders_bot_db backups/backup_2025-09-17.dump
# предварительно нужно убедиться в том, что таблицы созданы в базе данных и пусты
# Если таблицы не пусты к ним всем нужно применить команду TRUNCATE
