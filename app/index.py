import math

import unicodedata

from flask import render_template, request, redirect, session, jsonify, url_for
import dao, utils
from app import app, login,db
from flask_login import login_user, logout_user,current_user

from app.models import UserRole, Flight, CustomerInfo
from datetime import datetime


def remove_accents(input_str):
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str)
        if unicodedata.category(c) != 'Mn'
    )

@app.route("/")
def index():
        departure_name = request.args.get('departure', 'Ho Chi Minh')
        departure_name = remove_accents(departure_name)


        routes = dao.get_popular_routes(departure_name)

        cities = ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Singapore", "Bangkok", "Taipei", "Seoul", "Tokyo"]

        airports = dao.load_airports()


        page = request.args.get('page', 1)
        page = int(page)

        flights = dao.get_flights(page)
        flights_counter = dao.count_flights()
        total_pages = math.ceil(flights_counter / app.config['PAGE_SIZE'])

        return render_template(
            'index.html',
            airports=airports,
            routes=routes,
            cities=cities,
            flights=flights,
            departure_name=departure_name,
            pages=total_pages,
        )


@app.route('/register', methods=['get', 'post'])
def register_process():
    err_msg = ''
    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password.__eq__(confirm):
            data = request.form.copy()
            del data['confirm']

            gender = data.get('gender', '').lower()
            data['gender'] = True if gender == 'male' else False

            dob = data.get('dob')
            try:
                if dob:
                    data['dob'] = datetime.strptime(dob, '%Y-%m-%d').date()
                else:
                    err_msg = 'Ngày sinh không được bỏ trống.'
                    return render_template('register.html', err_msg=err_msg)
            except ValueError:
                err_msg = 'Định dạng ngày sinh không hợp lệ. Vui lòng nhập theo định dạng YYYY-MM-DD.'
                return render_template('register.html', err_msg=err_msg)

            dao.add_user(avatar=request.files.get('avatar'), **data)
            return redirect('/login')
        else:
            err_msg = 'Mật khẩu không khớp!'

    return render_template('register.html', err_msg=err_msg)


@app.route("/login", methods=['get', 'post'])
def login_process():
    if request.method.__eq__("POST"):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user)
            return redirect('/')

    return render_template('login.html')


@app.route("/logout")
def logout_process():
    logout_user()
    return redirect('/login')


@app.route("/login-admin", methods=['post'])
def login_admin_process():
    if request.method.__eq__("POST"):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password, role=UserRole.ADMIN)
        if user:
            login_user(user)
            return redirect('/admin')


@login.user_loader
def get_user_by_id(user_id):
    return dao.get_user_by_id(user_id)



@app.route('/search', methods=['GET'])
def search_flights_route():
    # Lấy thông tin từ yêu cầu
    departure = request.args.get('departure')
    arrival = request.args.get('arrival')
    departure_date = request.args.get('departure_date')
    adult_count = int(request.args.get('adult_count', 1))
    child_count = int(request.args.get('child_count', 0))
    infant_count = int(request.args.get('infant_count', 0))

    total_passengers = adult_count + child_count + infant_count

    # Gọi hàm tìm chuyến bay
    flights_result, error = dao.search_flights(departure, arrival, departure_date,total_passengers )

    if error:
        return render_template('booking.html', airports=dao.load_airports(), error=error)

    return render_template('booking.html', flights=flights_result, airports=dao.load_airports(),total_passengers=total_passengers)




@app.route("/payment_info/<int:flight_id>/<int:quantity>/<type_ticket>")
def payment_info(flight_id, quantity, type_ticket):
    flight = Flight.query.get(flight_id)

    if flight:
        # Lấy các thông tin từ chuyến bay
        company_name = flight.plane.company.com_name
        departure_time = flight.f_dept_time.strftime('%H:%M')
        arrival_time = flight.flight_arr_time.strftime('%H:%M')
        arrival_local = flight.flight_route.arrival_airport.airport_name
        departure_local = flight.flight_route.departure_airport.airport_name
        flight_duration = flight.flight_duration
        flight_type = flight.flight_type.name
        flight_price = flight.flight_price
        departure_date = flight.f_dept_time.date()
        formatted_date = departure_date.strftime('%Y-%m-%d')

        # Kiểm tra người dùng hiện tại
        if current_user.is_authenticated:
            user = get_user_by_id(current_user.id)
            current_role = user.user_role.name
        else:
            current_role = None

        # Truyền dữ liệu vào template
        return render_template(
            'payment_info.html',
            flight_id=flight_id,
            company_name=company_name,
            departure_time=departure_time,
            arrival_time=arrival_time,
            arrival_local=arrival_local,
            departure_local=departure_local,
            flight_duration=flight_duration,
            flight_price=flight_price,
            departure_date=formatted_date,
            flight_type=flight_type,
            quantity=quantity,
            type_ticket=type_ticket,
            current_role=current_role
        )
    else:
        return "Flight not found", 404


@app.route("/payment_qr/<int:flight_id>/<int:quantity>/<type_ticket>")
def payment_qr(flight_id,quantity,type_ticket):
    flight = Flight.query.get(flight_id)

    if flight:
        # Lấy các thông tin từ chuyến bay và các bảng liên quan
        company_name = flight.plane.company.com_name
        departure_time = flight.f_dept_time.strftime('%H:%M')
        arrival_time = flight.flight_arr_time.strftime('%H:%M')
        arrival_local =  flight.flight_route.arrival_airport.airport_name
        departure_local = flight.flight_route.departure_airport.airport_name
        flight_duration = flight.flight_duration
        flight_type=flight.flight_type.name
        flight_price = flight.flight_price
        departure_date = flight.f_dept_time.date()
        formatted_date = departure_date.strftime('%Y-%m-%d')

        # Truyền dữ liệu vào template
        return render_template(
            'payment_qr.html',
            company_name=company_name,
            departure_time=departure_time,
            arrival_time=arrival_time,
            arrival_local=arrival_local,
            departure_local=departure_local,
            flight_duration=flight_duration,
            flight_price=flight_price,
            departure_date =formatted_date,
            flight_type=flight_type,
            quantity=quantity,
            type_ticket=type_ticket
        )
    else:
        return "Flight not found", 404

@app.route('/booking', methods=['GET'])
def flights():
    airports = dao.load_airports()

    return render_template('booking.html', airports=airports)


@app.route("/api/carts", methods=['post'])
def add_to_cart():
    cart = session.get('cart', {})

    # Dữ liệu từ request JSON
    data = request.json
    flight_id = str(data.get('flight_id'))
    plane_name = data.get('plane_name')
    departure = data.get('departure')
    arrival = data.get('arrival')
    day = data.get('day')
    type_ticket = data.get('type_ticket')
    price = data.get('price')

    # Tạo khóa unique cho flight_id và type_ticket
    cart_key = f"{flight_id}_{type_ticket}"

    if cart_key in cart:
        # Nếu khóa đã tồn tại, tăng số lượng vé
        cart[cart_key]['quantity'] += 1
    else:
        # Nếu chưa tồn tại, tạo mục mới
        cart[cart_key] = {
            "flight_id": flight_id,
            "plane_name": plane_name,
            "departure": departure,
            "arrival": arrival,
            "day": day,
            "type_ticket": type_ticket,
            "price": float(price),
            "quantity": 1
        }

    session['cart'] = cart
    print(cart)

    return jsonify(utils.cart_stats(cart))

@app.route("/cart")
def cart_view():
    return render_template('cart.html')

@app.context_processor
def common_response_data():
    return {
        # 'categories': dao.load_categories(),
        'cart_stats': utils.cart_stats(session.get('cart'))
    }


@app.route('/cart/delete', methods=['POST'])
def delete_cart_item():
    flight_id = request.json.get('flight_id')
    type_ticket = request.json.get('type_ticket')

    if 'cart' in session:
        # Tìm và xóa phần tử giỏ hàng dựa trên flight_id và type_ticket
        cart = session['cart']
        key_to_delete = None
        for key, item in cart.items():
            if item['flight_id'] == flight_id and item['type_ticket'] == type_ticket:
                key_to_delete = key
                break

        if key_to_delete:
            del cart[key_to_delete]
            session['cart'] = cart  # Cập nhật lại giỏ hàng trong session
            session.modified = True

        # Tính lại tổng số lượng và giá
        stats = utils.cart_stats(cart)
        return jsonify({'success': True, 'stats': stats})

    return jsonify({'success': False, 'message': 'Cart not found!'})


@app.route('/cart/update', methods=['POST'])
def update_cart():
    flight_id = request.json.get('flight_id')
    type_ticket = request.json.get('type_ticket')
    quantity = int(request.json.get('quantity'))

    if 'cart' in session and quantity > 0:
        cart = session['cart']

        # Cập nhật số lượng cho mục phù hợp
        for item in cart.values():
            if item['flight_id'] == flight_id and item['type_ticket'] == type_ticket:
                item['quantity'] = quantity
                break

        # Lưu lại giỏ hàng vào session
        session['cart'] = cart
        session.modified = True

        # Tính toán lại tổng tiền và số lượng
        stats = utils.cart_stats(cart)
        return jsonify({'success': True, 'stats': stats})

    return jsonify({'success': False, 'message': 'Invalid cart or quantity'})

@app.route('/add_customer', methods=['POST'])
def add_customer():
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        flight_id = request.form.get('flight_id')
        quantity = request.form.get('quantity')
        type_ticket = request.form.get('type_ticket')

        # Tạo đối tượng Customer và lưu vào CSDL
        new_customer = CustomerInfo(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            email=email,
            user_id=current_user.id
        )

        db.session.add(new_customer)
        db.session.commit()

        # Sau khi lưu thành công, chuyển hướng đến trang thanh toán
        return redirect(url_for('payment_qr', flight_id=flight_id, quantity=quantity, type_ticket=type_ticket))


if __name__ == '__main__':
    with app.app_context():
        from app import admin
        app.run(debug=True)
