import os
import re
import sqlite3
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='css', static_url_path='/css')
# Klucz sesji pobierany ze zmiennej środowiskowej; losowy fallback dla developmentu.
app.secret_key = os.environ.get('YO_LINGO_SECRET_KEY', os.urandom(32).hex())
# Szablony Jinja przeładowywane przy każdej zmianie pliku (bez restartu serwera).
app.config['TEMPLATES_AUTO_RELOAD'] = True
DATABASE = 'yo_lingo.db'

ALLOWED_ROLES = ('STUDENT', 'TEACHER')
CEFR_LEVELS = ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')
MATERIAL_TYPES = ('PDF', 'VIDEO', 'LINK')
EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


# --- WARSTWA DOSTĘPU DO BAZY DANYCH ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # SQLite domyślnie NIE egzekwuje kluczy obcych – włączamy ON DELETE CASCADE.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    if os.path.exists(DATABASE):
        return
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        seed_data(db)
        db.commit()


def seed_data(db):
    demo_hash = generate_password_hash('password')
    db.executemany(
        'INSERT INTO users (first_name, last_name, email, password_hash, role, status) VALUES (?, ?, ?, ?, ?, ?)',
        [
            ('Jan', 'Kowalski', 'jan.kowalski@student.pl', demo_hash, 'STUDENT', 'ACTIVE'),
            ('Marta', 'Nowak', 'marta.nowak@lektor.pl', demo_hash, 'TEACHER', 'ACTIVE'),
            ('Admin', 'Yo-Lingo', 'admin@yo-lingo.pl', demo_hash, 'ADMIN', 'ACTIVE'),
            ('Paolo', 'Rossi', 'paolo.rossi@lektor.pl', demo_hash, 'TEACHER', 'ACTIVE'),
            ('Yuki', 'Tanaka', 'yuki.tanaka@lektor.pl', demo_hash, 'TEACHER', 'ACTIVE'),
        ],
    )

    # Kursy: (title, language, level, description, price, teacher_id, is_active)
    courses = [
        # Hiszpański (Marta Nowak)
        ('Hiszpański od zera do bohatera', 'Spanish', 'A1', 'Kompleksowy kurs podstaw języka hiszpańskiego – wymowa, gramatyka, słownictwo codzienne.', 299.00, 2, 1),
        ('Hiszpański w podróży', 'Spanish', 'A2', 'Praktyczne zwroty na wakacje: hotel, restauracja, transport, zakupy.', 199.00, 2, 1),
        ('Konwersacje hiszpańskie B1', 'Spanish', 'B1', 'Rozwijaj płynność wypowiedzi i pewność siebie w rozmowach.', 349.00, 2, 1),

        # Angielski (Marta Nowak)
        ('Business English Pro', 'English', 'B2', 'Konwersacje i słownictwo biznesowe dla zaawansowanych: negocjacje, prezentacje, e-maile.', 450.00, 2, 1),
        ('English Essentials A2', 'English', 'A2', 'Solidne podstawy gramatyki i słownictwa dla osób z minimalnym kontaktem z językiem.', 249.00, 2, 1),
        ('IELTS Preparation C1', 'English', 'C1', 'Intensywny kurs przygotowujący do egzaminu IELTS Academic – wszystkie cztery sprawności.', 599.00, 2, 1),

        # Niemiecki (Marta Nowak)
        ('Deutsch für Anfänger', 'German', 'A1', 'Wprowadzenie do języka niemieckiego: alfabet, liczby, podstawowe zwroty i czasowniki.', 279.00, 2, 1),
        ('Niemiecki techniczny B1', 'German', 'B1', 'Słownictwo specjalistyczne dla inżynierów i pracowników branży automotive.', 399.00, 2, 1),
        ('Nieaktywny Kurs Testowy', 'German', 'A2', 'Stary kurs przeznaczony do usunięcia przez admina.', 120.00, 2, 0),

        # Włoski (Paolo Rossi)
        ('Italiano per principianti', 'Italian', 'A1', 'Pierwsze kroki we włoskim z native speakerem – wymowa, melodia języka, podstawy.', 289.00, 4, 1),
        ('La Dolce Vita – kultura i język', 'Italian', 'B1', 'Naucz się włoskiego przez kuchnię, kino i muzykę. Konwersacje + reading.', 329.00, 4, 1),

        # Francuski (Paolo Rossi)
        ('Bonjour la France! A1', 'French', 'A1', 'Klasyczny kurs dla początkujących – fonetyka, podstawy gramatyki, zwroty codzienne.', 279.00, 4, 1),
        ('Français des affaires B2', 'French', 'B2', 'Język francuski w biznesie: korespondencja, spotkania, negocjacje handlowe.', 459.00, 4, 1),

        # Portugalski (Paolo Rossi)
        ('Português brasileiro A1', 'Portuguese', 'A1', 'Wariant brazylijski – wymowa karioka, słownictwo z życia codziennego, gramatyka.', 259.00, 4, 1),

        # Japoński (Yuki Tanaka)
        ('Nihongo Start! A1', 'Japanese', 'A1', 'Wprowadzenie do języka japońskiego: hiragana, katakana, pierwsze zdania, etykieta.', 349.00, 5, 1),
        ('Kanji Master A2', 'Japanese', 'A2', 'Systematyczna nauka 300 podstawowych znaków kanji wraz z przykładami zdań.', 399.00, 5, 1),

        # Rosyjski (Yuki Tanaka jako multi-lingual)
        ('Русский язык A1', 'Russian', 'A1', 'Kurs dla osób polskojęzycznych – cyrylica, akcent, podstawy gramatyki.', 269.00, 5, 1),
    ]
    db.executemany(
        'INSERT INTO courses (title, language, proficiency_level, description, price, teacher_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)',
        courses,
    )

    # Lekcje: (course_id, title, description, sort_order)
    lessons = [
        # Kurs 1: Hiszpański A1
        (1, 'Lekcja 1: Powitania i zwroty grzecznościowe', 'Hola, buenos días, ¿cómo estás? – budowa pierwszych dialogów.', 1),
        (1, 'Lekcja 2: Liczebniki i kolory', 'Nauka liczenia do 100 oraz opisywania otoczenia.', 2),
        (1, 'Lekcja 3: Czasownik SER i ESTAR', 'Dwa kluczowe czasowniki „być" – kiedy używać każdego.', 3),
        (1, 'Lekcja 4: Rodzina i opis osoby', 'Słownictwo rodzinne, przymiotniki opisujące wygląd i charakter.', 4),

        # Kurs 2: Hiszpański w podróży
        (2, 'Lekcja 1: Na lotnisku i w hotelu', 'Rezerwacja, odprawa, zameldowanie – kluczowe zwroty turystyczne.', 1),
        (2, 'Lekcja 2: W restauracji', 'Zamawianie tapas, czytanie menu, prośba o rachunek.', 2),
        (2, 'Lekcja 3: Transport miejski', 'Metro, autobus, taksówka – pytanie o drogę.', 3),

        # Kurs 3: Konwersacje B1
        (3, 'Lekcja 1: Wyrażanie opinii', 'Konstrukcje creo que, me parece, en mi opinión.', 1),
        (3, 'Lekcja 2: Czas przeszły pretérito', 'Praktyczne użycie pretérito indefinido vs. imperfecto.', 2),

        # Kurs 4: Business English B2
        (4, 'Lekcja 1: Business Emails', 'Zasady pisania formalnych wiadomości e-mail.', 1),
        (4, 'Lekcja 2: Negocjacje', 'Słownictwo przydatne podczas spotkań B2B.', 2),
        (4, 'Lekcja 3: Prezentacje produktów', 'Storytelling, struktura pitch deck, frazy do Q&A.', 3),

        # Kurs 5: English Essentials A2
        (5, 'Lekcja 1: Present Simple vs Continuous', 'Kiedy używać który czas teraźniejszy.', 1),
        (5, 'Lekcja 2: Past Simple – czasowniki regularne', 'Końcówka -ed, wymowa, wyjątki.', 2),

        # Kurs 6: IELTS C1
        (6, 'Lekcja 1: IELTS Writing Task 1', 'Opisywanie wykresów i diagramów – struktura, słownictwo akademickie.', 1),
        (6, 'Lekcja 2: IELTS Speaking Part 2', 'Cue card – jak budować spójną dwuminutową wypowiedź.', 2),
        (6, 'Lekcja 3: IELTS Listening Strategies', 'Techniki notowania, predykcji odpowiedzi.', 3),

        # Kurs 7: Niemiecki A1
        (7, 'Lekcja 1: Alphabet und Aussprache', 'Niemiecki alfabet, umlauty (ä, ö, ü), wymowa ß.', 1),
        (7, 'Lekcja 2: Sich vorstellen', 'Ich heiße..., Ich komme aus... – przedstawianie się.', 2),

        # Kurs 8: Niemiecki techniczny B1
        (8, 'Lekcja 1: Słownictwo branży automotive', 'Części samochodu, diagnoza usterek – dialogi w warsztacie.', 1),

        # Kurs 9 (nieaktywny) — bez lekcji

        # Kurs 10: Włoski A1
        (10, 'Lekcja 1: Buongiorno e ciao', 'Powitania formalne i nieformalne, dni tygodnia.', 1),
        (10, 'Lekcja 2: Articoli e nomi', 'Rodzajniki il/la/lo i rodzaj rzeczowników.', 2),

        # Kurs 11: La Dolce Vita B1
        (11, 'Lekcja 1: La cucina italiana', 'Słownictwo kulinarne, przepisy, dialogi w trattorii.', 1),
        (11, 'Lekcja 2: Cinema italiano', 'Fellini, Sorrentino – analiza fragmentów filmów.', 2),

        # Kurs 12: Francuski A1
        (12, 'Lekcja 1: Salutations et présentations', 'Bonjour, je m''appelle..., enchanté.', 1),
        (12, 'Lekcja 2: Les nombres et la date', 'Liczby 1–100, dni tygodnia, miesiące.', 2),

        # Kurs 13: Francuski biznesowy B2
        (13, 'Lekcja 1: Correspondance professionnelle', 'Struktura formalnego e-maila, zwroty grzecznościowe.', 1),

        # Kurs 14: Portugalski A1
        (14, 'Lekcja 1: Olá Brasil!', 'Wprowadzenie do brazylijskiej wymowy i podstawowe zwroty.', 1),

        # Kurs 15: Japoński A1
        (15, 'Lekcja 1: Hiragana – pierwsze 25 znaków', 'Systematyczna nauka znaków od あ do そ.', 1),
        (15, 'Lekcja 2: Podstawowe zdania z です', 'Konstrukcja XはYです – przedstawianie się.', 2),
        (15, 'Lekcja 3: Liczby i czas', 'Liczebniki, godziny, etykieta zegarka.', 3),

        # Kurs 16: Kanji Master A2
        (16, 'Lekcja 1: Pierwsze 50 kanji', 'Znaki podstawowe: liczby, dni tygodnia, części ciała.', 1),

        # Kurs 17: Rosyjski A1
        (17, 'Lekcja 1: Алфавит / Cyrylica', 'Litery drukowane i pisane, transliteracja.', 1),
        (17, 'Lekcja 2: Привет! Меня зовут...', 'Przywitania, przedstawianie się, prosta odmiana czasowników.', 2),
    ]
    db.executemany(
        'INSERT INTO lessons (course_id, title, description, sort_order) VALUES (?, ?, ?, ?)',
        lessons,
    )

    # Materiały: (lesson_id, title, type, url)
    db.executemany(
        'INSERT INTO materials (lesson_id, title, material_type, resource_url) VALUES (?, ?, ?, ?)',
        [
            (1, 'Słowniczek powitań (PDF)', 'PDF', 'https://yo-lingo.pl/materialy/powitania.pdf'),
            (1, 'Wymowa hiszpańska – wideo', 'VIDEO', 'https://yo-lingo.pl/materialy/wymowa-es.mp4'),
            (2, 'Karta pracy: liczby 1-100', 'PDF', 'https://yo-lingo.pl/materialy/liczby.pdf'),
            (10, 'Szablony e-maili biznesowych', 'LINK', 'https://yo-lingo.pl/materialy/szablony'),
            (10, 'Lista zwrotów formalnych (PDF)', 'PDF', 'https://yo-lingo.pl/materialy/biznes-zwroty.pdf'),
            (20, 'Tablica hiragana – plansza', 'PDF', 'https://yo-lingo.pl/materialy/hiragana.pdf'),
            (20, 'Hiragana – ćwiczenia pisania', 'VIDEO', 'https://yo-lingo.pl/materialy/hiragana-pisanie.mp4'),
            (23, 'Tablica cyrylicy', 'PDF', 'https://yo-lingo.pl/materialy/cyrylica.pdf'),
        ],
    )

    db.executemany(
        'INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)',
        [
            (1, 2, 'Dzień dobry, czy materiały z lekcji 1 obowiązują na teście?'),
            (2, 1, 'Cześć Janie, tak, proszę przejrzeć słowniczek powitań z załącznika PDF.'),
        ],
    )


# --- POMOCNICZE ---
def log_email_notification(to_email, subject, body):
    print(f"\n[EMAIL SYSTEM LOG] Wysyłanie e-mail do: {to_email}")
    print(f"[TEMAT]: {subject}")
    print(f"[TREŚĆ]: {body}\n")


def teacher_owns_course(db, course_id, uid):
    return db.execute('SELECT 1 FROM courses WHERE id = ? AND teacher_id = ?',
                      (course_id, uid)).fetchone() is not None


def teacher_owns_lesson(db, lesson_id, uid):
    return db.execute('''SELECT 1 FROM lessons l JOIN courses c ON l.course_id = c.id
                         WHERE l.id = ? AND c.teacher_id = ?''',
                      (lesson_id, uid)).fetchone() is not None


# --- WIDOK GŁÓWNY & WYSZUKIWARKA ---
@app.route('/')
def index():
    db = get_db()
    search_query = request.args.get('search', '')
    lang_filter = request.args.get('language', '')
    level_filter = request.args.get('level', '')

    query = '''SELECT c.*, u.first_name || " " || u.last_name AS teacher_name,
               (SELECT COUNT(*) FROM lessons WHERE course_id = c.id) AS lesson_count
               FROM courses c LEFT JOIN users u ON c.teacher_id = u.id
               WHERE c.is_active = 1'''
    params = []

    if search_query:
        query += ' AND c.title LIKE ?'
        params.append(f'%{search_query}%')
    if lang_filter:
        query += ' AND c.language = ?'
        params.append(lang_filter)
    if level_filter:
        query += ' AND c.proficiency_level = ?'
        params.append(level_filter)

    courses = db.execute(query, params).fetchall()
    return render_template('index.html', courses=courses)


# --- SZCZEGÓŁY KURSU (UC-15, widok publiczny przed zapisem) ---
@app.route('/course/<int:course_id>')
def course_details(course_id):
    db = get_db()
    course = db.execute('''SELECT c.*, u.first_name || " " || u.last_name AS teacher_name
                           FROM courses c LEFT JOIN users u ON c.teacher_id = u.id
                           WHERE c.id = ?''', (course_id,)).fetchone()
    if course is None:
        flash('Kurs nie istnieje.', 'danger')
        return redirect(url_for('index'))

    lessons = db.execute(
        'SELECT id, title, description, sort_order FROM lessons WHERE course_id = ? ORDER BY sort_order, id',
        (course_id,)
    ).fetchall()

    already_enrolled = False
    if session.get('user_id'):
        already_enrolled = db.execute(
            'SELECT 1 FROM enrollments WHERE student_id = ? AND course_id = ?',
            (session['user_id'], course_id)
        ).fetchone() is not None

    return render_template('course_details.html',
                           course=course, lessons=lessons,
                           already_enrolled=already_enrolled)


# --- PANEL LOGOWANIA I REJESTRACJI ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        password = request.form.get('password') or ''

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            if user['status'] == 'BLOCKED':
                flash('Twoje konto zostało zablokowane przez administratora.', 'danger')
                return render_template('login.html')

            session['user_id'] = user['id']
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            session['email'] = user['email']
            session['role'] = user['role']

            if user['role'] == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'TEACHER':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))

        flash('Niepoprawny e-mail lub hasło.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['POST'])
def register():
    first_name = (request.form.get('first_name') or '').strip()
    last_name = (request.form.get('last_name') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    password_confirm = request.form.get('password_confirm') or ''
    role = request.form.get('role', 'STUDENT')

    if not first_name or not last_name:
        flash('Imię i nazwisko są wymagane.', 'danger')
        return redirect(url_for('login'))
    if not EMAIL_REGEX.match(email):
        flash('Podaj poprawny adres e-mail.', 'danger')
        return redirect(url_for('login'))
    if len(password) < 6:
        flash('Hasło musi mieć co najmniej 6 znaków.', 'danger')
        return redirect(url_for('login'))
    if password != password_confirm:
        flash('Podane hasła nie są identyczne.', 'danger')
        return redirect(url_for('login'))
    if role not in ALLOWED_ROLES:
        flash('Nieprawidłowy typ konta.', 'danger')
        return redirect(url_for('login'))

    db = get_db()
    if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        flash('Użytkownik o podanym adresie e-mail już istnieje.', 'danger')
        return redirect(url_for('login'))

    db.execute('INSERT INTO users (first_name, last_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)',
               (first_name, last_name, email, generate_password_hash(password), role))
    db.commit()

    log_email_notification(email, "Witamy w Yo-Lingo!", f"Witaj {first_name}! Twoje konto zostało pomyślnie utworzone.")
    flash('Rejestracja przebiegła pomyślnie! Możesz się teraz zalogować.', 'success')
    return redirect(url_for('login'))


@app.route('/password-reset', methods=['POST'])
def password_reset():
    email = (request.form.get('email') or '').strip().lower()
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if user:
        log_email_notification(email, "Resetowanie hasła - Yo-Lingo", "Kliknij odnośnik, aby zresetować hasło: http://yo-lingo.pl/reset-link")
    flash('Jeśli konto istnieje, instrukcje resetowania hasła zostały wysłane na podany adres e-mail.', 'success')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# --- EDYCJA PROFILU (UC-12) ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    user = db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_data':
            first_name = (request.form.get('first_name') or '').strip()
            last_name = (request.form.get('last_name') or '').strip()
            email = (request.form.get('email') or '').strip().lower()

            if not first_name or not last_name:
                flash('Imię i nazwisko są wymagane.', 'danger')
                return redirect(url_for('profile'))
            if not EMAIL_REGEX.match(email):
                flash('Podaj poprawny adres e-mail.', 'danger')
                return redirect(url_for('profile'))

            # Sprawdzenie unikalności e-maila (poza bieżącym kontem).
            collision = db.execute('SELECT id FROM users WHERE email = ? AND id != ?',
                                   (email, uid)).fetchone()
            if collision:
                flash('Adres e-mail jest już używany przez inne konto.', 'danger')
                return redirect(url_for('profile'))

            db.execute('UPDATE users SET first_name = ?, last_name = ?, email = ? WHERE id = ?',
                       (first_name, last_name, email, uid))
            db.commit()
            session['user_name'] = f"{first_name} {last_name}"
            session['email'] = email
            flash('Dane profilu zostały zaktualizowane.', 'success')
            return redirect(url_for('profile'))

        elif action == 'change_password':
            current = request.form.get('current_password') or ''
            new = request.form.get('new_password') or ''
            confirm = request.form.get('confirm_password') or ''

            if not check_password_hash(user['password_hash'], current):
                flash('Aktualne hasło jest nieprawidłowe.', 'danger')
                return redirect(url_for('profile'))
            if len(new) < 6:
                flash('Nowe hasło musi mieć co najmniej 6 znaków.', 'danger')
                return redirect(url_for('profile'))
            if new != confirm:
                flash('Powtórzone hasło nie pasuje do nowego.', 'danger')
                return redirect(url_for('profile'))

            db.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                       (generate_password_hash(new), uid))
            db.commit()
            flash('Hasło zostało zmienione pomyślnie.', 'success')
            return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


# --- PANEL UCZNIA ---
@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'STUDENT':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']

    my_courses = db.execute('''
        SELECT c.*, e.progress_percentage, u.first_name || " " || u.last_name AS teacher_name
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN users u ON c.teacher_id = u.id
        WHERE e.student_id = ?''', (uid,)).fetchall()

    messages = db.execute('''
        SELECT m.*, u.first_name || " " || u.last_name AS sender_name
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.receiver_id = ? ORDER BY m.created_at DESC''', (uid,)).fetchall()

    # UC-28: oznaczamy wiadomości jako przeczytane po wyświetleniu skrzynki.
    # Stan "is_read" przekazany do szablonu pochodzi sprzed update'u – stąd na tej
    # stronie nowe wiadomości jeszcze wyświetlą się z badge'em "Nowa".
    db.execute('UPDATE messages SET is_read = 1 WHERE receiver_id = ? AND is_read = 0', (uid,))
    db.commit()

    teachers = db.execute('SELECT id, first_name, last_name FROM users WHERE role = "TEACHER" AND status = "ACTIVE"').fetchall()

    return render_template('student.html', courses=my_courses, messages=messages, teachers=teachers)


# --- ANULOWANIE ZAPISU (UC-16) ---
@app.route('/enrollment/cancel/<int:course_id>', methods=['POST'])
def cancel_enrollment(course_id):
    if session.get('role') != 'STUDENT':
        return redirect(url_for('login'))

    db = get_db()
    enr = db.execute('SELECT id FROM enrollments WHERE student_id = ? AND course_id = ?',
                     (session['user_id'], course_id)).fetchone()
    if enr is None:
        flash('Nie jesteś zapisany na ten kurs.', 'danger')
        return redirect(url_for('student_dashboard'))

    db.execute('DELETE FROM enrollments WHERE id = ?', (enr['id'],))
    db.commit()
    flash('Anulowano zapis na kurs. Dostęp do materiałów został odebrany.', 'success')
    return redirect(url_for('student_dashboard'))


# --- BRAMKA PŁATNOŚCI (ONLINE PAYMENT SIMULATION) ---
@app.route('/course/checkout/<int:course_id>', methods=['GET'])
def checkout(course_id):
    if not session.get('user_id'):
        flash('Zaloguj się, aby kontynuować zakup.', 'danger')
        return redirect(url_for('login'))
    if session.get('role') != 'STUDENT':
        flash('Tylko konto słuchacza może zapisać się na kurs.', 'danger')
        return redirect(url_for('index'))

    db = get_db()
    course = db.execute('''
        SELECT c.*, u.first_name || " " || u.last_name AS teacher_name
        FROM courses c LEFT JOIN users u ON c.teacher_id = u.id
        WHERE c.id = ? AND c.is_active = 1''', (course_id,)).fetchone()
    if course is None:
        flash('Wybrany kurs jest niedostępny.', 'danger')
        return redirect(url_for('index'))

    already = db.execute('SELECT 1 FROM enrollments WHERE student_id = ? AND course_id = ?',
                         (session['user_id'], course_id)).fetchone()
    if already:
        flash('Masz już dostęp do tego kursu.', 'warning')
        return redirect(url_for('student_dashboard'))

    return render_template('checkout.html', course=course)


@app.route('/course/enroll/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    if session.get('role') != 'STUDENT':
        flash('Tylko zalogowany słuchacz może zapisać się na kurs.', 'danger')
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    course = db.execute('SELECT * FROM courses WHERE id = ? AND is_active = 1', (course_id,)).fetchone()
    if course is None:
        flash('Wybrany kurs jest niedostępny.', 'danger')
        return redirect(url_for('index'))

    payment_method = request.form.get('payment_method', 'BLIK')
    if payment_method not in ('BLIK', 'CARD', 'TRANSFER'):
        flash('Wybierz prawidłową metodę płatności.', 'danger')
        return redirect(url_for('checkout', course_id=course_id))

    if payment_method == 'BLIK':
        blik = (request.form.get('blik_code') or '').strip()
        if not re.fullmatch(r'\d{6}', blik):
            flash('Nieprawidłowy kod BLIK – wymagane dokładnie 6 cyfr.', 'danger')
            return redirect(url_for('checkout', course_id=course_id))
        transaction_id = f"BLIK-{blik}"
    elif payment_method == 'CARD':
        card = re.sub(r'\s+', '', request.form.get('card_number') or '')
        cvv = (request.form.get('card_cvv') or '').strip()
        if not re.fullmatch(r'\d{13,19}', card) or not re.fullmatch(r'\d{3,4}', cvv):
            flash('Nieprawidłowe dane karty płatniczej.', 'danger')
            return redirect(url_for('checkout', course_id=course_id))
        transaction_id = "CARD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    else:
        transaction_id = "TR-" + ''.join(random.choices(string.digits, k=10))

    if not request.form.get('accept_terms'):
        flash('Musisz zaakceptować regulamin, aby sfinalizować płatność.', 'danger')
        return redirect(url_for('checkout', course_id=course_id))

    try:
        db.execute('INSERT INTO payments (user_id, course_id, amount, payment_status, transaction_id) VALUES (?, ?, ?, "COMPLETED", ?)',
                   (uid, course_id, course['price'], transaction_id))
        db.execute('INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)', (uid, course_id))
        db.commit()

        log_email_notification(session['email'], "Potwierdzenie zapisu", f"Płatność {course['price']} PLN za kurs '{course['title']}' zaksięgowana (Kod: {transaction_id}).")
        flash(f'Płatność zaksięgowana (Kod transakcji: {transaction_id}). Witamy na kursie!', 'success')
    except sqlite3.IntegrityError:
        db.rollback()
        flash('Płatność odrzucona: Masz już dostęp do tego kursu.', 'warning')

    return redirect(url_for('student_dashboard'))


# --- LEKCJE I MATERIAŁY KURSU (widok dla zapisanego ucznia / lektora / admina) ---
@app.route('/course/<int:course_id>/lessons')
def course_lessons(course_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']

    course = db.execute('''
        SELECT c.*, u.first_name || " " || u.last_name AS teacher_name
        FROM courses c LEFT JOIN users u ON c.teacher_id = u.id
        WHERE c.id = ?''', (course_id,)).fetchone()
    if course is None:
        flash('Kurs nie istnieje.', 'danger')
        return redirect(url_for('index'))

    role = session.get('role')
    is_owner_teacher = (role == 'TEACHER' and course['teacher_id'] == uid)
    is_admin = (role == 'ADMIN')
    has_access = (
        is_admin or is_owner_teacher
        or db.execute('SELECT 1 FROM enrollments WHERE student_id = ? AND course_id = ?',
                      (uid, course_id)).fetchone() is not None
    )
    if not has_access:
        flash('Nie masz dostępu do tego kursu. Zapisz się, aby przeglądać lekcje.', 'danger')
        return redirect(url_for('index'))

    lessons = db.execute(
        'SELECT * FROM lessons WHERE course_id = ? ORDER BY sort_order, id',
        (course_id,)
    ).fetchall()

    materials_by_lesson = {}
    for lesson in lessons:
        materials_by_lesson[lesson['id']] = db.execute(
            'SELECT * FROM materials WHERE lesson_id = ? ORDER BY id',
            (lesson['id'],)
        ).fetchall()

    return render_template('course_lessons.html',
                           course=course, lessons=lessons,
                           materials_by_lesson=materials_by_lesson,
                           can_edit=is_owner_teacher)


# --- PANEL LEKTORA ---
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']

    my_courses = db.execute('''
        SELECT c.*,
               (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.id) AS student_count,
               (SELECT COUNT(*) FROM lessons l WHERE l.course_id = c.id) AS lesson_count,
               (SELECT COALESCE(AVG(e.progress_percentage), 0) FROM enrollments e WHERE e.course_id = c.id) AS avg_progress
        FROM courses c
        WHERE c.teacher_id = ? ORDER BY c.created_at DESC''', (uid,)).fetchall()

    # UC-31: statystyki lektora (agregaty po wszystkich jego kursach).
    stats = {
        'total_courses': db.execute('SELECT COUNT(*) FROM courses WHERE teacher_id = ?', (uid,)).fetchone()[0],
        'active_courses': db.execute('SELECT COUNT(*) FROM courses WHERE teacher_id = ? AND is_active = 1', (uid,)).fetchone()[0],
        'total_students': db.execute('''SELECT COUNT(DISTINCT e.student_id) FROM enrollments e
                                        JOIN courses c ON e.course_id = c.id WHERE c.teacher_id = ?''', (uid,)).fetchone()[0],
        'total_revenue': db.execute('''SELECT COALESCE(SUM(p.amount), 0) FROM payments p
                                       JOIN courses c ON p.course_id = c.id
                                       WHERE c.teacher_id = ? AND p.payment_status = "COMPLETED"''', (uid,)).fetchone()[0],
    }

    messages = db.execute('''
        SELECT m.*, u.first_name || " " || u.last_name AS sender_name
        FROM messages m JOIN users u ON m.sender_id = u.id
        WHERE m.receiver_id = ? ORDER BY m.created_at DESC''', (uid,)).fetchall()

    # UC-28: auto-mark messages as read (po pobraniu listy z oryginalnym stanem).
    db.execute('UPDATE messages SET is_read = 1 WHERE receiver_id = ? AND is_read = 0', (uid,))
    db.commit()

    students = db.execute('SELECT id, first_name, last_name FROM users WHERE role = "STUDENT" AND status = "ACTIVE"').fetchall()

    return render_template('teacher.html', courses=my_courses, stats=stats,
                           messages=messages, students=students)


@app.route('/teacher/course/add', methods=['POST'])
def add_course():
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    title = (request.form.get('title') or '').strip()
    language = request.form.get('language')
    level = request.form.get('proficiency_level')
    description = (request.form.get('description') or '').strip()
    price_raw = request.form.get('price')

    if not title or not language or not level:
        flash('Tytuł, język i poziom kursu są wymagane.', 'danger')
        return redirect(url_for('teacher_dashboard'))
    if level not in CEFR_LEVELS:
        flash('Nieprawidłowy poziom CEFR.', 'danger')
        return redirect(url_for('teacher_dashboard'))
    try:
        price = float(price_raw)
        if price < 0:
            raise ValueError
    except (TypeError, ValueError):
        flash('Cena musi być liczbą nieujemną.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    db = get_db()
    db.execute('INSERT INTO courses (title, language, proficiency_level, description, price, teacher_id, is_active) VALUES (?, ?, ?, ?, ?, ?, 1)',
               (title, language, level, description, price, session['user_id']))
    db.commit()
    flash('Nowy kurs został utworzony pomyślnie.', 'success')
    return redirect(url_for('teacher_dashboard'))


# --- EDYCJA KURSU (UC-20) ---
@app.route('/teacher/course/edit/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if course is None or course['teacher_id'] != uid:
        flash('Nie masz uprawnień do edycji tego kursu.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        language = request.form.get('language')
        level = request.form.get('proficiency_level')
        description = (request.form.get('description') or '').strip()
        price_raw = request.form.get('price')

        if not title or not language or not level:
            flash('Tytuł, język i poziom są wymagane.', 'danger')
            return redirect(url_for('edit_course', course_id=course_id))
        if level not in CEFR_LEVELS:
            flash('Nieprawidłowy poziom CEFR.', 'danger')
            return redirect(url_for('edit_course', course_id=course_id))
        try:
            price = float(price_raw)
            if price < 0:
                raise ValueError
        except (TypeError, ValueError):
            flash('Cena musi być liczbą nieujemną.', 'danger')
            return redirect(url_for('edit_course', course_id=course_id))

        db.execute('''UPDATE courses SET title=?, language=?, proficiency_level=?, description=?, price=?
                      WHERE id=?''', (title, language, level, description, price, course_id))
        db.commit()
        flash('Dane kursu zostały zaktualizowane.', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('course_edit.html', course=course)


# --- USUNIĘCIE KURSU PRZEZ LEKTORA (UC-21) ---
@app.route('/teacher/course/delete/<int:course_id>', methods=['POST'])
def teacher_delete_course(course_id):
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    if not teacher_owns_course(db, course_id, uid):
        flash('Nie masz uprawnień do usunięcia tego kursu.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    db.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    db.commit()
    flash('Kurs został trwale usunięty wraz z lekcjami i materiałami.', 'success')
    return redirect(url_for('teacher_dashboard'))


# --- ZMIANA STATUSU KURSU (UC-22) ---
@app.route('/teacher/course/toggle/<int:course_id>', methods=['POST'])
def toggle_course_status(course_id):
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if course is None or course['teacher_id'] != uid:
        flash('Nie masz uprawnień.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    new_status = 0 if course['is_active'] else 1
    db.execute('UPDATE courses SET is_active = ? WHERE id = ?', (new_status, course_id))
    db.commit()
    flash(f'Kurs został {"aktywowany" if new_status else "zakończony"}.', 'success')
    return redirect(url_for('teacher_dashboard'))


# --- LEKCJE: DODAWANIE / EDYCJA / USUWANIE (UC-8, UC-23, UC-24) ---
@app.route('/teacher/lesson/add', methods=['POST'])
def add_lesson():
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    course_id = request.form.get('course_id', type=int)
    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    sort_order = request.form.get('sort_order', type=int) or 1

    if not course_id or not teacher_owns_course(db, course_id, uid):
        flash('Nie masz uprawnień do dodawania lekcji w tym kursie.', 'danger')
        return redirect(url_for('teacher_dashboard'))
    if not title:
        flash('Tytuł lekcji jest wymagany.', 'danger')
        return redirect(url_for('course_lessons', course_id=course_id))

    db.execute('INSERT INTO lessons (course_id, title, description, sort_order) VALUES (?, ?, ?, ?)',
               (course_id, title, description, sort_order))
    db.commit()
    flash(f'Lekcja "{title}" została dodana do kursu.', 'success')
    return redirect(url_for('course_lessons', course_id=course_id))


@app.route('/teacher/lesson/edit/<int:lesson_id>', methods=['POST'])
def edit_lesson(lesson_id):
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    lesson = db.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,)).fetchone()
    if lesson is None or not teacher_owns_lesson(db, lesson_id, uid):
        flash('Nie masz uprawnień do edycji tej lekcji.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    sort_order = request.form.get('sort_order', type=int) or lesson['sort_order']

    if not title:
        flash('Tytuł lekcji jest wymagany.', 'danger')
        return redirect(url_for('course_lessons', course_id=lesson['course_id']))

    db.execute('UPDATE lessons SET title=?, description=?, sort_order=? WHERE id=?',
               (title, description, sort_order, lesson_id))
    db.commit()
    flash('Lekcja zaktualizowana.', 'success')
    return redirect(url_for('course_lessons', course_id=lesson['course_id']))


@app.route('/teacher/lesson/delete/<int:lesson_id>', methods=['POST'])
def delete_lesson(lesson_id):
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    lesson = db.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,)).fetchone()
    if lesson is None or not teacher_owns_lesson(db, lesson_id, uid):
        flash('Nie masz uprawnień do usunięcia tej lekcji.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    course_id = lesson['course_id']
    db.execute('DELETE FROM lessons WHERE id = ?', (lesson_id,))
    db.commit()
    flash('Lekcja została usunięta wraz z przypisanymi materiałami.', 'success')
    return redirect(url_for('course_lessons', course_id=course_id))


# --- MATERIAŁY ---
@app.route('/teacher/material/add', methods=['POST'])
def add_material():
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    lesson_id = request.form.get('lesson_id', type=int)
    title = (request.form.get('title') or '').strip()
    m_type = request.form.get('material_type')
    url = (request.form.get('resource_url') or '').strip()

    if not title or not url:
        flash('Nazwa zasobu i adres URL są wymagane.', 'danger')
        return redirect(request.referrer or url_for('teacher_dashboard'))
    if m_type not in MATERIAL_TYPES:
        flash('Nieprawidłowy typ materiału.', 'danger')
        return redirect(request.referrer or url_for('teacher_dashboard'))

    db = get_db()
    if not lesson_id or not teacher_owns_lesson(db, lesson_id, session['user_id']):
        flash('Nie możesz dodać materiału do tej lekcji.', 'danger')
        return redirect(request.referrer or url_for('teacher_dashboard'))

    db.execute('INSERT INTO materials (lesson_id, title, material_type, resource_url) VALUES (?, ?, ?, ?)',
               (lesson_id, title, m_type, url))
    db.commit()
    flash(f'Materiał "{title}" został przypięty do lekcji.', 'success')

    course = db.execute('SELECT course_id FROM lessons WHERE id = ?', (lesson_id,)).fetchone()
    return redirect(url_for('course_lessons', course_id=course['course_id']))


@app.route('/teacher/material/delete/<int:material_id>', methods=['POST'])
def delete_material(material_id):
    if session.get('role') != 'TEACHER':
        return redirect(url_for('login'))

    db = get_db()
    uid = session['user_id']
    row = db.execute('''SELECT m.id, l.course_id FROM materials m
                        JOIN lessons l ON m.lesson_id = l.id
                        JOIN courses c ON l.course_id = c.id
                        WHERE m.id = ? AND c.teacher_id = ?''',
                     (material_id, uid)).fetchone()
    if row is None:
        flash('Nie masz uprawnień do usunięcia tego materiału.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    db.execute('DELETE FROM materials WHERE id = ?', (material_id,))
    db.commit()
    flash('Materiał został usunięty.', 'success')
    return redirect(url_for('course_lessons', course_id=row['course_id']))


# --- KOMUNIKATOR WEWNĘTRZNY ---
@app.route('/messages/send', methods=['POST'])
def send_message():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    receiver_id = request.form.get('receiver_id')
    content = (request.form.get('content') or '').strip()

    if not receiver_id or not content:
        flash('Odbiorca i treść wiadomości są wymagane.', 'danger')
        return redirect(request.referrer or url_for('index'))

    db = get_db()
    if db.execute('SELECT id FROM users WHERE id = ?', (receiver_id,)).fetchone() is None:
        flash('Wybrany odbiorca nie istnieje.', 'danger')
        return redirect(request.referrer or url_for('index'))

    db.execute('INSERT INTO messages (sender_id, receiver_id, content) VALUES (?, ?, ?)',
               (session['user_id'], receiver_id, content))
    db.commit()
    flash('Wiadomość została wysłana pomyślnie.', 'success')
    return redirect(request.referrer or url_for('index'))


# --- PANEL ADMINISTRATORA ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'ADMIN':
        return redirect(url_for('login'))

    db = get_db()
    users = db.execute('SELECT id, first_name, last_name, email, role, status, created_at FROM users').fetchall()

    stats = {
        "total_users": db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        "total_payments": db.execute('SELECT COUNT(*) FROM payments WHERE payment_status="COMPLETED"').fetchone()[0],
        "total_revenue": db.execute('SELECT SUM(amount) FROM payments WHERE payment_status="COMPLETED"').fetchone()[0] or 0.00,
        "active_courses_count": db.execute('SELECT COUNT(*) FROM courses WHERE is_active = 1').fetchone()[0]
    }

    all_courses = db.execute('SELECT id, title, language, proficiency_level, is_active FROM courses').fetchall()

    return render_template('admin.html', users=users, stats=stats, courses=all_courses)


@app.route('/admin/user/toggle/<int:user_id>', methods=['POST'])
def toggle_user_status(user_id):
    if session.get('role') != 'ADMIN':
        return redirect(url_for('login'))

    db = get_db()
    user = db.execute('SELECT status FROM users WHERE id = ?', (user_id,)).fetchone()
    if user is None:
        flash('Nie znaleziono użytkownika.', 'danger')
        return redirect(url_for('admin_dashboard'))

    new_status = 'BLOCKED' if user['status'] == 'ACTIVE' else 'ACTIVE'
    db.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
    db.commit()
    flash('Status blokady użytkownika został zaktualizowany.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/course/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if session.get('role') != 'ADMIN':
        return redirect(url_for('login'))

    db = get_db()
    db.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    db.commit()
    flash('Kurs został trwale usunięty z bazy.', 'success')
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, port=5000)
