import subprocess
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import date


load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")


Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


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
        "--data-only",
        "-f", str(today),
        DB_NAME
    ]
    
    
    subprocess.run(command, env=env, check=True)
    print(f"Database dumped to {today}")
    
    
if __name__ == "__main__":
    dump_postgres()