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

### Pobranie projektu
1. Wejdź na stronę https://github.com/xVictorPx/Project_WebApplication_Yo-Lingo
2. Pobierz projekt jako zip lub sklonuj repozytorium.

### Wymagania wstępne
- Python 3.10+ zainstalowany w systemie.

### Krok po kroku (Windows / PowerShell)

```powershell
# 1. Wejdź do katalogu projektu
cd Project_WebApplication_Yo-Lingo

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
cd Project_WebApplication_Yo-Lingo
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


## 8. Widoki w aplikacji

### 1. Strona główna — katalog kursów (/)
Publiczna strona startowa z dużym logo, hero sekcją i statystykami platformy. Wyszukiwarka z filtrami: po nazwie, języku (8 języków) i poziomie CEFR (A1–C2). Każda karta kursu prezentuje flagę języka, poziom, opis, lektora, liczbę lekcji i cenę.

<img width="1895" height="847" alt="image" src="https://github.com/user-attachments/assets/47c0acd6-9784-46a5-8022-292e206cd393" />
<img width="1904" height="914" alt="image" src="https://github.com/user-attachments/assets/5085af9a-f73c-4b8b-aa0b-daa63943cddf" />
<img width="1905" height="914" alt="image" src="https://github.com/user-attachments/assets/83eb46b5-a041-4d69-bd3f-2cb446a0ee56" />



### 2. Logowanie i rejestracja (/login)
Scentralizowany panel autoryzacji. Formularz logowania (e-mail + hasło), rejestracja nowego konta z wyborem roli (Słuchacz / Lektor), powtórzeniem hasła i walidacją po stronie serwera, oraz formularz resetu hasła. Hasła haszowane algorytmem scrypt.

<img width="1904" height="914" alt="image" src="https://github.com/user-attachments/assets/aa15cebb-13cf-4107-a42b-7be86f7cea7e" />
<img width="1902" height="861" alt="image" src="https://github.com/user-attachments/assets/7d260a4d-a3f9-445a-8ad1-bdb7115f31d7" />


### 3. Szczegóły kursu (/course/<id>)
Publiczny widok kursu przed zapisem (UC-15). Sekcja główna z opisem, programem nauczania (listą lekcji bez materiałów) oraz sticky-karta zakupowa z ceną, lektorem, liczbą lekcji i CTA — w zależności od roli: „Zapisz się i zapłać", „Zaloguj się", lub „Przejdź do lekcji" (gdy już zapisany).

<img width="1918" height="913" alt="image" src="https://github.com/user-attachments/assets/2e71f559-ada3-4f7b-b4a3-7ec4a286aca4" />



### 4. Bramka płatności (/course/checkout/<id>)
Krok 2 procesu zakupu (UC-6). Wybór metody płatności (BLIK / Karta / Przelew) z dynamicznym formularzem, kod BLIK 6-cyfrowy lub dane karty, akceptacja regulaminu, podsumowanie zamówienia z rozbiciem VAT 23%. Walidacja danych płatności po stronie serwera przed zaksięgowaniem.

<img width="1919" height="915" alt="image" src="https://github.com/user-attachments/assets/bb307235-e34f-475d-b9b9-8d2f5f9a26d4" />

### 5. Panel słuchacza (/student/dashboard)
Pulpit ucznia z listą opłaconych kursów (pasek postępu, dane lektora), przyciskami „Przejdź do lekcji" i „Anuluj zapis", oraz wewnętrzny komunikator z lektorami (skrzynka z badge'em „Nowa" dla nieprzeczytanych wiadomości, formularz wysyłki).

<img width="1904" height="913" alt="image" src="https://github.com/user-attachments/assets/52550486-feb0-4da9-9c67-2b2d789e7a6f" />


### 6. Panel lektora (/teacher/dashboard)
Pulpit dydaktyczny z 4 kafelkami statystyk (liczba kursów, zapisani słuchacze, łączny przychód, wiadomości), formularzem tworzenia nowego kursu, oraz listą własnych kursów z akcjami: edytuj, zakończ/aktywuj, usuń, podgląd lekcji. Skrzynka odbiorcza komunikatora po prawej.

<img width="1902" height="914" alt="image" src="https://github.com/user-attachments/assets/9d051fc5-e927-4bbf-aa46-93cb5625c872" />


### 7. Widok lekcji w trybie edycji (/course/<id>/lessons jako lektor)
Program kursu z rozwijaną listą lekcji. Dla właściciela: formularz dodawania nowej lekcji, edycja tytułu / opisu / kolejności każdej lekcji, dodawanie i usuwanie materiałów (PDF / wideo / link) oraz usunięcie całej lekcji. Tryb edycji oznaczony fioletowym badgem.

<img width="1905" height="917" alt="image" src="https://github.com/user-attachments/assets/f2aed164-b380-4fde-9397-cb6f984dc7e4" />


### 8. Widok lekcji dla ucznia (/course/<id>/lessons jako student)
Ten sam ekran w trybie read-only: lista lekcji z opisami i klikalne karty materiałów (otwierają się w nowej karcie). Dostępny tylko po zapisaniu się na kurs — autoryzacja sprawdzana po stronie serwera.

<img width="1917" height="914" alt="image" src="https://github.com/user-attachments/assets/6cfa0608-a8aa-473b-bc9c-aa121a31e074" />


### 9. Panel administratora (/admin/dashboard)
Konsola administratorska z 4 kafelkami statystyk finansowych (łączny przychód, transakcje, użytkownicy, aktywne kursy), tabelą zarządzania użytkownikami (blokowanie / odblokowanie) i listą kursów z możliwością usunięcia.

<img width="1902" height="914" alt="image" src="https://github.com/user-attachments/assets/4ef43a6d-1327-4adb-b890-bf8412799c42" />
<img width="1902" height="914" alt="image" src="https://github.com/user-attachments/assets/49aede11-3e6d-4c3f-93e1-75e22006e9f1" />


### 10. Mój profil (/profile)
Edycja danych konta dla każdej roli (UC-12). Dwa formularze: aktualizacja imienia / nazwiska / e-maila oraz zmiana hasła z weryfikacją obecnego. Walidacja unikalności e-maila i siły hasła po stronie serwera.

<img width="1919" height="914" alt="image" src="https://github.com/user-attachments/assets/c3a528d5-571f-473d-970a-3cd3814fc851" />

