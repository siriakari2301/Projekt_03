#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ENGETO - Projekt 3 - Datový analytik s pthonem 17/10/2024
Michal Dvořák, dvmichal@gmail.com
Tento skript slouží k načítání volebních výsledků z webu https://www.volby.cz
pro zvolený "okres" (resp. okresní město), následně tato data uloží do dočasného
JSON souboru a potom uloží konečný výsledek do Excelu. Dočasný JSON soubor se
po skončení zpracování automaticky smaže.
Pro podrobnou nápovědu k jednotlivým funkcím viz 'napoveda.md'.
"""

import requests       # Knihovna pro HTTP požadavky
from bs4 import BeautifulSoup   # Knihovna pro parsování HTML
import json           # Knihovna pro práci s formátem JSON (vestavěná v Pythonu)
import os             # Práce se soubory a operačním systémem (vestavěná v Pythonu)
from datetime import datetime  # Práce s datem a časem (vestavěná v Pythonu)
import pandas as pd   # Knihovna pro tabulková data
import re             # Regulární výrazy (vestavěná v Pythonu)
import subprocess     # Knihovna pro volání externích procesů (využijeme k volání Zahranici.py)

# Základní URL adresa pro volby
ZAKLADNI_URL = "https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ"


def ziskej_plnou_url(zakladni_url, relativni_url):
    """
    Převede relativní URL na plnou URL.

    Parametry:
        zakladni_url (str): Základní URL, ke které se relativní odkaz připojí.
        relativni_url (str): Relativní část URL, získaná např. z atributu 'href'.

    Návratová hodnota:
        str: Plná (absolutní) URL adresa.
    """
    return requests.compat.urljoin(zakladni_url, relativni_url)


def nacti_okresni_mesta():
    """
    Načte z hlavní stránky seznam tzv. 'krajů' a v nich vyhledá okresní města
    (resp. odkazy na detailní výpis obcí v daném okrese).

    Vrací:
        list: Seznam slovníků s klíči:
            - 'cislo': Pořadové číslo (int)
            - 'nazev': Název okresního města (str)
            - 'odkaz': Plná URL adresa vedoucí k detailu okresu (str)
    """
    response = requests.get(ZAKLADNI_URL)
    response.raise_for_status()  # Pokud dojde k chybě, vyvolá výjimku
    soup = BeautifulSoup(response.text, "html.parser")

    # Vyhledáme všechny elementy <h3> s class="kraj", což označuje kraje
    kraje = soup.find_all("h3", class_="kraj")
    okresni_mesta = []
    global_pocitadlo = 1

    # Pro každý kraj vyhledáme tabulku s okresními městy
    for kraj in kraje:
        print(f"\nKraj: {kraj.text.strip()}")
        tabulka = kraj.find_next("table", class_="table")
        if not tabulka:
            continue

        # Projdeme všechny řádky tabulky a hledáme data pro okresní města
        for radek in tabulka.find_all("tr"):
            # Pomocí regulárních výrazů najdeme požadované buňky
            obec_bunka = radek.find(
                "td",
                headers=re.compile(r"t[1-9][0-4]?sa1 t[1-9][0-4]?sb2")
            )
            odkaz_bunka = radek.find(
                "td",
                headers=re.compile(r"t[1-9][0-4]?sa3")
            )
            if obec_bunka and odkaz_bunka:
                nazev_obce = obec_bunka.text.strip()
                link = odkaz_bunka.find("a")["href"]
                okresni_mesta.append({
                    "cislo": global_pocitadlo,
                    "nazev": nazev_obce,
                    "odkaz": ziskej_plnou_url(ZAKLADNI_URL, link)
                })
                print(f"{global_pocitadlo}. {nazev_obce}")
                global_pocitadlo += 1

    return okresni_mesta


def nacti_obce(okres_odkaz):
    """
    Načte seznam všech obcí pro vybraný okres (okresní město).

    Parametry:
        okres_odkaz (str): URL adresa vedoucí na stránku s výpisem obcí v okrese.

    Vrací:
        list: Seznam slovníků s klíči:
            - 'cislo': Číslo obce (str)
            - 'obec': Název obce (str)
            - 'odkaz': Plná URL adresa k detailu obce (str)
    """
    response = requests.get(okres_odkaz)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    obce = []
    radky = soup.find_all('tr')
    for radek in radky:
        cislo_td = radek.find('td', class_='cislo')
        nazev_td = radek.find('td', class_='overflow_name')
        if cislo_td and nazev_td:
            link_tag = cislo_td.find('a')
            link = link_tag['href'] if link_tag else None
            if link:
                obce.append({
                    "cislo": cislo_td.text.strip(),
                    "obec": nazev_td.text.strip(),
                    "odkaz": ziskej_plnou_url(ZAKLADNI_URL, link)
                })

    return obce


def nacti_data_obce(obec):
    """
    Načte detailní volební data pro jednu konkrétní obec.

    Parametry:
        obec (dict): Slovník obsahující klíče 'cislo', 'obec', 'odkaz'.

    Vrací:
        dict: Slovník s detailními údaji o obci, včetně celkových statistik
              (např. počet voličů, odevzdaných obálek, platných hlasů) a
              hlasů pro jednotlivé strany.
    """
    url = obec["odkaz"]
    print(f"Zpracovávám obec: {obec['cislo']} - {obec['obec']}")

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    tabulky = soup.find_all('table', class_='table')

    # Připravíme základní strukturu vraceného slovníku
    data = {
        "Číslo obce": obec["cislo"],
        "Název obce": obec["obec"]
    }

    # 1. tabulka obsahuje celkové statistiky: voliči celkem, obálky, platné hlasy
    if tabulky:
        radky = tabulky[0].find_all('tr')
        if radky:
            posledni_radek = radky[-1]
            bunky = posledni_radek.find_all('td')
            # Očekáváme aspoň 8 sloupců
            if len(bunky) >= 8:
                data["Voliči celkem"] = bunky[3].get_text(strip=True)
                data["Odevzdané obálky"] = bunky[6].get_text(strip=True)
                data["Platné hlasy"] = bunky[7].get_text(strip=True)

    # Ostatní tabulky (2. a dál) obsahují výsledky pro jednotlivé strany
    for tabulka in tabulky[1:]:
        radky_stran = tabulka.find_all('tr')[1:]  # Přeskočíme hlavičkový řádek
        for radek in radky_stran:
            bunky = radek.find_all(['th', 'td'])
            if len(bunky) >= 3:
                nazev_strany = bunky[1].get_text(strip=True)
                hlasy_strany = bunky[2].get_text(strip=True)
                # Přeskočíme případy, kdy "název_strany" je prázdný nebo "název"
                if nazev_strany.lower() != "název" and nazev_strany.strip():
                    data[nazev_strany] = hlasy_strany

    return data


def main():
    """
    Hlavní spouštěcí funkce.
    1. Načte seznam okresů (okresních měst).
    2. Umožní uživateli vybrat konkrétní okres k analýze.
    3. Načte všechny obce v daném okrese a uloží je do dočasného JSON souboru.
    4. Poté zpracuje detailní data o každé obci a uloží je do Excelu.
    5. Smaže dočasný JSON soubor.
    """

    # Získáme cestu ke složce, odkud je skript spuštěn
    skript_cesta = os.path.dirname(os.path.abspath(__file__))
    # Sestavíme plnou cestu k souboru Zahranici.py
    zahranici_script = os.path.join(skript_cesta, "Zahranici.py")

    # Vygenerujeme časové razítko pro pojmenování souborů
    casove_razitko = datetime.now().strftime("%Y%m%d_%H%M")
    json_soubor = os.path.join(skript_cesta, f"obce_{casove_razitko}.json")
    excel_soubor = os.path.join(skript_cesta, f"vysledky_{casove_razitko}.xlsx")

    # Krok 1: Načtení okresních měst
    print("1. Načítám seznam okresních měst...")
    okresni_mesta = nacti_okresni_mesta()

    # Uživatel vybere pořadové číslo okresu
    try:
        vyber = int(input("\nZadejte číslo okresního města pro zpracování: "))

        # Pokud uživatel zadá číslo 14, spustíme skript Zahranici.py
        if vyber == 14:
            print("Spouštím skript Zahranici.py ...")
            subprocess.run(["python", zahranici_script])
            return  # Ukončíme provádění tohoto skriptu

        vybrany_okres = next(
            (mesto for mesto in okresni_mesta if mesto["cislo"] == vyber),
            None
        )
        if not vybrany_okres:
            print("Neplatný výběr!")
            return
    except ValueError:
        print("Chybný vstup! Zadejte číslo.")
        return

    # Krok 2: Načtení obcí v daném okrese a uložení do dočasného JSON souboru
    print("\n2. Načítám seznam obcí...")
    obce = nacti_obce(vybrany_okres["odkaz"])
    with open(json_soubor, "w", encoding="utf-8") as soubor:
        json.dump(obce, soubor, ensure_ascii=False, indent=4)

    print(f"Načteno {len(obce)} obcí. Data uložena do souboru '{json_soubor}'.")

    # Krok 3: Zpracování detailních dat o každé obci a uložení do Excelu
    print("\n3. Zpracovávám detailní data o obcích...")
    vysledky = []
    for o in obce:
        data_obce = nacti_data_obce(o)
        vysledky.append(data_obce)

    df = pd.DataFrame(vysledky)
    df.to_excel(excel_soubor, index=False, engine='openpyxl')

    print(f"\nVýsledky byly uloženy do souboru: {excel_soubor}")

    # Krok 4: Odstranění dočasného JSON souboru
    os.remove(json_soubor)
    print(f"Dočasný soubor '{json_soubor}' byl smazán.")



if __name__ == "__main__":
    main()
