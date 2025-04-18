import os
import re
import sqlite3
import csv
import sys
import requests

# A NE TOUCHER EN AUCUN CAS CE PATTERN REGEX, IL MARCHE, C'EST TOUT CE QUI COMPTE (M'A PRIS DES HEURES)
PATTERN = r"^([^*]*)(?:\*)([^\/]*)(?:\/)\s*(\d{1})(\d{8})([\dA-Z]{0,5})\s*([A-Z\- '0-9,.°\(\)\/]{1,30})\s*(\D+\s*)?(\d{8})([\dA-Z]{5}|\s*)(.*)\s*$"

def create_deaths_table(db_path):
    """
    Crée une table 'deces' dans la base de données SQLite si elle n'existe pas.

    ARGUMENTS
        db_path: (str), chemin vers la base de données SQLite.
    """
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()

        # Si doutes concernant le type des données, n'en ayez aucun, tout est fait pour marcher dans tous
        # les cas qu'on risque de rencontrer
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deces (
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            sexe CHAR(1) CHECK (sexe IN ('H', 'F')),
            date_naissance TEXT NOT NULL,
            code_lieu_naissance TEXT NOT NULL,
            commune_naissance TEXT NOT NULL,
            pays_naissance TEXT NOT NULL,
            date_deces TEXT NOT NULL,
            code_lieu_deces TEXT NOT NULL,
            numero_acte TEXT NOT NULL,
            annee_deces TEXT NOT NULL
        )
        """)
    except Exception as e:
        print(e)
    finally:
        connection.commit()
        connection.close()

def gen_deces_csv(input_path, output_path):
    """
    Génère un fichier CSV à partir d'un fichier texte contenant des données de décès.

    ARGUMENTS
        input_path: (str), chemin vers le fichier texte source.
        output_path: (str), chemin vers le fichier CSV généré.
    """
    with open(output_path, "w", newline='' ,encoding="UTF-8") as csvfile:

        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["nom", "prenom", "sexe", "date_naissance", "code_lieu_naissance", "commune_naissance", "pays_naissance", "date_deces", "code_lieu_deces", "numero_acte", "annee_deces"])


        with open(input_path, "r", encoding="UTF-8") as f:

            for line in f:

                match = re.match(PATTERN, line)

                # Vérifie si la ligne correspond au pattern regex
                if match:

                    last = match.group(1)
                    first = match.group(2)
                    sex = "F" if int(match.group(3)) == 2 else "H"
                    birth_date = match.group(4)
                    birth_place_code = match.group(5)
                    birth_place_name = match.group(6).strip()
                    birth_country = match.group(7).strip() if match.group(7) else ""
                    death_date = match.group(8)
                    death_place_code = match.group(9)
                    death_certificate_num = match.group(10).strip()
                    death_year = death_date[0:4] if death_date[0:4] != "0000" else "2024"

                    csv_writer.writerow([last, first, sex, birth_date, birth_place_code, birth_place_name, birth_country, death_date, death_place_code, death_certificate_num, death_year])

def import_csv_to_db(db_path, input_file):
    """
    Importe les données d'un fichier CSV dans la table 'deces' de la base de données.

    ARGUMENTS
        db_path: (str), chemin vers la base de données SQLite.
        input_file: (str), chemin vers le fichier CSV contenant les données.
    """
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()

        with open(input_file, mode='r', encoding="UTF-8") as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Ignore la première ligne (en-têtes)

            for row in csv_reader:
                cursor.execute("""
                    INSERT INTO deces (nom, prenom, sexe, date_naissance, code_lieu_naissance, commune_naissance, pays_naissance, date_deces, code_lieu_deces, numero_acte, annee_deces)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, row)
    except Exception as e:
        print(e)
    finally:
        connection.commit()
        connection.close()

def import_deaths_to_sql(db_path, data_dir, file_urls, first_year):
    """
    Télécharge des fichiers texte contenant des données de décès, les convertit en CSV,
    puis les importe dans la base de données SQLite.

    ARGUMENTS
        db_path: (str), chemin vers la base de données SQLite.
        data_dir: (str), répertoire où les fichiers seront temporairement stockés.
        file_urls: (list), liste des URLs des fichiers texte à télécharger.
        first_year: (int), première année correspondant aux fichiers à importer.

    RETOURNE
        (bool): False en cas d'erreur, sinon rien.
    """
    create_deaths_table(db_path)
    for i, url in enumerate(file_urls):
        try:
            response = requests.get(url)
            response.raise_for_status()
            txt_path = os.path.join(data_dir, f"deces-{int(first_year)+i}.txt")
            csv_path = os.path.join(data_dir, f"deces-{int(first_year)+i}.csv")
            with open(txt_path, "wb") as f:
                f.write(response.content)
            if os.path.exists(txt_path):
                gen_deces_csv(txt_path, csv_path)
                import_csv_to_db(db_path, csv_path)
                os.remove(txt_path)
                os.remove(csv_path)
            else:
                sys.stderr.write(f"Err: Le fichier {txt_path} n'a pas été trouvé")
                return False

        except requests.exceptions.RequestException as e:
            sys.stderr.write(f"Err. lors du téléchargement du fichier txt des decès de l'année {first_year+i}: {e}")
            return False


