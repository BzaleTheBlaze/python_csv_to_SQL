import csv
import sqlite3
import sys
import requests
import os

def create_trivia_table(db_path):
    """
    Crée une table 'trivia' dans la base de données SQLite si elle n'existe pas.

    ARGUMENTS
        db_path: (str), chemin vers la base de données SQLite.
    """
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trivia (
                prenom TEXT,
                biographie TEXT,
                origine TEXT,
                funfact TEXT
            )
        """)
    except Exception as e:
        print(e)
    finally:
        connection.commit()
        connection.close()

def import_csv_sql_trivia(db_path, csv_file_path):
    """
    Importe les données d'un fichier CSV dans la table 'trivia' de la base de données.

    ARGUMENTS
        db_path: (str), chemin vers la base de données SQLite.
        csv_file_path: (str), chemin vers le fichier CSV contenant les données.
    """
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        with open(csv_file_path, 'r', encoding='UTF-8') as f:
            csv_read = csv.reader(f, delimiter=',', quotechar='"')
            next(csv_read)  # Ignore la première ligne (en-têtes)
            for ligne in csv_read:
                cursor.execute("""
                    INSERT INTO trivia (prenom, biographie, origine, funfact)
                    VALUES (?, ?, ?, ?)    
                """, (ligne[0], ligne[1], ligne[2], ligne[3]))
    except Exception as e:
        print(e)
    finally:
        connection.commit()
        connection.close()

def import_trivia_to_sql(db_path, data_dir, file_url):
    """
    Télécharge un fichier CSV depuis une URL, l'importe dans la base de données, puis le supprime.

    ARGUMENTS
        db_path: (str), chemin vers la base de données SQLite.
        data_dir: (str), répertoire où le fichier sera temporairement stocké.
        file_url: (str), URL du fichier CSV à télécharger.

    RETOURNE
        (bool): False en cas d'erreur, sinon rien.
    """
    if file_url:
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            trivia_csv_path = os.path.join(data_dir, "prenomsinfo.csv")
            with open(trivia_csv_path, "wb") as f:
                f.write(response.content)
            
            if os.path.exists(trivia_csv_path):
                create_trivia_table(db_path)
                import_csv_sql_trivia(db_path, trivia_csv_path)
                os.remove(trivia_csv_path)
            else:
                sys.stderr.write(f"Err: Le fichier {trivia_csv_path} n'a pas été trouvé")
                return False
        except requests.exceptions.RequestException as e:
            sys.stderr.write(f"Err. lors du téléchargement du fichier trivia prenoms: {e}")
            return False
    else:
        sys.stderr.write("URL pour le fichier trivia prenoms non configurée dans config.ini")
        return False


