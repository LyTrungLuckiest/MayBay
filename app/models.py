import random
from cloudinary.utils import unique
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum, Boolean, Date, DateTime
from app import db, app
from enum import Enum as RoleEnum
import hashlib
from flask_login import UserMixin
from datetime import datetime, timezone, date


class UserRole(RoleEnum):
    ADMIN = 1
    STAFF_MANAGE = 2
    STAFF_TICKET = 3
    CUSTOMER = 4


class SeatClass(RoleEnum):
    BUSINESS = 1
    ECONOMY = 2


# Enum cho loại chuyến bay
class FlightType(RoleEnum):
    DIRECT = 1  # Bay thẳng
    ONE_STOP = 2  # 1 điểm dừng
    MULTIPLE_STOP = 3  # Nhiều điểm dừng


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    dob = Column(Date)
    gender = Column(Boolean)
    avatar = Column(String(200),
                    default="https://res.cloudinary.com/dxxwcby8l/image/upload/v1690528735/cg6clgelp8zjwlehqsst.jpg")
    user_role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER)

    def __str__(self):
        return self.name


class Payment(db.Model):
    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    payment_card_no = Column(String(20), nullable=False)
    payment_type = Column(Boolean, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_cost = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


class Cancellation(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    refund = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    payment_id = Column(Integer, ForeignKey(Payment.payment_id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


class Airport(db.Model):
    airport_id = Column(Integer, primary_key=True, autoincrement=True)
    airport_name = Column(String(255), nullable=False)
    airport_address = Column(String(255), nullable=False)
    airport_image = Column(String(255), nullable=False)

    def __str__(self):
        return self.airport_name

class Plane(db.Model):
    plane_id = Column(Integer, primary_key=True, autoincrement=True)
    plane_name = Column(String(255), nullable=False)
    total_seat = Column(Integer, nullable=False)
    company_id = Column(Integer, ForeignKey('company.com_id'), nullable=False)  # Khóa ngoại liên kết đến bảng Company

    seats = relationship('Seat', backref='plane', lazy=True, cascade="all, delete")
    company = relationship('Company', backref='planes', lazy=True)  # Mối quan hệ với Company

    def __str__(self):
        return self.plane_name


class Company(db.Model):
    com_id = Column(Integer, primary_key=True, autoincrement=True)
    com_name = Column(String(255), nullable=False)
    com_country = Column(String(255), nullable=False)


class Seat(db.Model):
    seat_id = Column(Integer, primary_key=True, autoincrement=True)
    seat_number = Column(Integer, nullable=False)
    seat_class = Column(SQLEnum(SeatClass), default=SeatClass.ECONOMY)
    seat_status = Column(Boolean, nullable=False, default=False)  # False = available, True = booked
    plane_id = Column(Integer, ForeignKey(Plane.plane_id), nullable=False)

    __table_args__ = (db.UniqueConstraint('plane_id', 'seat_number', name='uix_plane_seat_number'),)

    def __str__(self):
        return f"Seat {self.seat_number}"

class FlightRoute(db.Model):
    fr_id = Column(Integer, primary_key=True, autoincrement=True)
    departure_airport_id = Column(Integer, ForeignKey(Airport.airport_id), nullable=False)
    arrival_airport_id = Column(Integer, ForeignKey(Airport.airport_id), nullable=False)
    distance = Column(Float)
    description = Column(String(255))
    flights = relationship('Flight', backref='flight_route', lazy=True)

    # Định nghĩa quan hệ để truy cập thông tin sân bay
    departure_airport = relationship('Airport', foreign_keys=[departure_airport_id])
    arrival_airport = relationship('Airport', foreign_keys=[arrival_airport_id])

    def __str__(self):
        return f"Route {self.fr_id}"


class Flight(db.Model):
    flight_id = Column(Integer, primary_key=True, autoincrement=True)
    f_dept_time = Column(DateTime, nullable=False) #tg di
    flight_arr_time = Column(DateTime, nullable=False) #tg toi
    flight_duration = Column(Float) # tong tg di
    flight_price = Column(Float)
    flight_type = Column(SQLEnum(FlightType), default=FlightType.DIRECT)  # Enum cho flight_type
    flight_route_id = Column(Integer, ForeignKey(FlightRoute.fr_id), nullable=False)
    plane_id = Column(Integer, ForeignKey(Plane.plane_id), nullable=False)

    plane = relationship('Plane', backref='flights', lazy=True)

    def available_business_seats(self):
        return len(
            [seat for seat in self.plane.seats if seat.seat_class == SeatClass.BUSINESS and seat.seat_status == False])

    def available_economy_seats(self):
        return len(
            [seat for seat in self.plane.seats if seat.seat_class == SeatClass.ECONOMY and seat.seat_status == False])

    def __str__(self):
        return f"Flight {self.flight_id} - Available seats: Business: {self.available_business_seats()}, Economy: {self.available_economy_seats()}"



class FlightSchedule(db.Model):
    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey(Flight.flight_id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


class Booking(db.Model):
    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    book_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    booking_status = Column(Boolean, nullable=False, default=False)  # False: chưa thanh toán, True: đã thanh toán
    group_size = Column(Integer, nullable=False, default=1)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    flight_id = Column(Integer, ForeignKey(Flight.flight_id), nullable=False)
    seat_id = Column(Integer, ForeignKey(Seat.seat_id), nullable=False)

    user = relationship('User', backref='bookings', lazy=True)
    flight = relationship('Flight', backref='bookings', lazy=True)
    seat = relationship('Seat', backref='bookings', lazy=True)

    def __str__(self):
        return f"Booking {self.booking_id} - User: {self.user.name} - Flight: {self.flight.flight_id} - Seat: {self.seat.seat_number} - Type: {self.seat.seat_type}"

class Luggage(db.Model):
    luggage_id = Column(Integer, primary_key=True, autoincrement=True)
    luggage_name = Column(String(255), nullable=False)
    weight = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    flight_id = Column(Integer, ForeignKey(Flight.flight_id), nullable=False)

class CustomerInfo(db.Model):
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    user_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)  # Khóa ngoại liên kết đến bảng User
    user = relationship('User', backref='customers')  # Quan hệ với bảng User

class Ticket(db.Model):
    ticket_id = Column(Integer, primary_key=True, autoincrement=True)
    issue_date = Column(Date, nullable=False)
    ticket_price = Column(Float, nullable=False)
    ticket_status = Column(Boolean, nullable=False)
    ticket_gate = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False) # customer_id = null thì là người mua ngược lại là người bán
    flight_id = Column(Integer, ForeignKey(Flight.flight_id), nullable=False)
    seat_id = Column(Integer, ForeignKey(Seat.seat_id), nullable=False)
    customer_id = Column(Integer, ForeignKey(CustomerInfo.customer_id)) # nếu mua tại quầy thì lưu thông tin vào bảng CustomerInfo, mặc định là 1 (staff)

class IntermediateAirport(db.Model):
    intermediate_id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey(Flight.flight_id), nullable=False)  # Liên kết với bảng Flight
    airport_id = Column(Integer, ForeignKey(Airport.airport_id), nullable=False)  # Liên kết với bảng Airport
    stopover_duration = Column(Integer, nullable=False)  # Thời gian dừng (phút)
    stop_order = Column(Integer, nullable=False)  # Thứ tự dừng

    flight = relationship("Flight", backref="intermediate_airports")
    airport = relationship("Airport", backref="intermediate_airports")


class Regulation(db.Model):
    regulation_id = Column(Integer, primary_key=True, autoincrement=True)
    airport_quantity = Column(Integer, nullable=False)
    minimum_flight_time = Column(Integer, nullable=False) # Thời gian bay tối thiểu (phút)
    max_intermediate_airports = Column(Integer, nullable=False)
    min_stopover_time = Column(Integer, nullable=False) # Thời gian dừng tối thiểu (phút)
    max_stopover_time = Column(Integer, nullable=False) # Thời gian dừng tối đa (phút)
    ticket_booking_hours = Column(Integer, nullable=False) # Số giờ đặt vé trước (giờ)
    ticket_selling_hours = Column(Integer, nullable=False) # Số giờ bán vé trước (giờ)

    def __str__(self):
        return f"Regulation {self.regulation_id} - Airport Quantity: {self.airport_quantity}"




if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tạo lại các bảng

        # Add Users
        users = [
            User(name='admin', username='admin', password=hashlib.md5('123456'.encode('utf-8')).hexdigest(),
                 user_role=UserRole.ADMIN, email='admin@gmail.com', dob=date(2000, 10, 10), gender=True),
            User(name='staff1', username='staff1', password=hashlib.md5('staff123'.encode('utf-8')).hexdigest(),
                 user_role=UserRole.STAFF_MANAGE, email='staff1@gmail.com', dob=date(1990, 5, 15), gender=True),
            User(name='staff2', username='staff2', password=hashlib.md5('staff123'.encode('utf-8')).hexdigest(),
                 user_role=UserRole.STAFF_TICKET, email='staff2@gmail.com', dob=date(1992, 7, 12), gender=False),
            User(name='customer1', username='customer1',
                 password=hashlib.md5('customer123'.encode('utf-8')).hexdigest(),
                 user_role=UserRole.CUSTOMER, email='customer1@gmail.com', dob=date(1995, 8, 10), gender=False),
            User(name='customer2', username='customer2',
                 password=hashlib.md5('customer123'.encode('utf-8')).hexdigest(),
                 user_role=UserRole.CUSTOMER, email='customer2@gmail.com', dob=date(1998, 3, 22), gender=True),
        ]
        db.session.add_all(users)
        db.session.commit()

        # Add Airports
        airports = [
            Airport(airport_name='Noi Bai International Airport', airport_address='Hanoi, Vietnam',
                    airport_image='https://example.com/noi_bai.jpg'),
            Airport(airport_name='Tan Son Nhat International Airport', airport_address='Ho Chi Minh, Vietnam',
                    airport_image='https://example.com/tan_son_nhat.jpg'),
            Airport(airport_name='Da Nang International Airport', airport_address='Da Nang, Vietnam',
                    airport_image='https://example.com/da_nang.jpg'),
            Airport(airport_name='Incheon International Airport', airport_address='Seoul, South Korea',
                    airport_image='https://example.com/incheon.jpg'),
            Airport(airport_name='Changi Airport', airport_address='Singapore',
                    airport_image='https://example.com/changi.jpg')
        ]
        db.session.add_all(airports)
        db.session.commit()

        # Add Companies
        companies = [
            Company(com_name='Vietnam Airlines', com_country='Vietnam'),
            Company(com_name='Korean Air', com_country='South Korea'),
            Company(com_name='Singapore Airlines', com_country='Singapore'),
            Company(com_name='Bamboo Airways', com_country='Vietnam'),
            Company(com_name='VietJet Air', com_country='Vietnam')
        ]
        db.session.add_all(companies)
        db.session.commit()

        # Add Planes
        planes = [
            Plane(plane_name='Airbus A321', total_seat=200, company_id=1),
            Plane(plane_name='Boeing 787', total_seat=250, company_id=2),
            Plane(plane_name='Airbus A350', total_seat=300, company_id=3),
            Plane(plane_name='Boeing 737', total_seat=180, company_id=4),
            Plane(plane_name='Embraer 190', total_seat=100, company_id=5)
        ]
        db.session.add_all(planes)
        db.session.commit()

        # Add Seats
        seat1 = Seat(seat_number=1, seat_class=SeatClass.ECONOMY, seat_status=False, plane_id=1)
        seat2 = Seat(seat_number=2, seat_class=SeatClass.ECONOMY, seat_status=False, plane_id=1)
        seat3 = Seat(seat_number=3, seat_class=SeatClass.ECONOMY, seat_status=False, plane_id=1)
        seat4 = Seat(seat_number=4, seat_class=SeatClass.ECONOMY, seat_status=True, plane_id=1)
        seat5 = Seat(seat_number=5, seat_class=SeatClass.ECONOMY, seat_status=True, plane_id=1)
        seat6 = Seat(seat_number=6, seat_class=SeatClass.ECONOMY, seat_status=True, plane_id=1)
        seat7 = Seat(seat_number=7, seat_class=SeatClass.ECONOMY, seat_status=False, plane_id=1)
        seat8 = Seat(seat_number=8, seat_class=SeatClass.BUSINESS, seat_status=True, plane_id=1)
        seat9 = Seat(seat_number=9, seat_class=SeatClass.BUSINESS, seat_status=False, plane_id=1)
        seat10 = Seat(seat_number=10, seat_class=SeatClass.BUSINESS, seat_status=False, plane_id=1)

        seat11 = Seat(seat_number=1, seat_class=SeatClass.ECONOMY, seat_status=False, plane_id=2)
        seat12 = Seat(seat_number=2, seat_class=SeatClass.ECONOMY, seat_status=False, plane_id=2)
        seat13 = Seat(seat_number=3, seat_class=SeatClass.ECONOMY, seat_status=False, plane_id=2)
        seat14 = Seat(seat_number=4, seat_class=SeatClass.ECONOMY, seat_status=True, plane_id=2)
        seat15 = Seat(seat_number=5, seat_class=SeatClass.ECONOMY, seat_status=True, plane_id=2)
        seat16 = Seat(seat_number=6, seat_class=SeatClass.ECONOMY, seat_status=True, plane_id=2)
        seat17 = Seat(seat_number=7, seat_class=SeatClass.ECONOMY, seat_status=False, plane_id=2)
        seat18 = Seat(seat_number=8, seat_class=SeatClass.BUSINESS, seat_status=True, plane_id=2)
        seat19 = Seat(seat_number=9, seat_class=SeatClass.BUSINESS, seat_status=True, plane_id=2)
        seat20 = Seat(seat_number=10, seat_class=SeatClass.BUSINESS, seat_status=True, plane_id=2)

        db.session.add_all(
            [seat1, seat2, seat3, seat4, seat5, seat6, seat7, seat8, seat9, seat10, seat11, seat12, seat13, seat14,
             seat15, seat16, seat17, seat18, seat19, seat20])
        db.session.commit()

        # Add Flight Routes
        routes = [
            FlightRoute(departure_airport_id=1, arrival_airport_id=2, distance=1150.0, description='Hanoi to HCM City'),
            FlightRoute(departure_airport_id=1, arrival_airport_id=3, distance=764.0, description='Hanoi to Da Nang'),
            FlightRoute(departure_airport_id=3, arrival_airport_id=2, distance=964.0,
                        description='Da Nang to HCM City'),
            FlightRoute(departure_airport_id=4, arrival_airport_id=1, distance=2740.0, description='Seoul to Hanoi'),
            FlightRoute(departure_airport_id=5, arrival_airport_id=1, distance=2224.0, description='Singapore to Hanoi')
        ]
        db.session.add_all(routes)
        db.session.commit()

        # Add Flights
        flights = [
            Flight(f_dept_time=datetime(2024, 12, 15, 6, 0), flight_arr_time=datetime(2024, 12, 15, 8, 0),
                   flight_duration=2.0, flight_price=150.0, flight_type=FlightType.DIRECT, flight_route_id=1,
                   plane_id=1),
            Flight(f_dept_time=datetime(2024, 12, 16, 7, 0), flight_arr_time=datetime(2024, 12, 16, 8, 30),
                   flight_duration=1.5, flight_price=120.0, flight_type=FlightType.DIRECT, flight_route_id=2,
                   plane_id=2),
            Flight(f_dept_time=datetime(2024, 12, 17, 9, 0), flight_arr_time=datetime(2024, 12, 17, 12, 0),
                   flight_duration=3.0, flight_price=200.0, flight_type=FlightType.ONE_STOP, flight_route_id=3,
                   plane_id=3),
            Flight(f_dept_time=datetime(2024, 12, 18, 10, 0), flight_arr_time=datetime(2024, 12, 18, 16, 0),
                   flight_duration=6.0, flight_price=400.0, flight_type=FlightType.DIRECT, flight_route_id=4,
                   plane_id=4),
            Flight(f_dept_time=datetime(2024, 12, 19, 11, 0), flight_arr_time=datetime(2024, 12, 19, 15, 0),
                   flight_duration=4.0, flight_price=350.0, flight_type=FlightType.MULTIPLE_STOP, flight_route_id=5,
                   plane_id=5)
        ]
        db.session.add_all(flights)
        db.session.commit()

        # Add Intermediate Airports
        intermediates = [
            IntermediateAirport(flight_id=3, airport_id=3, stopover_duration=45, stop_order=1),
            IntermediateAirport(flight_id=5, airport_id=4, stopover_duration=60, stop_order=1),
            IntermediateAirport(flight_id=5, airport_id=3, stopover_duration=30, stop_order=2)
        ]
        db.session.add_all(intermediates)
        db.session.commit()

        # Add CustomerInfor
        customer_info = [
            CustomerInfo(first_name="Thanh Ly Trung", last_name="Le", email="trung@gmail.com", phone_number="0321456782",user_id=2)
        ]
        db.session.add_all(customer_info)
        db.session.commit()

        # Add Tickets
        tickets = [
            Ticket(issue_date=date.today(), ticket_price=150.0, ticket_status=True, ticket_gate=1, user_id=2,
                   flight_id=1, seat_id=1, customer_id = 1),
            Ticket(issue_date=date.today(), ticket_price=120.0, ticket_status=True, ticket_gate=2, user_id=4,
                   flight_id=2, seat_id=2),
            Ticket(issue_date=date.today(), ticket_price=200.0, ticket_status=True, ticket_gate=3, user_id=5,
                   flight_id=3, seat_id=3),
            Ticket(issue_date=date.today(), ticket_price=400.0, ticket_status=True, ticket_gate=4, user_id=5,
                   flight_id=4, seat_id=4),
            Ticket(issue_date=date.today(), ticket_price=350.0, ticket_status=True, ticket_gate=5, user_id=4,
                   flight_id=5, seat_id=5)
        ]
        db.session.add_all(tickets)
        db.session.commit()

        regulation = [
            Regulation(airport_quantity=10, minimum_flight_time=30, min_stopover_time=20,
                       max_stopover_time=30, ticket_booking_hours=12, max_intermediate_airports=2,
                       ticket_selling_hours=4)
        ]
        db.session.add_all(regulation)
        db.session.commit()

