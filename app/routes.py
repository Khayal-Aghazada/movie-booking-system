from flask import Blueprint, render_template, request, redirect, session, flash, current_app
import cx_Oracle
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import send_confirmation_email
import openpyxl
from flask import send_file
import io


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return redirect('/login')



@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)
        conn = current_app.config['DB_CONN']
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO u (name, email, password) VALUES (:1, :2, :3)",
                           (name, email, hashed_password))
            conn.commit()
            flash("Registered successfully. Please log in.", "success")
            return redirect('/login')
        except cx_Oracle.IntegrityError:
            flash("Email already registered.", "danger")
        finally:
            cursor.close()
    return render_template("register.html")



@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = current_app.config['DB_CONN']
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password, is_admin FROM u WHERE email = :1", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = True if user[3] and user[3].upper() == 'Y' else False

            # 🔍 Debug print (TEMP)
            print("Logged in as admin:", session['is_admin'])

            return redirect('/dashboard')
        else:
            flash("Invalid email or password", "danger")
    return render_template("login.html")



@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, genre, duration, image_url FROM m")
    movies = cursor.fetchall()
    cursor.close()

    return render_template("dashboard.html", username=session['username'], movies=movies)



@main.route('/showtimes/<int:movie_id>')
def showtimes(movie_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM m WHERE id = :1", (movie_id,))
    movie = cursor.fetchone()

    cursor.execute("SELECT id, TO_CHAR(show_time, 'YYYY-MM-DD HH24:MI') FROM st WHERE movie_id = :1", (movie_id,))
    showtimes = cursor.fetchall()
    cursor.close()

    return render_template("showtimes.html", movie=movie, showtimes=showtimes)




@main.route('/bookings')
def user_bookings():
    if 'user_id' not in session:
        return redirect('/login')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, m.title, TO_CHAR(st.show_time, 'YYYY-MM-DD HH24:MI'), b.seat_ids, TO_CHAR(b.booking_time, 'YYYY-MM-DD HH24:MI')
        FROM b
        JOIN st ON b.showtime_id = st.id
        JOIN m ON st.movie_id = m.id
        WHERE b.user_id = :1
        ORDER BY b.booking_time DESC
    """, (session['user_id'],))
    bookings = cursor.fetchall()
    cursor.close()

    return render_template("user_bookings.html", bookings=bookings)



@main.route('/booking/<int:showtime_id>', methods=['GET', 'POST'])
def booking(showtime_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()

    if request.method == 'POST':
        selected_seats = request.form.getlist('seats')
        if not selected_seats:
            flash("Please select at least one seat.", "warning")
            return redirect(request.url)

        seat_ids_str = ','.join(selected_seats)

        # 1. Insert booking into 'b' table
        cursor.execute("""
            INSERT INTO b (user_id, showtime_id, seat_ids)
            VALUES (:1, :2, :3)
        """, (session['user_id'], showtime_id, seat_ids_str))

        # 2. Update seat availability
        for seat in selected_seats:
            cursor.execute("""
                UPDATE st_seats SET is_booked = 'Y'
                WHERE showtime_id = :1 AND seat_number = :2
            """, (showtime_id, seat))

        conn.commit()

        # 🔔 3. SEND CONFIRMATION EMAIL HERE
        cursor.execute("SELECT email FROM u WHERE id = :1", (session['user_id'],))
        user_email = cursor.fetchone()[0]

        cursor.execute("SELECT title FROM m WHERE id = (SELECT movie_id FROM st WHERE id = :1)", (showtime_id,))
        movie_title = cursor.fetchone()[0]

        message = f"🎟️ Booking Confirmed!\n\nMovie: {movie_title}\nShowtime ID: {showtime_id}\nSeats: {', '.join(selected_seats)}\n\nThank you!"

        from app.utils import send_confirmation_email
        send_confirmation_email(user_email, "Your Movie Ticket Booking", message)

        cursor.close()
        flash("Booking successful! Confirmation sent via email.", "success")
        return redirect('/dashboard')

    # GET: Show seat layout
    cursor.execute("""
        SELECT seat_number, is_booked FROM st_seats
        WHERE showtime_id = :1
    """, (showtime_id,))
    seats = cursor.fetchall()
    cursor.close()

    return render_template("booking.html", seats=seats, showtime_id=showtime_id)



@main.route('/logout')
def logout():
    session.clear()
    return redirect('/login')



@main.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect('/dashboard')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM m")
    movies_raw = cursor.fetchall()

    movies = []
    for m_id, m_title in movies_raw:
        cursor.execute("SELECT id, TO_CHAR(show_time, 'YYYY-MM-DD HH24:MI') FROM st WHERE movie_id = :1", (m_id,))
        showtimes = cursor.fetchall()
        movies.append((m_id, m_title, showtimes))

    cursor.close()
    return render_template("admin_panel.html", movies=movies)



@main.route('/admin/movies/add', methods=['GET', 'POST'])
def add_movie():
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect('/dashboard')

    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        duration = request.form['duration']
        image_url = request.form['image_url']

        conn = current_app.config['DB_CONN']
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO m (title, genre, duration, image_url)
            VALUES (:1, :2, :3, :4)
        """, (title, genre, duration, image_url))
        conn.commit()
        cursor.close()

        flash("Movie added successfully!", "success")
        return redirect('/admin')

    return render_template("add_movie.html")



@main.route('/admin/showtimes/<int:movie_id>', methods=['GET', 'POST'])
def add_showtime(movie_id):
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect('/dashboard')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM m WHERE id = :1", (movie_id,))
    movie = cursor.fetchone()

    if not movie:
        flash("Movie not found.", "danger")
        return redirect('/admin')

    if request.method == 'POST':
        datetime_str = request.form['datetime']  # Expected: 2025-05-20T18:00
        cursor.execute("""
            INSERT INTO st (movie_id, show_time)
            VALUES (:1, TO_TIMESTAMP(:2, 'YYYY-MM-DD\"T\"HH24:MI'))
        """, (movie_id, datetime_str))
        conn.commit()
        cursor.close()

        flash("Showtime added successfully!", "success")
        return redirect('/admin')

    return render_template("add_showtime.html", movie=movie, movie_id=movie_id)



@main.route('/admin/seats/generate/<int:showtime_id>')
def generate_seats(showtime_id):
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect('/dashboard')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()

    # Generate A1–A10 and B1–B10 (20 seats total)
    seat_rows = ['A', 'B']
    seat_numbers = [str(i) for i in range(1, 11)]

    for row in seat_rows:
        for num in seat_numbers:
            seat_code = row + num
            cursor.execute("""
                INSERT INTO st_seats (showtime_id, seat_number, is_booked)
                VALUES (:1, :2, 'N')
            """, (showtime_id, seat_code))

    conn.commit()
    cursor.close()

    flash("Seats generated successfully!", "success")
    return redirect('/admin')



@main.route('/admin/bookings')
def admin_bookings():
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect('/dashboard')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, u.name, m.title, TO_CHAR(st.show_time, 'YYYY-MM-DD HH24:MI'),
               b.seat_ids, TO_CHAR(b.booking_time, 'YYYY-MM-DD HH24:MI')
        FROM b
        JOIN u ON b.user_id = u.id
        JOIN st ON b.showtime_id = st.id
        JOIN m ON st.movie_id = m.id
        ORDER BY b.booking_time DESC
    """)
    bookings = cursor.fetchall()
    cursor.close()

    return render_template("admin_bookings.html", bookings=bookings)



@main.route('/admin/bookings/export')
def export_bookings():
    if not session.get('is_admin'):
        flash("Access denied.", "danger")
        return redirect('/dashboard')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.id, u.name, m.title, TO_CHAR(st.show_time, 'YYYY-MM-DD HH24:MI'),
               b.seat_ids, TO_CHAR(b.booking_time, 'YYYY-MM-DD HH24:MI')
        FROM b
        JOIN u ON b.user_id = u.id
        JOIN st ON b.showtime_id = st.id
        JOIN m ON st.movie_id = m.id
    """)
    bookings = cursor.fetchall()
    cursor.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Booking ID", "User", "Movie", "Showtime", "Seats", "Booked At"])

    for row in bookings:
        ws.append(list(row))

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output,
                     as_attachment=True,
                     download_name="booking_report.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



@main.route('/admin/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    if not session.get('is_admin'):
        return redirect('/dashboard')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        duration = request.form['duration']
        image_url = request.form['image_url']
        cursor.execute("""
            UPDATE m SET title = :1, genre = :2, duration = :3, image_url = :4
            WHERE id = :5
        """, (title, genre, duration, image_url, movie_id))
        conn.commit()
        cursor.close()
        flash("Movie updated!", "success")
        return redirect('/admin')

    cursor.execute("SELECT title, genre, duration, image_url FROM m WHERE id = :1", (movie_id,))
    movie = cursor.fetchone()
    cursor.close()
    return render_template("edit_movie.html", movie=movie, movie_id=movie_id)



@main.route('/admin/movies/delete/<int:movie_id>')
def delete_movie(movie_id):
    if not session.get('is_admin'):
        return redirect('/dashboard')

    conn = current_app.config['DB_CONN']
    cursor = conn.cursor()

    # Delete related seats and showtimes
    cursor.execute("SELECT id FROM st WHERE movie_id = :1", (movie_id,))
    showtime_ids = [row[0] for row in cursor.fetchall()]

    for st_id in showtime_ids:
        cursor.execute("DELETE FROM st_seats WHERE showtime_id = :1", (st_id,))
        cursor.execute("DELETE FROM b WHERE showtime_id = :1", (st_id,))

    cursor.execute("DELETE FROM st WHERE movie_id = :1", (movie_id,))
    cursor.execute("DELETE FROM m WHERE id = :1", (movie_id,))
    conn.commit()
    cursor.close()

    flash("Movie and related data deleted.", "success")
    return redirect('/admin')
