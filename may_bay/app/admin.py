from app import db, app, dao
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.models import User, UserRole, Company, Flight, FlightRoute, Airport, Plane, Ticket, Luggage, Cancellation, Payment, Seat, FlightSchedule, IntermediateAirport
from flask_login import current_user, logout_user
from flask_admin import BaseView, expose, AdminIndexView
from flask import redirect, render_template, url_for


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html', stats=dao.products_stats())


admin = Admin(app=app, name='eCommerce Admin', template_mode='bootstrap4', index_view=MyAdminIndexView())

class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

class FlightAdminView(AuthenticatedView):
    can_export = True
    can_view_details = True
    column_searchable_list = ['flight_id', 'flight_price']
    column_filters = ['flight_id', 'flight_price', 'flight_route_id']
    column_list = ['flight_id', 'flight_route_id', 'f_dept_time', 'flight_arr_time', 'flight_duration', 'flight_price']
    form_columns = ['f_dept_time', 'flight_arr_time', 'flight_duration', 'flight_price', 'flight_route_id']


class FlightRouteAdminView(AuthenticatedView):
    can_export = True
    column_searchable_list = ['fr_id']
    column_filters = ['fr_id']
    can_view_details = True
    column_list = ['fr_id', 'flights', 'departure_airport_id', 'arrival_airport_id']
    form_columns = ['departure_airport_id', 'arrival_airport_id', 'description']


class TicketAdminView(AuthenticatedView):
    can_export = True
    column_searchable_list = ['ticket_id']
    column_filters = ['ticket_id']
    can_view_details = True

    column_list = ['ticket_id', 'issue_date', 'ticket_price', 'ticket_status', 'ticket_gate', 'user_id', 'flight_id' ]
    form_columns = ['issue_date', 'ticket_price', 'ticket_status', 'ticket_gate', 'user_id', 'flight_id' ]

class LuggageAdminView(AuthenticatedView):
    column_list = ['luggage_id',  'luggage_name', 'weight', 'user_id', 'flight_id']
    form_columns = ['luggage_name', 'weight', 'user_id', 'flight_id']

class FlightScheduleAdminView(AuthenticatedView):
    column_list = ['schedule_id', 'flight_id', 'user_id']
    form_columns = ['flight_id', 'user_id']


class PlaneAdminView(AuthenticatedView):
    column_list = ['plane_id', 'plane_name']

class IntermediateAirportAdminView(AuthenticatedView):
    column_list = ['intermediate_id', 'flight_id', 'airport_id', 'stopover_duration', 'stop_order']
    form_columns = ['flight_id', 'airport_id', 'stopover_duration', 'stop_order']



class MyView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


class LogoutView(MyView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect('/admin')


class StatsView(MyView):
    @expose("/")
    def index(self):

        return self.render('admin/stats.html')

class HomeRedirectView(BaseView):
    @expose("/")
    def index(self):
        return redirect(url_for('index'))



admin.add_view(HomeRedirectView(name = 'Home page buy tickets'))
admin.add_view(FlightAdminView(Flight, db.session))
admin.add_view(FlightRouteAdminView(FlightRoute, db.session))
admin.add_view(PlaneAdminView(Plane, db.session))
admin.add_view(AuthenticatedView(Airport, db.session))
admin.add_view(TicketAdminView(Ticket, db.session))
admin.add_view(LuggageAdminView(Luggage, db.session))
admin.add_view(AuthenticatedView(Cancellation, db.session))
admin.add_view(AuthenticatedView(Payment, db.session))
admin.add_view(AuthenticatedView(Seat, db.session))
admin.add_view(FlightScheduleAdminView(FlightSchedule, db.session))
admin.add_view(AuthenticatedView(Company, db.session))
admin.add_view(IntermediateAirportAdminView(IntermediateAirport, db.session))
admin.add_view(StatsView(name = 'Stast'))
admin.add_view(LogoutView(name = 'Logout'))

