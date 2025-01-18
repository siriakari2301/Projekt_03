NOTE:
Skript volby_okresy.py sám o sobě neimportuje data při uživatelské volbě "14 Zahraničí",
ale spolu se skriptem Zahranici.py tento nedostatek sanují. Při volbě 14 je v hlavním skriptu (volby_okresy.py)
volán skript Zahranici.py. Oba skripty byly vyvíjeny odděleně a mají proto poněkud odlišný design procesu. Výsledek
je ale identický.

SEZNAM KNIHOVEN

1) requests
		Instalace: pip install requests
		Web: https://pypi.org/project/requests/
Popis: Umožňuje snadné a čitelné posílání HTTP požadavků (GET, POST atd.).

2) beautifulsoup4
		Instalace: pip install beautifulsoup4
		Web: https://www.crummy.com/software/BeautifulSoup/bs4/
Popis: Knihovna pro parsování HTML a XML, usnadňuje hledání elementů a tříd ve struktuře HTML.

3) pandas
		Instalace: pip install pandas
		Web: https://pandas.pydata.org/
Popis: Knihovna pro datové analýzy a manipulace s tabulkovými daty.

4) openpyxl
		Instalace: pip install openpyxl
		Web: https://openpyxl.readthedocs.io/en/stable/
Popis: Knihovna pro čtení a zápis souborů typu Excel (.xlsx).

5) Standardní knihovny jazyka Python (není nutné instalovat):
json (práce s JSON)
os (práce se soubory a adresáři)
re (regulární výrazy)
datetime (práce s daty a časy)
