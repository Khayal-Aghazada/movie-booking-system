# 🎬 Movie Ticket Booking System

Welcome to a full-featured movie ticket booking platform built using **Flask**, **Oracle SQL**, and modern web technologies.

---

## 🌟 Features

### 👤 User Side
- ✅ Register and login securely
- 🎞️ Browse current movies with posters
- 🕒 View showtimes per movie
- 💺 Select available seats visually
- 📧 Receive email confirmations after booking
- 📋 View your booking history

### 🛠️ Admin Panel
- ➕ Add/Edit/Delete movies
- 🗓️ Add showtimes for each movie
- 🪑 Auto-generate seats for showtimes
- 📊 View all bookings
- 📤 Export bookings as Excel (.xlsx)

---

## 🧱 Tech Stack

| Layer      | Technology         |
|------------|--------------------|
| Frontend   | HTML, CSS, JavaScript |
| Backend    | Python (Flask)     |
| Database   | Oracle SQL         |
| Email      | SMTP (Gmail API)   |
| Reporting  | openpyxl (Excel export) |

---

## 📁 Folder Structure

```
movie_booking/
├── app/
│   ├── routes.py
│   ├── utils.py
│   ├── templates/
│   └── static/
├── config.py
├── run.py
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/Khayal-Aghazada/movie-booking-system.git
cd movie-booking-system
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure Oracle DB**

- Update your DB credentials in `config.py`
- Run `schema.sql` to create tables (`u`, `m`, `st`, `st_seats`, `b`)

4. **Start the app**

```bash
python run.py
```

Open `http://localhost:5000` in your browser.

---

## 📌 Status

✅ Fully implemented project — ready for deployment or extension!
