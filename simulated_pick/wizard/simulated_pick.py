# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#    
#    Copyright (C) 2014 Asphalt Zipper, Inc.
#    Author scosist
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import time
import openerp.addons.decimal_precision as dp
from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class simulated_pick(models.TransientModel):
    _name = 'simulated.pick'
    _description = 'Material Requirements Calculator'

    product_id = fields.Many2one('product.product', 'Product', required=True, domain=[('type','!=','service'),('bom_ids', '!=', False),('bom_ids.type','!=','phantom')])
    product_qty = fields.Float('Product Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    date_planned = fields.Date('Scheduled Date', required=True, select=1, copy=False, default=time.strftime('%Y-%m-%d'))
    
    # method in the old API style
    #def _action_compute_lines(self, cr, uid, product_id, product_qty, pick_results=None, properties=None, initial_run=0, context=None):
    @api.model
    def _action_compute_lines(self, product_id, product_qty, pick_results=None, properties=None, initial_run=0):
        #context = self._context
        self = self.with_context(to_date=self.date_planned)
        if properties is None:
            properties = []
        results = []
        bom_obj = self.pool.get('mrp.bom')
        uom_obj = self.pool.get('product.uom')
        prod_obj = self.pool.get('product.product')
        pick_obj = self.pool.get('simulated.pick.product')
        stock_loc_obj = self.pool.get('stock.location.route')
        bom = self.env['mrp.bom']
        uom = self.env['product.uom']
        prod = self.env['product.product']
        pick_prod = self.env['simulated.pick.product']
        route = self.env['stock.location.route']

        #bom_id = bom_obj._bom_find(cr, uid, product_id=product_id)
        bom_id = bom._bom_find(product_id=product_id)
        if bom_id:
            #bom_point = bom_obj.browse(cr, uid, bom_id)
            bom_point = bom.browse(bom_id)
        else:
            raise exceptions.except_orm(_('Error!'), _("Cannot find a bill of materials for this product."))

        pick_results = pick_results or {}
        #for p in prod_obj.browse(cr, uid, product_id, context=context):
        #    factor = uom_obj._compute_qty(cr, uid, p.uom_id.id, product_qty, bom_point.product_uom.id)
        #    results, results2 = bom_obj._bom_explode(cr, uid, bom_point, product_id, factor / bom_point.product_qty, properties, context=context)
        for p in prod.browse(product_id):
            factor = uom._compute_qty(p.uom_id.id, product_qty, bom_point.product_uom.id)
            results, results2 = bom._bom_explode(bom_point, product_id, factor / bom_point.product_qty, properties)

            if initial_run:
                #diff = p.virtual_available-context.get('product_qty')
                diff = p.virtual_available-self.product_qty
                new_pick = {
                    'product_id': p.id,
                    'name': p.product_tmpl_id.name,
                    'default_code': p.default_code,
                    'product_uom': p.product_tmpl_id.uom_id.id,
                    'categ_id': p.product_tmpl_id.categ_id.id,
                    #'route_name': stock_loc_obj.browse(cr, uid, p.product_tmpl_id.route_ids.id, context=context).name,
                    #'product_qty': context.get('product_qty'),
                    'route_name': route.browse(p.product_tmpl_id.route_ids.id).name,
                    'product_qty': self.product_qty,
                    'on_hand_before': p.virtual_available,
                    'on_hand_after': diff,
                    'short': -(diff) if diff < 0 else 0,
                }
                pick_results[new_pick['product_id']] = new_pick

            for line in results:
                #p = prod_obj.browse(cr, uid, line['product_id'], context=context)
                #p = self.env['product.product'].browse(line['product_id']).with_context(self._context)
                p = prod.browse(line['product_id'])
                if line['product_id'] in pick_results and line['product_id'] == pick_results[line['product_id']]['product_id']:
                    pick_results[line['product_id']]['product_qty'] += line['product_qty']
                    diff = p.virtual_available-pick_results[line['product_id']]['product_qty']
                    pick_results[line['product_id']]['on_hand_after'] = diff
                    pick_results[line['product_id']]['short'] = -(diff) if diff < 0 else 0
                else:
                    diff = p.virtual_available-line['product_qty']
                    line['default_code'] = p.default_code
                    line['categ_id'] = p.product_tmpl_id.categ_id.id
                    #line['route_name'] = stock_loc_obj.browse(cr, uid, p.product_tmpl_id.route_ids.id, context=context).name
                    line['route_name'] = route.browse(p.product_tmpl_id.route_ids.id).name
                    line['on_hand_before'] = p.virtual_available
                    line['on_hand_after'] = diff
                    line['short'] = -(diff) if diff < 0 else 0
                    pick_results[line['product_id']] = line

                #bom_id = bom_obj._bom_find(cr, uid, product_id=line['product_id'])
                bom_id = bom._bom_find(product_id=line['product_id'])
                if bom_id:
                    #self._action_compute_lines(cr, uid, line['product_id'], line['product_qty'], pick_results, context=context)
                    self._action_compute_lines(line['product_id'], line['product_qty'], pick_results)

        return pick_results


    # method in the new API style
    @api.model
    def _new_action_compute_lines(self, product_id, product_qty, pick_results=None, properties=None, initial_run=0):
        self._action_compute_lines(self, self._cr, self.env.user, product_id, product_qty, pick_results, properties, initial_run, context = self._context)


    #def action_compute(self, cr, uid, ids, context=None):
    @api.multi
    def action_compute(self):
        """
            @param cr: the current row, from the database cursor,
            @param uid: the current user ID for security checks,
            @param ids: the ID or list of IDs if we want more than one

            @return:
        """
        #context = dict(context or {})
        context = self._context

        def ref(module, xml_id):
            #proxy = self.pool.get('ir.model.data')
            #return proxy.get_object_reference(cr, uid, module, xml_id)
            proxy = self.env['ir.model.data']
            return proxy.get_object_reference(module, xml_id)

        model, search_view_id = ref('simulated_pick', 'simulated_pick_product_search_form_view')
        model, tree_view_id = ref('simulated_pick', 'simulated_pick_product_tree_view')

        # get the current simulated.pick object to obtain the values
        #records = self.browse(cr, uid, ids, context=context)
        #record = records[0]

        #context.update(product_id=record.product_id.id)
        #context.update(product_qty=record.product_qty)
        #context.update(date_planned=record.date_planned)
        # add from_date, to_date for _product_available > _get_domain_dates
        #context.update(to_date=self.date_planned)

        #pick_obj = self.pool.get('simulated.pick.product')
        #all_pick_ids = pick_obj.search(cr, uid, [('create_uid', '=', uid)])
        pick_obj = self.env['simulated.pick.product']
        all_pick_ids = pick_obj.search([('create_uid', '=', self._uid)])
        # delete any existing records in simulated.pick.product for current uid
        if all_pick_ids:
            #pick_obj.unlink(cr, uid, all_pick_ids)
            all_pick_ids.unlink()

        #all_picks = self._action_compute_lines(cr, uid, record.product_id.id, record.product_qty, initial_run=1, context=context)
        #all_picks = self._action_compute_lines(record.product_id.id, record.product_qty, initial_run=1)
        #all_picks = self._action_compute_lines(self.product_id.id, self.product_qty, initial_run=1).with_context(product_id=self.product_id.id, product_qty=self.product_qty, date_planned=self.date_planned, to_date=self.date_planned)
        all_picks = self._action_compute_lines(self.product_id.id, self.product_qty, initial_run=1)
        for key, pick in all_picks.iteritems():
            #pick_obj.create(cr, uid, pick)
            pick_obj.create(pick)

        views = [
            (tree_view_id, 'tree'),
        ]

        return {
            'name': _('Requirements Calculator'),
            #'domain': [('create_uid', '=', uid)],
            'domain': [('create_uid', '=', self._uid)],
            'context': context,
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'simulated.pick.product',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
            'search_view_id': search_view_id,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
