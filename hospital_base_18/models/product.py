
from odoo import models, fields, api, _


class Product(models.Model):
    _inherit = 'product.template'

    hospital_product_type = fields.Selection([
        ('medicament', 'أدوية'),
        ('consumable', 'مستهلكات'),
        ('medical_service', 'خدمة طبية'),
        ('os', 'خدمات أخري'),
        ('accommodation', 'إقامة')
    ], string="نوع الصنف", tracking=True)
    is_contract = fields.Boolean(default=True, tracking=True, string="تعاقد")
    is_device = fields.Boolean(default=True, tracking=True, string="جهاز")
    available_in = fields.Selection([
        ('surgeries', 'عمليات'),
        ('clinic', 'عيادات خارجية'),
        ('inpatient', 'الداخلي'),
        ('icu', 'عناية مركزة'),
        ('laboratory', 'المعمل'),
        ('catheterization', 'القسطرة'),
        ('radiology', 'الاشعة'),
        ('nursing', 'تمريض')
    ], string="متاح في", tracking=True)
    service_exp_amount = fields.Float(default=0, digits='Product Price', tracking=True, string="مصروفات ادارية")
    service_tax_amount = fields.Float(default=0, digits='Product Price', tracking=True, string="ضريبة")
    can_be_installment = fields.Boolean(default=False, string="يمكن تقسيط القيمة")
    producing_company = fields.Char()
    brands = fields.Char()
    primary_supplier = fields.Char()
    primary_supplier_code = fields.Char()
    pro_barcode = fields.Char()
    # New Pharma-specific fields
    is_pharma = fields.Boolean(
        string="Pharma Product",
        default=False,
        tracking=True,
        help="Check if this is a pharmaceutical product"
    )
    old_items_id = fields.Char(string='old item id')


    # Optional: Add constraint to ensure only Pharma users can create/edit pharma products
    @api.constrains('is_pharma')
    def _check_pharma_product_access(self):
        for record in self:
            if record.is_pharma and not self.env.user.has_group('hospital_base.group_pharmacy_user'):
                raise models.ValidationError("Only Pharma Users can create or modify Pharma Products")
