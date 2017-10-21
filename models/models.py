# -*- coding: utf-8 -*-

from datetime import timedelta, datetime
from openerp.tools.safe_eval import safe_eval
from openerp import models, fields, api, _


class report_account_general_ledger(models.AbstractModel):
    _inherit = "account.general.ledger"
    
    def do_query(self, line_id, account_ids=None):
        
        select = ',COALESCE(SUM(\"account_move_line\".debit-\"account_move_line\".credit), 0),SUM(\"account_move_line\".amount_currency),SUM(\"account_move_line\".debit),SUM(\"account_move_line\".credit)'
        if self.env.context.get('cash_basis'):
            select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        sql = "SELECT \"account_move_line\".account_id%s FROM %s WHERE %s%s GROUP BY \"account_move_line\".account_id"

        # add domain to _get_query 
        domain = [('account_id', 'in', account_ids)] if account_ids else None
        
        tables, where_clause, where_params = self.env['account.move.line']._query_get(domain=domain)
        line_clause = line_id and ' AND \"account_move_line\".account_id = ' + str(line_id) or ''
        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        results = dict([(k[0], {'balance': k[1], 'amount_currency': k[2], 'debit': k[3], 'credit': k[4]}) for k in results])
        return results    
    
    def group_by_account_id(self, line_id, account_ids=None):
        accounts = {}
        results = self.do_query(line_id, account_ids)
        initial_bal_date_to = datetime.strptime(self.env.context['date_from_aml'], "%Y-%m-%d") + timedelta(days=-1)
        initial_bal_results = self.with_context(date_to=initial_bal_date_to.strftime('%Y-%m-%d')).do_query(line_id)
        context = self.env.context
        base_domain = [('date', '<=', context['date_to']), ('company_id', 'in', context['company_ids'])]
        if context.get('journal_ids'):
            base_domain.append(('journal_id', 'in', context['journal_ids']))
        if context['date_from_aml']:
            base_domain.append(('date', '>=', context['date_from_aml']))
        if context['state'] == 'posted':
            base_domain.append(('move_id.state', '=', 'posted'))
        for account_id, result in results.items():
            domain = list(base_domain)  # copying the base domain
            domain.append(('account_id', '=', account_id))
            account = self.env['account.account'].browse(account_id)
            accounts[account] = result
            accounts[account]['initial_bal'] = initial_bal_results.get(account.id, {'balance': 0, 'amount_currency': 0, 'debit': 0, 'credit': 0})
            
            # removed limit=81 from the parent function. limit=81
            accounts[account]['lines'] = self.env['account.move.line'].search(domain, order='date') 
        return accounts
    
    @api.model
    def get_lines(self, context_id, line_id=None):
        if type(context_id) == int:
            context_id = self.env['account.context.general.ledger'].search([['id', '=', context_id]])
        new_context = dict(self.env.context)
        new_context.update({
            'date_from': context_id.date_from,
            'date_to': context_id.date_to,
            'state': context_id.all_entries and 'all' or 'posted',
            'cash_basis': context_id.cash_basis,
            'context_id': context_id,
            'company_ids': context_id.company_ids.ids,
            'journal_ids': context_id.journal_ids.ids,
            'account_ids': context_id.account_ids.ids
        })
        return self.with_context(new_context)._lines(line_id)    
    
    @api.model
    def _lines(self, line_id=None):
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        grouped_accounts = self.with_context(
                date_from_aml=context['date_from'], 
                date_from=context['date_from'] and company_id.compute_fiscalyear_dates(datetime.strptime(context['date_from'], "%Y-%m-%d"))['date_from'] or None
            ).group_by_account_id(line_id, self.env.context['account_ids'])  # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
        sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
        unfold_all = context.get('print_mode') and not context['context_id']['unfolded_accounts']
        for account in sorted_accounts:
            debit = grouped_accounts[account]['debit']
            credit = grouped_accounts[account]['credit']
            balance = grouped_accounts[account]['balance']
            amount_currency = '' if not account.currency_id else grouped_accounts[account]['amount_currency']
            lines.append({
                'id': account.id,
                'type': 'line',
                'name': account.code + " " + account.name,
                'footnotes': self.env.context['context_id']._get_footnotes('line', account.id),
                'columns': ['', '', '', amount_currency, self._format(debit), self._format(credit), self._format(balance)],
                'level': 2,
                'unfoldable': True,
                'unfolded': account in context['context_id']['unfolded_accounts'] or unfold_all,
                'colspan': 4,
            })
            if account in context['context_id']['unfolded_accounts'] or unfold_all:
                progress = 0
                domain_lines = []
                amls = grouped_accounts[account]['lines']
                too_many = False
                
                ''' 
                :NOTE We don't want limit 80
                '''           
#                 if len(amls) > 80 and not context.get('print_mode'):
#                     amls = amls[-80:]
#                     too_many = True
                for line in amls:
                    if self.env.context['cash_basis']:
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit
                    progress = progress + line_debit - line_credit
                    currency = "" if not line.account_id.currency_id else line.amount_currency
                    name = []
                    name = line.name and line.name or ''
                    if line.ref:
                        name = name and name + ' - ' + line.ref or line.ref
                    if len(name) > 35:
                        name = name[:32] + "..."
                    partner_name = line.partner_id.name
                    if partner_name and len(partner_name) > 35:
                        partner_name = partner_name[:32] + "..."
                    domain_lines.append({
                        'id': line.id,
                        'type': 'move_line_id',
                        'move_id': line.move_id.id,
                        'action': line.get_model_id_and_name(),
                        'name': line.move_id.name if line.move_id.name else '/',
                        'footnotes': self.env.context['context_id']._get_footnotes('move_line_id', line.id),
                        'columns': [line.date, name, partner_name, currency,
                                    line_debit != 0 and self._format(line_debit) or '',
                                    line_credit != 0 and self._format(line_credit) or '',
                                    self._format(progress)],
                        'level': 1,
                    })
                initial_debit = grouped_accounts[account]['initial_bal']['debit']
                initial_credit = grouped_accounts[account]['initial_bal']['credit']
                initial_balance = grouped_accounts[account]['initial_bal']['balance']
                initial_currency = '' if not account.currency_id else grouped_accounts[account]['initial_bal']['amount_currency']
                domain_lines[:0] = [{
                    'id': account.id,
                    'type': 'initial_balance',
                    'name': _('Initial Balance'),
                    'footnotes': self.env.context['context_id']._get_footnotes('initial_balance', account.id),
                    'columns': ['', '', '', initial_currency, self._format(initial_debit), self._format(initial_credit), self._format(initial_balance)],
                    'level': 1,
                }]
                domain_lines.append({
                    'id': account.id,
                    'type': 'o_account_reports_domain_total',
                    'name': _('Total ') + account.name,
                    'footnotes': self.env.context['context_id']._get_footnotes('o_account_reports_domain_total', account.id),
                    'columns': ['', '', '', amount_currency, self._format(debit), self._format(credit), self._format(balance)],
                    'level': 1,
                })
                if too_many:
                    domain_lines.append({
                        'id': account.id,
                        'type': 'too_many',
                        'name': _('There are more than 80 items in this list, click here to see all of them'),
                        'footnotes': [],
                        'colspan': 8,
                        'columns': [],
                        'level': 3,
                    })
                lines += domain_lines
        return lines
    
    
class account_context_general_ledger(models.TransientModel):
    _description = "A particular context for the general ledger"
    _inherit = "account.context.general.ledger"
    
    @api.model
    def company_accounts(self):
        
        company_ids = self.company_ids.ids or [self.env.user.company_id.id]
        account_ids = self.env['account.account'].search([('company_id', 'in', company_ids)])
        return [(6, 0, account_ids.ids)]    

    account_ids = fields.Many2many('account.account', relation='account_report_gl_accounts', default=company_accounts)
    available_account_ids = fields.Many2many('account.account', relation='account_report_gl_available_accounts', default=company_accounts)

    @api.multi
    def get_available_account_ids_and_names(self):
        company_ids = self.company_ids.ids or [self.env.user.company_id.id]
        account_ids = self.env['account.account'].search([('company_id', 'in', company_ids)])        
        return [[c.id, c.name] for c in account_ids]

    @api.model
    def get_available_accounts(self):
        return self.env.user.account_ids

    def get_report_obj(self):
        return self.env['account.general.ledger']

    @api.multi
    def get_html_and_data(self, given_context=None):
        result = super(account_context_general_ledger, self).get_html_and_data(given_context)
         
        if self.get_report_obj().get_name() == 'general_ledger':
            print self.read(['account_ids'])
            print self.get_available_account_ids_and_names()
            result['report_context'].update( self.read(['account_ids'])[0] )
            result['available_accounts'] = self.get_available_account_ids_and_names()    
            
        return result