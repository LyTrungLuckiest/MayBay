from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary
from unidecode import unidecode


app = Flask(__name__)
app.secret_key = "KJGHJG^&*%&*^T&*(IGFG%ERFTGHCFHGFasdasIU"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/flightdb?charset=utf8mb4" % quote('aiconcha123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 3

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login_process'



cloudinary.config(
    cloud_name="dd1frsvzk",
    api_key="172266497937733",
    api_secret="W_FvA2NSah3Jlv8cxhubvnw2mVM",  # Click 'View API Keys' above to copy your API secret
    secure=True
)

@app.template_filter('intcomma')
def intcomma_filter(value):
    # Trả về giá trị đã format với dấu phẩy
    if value is None:
        return value
    return "{:,}".format(value)

# Định nghĩa bộ lọc remove_accents
@app.template_filter('remove_accents')
def remove_accents_filter(s):
    return unidecode(s)

# Đăng ký filter với Jinja2
app.jinja_env.filters['remove_accents'] = remove_accents_filter

VNP_TMN_CODE = "2VU2K1SA"  # Mã TmnCode được cung cấp bởi VNPay
VNP_HASH_SECRET = "UGGCBO74IZTRAS5YULYFU9NJ74F5SFV1"  # Khóa bí mật được cung cấp bởi VNPay
VNP_URL = " https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"  # URL Sandbox (thử nghiệm)
RETURN_URL = "http://127.0.0.1:5000/payment_return"  # URL khách hàng quay lại sau thanh toán
CALLBACK_URL = "http://127.0.0.1:5000/payment_return"  # URL nhận Webhook từ VNPay
