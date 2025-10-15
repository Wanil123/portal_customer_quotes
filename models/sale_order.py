# -*- coding: utf-8 -*-
from odoo import models, fields
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Custom fields for quote form
    x_project_description = fields.Text(string='Project Description')
    x_customer_reference = fields.Char(string='Customer Reference')
    x_expected_date = fields.Date(string='Expected Delivery Date')
    x_note = fields.Text(string='Additional Notes')
    x_delivery_method = fields.Selection([
        ('pickup', 'In-Store Pickup'),
        ('ship_qc', 'Shipping in Quebec'),
    ], string='Delivery Method')
    x_shipping_fee = fields.Float(string='Shipping Fee', default=0.0)