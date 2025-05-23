-- schema.sql

-- USERS
CREATE TABLE u (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name VARCHAR2(100),
    email VARCHAR2(100) UNIQUE,
    password VARCHAR2(255),
    is_admin CHAR(1) DEFAULT 'N'
);

-- MOVIES
CREATE TABLE m (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    title VARCHAR2(100),
    genre VARCHAR2(50),
    duration NUMBER,
    image_url VARCHAR2(255)
);

-- SHOWTIMES
CREATE TABLE st (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    movie_id NUMBER REFERENCES m(id),
    show_time TIMESTAMP
);

-- SEATS
CREATE TABLE st_seats (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    showtime_id NUMBER REFERENCES st(id),
    seat_number VARCHAR2(10),
    is_booked CHAR(1) DEFAULT 'N'
);

-- BOOKINGS
CREATE TABLE b (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    user_id NUMBER REFERENCES u(id),
    showtime_id NUMBER REFERENCES st(id),
    seat_ids VARCHAR2(255),
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
