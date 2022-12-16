# -*- coding: utf-8 -*-

from ast import literal_eval
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError
import tempfile
from base64 import encodebytes
import re
from datetime import datetime, date, timedelta
from io import BytesIO
from importlib import reload
# from imp import reload
import sys
from num2words import num2words
import logging
_logging = logging.getLogger(__name__)


try:
    import qrcode
    qr_mod = True
except:
    qr_mod = False

TYPE2JOURNAL = {'out_invoice': 'sale',
                'in_invoice': 'purchase',  'out_refund': 'sale',
                'in_refund': 'purchase'}


class AccountMove(models.Model):
    _inherit = 'account.move'

    pa_dgi_type_emission = fields.Selection(
        selection=[
            ('01', '[01] Autorización de Uso Previa, operación normal'),
            ('02', '[02] Autorización de Uso Previa, operación en contingencia'),
            ('03', '[03] Autorización de Uso Posterior, operación normal.'),
            ('04', '[04] Autorización de Uso posterior, operación en contingencia.')
        ],
        string="Tipo de Emisión",
        store=True, readonly=False,
        compute='_compute_l10n_pa_edi_emission_type')
    pa_dgi_date_contingency = fields.Datetime(
        'Fecha/Hora de Contingencia', copy=False, help="Obligatorio si, tipoEmision = 02 / 04")
    pa_dgi_reason_contingency = fields.Char('Motivo de Contingencia', copy=False,
                                            help="Obligatorio si tipoEmision=02 / 04 Si la contingencia dura más de 72 horas también debe explicar las razones para no haber regresado a la operación normal.")
    pa_dgi_nature_operation = fields.Selection(
        selection=[
            ('01', 'Venta'),
            ('02', 'Exportación'),
            ('10', 'Transferencia'),
            ('11', 'Devolución'),
            ('12', 'Consignación'),
            ('13', 'Remesa'),
            ('14', 'Entrega gratuita'),
            ('20', 'Compra'),
            ('21', 'Importación'),
        ],
        string='Naturaleza de la Operacion',
        default='01', readonly=True, states={'draft': [('readonly', False)]})
    pa_dgi_type_operation = fields.Selection(
        selection=[
            ('1', 'Salida o venta'),
            ('2', 'Entrada o compra (factura de compra- para comercio informal. Ej.: taxista, trabajadores manuales)')
        ],
        string='Tipo de Operación',
        default='1', readonly=True, states={'draft': [('readonly', False)]})
    pa_dgi_destiny_operation = fields.Selection(
        selection=[
            ('1', 'Panamá'),
            ('2', 'Extranjero')
        ],
        string='Destino de la Operación',
        default='1', readonly=True, states={'draft': [('readonly', False)]})
    pa_dgi_type_sale = fields.Selection(
        selection=[
            ('1', 'Venta de Giro del negocio'),
            ('2', 'Venta Activo Fijo'),
            ('3', 'Venta de Bienes Raíces.'),
            ('4', 'Prestación de Servicio'),
        ],
        string='Tipo de Venta',
        help='Tipo de Venta para el vendedor. Si no es venta, no informar este campo',
        default='1', readonly=True, states={'draft': [('readonly', False)]})
    pa_payment_journal_id = fields.Many2one('account.journal', 'Metodo de Pago', readonly=True, states={
                                            'draft': [('readonly', False)]}, domain="[('pa_payment_method', '!=', False)]")
    pa_document_type = fields.Many2one(
        'l10n_latam.document.type', string='Tipo de Documento FE')

    pa_payment_method = fields.Selection(
        selection=[
            ('01', 'Crédito'),
            ('02', 'Contado'),
            ('03', 'Tarjeta Crédito'),
            ('04', 'Tarjeta Débito'),
            ('05', 'Tarjeta Fidelización'),
            ('06', 'Vale'),
            ('07', 'Tarjeta de Regalo'),
            ('08', 'Transf/Deposito cta Bancaria '),
            ('99', 'Otro.'),
        ],
        string='Método de pago para DGI',
        help='Método de pago para envio de FE-DGI')
    cancellation_reason = fields.Char(
        'Motivo de Anulación', readonly=True,  copy=False)
    pa_edocument_id = fields.Many2one('odoopanama.cpe',
                                      'PAC CPE', states={'draft': [('readonly', False)]}, copy=False)
    pa_response = fields.Char('Respuesta', related='pa_edocument_id.response')
    is_cpe = fields.Boolean('Es CPE', related='journal_id.is_cpe')
    pa_voided_id = fields.Many2one('odoopanama.cpe', 'Documento anulado', states={'cancel': [('readonly', False)]},
                                   copy=False)

    @api.depends('move_type', 'company_id')
    def _compute_l10n_pa_edi_emission_type(self):
        for move in self:
            move.pa_dgi_type_emission = '01'

    pa_doc_name = fields.Char('Nombre del documento',
                              compute='_get_panamanian_doc_name')
    pa_invoice_state = fields.Selection(
        string='Estado cpe',
        related='pa_edocument_id.state',
        copy=False)
    state_dgi = fields.Char(string='Estado DGI',
                            related='pa_edocument_id.response_code')
    pa_invoice_date = fields.Datetime('Hora/fecha de la factura', copy=False)
    dgi_qr_code = fields.Binary(
        'QR Code Sunat', compute='_compute_get_qr_code')
    pe_total_discount = fields.Float(
        'Descuento total', compute='_compute_discount')
    pe_amount_discount = fields.Monetary(string='Descuento',
                                         compute='_compute_discount',
                                         tracking=True)
    pe_total_discount_tax = fields.Monetary(string='Impuesto de descuento',
                                            compute='_compute_discount',
                                            tracking=True)
    pe_charge_total = fields.Monetary('Precio a cobrar',
                                      compute='get_pe_charge_amount', currency_field='company_currency_id')
    pe_payment_lines = fields.One2many('pe.payment.date', 'move_id', 'Payment Lines',  readonly=True, states={
        'draft': [('readonly', False)]})
    pe_qty_fees = fields.Integer("Cantidad de Cuotas", default=1, readonly=True, states={
                                 'draft': [('readonly', False)]}, copy=False)
    from_wizard_revert = fields.Boolean()

    @api.model
    def _l10n_pe_edi_amount_to_text(self):
        """Transform a float amount to text words on panamanian format: AMOUNT IN TEXT 11/100
        :returns: Amount transformed to words panamanian format for invoices
        :rtype: str
        """
        self.ensure_one()
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = int(round(amount_d * 100, 2))
        words = num2words(amount_i, lang='es')
        result = '%(words)s Y %(amount_d)02d/100 %(currency_name)s' % {
            'words': words,
            'amount_d': amount_d,
            'currency_name':  self.currency_id.currency_unit_label,
        }
        return result.upper()

    def generate_pe_fees(self):
        self.ensure_one()
        if self.pe_qty_fees <= 0:
            raise UserError(_("Las cuotas deben ser superiores a cero"))
        elif self.amount_total <= 0.0:
            raise UserError(_("El total debe ser mayor que cero"))
        if self.invoice_date == self.invoice_date_due:
            raise UserError(
                _("La fecha de la factura debe ser diferente a la fecha de vencimiento."))
        pe_start_date = self.invoice_date or fields.Date.context_today(self)
        pe_payment_date_start = pe_start_date
        pe_payment_date_end = self.invoice_date_due or fields.Date.context_today(
            self)
        self.pe_payment_lines.unlink()
        context = dict(self.env.context)
        context['pe_payment_date_start'] = pe_payment_date_start
        context['pe_payment_date_end'] = pe_payment_date_end
        context['pe_payment_qty'] = self.pe_qty_fees
        context['pa_payment_method'] = self.pa_payment_method
        context['pe_payment_amount'] = self.amount_total
        pe_payment_lines = self.env['pe.payment.date'].with_context(
            **context).get_payment_by_qty_date()
        self.pe_payment_lines = pe_payment_lines

    def _get_address_details(self, partner):
        self.ensure_one()
        address = ''
        if partner.l10n_pa_corregimiento:
            address = "%s" % (partner.l10n_pa_corregimiento.name)
        if partner.city:
            address += ", %s" % (partner.city)
        if partner.state_id.name:
            address += ", %s" % (partner.state_id.name)
        if partner.zip:
            address += ", %s" % (partner.zip)
        if partner.country_id.name:
            address += ", %s" % (partner.country_id.name)
        reload(sys)
        html_text = str(tools.plaintext2html(address, container_tag=True))
        data = html_text.split('p>')
        if data:
            return data[1][:-2]
        return False

    def _get_street(self, partner):
        self.ensure_one()
        address = ''
        if partner.street:
            address = "%s" % (partner.street)
        if partner.street2:
            address += ", %s" % (partner.street2)
        reload(sys)
        html_text = str(tools.plaintext2html(address, container_tag=True))
        data = html_text.split('p>')
        if data:
            return data[1][:-2]
        return False

    @api.model
    def get_pe_charge_amount(self):
        for invoice_id in self:
            pe_charge_total = 0.0
            for line in invoice_id.invoice_line_ids.filtered(lambda line: not line.display_type):
                pe_charge_total += line.pe_charge_amount

            invoice_id.pe_charge_total = pe_charge_total

    @api.onchange('invoice_date')
    def onchange_pa_invoice_date(self):
        self.action_date_assign()

    @api.model
    def action_date_assign(self):
        for inv in self:
            today = fields.Date.context_today(self)
            if not inv.invoice_date:
                inv.pa_invoice_date = today
            else:
                local_date = fields.Date.from_string(today)
                dt = local_date == fields.Date.from_string(
                    inv.invoice_date) and today or str(inv.invoice_date) + ' 23:55:00'
                inv.pa_invoice_date = dt

    @api.depends('amount_total', 'currency_id', 'invoice_line_ids', 'invoice_line_ids.amount_discount')
    def _compute_discount(self):
        total_discount = 0.0
        ICPSudo = self.env['ir.config_parameter'].sudo()
        default_deposit_product_id = literal_eval(ICPSudo.get_param('sale.default_deposit_product_id',
                                                                    default='False'))
        discount = 0.0
        total_discount_tax = 0.0
        for line in self.invoice_line_ids.filtered(lambda line: not line.display_type):
            if line.price_total < 0.0:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price, self.currency_id, line.quantity, line.product_id, self.partner_id)
                if default_deposit_product_id:
                    if default_deposit_product_id != line.product_id.id:
                        if taxes:
                            for tax in taxes.get('taxes', []):
                                total_discount_tax += tax.get('amount', 0.0)

                        total_discount += line.price_total
                if not default_deposit_product_id:
                    total_discount += line.price_total
                    if taxes:
                        for tax in taxes.get('taxes', []):
                            total_discount_tax += tax.get('amount', 0.0)

            discount += line.amount_discount

        self.pe_total_discount = abs(total_discount)
        self.pe_total_discount_tax = abs(total_discount_tax)
        self.pe_amount_discount = discount

    @api.depends('l10n_latam_document_type_id')
    def _get_panamanian_doc_name(self):
        for invoice_id in self:
            if invoice_id.l10n_latam_document_type_id:
                pa_doc_name = invoice_id.l10n_latam_document_type_id and invoice_id.l10n_latam_document_type_id.name or ''
                invoice_id.pa_doc_name = pa_doc_name.title()
            else:
                invoice_id.pa_doc_name = ""

    @api.depends('name', 'journal_id.is_cpe', 'pa_edocument_id')
    def _compute_get_qr_code(self):
        for invoice in self:
            if not all((invoice.name != '/', invoice.journal_id.is_cpe, invoice.pa_edocument_id.note, qr_mod)):
                invoice.dgi_qr_code = ''
            else:
                if invoice.pa_edocument_id.note and invoice.journal_id.is_cpe:
                    qr_string = str(invoice.pa_edocument_id.note)
                    qr = qrcode.QRCode(version=1,
                                    error_correction=(qrcode.constants.ERROR_CORRECT_Q))
                    qr.add_data(qr_string)
                    qr.make(fit=True)
                    image = qr.make_image(fill='black')
                    tmpf = BytesIO()
                    image.save(tmpf, 'png')
                    invoice.dgi_qr_code = encodebytes(tmpf.getvalue())
                else:
                    invoice.dgi_qr_code = ''

    def _validate_pe_fees(self):
        if not self.invoice_date == self.invoice_date_due and len(self.pe_payment_lines) < 1:
            if self.pe_qty_fees < 2:
                self.generate_pe_fees()
            else:
                if len(self.pe_payment_lines) < 2:
                    note = "Ud. Asignó {} cuotas. Por favor detalle las fechas y los montos de las cuotas de crédito".format(
                        self.pe_qty_fees)
                    raise UserError((note))

    def validate_dgi_invoice(self):
        lines = self.invoice_line_ids.filtered(
            lambda line: not line.display_type)
        doc_type = self.partner_id.l10n_latam_identification_type_id.l10n_pa_vat_code
        is_government = True if doc_type == '03' else False
        for line in lines:
            if not line.tax_ids:
                if line.quantity > 0:
                    raise UserError(
                        'Es Necesario definir por lo menos un impuesto para el producto %s' % line.name)
            if is_government and not line.product_id.pa_unspsc_code_id:
                raise UserError(
                    'El cliente {} Es una entidad Gubernamental\nEs necesario asignar un código UNSPSC en el producto: {}'.format(self.partner_id.name,line.product_id.name))
            
        if doc_type == '01' and not self.partner_id.l10n_pa_corregimiento:
            raise UserError(
                'Ingrese el Corregimiento del Cliente: {}'.format(self.partner_id.name))
        if not self.pa_payment_method:
            raise UserError(
                'Seleccione un método de pago.')
        # if not self.pa_payment_journal_id.pa_payment_method:
        #     raise UserError(
        #         'Configure el método de pago seleccionado en: \n (Diarios Contables/Configuracion Panameña)')

        if self.partner_id.parent_id and self.partner_id.vat:
            raise UserError(
                'Para generar este comprobante debe cambiar los datos  de contacto {} \nPor los datos de la Empresa principal {}'.format(self.partner_id.name, self.partner_id.parent_id.name))
        if not self.partner_id.vat and doc_type in ('01','03'):
            raise UserError('El cliente {}, no tiene asignado un número de documento'.format(
                self.partner_id.name))

        if self.l10n_latam_document_type_id.code in ('03', ) or self.reversed_entry_id.l10n_latam_document_type_id.code in ('03', ):
            doc_type = doc_type or "-"
            vat = self.partner_id.vat or '-'
            if doc_type == '6':
                raise UserError('El dato ingresado no cumple con el estandar \nTipo: %s \nNumero de documento: %s\nDeberia emitir una Factura. Cambiar en Factura/Otra Informacion/Diario' % (
                    doc_type, vat))
            amount = 700.00
            if self.amount_total >= amount and (doc_type == '0' or vat == '0'):
                raise UserError('El monto de la venta supera los S/ 700, debe elegir un cliente con DNI o RUC valido. \nTipo: %s \nNumero de documento: %s' % (
                    doc_type, vat))

        if self.l10n_latam_document_type_id.code in ('01', ) or self.reversed_entry_id.l10n_latam_document_type_id.code in ('01', ):
            doc_type = doc_type or self.partner_id.parent_id.l10n_latam_identification_type_id.l10n_pa_vat_code or "-"
            vat = self.partner_id.vat or self.partner_id.parent_id.vat or '-'
        date_invoice = fields.Datetime.from_string(
            self.pa_invoice_date or self.invoice_date)
        today = fields.Datetime.context_timestamp(self, datetime.now())
        days = today.replace(tzinfo=None) - date_invoice
        if days.days > 6 and (self.l10n_latam_document_type_id.code in ('01',) or self.reversed_entry_id.l10n_latam_document_type_id.code in ('01',)):
            raise UserError(
                'La fecha de emision no puede ser menor a 6 dias de hoy ni mayor a la fecha de hoy.')
        if days.days < 0:
            raise UserError(
                'La fecha de emision no puede ser menor a 6 dias de hoy ni mayor a la fecha de hoy.')
        company_id = self.company_id.partner_id

    @api.depends('l10n_latam_available_document_type_ids', 'debit_origin_id')
    def _compute_l10n_latam_document_type(self):
        debit_note = self.debit_origin_id
        document_type_fe = False
        for rec in self.filtered(lambda x: x.state == 'draft'):
            if rec.pa_dgi_destiny_operation == "2":
                document_type_fe = self.env['l10n_latam.document.type'].search([('code', '=', '03')])
            document_types = rec.journal_id.l10n_latam_document_type_id or rec.l10n_latam_available_document_type_ids._origin
            document_types = debit_note and document_types.filtered(
                lambda x: x.internal_type == 'debit_note') or document_types
            rec.l10n_latam_document_type_id = document_types and document_types[0].id
            rec.pa_document_type = document_type_fe if document_type_fe else rec.l10n_latam_document_type_id
    
    @api.onchange('pa_dgi_destiny_operation')
    def _pa_destiny_operation(self):
        self._compute_l10n_latam_document_type()

    def pa_generate_send(self):
        for invoice_id in self:
            if invoice_id.pa_edocument_id:
                invoice_id.pa_edocument_id.pa_edocument = False
            invoice_id.pa_edocument_id.generate_cpe()
            invoice_id.pa_edocument_id.action_send()
            

    def _post(self, soft=True):
        res = super(AccountMove, self)._post()
        for invoice_id in self.filtered(lambda x: x.move_type != 'entry'):
            invoice_id.action_date_assign()
            if invoice_id.is_cpe and invoice_id.journal_id.l10n_latam_document_type_id.code in ('01', '04', '07', '08'):
                to_write = {}
                if len(((invoice_id.name).replace(" ", "")).split("-")) < 2:
                    invoice_id.payment_reference = (
                        (invoice_id.name).replace(" ", ""))
                invoice_id.validate_dgi_invoice()
                invoice_id._validate_pe_fees()
                if not invoice_id.pa_edocument_id:
                    cpe_id = self.env['odoopanama.cpe'].create_from_invoice(
                        invoice_id)
                    invoice_id.pa_edocument_id = cpe_id.id
                else:
                    cpe_id = invoice_id.pa_edocument_id
                if invoice_id.company_id.pe_is_sync:
                    cpe_id.generate_cpe()
                    if invoice_id.journal_id.is_synchronous or invoice_id.journal_id.l10n_latam_document_type_id.code in ('01', '04'):
                        if not self.env.context.get('is_pos_invoice'):
                            cpe_id.action_send()
                else:
                    cpe_id.generate_cpe()
        return res

    @api.depends('currency_id', 'partner_id', 'invoice_line_ids', 'invoice_line_ids.tax_ids', 'invoice_line_ids.quantity', 'invoice_line_ids.product_id', 'invoice_line_ids.discount')
    def _pe_compute_operations(self):
        for invoice_id in self:
            total_1004 = 0
            for line in invoice_id.invoice_line_ids.filtered(lambda line: not line.display_type):
                price_unit = line.price_unit * \
                    (1 - (line.discount or 0.0) / 100.0)
                total_excluded = line.tax_ids.compute_all(
                    price_unit, invoice_id.currency_id, line.quantity, line.product_id, invoice_id.partner_id)['total_excluded']

                price_unit = line.price_unit
                total_excluded = line.tax_ids.compute_all(
                    price_unit, invoice_id.currency_id, line.quantity, line.product_id, invoice_id.partner_id)['total_excluded']
                total_1004 += total_excluded

    def button_cancel(self):
        res = super().button_cancel()
        if res:
            for invoice_id in self:
                if invoice_id.is_cpe and invoice_id.pa_edocument_id and invoice_id.pa_edocument_id.state not in ('draft',
                                                                                                                 'cancel'):
                    raise UserError(
                        'No puede cancelar este documento, esta enviado a la sunat')
        return res

    def action_annul(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "odoopanama_org_cpe.action_view_account_move_annul")
        return action

    def button_annul(self):
        self.button_cancel()
        self.write({'annul': True})
        for invoice_id in self:
            if invoice_id.is_cpe and invoice_id.pa_edocument_id and invoice_id.pa_edocument_id.state not in ["draft"]:
                invoice_date = fields.Datetime.from_string(
                    invoice_id.pa_invoice_date or invoice_id.invoice_date)
                today = fields.Datetime.context_timestamp(self, datetime.now())
                days = today.replace(tzinfo=None) - invoice_date
                if days.days > 3:
                    raise UserError("No puede anular este documento, solo se puede hacer antes de las 72 horas "
                                    "contadas a partir del día siguiente de la fecha consignada en el CDR (constancia de recepción)."
                                    "\nPara cancelar este Documento emita una Nota de Credito")

                voided_id = self.env['odoopanama.cpe'].get_cpe_async(
                    'ra', invoice_id)
                invoice_id.pa_voided_id = voided_id.id

                if not invoice_id.pa_voided_id:
                    voided_id = self.env['odoopanama.cpe'].get_cpe_async(
                        'ra', voided_id)
                    invoice_id.pa_voided_id = voided_id.id
                else:
                    pa_voided_id = invoice_id.pa_voided_id
                if invoice_id.company_id.pe_is_sync:
                    pa_voided_id.generate_cpe()
                    if invoice_id.journal_id.is_synchronous or invoice_id.journal_id.l10n_latam_document_type_id.code == '01':
                        if not self.env.context.get('is_pos_invoice'):
                            pa_voided_id.action_send()
                else:
                    pa_voided_id.generate_cpe()

        return True

    def button_draft(self):
        states = self.mapped('state')
        res = super().button_draft()
        if self.filtered(lambda inv: inv.pa_edocument_id and (inv.pa_edocument_id.state in ['send', 'verify', 'done']) and inv.journal_id.is_cpe):
            raise UserError(
                "Este documento ha sido informado a la SUNAT no se puede cambiar a borrador")
        self.write({'annul': False})
        return res

    def action_invoice_sent(self):
        res = super().action_invoice_sent()
        self.ensure_one()
        if self.journal_id.is_cpe and self.pa_edocument_id:
            template = self.env.ref(
                'odoopanama_org_cpe.email_template_edi_invoice_cpe2', False)
            attachment_ids = []
            attach = {}
            result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
                'account.report_invoice')._render_qweb_pdf(self.ids)
            attach['name'] = '%s.pdf' % self.pa_edocument_id.get_document_name()
            attach['type'] = 'binary'
            attach['datas'] = encodebytes(result_pdf)
            attach['res_model'] = 'mail.compose.message'
            attachment_id = self.env['ir.attachment'].create(attach)
            attachment_ids.append(attachment_id.id)
            vals = {}
            vals['default_use_template'] = bool(template)
            vals['default_template_id'] = template and template.id or False
            vals['default_attachment_ids'] = [(6, 0, attachment_ids)]
            res['context'].update(vals)
        return res

    def get_public_cpe(self):
        self.ensure_one()
        res = {}
        if self.journal_id.is_cpe and self.pa_edocument_id:
            result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
                'account.report_invoice').render_qweb_pdf(self.ids)
            res['datas_invoice'] = str(encodebytes(result_pdf), "utf-8")
            res['name'] = self.pa_edocument_id.get_document_name()
        return res

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        journal_type = TYPE2JOURNAL.get(self.move_type)
        if not journal_type:
            return res
        journal = self.env['account.journal']
        if not all((self.partner_id, self.env.context.get('force_pe_journal'))):
            return res
        return res

    def _get_starting_sequence(self):
        journal = self.journal_id
        if journal and journal.l10n_latam_use_documents and self.env.company.country_id.code == "PA":
            return self._l10n_pe_cpe_get_formatted_sequence()
        return super(AccountMove, self)._get_starting_sequence()

    def _l10n_pe_cpe_get_formatted_sequence(self, number=0):
        return "{}-00000001".format(self.journal_id.code)

    @api.onchange('l10n_latam_document_type_id', 'l10n_latam_document_number')
    def _inverse_l10n_latam_document_number(self):
        from_reversed = self.filtered(
            lambda x: x.from_wizard_revert and x.name != '/' and not x._get_last_sequence(True))
        super(AccountMove, self-from_reversed)._inverse_l10n_latam_document_number()
        for rec in self.filtered(lambda x: x.name != '/'):
            if not rec.l10n_latam_document_number:
                rec.l10n_latam_document_number = rec.name
                continue
            rec.name = rec.l10n_latam_document_number
        self._set_sequence_from_revert()
        if self.l10n_latam_document_type_id.code == '03':
            self.pa_dgi_destiny_operation = '2'

    def _set_sequence_from_revert(self):
        for rec in self.filtered(lambda x: x.from_wizard_revert and x.name == '/'):
            rec._set_next_sequence()

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(
            AccountMove, self)._get_last_sequence_domain(relaxed)
        if not self.date or not self.journal_id:
            return where_string, param
        if self.company_id.country_id.code == "PA" and self.l10n_latam_use_documents:
            if self.move_type in ('out_refund', 'out_invoice'):
                where_string = where_string.replace(
                    'AND sequence_prefix !~ %(anti_regex)s', '')
                where_string += ' AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s AND ' \
                    'company_id = %(company_id)s AND move_type IN (\'out_invoice\', \'out_refund\')'
            param['company_id'] = self.company_id.id or False
            param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
        return where_string, param


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    pe_charge_amount = fields.Float('Charge Amount',
                                    compute='get_pe_charge_amount')

    @api.depends('price_unit', 'tax_ids', 'discount')
    def get_pe_charge_amount(self):
        for line in self:
            pe_charge_amount = 0.0
            if line.tax_ids.filtered(lambda tax: tax.pa_is_charge == True):
                price_unit = line.price_unit * \
                    (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.with_context(round=False).compute_all(
                    price_unit, line.move_id.currency_id, 1, line.product_id, line.move_id.partner_id).get('taxes', [])
                for tax_val in taxes:
                    tax = self.env['account.tax'].browse(tax_val.get('id'))
                    if tax.pa_is_charge:
                        pe_charge_amount += tax_val.get('amount', 0.0)

            line.pe_charge_amount = pe_charge_amount

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        self = self.with_context(check_move_validity=False)
        return res

    def get_price_unit(self, all=False):
        self.ensure_one()
        price_unit = self.price_unit
        if all:
            price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            tax_ids = self.tax_ids

        res = tax_ids.with_context(round=False).compute_all(
            price_unit, self.move_id.currency_id, 1, self.product_id, self.move_id.partner_id)
        return res
