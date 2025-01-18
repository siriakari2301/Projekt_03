#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ENGETO - Analytik s Pythonem 17.10.2024
Michal Dvořák, dvmichal@gmail.com
Skript Zahranici.py slouží k doplňujícímu zpracování volebních dat
ze zahraničních okrsků. Stahuje data z předem určených URL adres,
parsuje je z HTML tabulek a výsledky ukládá do Excel souboru.
Dočasné soubory (JSON) se po dokončení zpracování mažou.
"""

import requests               # Knihovna pro HTTP požadavky
from bs4 import BeautifulSoup # Knihovna pro parsování HTML
import json                   # Práce s JSON (vestavěná v Pythonu)
import os                     # Práce se soubory a operačním systémem (vestavěná v Pythonu)
import pandas as pd           # Práce s tabulkovými daty
from datetime import datetime # Práce s datem a časem
from pathlib import Path      # Bezpečnější manipulace s cestami k souborům

def nacti_tabulku_1(url):
    """
    Načte (extrahuje) data z "Tabulky 1" pro zahraniční okrsky.

    Parametry:
        url (str): URL adresa, na které se nachází cílová tabulka.

    Návratová hodnota:
        list: Seznam slovníků, kde každý slovník reprezentuje jeden řádek tabulky.
              Klíče zahrnují 'Kontinent', 'Země', 'Město', 'Okrsek' a 'Odkaz'.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Pokud dojde k chybě HTTP, vyvolá výjimku
        soup = BeautifulSoup(response.text, 'html.parser')

        # Najdeme tabulku s class="table"
        table = soup.find('table', class_='table')
        if not table:
            print("Tabulka 1 nenalezena.")
            return []

        data = []
        aktualni_kontinent = None
        aktualni_zeme = None

        # Přeskočíme hlavičkový řádek tabulky (index 0)
        radky = table.find_all('tr')[1:]
        print("Extrahuji data z Tabulky 1:")

        # Procházíme každý řádek tabulky a podle počtu sloupců doplňujeme chybějící údaje
        for i, radek in enumerate(radky, start=1):
            sloupce = radek.find_all('td')

            # Pokud je v řádku 4 sloupce => Kontinent, Země, Město, Okrsek
            if len(sloupce) == 4:
                aktualni_kontinent = sloupce[0].get_text(strip=True) or aktualni_kontinent
                aktualni_zeme = sloupce[1].get_text(strip=True) or aktualni_zeme
                mesto = sloupce[2].get_text(strip=True)
                okrsek = sloupce[3].get_text(strip=True)

                # Pokud je v posledním sloupci odkaz, získáme ho
                odkaz_tag = sloupce[3].find('a')
                odkaz = odkaz_tag['href'] if odkaz_tag else None

                zaznam = {
                    "Kontinent": aktualni_kontinent,
                    "Země": aktualni_zeme,
                    "Město": mesto,
                    "Okrsek": okrsek,
                    "Odkaz": odkaz
                }
                data.append(zaznam)

                print(f"{i}. {aktualni_kontinent} | {aktualni_zeme} | {mesto} | (Zpracovávám data)")

            # Pokud je 3 sloupce => Chybí kontinent (sloupec 0 bude Země)
            elif len(sloupce) == 3:
                aktualni_zeme = sloupce[0].get_text(strip=True) or aktualni_zeme
                mesto = sloupce[1].get_text(strip=True)
                okrsek = sloupce[2].get_text(strip=True)

                odkaz_tag = sloupce[2].find('a')
                odkaz = odkaz_tag['href'] if odkaz_tag else None

                zaznam = {
                    "Kontinent": aktualni_kontinent,
                    "Země": aktualni_zeme,
                    "Město": mesto,
                    "Okrsek": okrsek,
                    "Odkaz": odkaz
                }
                data.append(zaznam)

                print(f"{i}. {aktualni_kontinent} | {aktualni_zeme} | {mesto} | (Zpracovávám data)")

            # Pokud jsou pouze 2 sloupce => Chybí kontinent i země (první sloupec = Město)
            elif len(sloupce) == 2:
                mesto = sloupce[0].get_text(strip=True)
                okrsek = sloupce[1].get_text(strip=True)

                odkaz_tag = sloupce[1].find('a')
                odkaz = odkaz_tag['href'] if odkaz_tag else None

                zaznam = {
                    "Kontinent": aktualni_kontinent,
                    "Země": aktualni_zeme,
                    "Město": mesto,
                    "Okrsek": okrsek,
                    "Odkaz": odkaz
                }
                data.append(zaznam)

                print(f"{i}. {aktualni_kontinent} | {aktualni_zeme} | {mesto} | (Zpracovávám data)")

        print(f"Celkový počet extrahovaných řádků: {len(data)}")
        return data

    except requests.RequestException as e:
        print(f"Chyba při načítání dat z Tabulky 1: {e}")
        return []


def nacti_data_z_odkazu(zakladni_url, relativni_odkaz):
    """
    Načte detailní data ze zadaného odkazu (relativní cesta),
    který obsahuje další tabulky se stranami a jejich hlasy.

    Parametry:
        zakladni_url (str): Základní URL (např. https://www.volby.cz/pls/ps2017nss/)
        relativni_odkaz (str): Relativní odkaz, např. 'xyz?'
    
    Návratová hodnota:
        dict: Obsahuje 2 klíče:
              - "table_1": list slovníků extrahovaných z 1. tabulky
              - "table_2_3": slovník {název_strany: počet_hlasů}
              nebo None, pokud není možné data načíst.
    """
    try:
        response = requests.get(zakladni_url + relativni_odkaz, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Najdeme všechny tabulky s class="table"
        tabulky = soup.find_all('table', class_='table')

        # Očekáváme alespoň 3 tabulky
        if len(tabulky) < 3:
            print(f"Není dostatek tabulek na stránce {relativni_odkaz}. Očekávám alespoň 3.")
            return None

        # 1) Extrahování dat z první tabulky
        table_1 = tabulky[0]
        hlavicky = [
            " ".join(th.stripped_strings) for th in table_1.find_all('th')
        ]
        radky = table_1.find_all('tr')[1:]  # Přeskočíme hlavičkový řádek
        table_1_data = []
        for radek in radky:
            sloupce = radek.find_all('td')
            zaznam = {}
            for i, td in enumerate(sloupce):
                zaznam[hlavicky[i]] = td.get_text(strip=True)
            table_1_data.append(zaznam)

        # 2) Extrahování dat z druhé a třetí tabulky (strany a hlasy)
        #    Budeme je ukládat do jednoho slovníku
        table_2_3_data = {}
        for tabulka in tabulky[1:3]:
            radky_stran = tabulka.find_all('tr')[1:]  # Přeskočíme hlavičkový řádek
            for radek in radky_stran:
                sloupce = radek.find_all('td')
                if len(sloupce) >= 3:
                    strana = sloupce[1].get_text(strip=True)
                    hlasy = sloupce[2].get_text(strip=True)

                    # Pokud je text v hlasy opravdu číslo, sčítáme
                    if hlasy.isdigit():
                        hlasy_int = int(hlasy)
                        if strana not in table_2_3_data:
                            table_2_3_data[strana] = 0
                        table_2_3_data[strana] += hlasy_int

        return {
            "table_1": table_1_data,
            "table_2_3": table_2_3_data
        }

    except requests.RequestException as e:
        print(f"Chyba při načítání dat z odkazu {relativni_odkaz}: {e}")
        return None


def uloz_do_excelu(data):
    """
    Uloží předaná data do Excel souboru.

    Parametry:
        data (list): Seznam slovníků, které se uloží do Excelu (každý slovník = jeden řádek).
    """
    try:
        # Vytvoříme název souboru s časovou značkou
        casove_razitko = datetime.now().strftime("%Y%m%d_%H%M")
        # Sestavíme cestu k výstupnímu souboru na základě umístění skriptu
        vystupni_slozka = Path(__file__).parent
        vystupni_soubor = vystupni_slozka / f"Vysledek_{casove_razitko}.xlsx"

        df = pd.DataFrame(data)
        df.to_excel(vystupni_soubor, index=False)

        print(f"Data úspěšně uložena do {vystupni_soubor}")

    except Exception as e:
        print(f"Chyba při ukládání dat do Excelu: {e}")


def uloz_do_json(data, json_soubor):
    """
    Uloží předaná data do JSON souboru.

    Parametry:
        data (list nebo dict): Data, která chceme uložit.
        json_soubor (str nebo Path): Cesta k souboru, kam se data uloží.
    """
    try:
        with open(json_soubor, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data úspěšně uložena do {json_soubor}")
    except Exception as e:
        print(f"Chyba při ukládání dat do JSON: {e}")


def vymaz_json(json_soubor):
    """
    Odstraní dočasný JSON soubor, pokud existuje.

    Parametry:
        json_soubor (str nebo Path): Cesta k JSON souboru, který chceme smazat.
    """
    try:
        if os.path.exists(json_soubor):
            os.remove(json_soubor)
            print(f"Dočasný JSON soubor {json_soubor} byl vymazán.")
    except Exception as e:
        print(f"Chyba při mazání JSON souboru: {e}")


def main():
    """
    Hlavní funkce skriptu:
     1. Načte data z "Tabulky 1" (kontinenty, země, města, odkazy).
     2. Uloží je do JSON (dočasného) souboru.
     3. Pro každý záznam v Tabulce 1 stáhne a zpracuje detailní data (tabulky se stranami a hlasy).
     4. Vše spojí do jednoho seznamu slovníků a uloží do Excel souboru.
     5. Smaže dočasný JSON soubor.
    """
    # Základní URL adresa
    zakladni_url = "https://www.volby.cz/pls/ps2017nss/"
    # URL s tabulkou, kterou chceme načíst (Tabulka 1)
    tabulka_1_url = zakladni_url + "ps36?xjazyk=CZ"

    # Sestavíme cestu pro dočasný JSON soubor (uloží se do složky, kde je skript)
    json_soubor = Path(__file__).parent / "election_data.json"

    # 1) Načítání dat z Tabulky 1
    print("Extrahování dat z Tabulky 1...")
    tabulka_1_data = nacti_tabulku_1(tabulka_1_url)

    # 2) Uložit extrahovaná data do JSON
    print("Ukládání extrahovaných dat do JSON...")
    uloz_do_json(tabulka_1_data, json_soubor)

    # 3) Iterovat přes záznamy z tabulky a získat detailní data pro každé město/okrsek
    print("Extrahování dat z odkazovaných stránek...")
    podrobna_data = []
    vsechny_strany = set()

    for zaznam in tabulka_1_data:
        # Každý záznam obsahuje 'Odkaz', který vede na detail
        link_data = nacti_data_z_odkazu(zakladni_url, zaznam['Odkaz'])
        if link_data:
            detailni_zaznam = {
                "Kontinent": zaznam['Kontinent'],
                "Země": zaznam['Země'],
                "Město": zaznam['Město'],
            }

            # Přidání obsahu z "table_1"
            for polozka in link_data.get("table_1", []):
                detailni_zaznam.update(polozka)

            # Přidání (sloučení) dynamických dat o stranách z "table_2_3"
            for strana, hlasy in link_data["table_2_3"].items():
                vsechny_strany.add(strana)
                detailni_zaznam[strana] = hlasy

            podrobna_data.append(detailni_zaznam)

    # Ujistíme se, že pro každou stranu existuje sloupec i u ostatních záznamů
    vsechny_strany = list(vsechny_strany)
    for zaznam in podrobna_data:
        for strana in vsechny_strany:
            if strana not in zaznam:
                zaznam[strana] = 0

    # 4) Uložit detailní data do Excelu
    print("Ukládání podrobných dat do Excelu...")
    uloz_do_excelu(podrobna_data)

    # 5) Vymazat dočasný JSON soubor
    print("Vymazání dočasného JSON souboru...")
    vymaz_json(json_soubor)


if __name__ == "__main__":
    main()
