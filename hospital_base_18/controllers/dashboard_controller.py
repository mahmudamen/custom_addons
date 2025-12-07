from odoo import http
from odoo.http import request
import json

class DashboardController(http.Controller):
    @http.route('/hospital/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self, filter_date='today'):
        dashboard = request.env['hospital.dashboard']
        return dashboard.get_dashboard_data(filter_date)
