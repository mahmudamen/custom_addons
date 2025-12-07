# from odoo import http


# class HospitalBase(http.Controller):
#     @http.route('/hospital_base/hospital_base', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hospital_base/hospital_base/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hospital_base.listing', {
#             'root': '/hospital_base/hospital_base',
#             'objects': http.request.env['hospital_base.hospital_base'].search([]),
#         })

#     @http.route('/hospital_base/hospital_base/objects/<model("hospital_base.hospital_base"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hospital_base.object', {
#             'object': obj
#         })

