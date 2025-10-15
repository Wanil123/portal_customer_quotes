# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalQuotes(CustomerPortal):

    # -------- Utils --------
    def _get_lang_context(self):
        """Détermine la langue à utiliser (priorité: param > cookie > user > défaut)."""
        lang = (
            request.params.get('lang')
            or request.httprequest.cookies.get('frontend_lang')
            or request.env.user.lang
            or 'fr_CA'
        )
        # on ne touche pas à request.env; on retournera ce ctx aux .with_context(...)
        return dict(request.env.context, lang=lang)

    def _render(self, template, qcontext, ctx):
        """Rend un template QWeb avec un contexte de langue."""
        html = (
            request.env['ir.ui.view']
            .sudo()
            .with_context(ctx)
            ._render_template(template, qcontext)
        )
        resp = request.make_response(html)
        # cookie pour les prochaines requêtes (90 jours)
        resp.set_cookie('frontend_lang', ctx['lang'], max_age=60 * 60 * 24 * 90)
        return resp

    # -------- List --------
    @http.route(['/my/quotes'], type='http', auth='user', website=True)
    def portal_my_quotes(self, **kw):
        """Liste des soumissions (brouillon/envoyée)."""
        ctx = self._get_lang_context()
        partner = request.env.user.partner_id

        quotes = (
            request.env['sale.order']
            .sudo()
            .with_context(ctx)
            .search(
                [
                    ('partner_id', 'child_of', partner.commercial_partner_id.id),
                    ('state', 'in', ['draft', 'sent']),
                ],
                order='create_date desc',
                limit=80,
            )
        )

        qcontext = {'quotes': quotes, '_': _}
        return self._render('portal_customer_quotes.portal_my_quotes', qcontext, ctx)

    # -------- Validation --------
    def _validate_quote_post(self, post, order):
        g = lambda k: (post.get(k) or '').strip()
        errors = []

        if not g('x_project_description'):
            errors.append(_("Please provide the project description."))
        if not g('x_customer_reference'):
            errors.append(_("Please provide the customer reference."))
        if not g('x_expected_date'):
            errors.append(_("Please choose the expected delivery date."))
        if not g('x_delivery_method'):
            errors.append(_("Please choose a delivery method."))

        if g('x_delivery_method') == 'ship_qc':
            try:
                fee = float(g('x_shipping_fee') or 0.0)
                if fee < 0:
                    errors.append(_("Shipping fee must be a positive number."))
            except ValueError:
                errors.append(_("Shipping fee must be a number."))

        if post.get('action') == 'submit':
            if order and not order.order_line:
                errors.append(_("Add at least one product before submitting the quote."))

        return errors

    # -------- Form (create/edit) --------
    @http.route(['/my/quotes/new', '/my/quotes/<int:order_id>/edit'],
                type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_quote_form(self, order_id=None, **post):
        """Création/édition d'une soumission."""
        ctx = self._get_lang_context()
        partner = request.env.user.partner_id

        # recordset avec contexte (sans toucher à request.env directement)
        SaleOrder = request.env['sale.order'].sudo().with_context(ctx)
        SOLine = request.env['sale.order.line'].sudo().with_context(ctx)
        Product = request.env['product.product'].sudo().with_context(ctx)
        Category = request.env['product.category'].sudo().with_context(ctx)

        order = SaleOrder.browse(order_id).exists() if order_id else False

        # Sécurité d'accès
        if order and order.partner_id.commercial_partner_id != partner.commercial_partner_id:
            return request.redirect(f'/my/quotes?lang={ctx["lang"]}')

        # ----- POST -----
        if request.httprequest.method == 'POST':
            # création au besoin
            if not order:
                order = SaleOrder.create({
                    'partner_id': partner.commercial_partner_id.id,
                    'state': 'draft',
                })

            # champs simples
            vals = {}
            for k in ('x_project_description', 'x_customer_reference', 'x_expected_date',
                      'x_note', 'x_delivery_method'):
                if k in post:
                    vals[k] = post.get(k) or False

            # frais d'expédition
            if 'x_shipping_fee' in post:
                try:
                    vals['x_shipping_fee'] = float(post.get('x_shipping_fee') or 0.0)
                except ValueError:
                    vals['x_shipping_fee'] = 0.0

            if vals:
                order.write(vals)

            # ajout ligne produit
            if post.get('add_product'):
                try:
                    product_id = int(post['add_product'])
                    qty = float(post.get('add_qty', 1.0) or 1.0)
                except (ValueError, TypeError):
                    return request.redirect(f'/my/quotes/{order.id}/edit?lang={ctx["lang"]}')

                product = Product.browse(product_id).exists()
                if product:
                    line_name = product.get_product_multiline_description_sale() or product.display_name
                    SOLine.create({
                        'order_id': order.id,
                        'product_id': product.id,
                        'product_uom_qty': qty,
                        'price_unit': product.lst_price,
                        'name': line_name,
                    })
                return request.redirect(f'/my/quotes/{order.id}/edit?lang={ctx["lang"]}')

            # mise à jour des quantités
            for key, val in post.items():
                if key.startswith('set_qty_'):
                    try:
                        line_id = int(key.replace('set_qty_', ''))
                        qty = float(val or 0)
                    except (ValueError, TypeError):
                        continue
                    line = SOLine.browse(line_id).exists()
                    if line and line.order_id.id == order.id:
                        if qty > 0:
                            line.write({'product_uom_qty': qty})
                        else:
                            line.unlink()

            # suppression d'une ligne
            if post.get('rm_line'):
                try:
                    line_id = int(post['rm_line'])
                    line = SOLine.browse(line_id).exists()
                    if line and line.order_id.id == order.id:
                        line.unlink()
                except (ValueError, TypeError):
                    pass
                return request.redirect(f'/my/quotes/{order.id}/edit?lang={ctx["lang"]}')

            # validation / envoi
            action = post.get('action')
            if action in ('save', 'submit'):
                errors = self._validate_quote_post(post, order)
                if errors:
                    products = Product.search([('sale_ok', '=', True)], limit=400, order='name')
                    categories = Category.search([], order='complete_name')
                    qcontext = {
                        'quote': order,
                        'products': products,
                        'categories': categories,
                        'errors': errors,
                        '_': _,
                    }
                    return self._render('portal_customer_quotes.portal_quote_form', qcontext, ctx)

                if action == 'submit':
                    order.write({'state': 'sent'})
                return request.redirect(f'/my/quotes?lang={ctx["lang"]}')

        # ----- GET -----
        products = Product.search([('sale_ok', '=', True)], limit=400, order='name')
        categories = Category.search([], order='complete_name')
        qcontext = {
            'quote': order or False,
            'products': products,
            'categories': categories,
            'errors': [],
            '_': _,  # pour usages éventuels
        }
        return self._render('portal_customer_quotes.portal_quote_form', qcontext, ctx)

    # -------- Delete --------
    @http.route(['/my/quotes/<int:order_id>/delete'], type='http', auth='user',
                website=True, methods=['POST'])
    def portal_delete_quote(self, order_id=None, **post):
        """Suppression d'une soumission à l'état brouillon."""
        ctx = self._get_lang_context()
        partner = request.env.user.partner_id
        order = request.env['sale.order'].sudo().browse(order_id).exists()

        if (
            order
            and order.state == 'draft'
            and order.partner_id.commercial_partner_id == partner.commercial_partner_id
        ):
            order.unlink()

        return request.redirect(f'/my/quotes?lang={ctx["lang"]}')
