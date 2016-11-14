# -*- coding: utf-8 -*-
##############################################################################
#
#    Smart Solution bvba
#    Copyright (C) 2010-Today Smart Solution BVBA (<http://www.smartsolution.be>).
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
############################################################################## 

import base64
import ast
import datetime, re, random

from openerp.tools.translate import _
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class project_theme_general(osv.osv):
    _name = 'project.theme.general'
    _description = 'Project Theme General'

    _columns = {
        'name': fields.char('Naam', size=64, required=True, translate=True),
                }

project_theme_general()

class project_theme_detail(osv.osv):
    _name = 'project.theme.detail'
    _description = 'Project Theme Detail'

    _columns = {
        'name': fields.char('Naam', size=64, required=True, translate=True),
                }
 
project_theme_detail()
 
class project(osv.osv):

    _inherit = 'project.project'
    
    _columns = {
        'full_name': fields.text('Volledige naam', required=True, translate=True),
        'ident_nbr': fields.char('Ident. nummer', size=64),
        'seq': fields.many2one('ir.sequence', 'Volgnummer reeks', required=True, select=True ),
        'description': fields.text('Omschrijving'),
        'theme_general_ids': fields.many2many('project.theme.general', 'project_theme_general_rel', 'theme_general_id', 'project_id', 'Projects Themes General'),
        'theme_detail_ids': fields.many2many('project.theme.detail', 'project_theme_detail_rel', 'theme_detail_id', 'project_id', 'Project Themes Detail'),
        'contact_id': fields.many2one('res.partner', 'Contactpersoon', select=True),
        'main_contractor_id': fields.many2one('res.partner', 'Hoofdopdrachtgever', select=True),
        'co_contractor_ids': fields.many2many('res.partner', 'project_co_contractor_rel', 'partner_id', 'project_id', 'Co Contractors'),
        'sub_contractor_ids': fields.many2many('res.partner', 'project_sub_contractor_rel', 'partner_id', 'project_id', 'Sub Contractors'),
        'req_amount': fields.float('Aangevraagd bedrag', digits=(16,2)),
        'appr_amount_incl': fields.float('Goedgekeurd bedrag incl', digits=(16,2)),
        'appr_amount_excl': fields.float('Goedgekeurd bedrag', digits=(16,2)),
        'date_approved': fields.date('Datum goedgekeurd'),   
        'timesheet_required': fields.boolean('Tijdsregistratie verplicht'),                             
        'caution': fields.boolean('Borg', required=False),
        'caution_amt': fields.float('Borg bedrag', digits=(16,2)),
        'vat': fields.boolean('BTW'),
        'overhead_pct': fields.float('Overhead PCT', digits=(16,2)),                            
        'subs_pct': fields.float('Subsidie PCT', digits=(16,2)),
        'reserv_ids': fields.many2many('res.partner', 'project_reserv_rel', 'partner_id', 'project_id', 'Project Reservaten'),
        'user_agreement': fields.boolean('Gebruiksovereenkomst'),
        'partner_agreement': fields.boolean('Partnerovereenkomst'),
        'certif': fields.boolean('Certif. van goede uitvoering'),
        'subc_agreement': fields.boolean('Overeenkomst onderaanneming'),
        'project_state': fields.selection([
            ('draft', 'Ontwerp'),
            ('not_submitted', 'Niet Inged.'),
            ('submitted', 'Ingediend'),
            ('partial_approved', 'Deels Goedgek.'),
            ('approved', 'Goedgekeurd'),
            ('in_process', 'Lopend'),
            ('closed', 'Beëindigd'),
            ('refused', 'Afgekeurd'),
            ], 'Status', readonly=True, track_visibility='onchange', select=True),
        'company_id': fields.related('analytic_account_id', 'company_id', type="many2one", relation="res.company", string="Company", store=True),
        'project_code': fields.related('analytic_account_id', 'code', type="char", string="Project Code", store=True),
    }

    _defaults = {
        'project_state': 'draft',
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        res = super(project, self).onchange_partner_id(cr, uid, ids, partner_id)
    	res['value']['main_contractor_id'] = partner_id
        return res

    def onchange_vat(self, cr, uid, ids, amount_excl, vat):
        res = {}
        res['value'] = {}
        amount = 0.00
        if vat:
            amount = round((amount_excl * 1.21), 2)
    	res['value']['appr_amount_incl'] = amount
        return res

    def create(self, cr, uid, vals, context=None):
        print 'VALS:',vals
        
        if not 'analytic_account_id' in vals:
            seq_id = self.pool.get('ir.sequence').search(cr, uid, [('id','=', vals['seq'])])
            vals['code'] = self.pool.get('ir.sequence').next_by_id(cr, uid, seq_id, context)
        else:
            vals['seq'] = self.pool.get('ir.sequence').search(cr, uid, [('code', '=', 'project.project')])[0]
            vals['full_name'] = 'Volledige naam'
       
        return super(project, self).create(cr, uid, vals, context=context)

    def project_not_submitted(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'not_submitted'}, context=context)
        return True

    def project_submitted(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'submitted'}, context=context)
        return True

    def project_partial_approved(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'partial_approved'}, context=context)
        return True

    def project_approved(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'approved'}, context=context)
        return True

    def project_in_process(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'in_process'}, context=context)
        return True

    def project_reset_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'draft'}, context=context)
        return True

    def project_closed(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'closed'}, context=context)
        return True

    def project_refused(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'project_state': 'refused'}, context=context)
        return True

project() 
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
