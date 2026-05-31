# Yo-Lingo Platform – Platforma E-learningowa do Nauki Języków

**Zespół:** Alicja Radłowska, Wiktor Patajewicz
**Technologia:** Python 3 · Flask · SQLite · Jinja2 · HTML/CSS

---

## 1. Opis aplikacji

**Yo-Lingo** to webowa platforma e-learningowa do nauki języków obcych. Aplikacja
obsługuje trzy role użytkowników, z których każda ma dedykowany panel:

- **Słuchacz (STUDENT)** – przegląda i wyszukuje kursy, zapisuje się na nie poprzez
  symulowaną bramkę płatności (BLIK), śledzi swoje kursy i komunikuje się z lektorem.
- **Lektor (TEACHER)** – tworzy autorskie kursy, dodaje materiały dydaktyczne
  (PDF/wideo/link) do lekcji, odpowiada na wiadomości słuchaczy.
- **Administrator (ADMIN)** – zarządza użytkownikami (blokowanie/odblokowanie),
  usuwa kursy, przegląda statystyki finansowe platformy.

## 2. Wykorzystane technologie

| Warstwa | Technologia |
|---|---|
| Backend / logika | Python 3, Flask 3 |
| Baza danych | SQLite 3 (7 tabel relacyjnych) |
| Szablony / widoki | Jinja2 (autoescaping → ochrona przed XSS) |
| Interfejs | HTML5 + CSS3 (Google Fonts: Space Grotesk, Bebas Neue) |
| Bezpieczeństwo | `werkzeug.security` – haszowanie haseł (scrypt) |

## 3. Mechanizmy bezpieczeństwa

- **Haszowanie haseł** algorytmem scrypt (`generate_password_hash` / `check_password_hash`) –
  hasła nigdy nie są przechowywane jawnie.
- **Zapytania parametryzowane** (placeholdery `?`) w całej aplikacji – ochrona przed SQL Injection.
- **Walidacja danych po stronie serwera** (format e-mail, długość hasła ≥ 6 znaków,
  poprawność roli/poziomu/ceny).
- **Kontrola ról i autoryzacja obiektowa** – każdy panel sprawdza rolę z sesji; lektor może
  dodać materiał tylko do lekcji we własnym kursie.
- **Egzekwowanie kluczy obcych** (`PRAGMA foreign_keys = ON`) – spójność danych przy usuwaniu.
- **Klucz sesji** pobierany ze zmiennej środowiskowej, tryb debug wyłączony domyślnie.

## 4. Struktura katalogów

```
projekt/
│
├── app.py             # Serwer Flask – cała logika aplikacji (routing, walidacja, DB)
├── schema.sql         # Skrypt tworzący strukturę bazy (7 tabel)
├── requirements.txt   # Lista zależności Pythona
├── .gitignore         # Pliki ignorowane przez git (venv, baza, cache)
├── yo_lingo.db        # Plik bazy SQLite (generowany automatycznie przy 1. starcie)
├── css/
│   ├── style.css      # Globalny arkusz stylów
│   └── logo.svg       # Logo aplikacji
└── templates/
    ├── index.html     # Strona główna – wyszukiwarka i lista kursów
    ├── login.html     # Logowanie, rejestracja, reset hasła
    ├── student.html   # Panel słuchacza
    ├── teacher.html   # Panel lektora
    └── admin.html     # Panel administratora
```

## 5. Instalacja i uruchomienie

### Wymagania wstępne
- Python 3.10+ zainstalowany w systemie.

### Krok po kroku (Windows / PowerShell)

```powershell
# 1. Wejdź do katalogu projektu
cd yo_lingo_projekt

# 2. Utwórz i aktywuj środowisko wirtualne
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Uruchom aplikację (baza utworzy się automatycznie wraz z danymi startowymi)
python app.py
```

### Linux / macOS

```bash
cd yo_lingo_projekt
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Po uruchomieniu aplikacja jest dostępna pod adresem: **http://127.0.0.1:5000**

> Aby uruchomić w trybie deweloperskim (auto-reload, debugger), ustaw zmienną
> środowiskową `FLASK_DEBUG=1` przed startem.

## 6. Konta testowe (dane startowe)

Przy pierwszym uruchomieniu baza zostaje zasilona kontami demonstracyjnymi.
Hasło dla wszystkich kont: **`password`**

| Rola | E-mail |
|---|---|
| Administrator | `admin@yo-lingo.pl` |
| Lektor | `marta.nowak@lektor.pl` |
| Słuchacz | `jan.kowalski@student.pl` |

## 7. Operacje na danych (CRUD)

- **Create:** rejestracja użytkownika, dodawanie kursów, materiałów, zapisy na kurs, wiadomości.
- **Read:** logowanie, lista i filtrowanie kursów, panele ról, statystyki.
- **Update:** zmiana statusu użytkownika (blokada/odblokowanie) przez admina.
- **Delete:** usuwanie kursu przez admina (z kaskadowym usunięciem powiązań).
