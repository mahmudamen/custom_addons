# -*- coding: utf-8 -*-
# from odoo import http


# class HighDamHr(http.Controller):
#     @http.route('/high_dam_hr/high_dam_hr', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/high_dam_hr/high_dam_hr/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('high_dam_hr.listing', {
#             'root': '/high_dam_hr/high_dam_hr',
#             'objects': http.request.env['high_dam_hr.high_dam_hr'].search([]),
#         })

#     @http.route('/high_dam_hr/high_dam_hr/objects/<model("high_dam_hr.high_dam_hr"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('high_dam_hr.object', {
#             'object': obj
#         })
