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
from natuurpunt_tools import get_eth0
from openerp import SUPERUSER_ID

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

    def _get_max_subs_amt(self, cr, uid, ids, name, args=None, context=None):
        result = dict.fromkeys(ids, False)
        for line in self.browse(cr, uid, ids, context=context):
            if not 'max_subs_amt' in context:
                # if max_subs_amt has already been overriden, don't calculate
                if not line.max_subs_amt_override:
                    result[line.id]= line.appr_amount_excl * line.subs_pct / 100
                else:
                    result[line.id] = line.max_subs_amt
            else:
                result[line.id]=context['max_subs_amt']
        return result

    def _set_max_subs_amt(self, cr, uid, id, name, value, args=None, context=None):
        return True

    def onchange_max_subs_amt(self, cr, uid, ids):
        res = {}
        res['max_subs_amt_override'] = True
        return {'value':res}

    _inherit = 'project.project'
    
    _columns = {
        'full_name': fields.text('Volledige naam', required=True, translate=True),
        'ident_nbr': fields.char('Ident. nummer', size=64),
        'seq': fields.many2one('ir.sequence', 'Volgnummer reeks', required=True, select=True ),
        'description': fields.text('Omschrijving'),
        'theme_general_ids': fields.many2many('project.theme.general', 'project_theme_general_rel', 'project_id', 'theme_general_id', 'Projects Themes General'),
        'theme_detail_ids': fields.many2many('project.theme.detail', 'project_theme_detail_rel', 'project_id', 'theme_detail_id', 'Project Themes Detail'),
        'contact_id': fields.many2one('res.users', 'Contactpersoon', select=True),
        'main_contractor_id': fields.many2one('res.partner', 'Hoofdopdrachtgever', select=True),
        'co_contractor_ids': fields.many2many('res.partner', 'project_co_contractor_rel', 'project_id', 'partner_id', 'Co Contractors'),
        'sub_contractor_ids': fields.many2many('res.partner', 'project_sub_contractor_rel', 'project_id', 'partner_id', 'Sub Contractors'),
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
        'max_subs_amt': fields.function(
                string='Maximum subsidiebedrag',
                fnct=_get_max_subs_amt,
                fnct_inv=_set_max_subs_amt,
                type='float',
                store=True,),
        'max_subs_amt_override': fields.boolean('max_subs_amt_override'),
        'reserv_ids': fields.many2many('res.partner', 'project_reserv_rel', 'project_id', 'partner_id', 'Project Reservaten'),
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
        'eindrapp': fields.boolean('Meenemen in eindrapportering', required=False),
        'ref_eindrapport': fields.text('Referenties eindrapporten'),
        'prijsherziening': fields.boolean('Prijsherziening'),
        'prijsherziening_comment': fields.text('Opmerking'),
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

    def write(self, cr, uid, ids, vals, context=None):
        # check if we want to override a calculated max_subs_amt value
        if 'max_subs_amt_override' not in vals:
            # check if we want to override an already overriden max_subs_amt value
            if 'max_subs_amt' in vals:
                context['max_subs_amt'] = vals['max_subs_amt']
            # recalculate overriden value if subs_pct changed
            elif 'subs_pct' in vals:
                vals['max_subs_amt_override'] = False
        else:
            context['max_subs_amt'] = vals['max_subs_amt']
        return super(project, self).write(cr, uid, ids, vals, context=context)

    def create(self, cr, uid, vals, context=None):
        if 'max_subs_amt_override' not in vals:
            vals['max_subs_amt_override'] = False
        else:
            if vals['max_subs_amt_override'] == True:
                context['max_subs_amt'] = vals['max_subs_amt']
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

class project_task_reminder(osv.osv_memory):

    _name = 'project.task.reminder'

    def send_project_task_reminders_email(self, cr, uid, user, msg_vals, context=None):
        """Send daily project task reminders via e-mail"""

        if user.email_work:
            try:
                data_obj = self.pool.get('ir.model.data')
                template = data_obj.get_object(cr, uid, 'natuurpunt_projects', 'email_template_project_tasks_reminder')
            except ValueError:
                raise osv.except_osv(_('Error!'),_("Cannot send email: no email template configured.\nYou can configure it under Settings/Technical/Email."))
            assert template._name == 'email.template'
            context['subject']   = msg_vals['subject']
            context['email_to']  = user.email_work
            context['body_html'] = msg_vals['body']
            context['body']      = msg_vals['body']
            context['res_id']    = False

            self.pool.get('email.template').send_mail(cr, uid, template.id, False, force_send=True, context=context)

        return True
    
    
    def generate_project_task_reminders(self, cr, uid, context=None):
        """Generates daily project task reminders"""
        if context == None:
            context = {}

        msg_obj = self.pool.get('mail.message')
        item_obj = self.pool.get('project.task')
        user_obj = self.pool.get('res.users')

        # we need to check all users
        users = user_obj.search(cr, uid, [])

        html_body_end = "<span><p><p/>"+_('Send from host %s - db %s')%(get_eth0(),cr.dbname)+"</span>"
        link = "<b><a href='{}?db={}#id={}&view_type=form&model={}&menu_id={}&action={}'>{}</a></b><br>"
        base_url = self.pool.get('ir.config_parameter').get_param(cr, SUPERUSER_ID, 'web.base.url')
        time_now = datetime.datetime.today().strftime('%Y-%m-%d')
        for user in user_obj.browse(cr, uid, users):

            task_items = []
            domain_filter = [('state', '!=', 'cancelled'),
                             ('state', '!=', 'done'),
                             ('user_id','=',user.id),
                             ('date_deadline','=',time_now)]

            items = item_obj.search(cr, uid, domain_filter)
            for item in item_obj.browse(cr, uid, items):
                task_items.append([item.id,item.name])

            context.update({'lang': user.lang})

            if task_items:
                task_items_links = ""
                for item in task_items:                 
                    task_items_links += link.format(base_url,cr.dbname,item[0],'project.task',288,336,item[1])
                body = _("You have {0} {1} {2}").format(len(task_items),_('project tasks with deadline today:<br>'),task_items_links)
                msg_vals = {
                    'subject': _("Deadline Project Task Reminder"),
                    'body': body + html_body_end,
                    'type': 'notification',
                    'notified_partner_ids': [(6,0,[user.partner_id.id])],
                }
                msg_obj.create(cr, uid, msg_vals)
                self.send_project_task_reminders_email(cr, uid, user, msg_vals, context=context)

        return True
    
