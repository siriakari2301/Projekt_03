# Nápověda k funkcím

Tento dokument obsahuje podrobnější nápovědu k funkcím, které jsou definovány ve skriptu `Projekt_03_20250117.py`.

---

## `ziskej_plnou_url(zakladni_url, relativni_url)`
**Popis:**  
Slouží k připojení relativní URL adresy k základní adrese. Využívá funkci `requests.compat.urljoin`.

**Parametry:**  
- `zakladni_url` (str): Základní URL adresa.  
- `relativni_url` (str): Relativní odkaz (např. získaný z atributu `href`).

**Návratová hodnota:**  
- (str) Plná URL adresa.

---

## `nacti_okresni_mesta()`
**Popis:**  
Načte z hlavní stránky přehled krajů a v nich vyhledá tzv. okresní města (resp. odkazy směřující na seznam obcí).

**Parametry:**  
- *(Žádné parametry)*

**Návratová hodnota:**  
- (list) Seznam slovníků. Každý slovník obsahuje klíče `cislo` (int), `nazev` (str) a `odkaz` (str).

---

## `nacti_obce(okres_odkaz)`
**Popis:**  
Načte seznam obcí pro vybraný okres (okresní město).

**Parametry:**  
- `okres_odkaz` (str): URL adresa pro seznam obcí v daném okrese.

**Návratová hodnota:**  
- (list) Seznam slovníků, obsahuje klíče `cislo`, `obec` a `odkaz`.

---

## `nacti_data_obce(obec)`
**Popis:**  
Načte detailní data pro jednu obec (počet voličů, hlasů, jednotlivé strany a jejich výsledky).

**Parametry:**  
- `obec` (dict): Slovník s klíči `cislo`, `obec`, `odkaz`.  

**Návratová hodnota:**  
- (dict) Klíče:  
  - `"Číslo obce"`  
  - `"Název obce"`  
  - `"Voliči celkem"`  
  - `"Odevzdané obálky"`  
  - `"Platné hlasy"`  
  - plus název každé strany (jako klíč) a její počet hlasů (jako hodnota).

---

## `main()`
**Popis:**  
Hlavní funkce skriptu, zajišťuje interakci s uživatelem, spouští ostatní funkce, ukládá výstup do Excelu a odstraňuje dočasné soubory.

**Parametry:**  
- *(Žádné parametry přímo, ale využívá globální proměnné a volá jiné funkce.)*

**Návratová hodnota:**  
- *(Žádná, funkce přímo vypisuje a ukládá soubory.)*
