import hashlib
import hmac
import math
import urllib
import uuid
from urllib.parse import urlencode
import unicodedata
from flask import render_template, request, redirect, session, jsonify, url_for,g
from app import dao, utils
from app import app, login, db, VNP_TMN_CODE, VNP_HASH_SECRET, VNP_URL, RETURN_URL, CALLBACK_URL
from flask_login import login_user, logout_user,current_user, login_required
from datetime import datetime
from app.models import UserRole, Flight, CustomerInfo, Ticket, Regulation
from datetime import datetime



def remove_accents(input_str):
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str)
        if unicodedata.category(c) != 'Mn'
    )
@app.before_request
def before_request():
    departure_name = request.args.get('departure', 'Ho Chi Minh')
    departure_name = remove_accents(departure_name)
    g.routes = dao.get_popular_routes(departure_name)
    g.cities = ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Singapore", "Bangkok", "Taipei", "Seoul", "Tokyo"]
    g.airports = dao.load_airports()
    g.departure_name = departure_name

    # Tính toán số trang
    page = request.args.get('page', 1)
    page = int(page)
    g.page = page
    g.flights = dao.get_flights(g.page)

    flights_counter = dao.count_flights()
    g.total_pages = math.ceil(flights_counter / app.config['PAGE_SIZE'])

@app.route("/")
def index():
    return render_template(
        'index.html',
        flights=g.flights,
        current_page=g.page,   # Truyền trang hiện tại
        pages=g.total_pages    # Truyền tổng số trang
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
@login_required
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
    ticket_id = str(uuid.uuid4())

    if flight:
        # Lấy các thông tin từ chuyến bay và các bảng liên quan
        company_name = flight.plane.company.com_name
        flight_price = flight.flight_price

        # Truyền dữ liệu vào template
        return render_template(
            'payment_qr.html',
            flight_id = flight_id,
            company_name = company_name,
            flight_price = flight_price,
            quantity = quantity,
            type_ticket = type_ticket,
            ticket_id=ticket_id
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
    is_customer = current_user.is_authenticated and current_user.user_role == UserRole.CUSTOMER



    return render_template('cart.html', is_customer=is_customer)

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
        type_ticket = request.form.get('type_ticket')
        ticket_price = request.form.get('ticket_price')
        issue_date = request.form.get('departure_date')
        quantity = int(request.form.get('quantity'))

        # Gọi DAO để lấy ghế đầu tiên
        seat_ids = []
        for _ in range(quantity):
            seat_id = dao.get_first_available_seat(flight_id,quantity, type_ticket)
            if not seat_id:
                return render_template('index.html', airports=g.airports,
                                       routes=g.routes,
                                       cities=g.cities,
                                       flights=g.flights,
                                       departure_name=g.departure_name,
                                       pages=g.total_pages,
                                       error_message="Không đủ ghế. Vui lòng thử lại sau."
                                       )
            seat_ids.append(seat_id)
            dao.mark_seat_as_booked(seat_id)

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

        ticket_ids = []
        for seat_id in seat_ids:
            ticket_id = str(uuid.uuid4())
            ticket = Ticket(
                transaction_id=ticket_id,
                issue_date=issue_date,
                ticket_price=ticket_price,
                ticket_status=True,
                ticket_gate=1,
                user_id=current_user.id,
                flight_id=flight_id,
                seat_id=seat_id,
                customer_id=new_customer.customer_id
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_ids.append(ticket_id)

        # Sau khi lưu thành công, chuyển hướng về trang chủ với thông điệp
        return render_template(
            'index.html', airports=g.airports,
            routes=g.routes,
            cities=g.cities,
            flights=g.flights,
            departure_name=g.departure_name,
            pages=g.total_pages,
            success_message="Đặt vé thành công"
        )


@app.route('/regulations')
def show_regulations():
    regulations = Regulation.query.all()
    return render_template('regulations.html', regulations=regulations)


def get_payment_url(request_data, secret_key):
    # Sắp xếp dữ liệu theo thứ tự alphabe
    inputData = sorted(request_data.items())
    queryString = '&'.join([f"{key}={urllib.parse.quote_plus(str(val))}" for key, val in inputData])

    # Tạo mã băm HMACSHA512
    hash_value = hmac.new(secret_key.encode('utf-8'), queryString.encode('utf-8'), hashlib.sha512).hexdigest()

    # Trả về URL thanh toán
    return f"{VNP_URL}?{queryString}&vnp_SecureHash={hash_value}"


@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        flight_id = request.form['flight_id']
        quantity = request.form['quantity']
        type_ticket = request.form['type_ticket']
        ticket_id = request.form['ticket_id']
        total_amount = request.form.get('amount')
        total_amount = int(float(total_amount))
        order_type = "Bán Sach"
        order_desc = f"KaliLove Thanh Toán số tiền là {total_amount} VND"
        bank_code = "ncb"
        language = "vn"
        ipaddr = request.remote_addr
        create_date = datetime.now().strftime('%Y%m%d%H%M%S')

        session['flight_id'] = flight_id
        session['ticket_id'] = request.form['ticket_id']
        session['quantity'] = request.form['quantity']
        session['type_ticket'] = request.form['type_ticket']

        if not flight_id or not quantity or not ticket_id or not type_ticket:
            return "Required fields missing", 400

        # Xây dựng requestData
        request_data = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': VNP_TMN_CODE,
            'vnp_Amount': total_amount * 100,
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': ticket_id,
            'vnp_OrderInfo': order_desc,
            'vnp_OrderType': order_type,
            'vnp_Locale': language if language else 'vn',
            'vnp_BankCode': bank_code if bank_code else '',
            'vnp_CreateDate': create_date,
            'vnp_IpAddr': ipaddr,
            'vnp_ReturnUrl': RETURN_URL,
        }

        # Lấy URL thanh toán
        payment_url = get_payment_url(request_data, VNP_HASH_SECRET)
        print(f"Payment URL: {payment_url}")

        return redirect(payment_url)

    return render_template('payment.html')



@app.route('/payment_return', methods=['GET', 'POST'])
def payment_return():
    # Retrieve data from session
    flight_id = session.get('flight_id')
    ticket_id = session.get('ticket_id')
    quantity = session.get('quantity')
    quantity = int(quantity)
    type_ticket = session.get('type_ticket')

    # Get data from payment gateway response (GET or POST)
    input_data = request.args if request.method == 'GET' else request.form
    print(input_data)  # For debugging purposes

    if input_data:
        vnp_secure_hash = input_data.get('vnp_SecureHash')
        vnp_response_code = input_data.get('vnp_ResponseCode')

        # Calculate the secure hash for verification
        request_data = {key: value for key, value in input_data.items() if key != 'vnp_SecureHash'}
        hash_value = hmac.new(VNP_HASH_SECRET.encode('utf-8'), urllib.parse.urlencode(request_data).encode('utf-8'),
                              hashlib.sha512).hexdigest()

        # Check the secure hash and response code
        if vnp_secure_hash == hash_value:
            if vnp_response_code == "00":
                # Payment successful
                result = "Thành công"
                # Query the flight details from the database (for display)
                flight = Flight.query.get(flight_id)  # Example: Assuming you have a Flight model
                if flight:
                    company_name = flight.plane.company.com_name
                    departure_time = flight.f_dept_time
                    arrival_time = flight.flight_arr_time
                    departure_local = flight.flight_route.departure_airport.airport_name
                    arrival_local = flight.flight_route.arrival_airport.airport_name
                    issue_date = departure_time

                    # Gọi DAO để lấy ghế đầu tiên
                    seat_ids = []
                    for _ in range(quantity):
                        seat_id = dao.get_first_available_seat(flight_id,quantity, type_ticket)
                        if not seat_id:
                            return render_template('index.html', airports=g.airports,
                                                   routes=g.routes,
                                                   cities=g.cities,
                                                   flights=g.flights,
                                                   departure_name=g.departure_name,
                                                   pages=g.total_pages,
                                                   error_message="Không đủ ghế. Vui lòng thử lại sau."
                                                   )
                        seat_ids.append(seat_id)
                        dao.mark_seat_as_booked(seat_id)

                    ticket_ids = []
                    for seat_id in seat_ids:
                        ticket_id = str(uuid.uuid4())
                        ticket = Ticket(
                            transaction_id=ticket_id,
                            issue_date=issue_date,
                            ticket_price=int(float(input_data.get('vnp_Amount'))) / 100,
                            ticket_status=True,
                            ticket_gate=1,
                            user_id=current_user.id,
                            flight_id=flight_id,
                            seat_id=seat_id
                        )
                        db.session.add(ticket)
                        db.session.commit()
                        ticket_ids.append(ticket_id)

                    return render_template('payment_return.html', result=result,
                                           ticket_id=ticket_id,
                                           total_amount=int(float(input_data.get('vnp_Amount'))) / 100,
                                           company_name=company_name, departure_time=departure_time,
                                           arrival_time=arrival_time,
                                           departure_local=departure_local, arrival_local=arrival_local,
                                           type_ticket=type_ticket, quantity=quantity)
                else:
                    result = "Lỗi: Không tìm thấy chuyến bay"
                    return render_template('payment_return.html', result=result, ticket_id=ticket_id)
            else:
                # Payment failed
                result = "Lỗi"
                return render_template('payment_return.html', result=result, ticket_id=ticket_id)
        else:
            # Invalid secure hash
            result = "Sai mã băm"
            return render_template('payment_return.html', result=result, ticket_id=ticket_id)

    return render_template('payment_return.html', result="Không nhận được dữ liệu")


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
