# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from .cpe_core import get_document, send_dgi_cpe, get_status_pac
from datetime import datetime
from odoo.exceptions import Warning
import logging
from zeep.helpers import serialize_object
log = logging.getLogger(__name__)


class PeruSunatCpe(models.Model):
    _name = 'odoopanama.cpe'
    _description = 'Factura Electronica Pama'

    name = fields.Char("Name", default="/")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('generate', 'Generated'),
        ('send', 'Send'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft', copy=False)
    type = fields.Selection([
        ('sync', 'Envio online'),
        ('rc', 'Resumen diario'),
        ('ra', 'Comunicación de Baja'),
    ], string="Type", default='sync', states={'draft': [('readonly', False)]})
    date = fields.Datetime("Date", default=fields.Datetime.now, states={
                           'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('pe.sunat.cpe'))
    pa_edocument = fields.Text("XML Document", states={
        'draft': [('readonly', False)]})

    note = fields.Text("Note", readonly=True)
    error_code = fields.Char(string="Error Code", readonly=True)
    digest = fields.Char("Digest", readonly=True)
    invoice_ids = fields.One2many(
        "account.move", 'pa_edocument_id', string="Invoices", readonly=True)
    ticket = fields.Char("Ticket", readonly=True)
    date_end = fields.Datetime(
        "End Date", states={'draft': [('readonly', False)]})
    send_date = fields.Datetime(
        "Send Date", states={'draft': [('readonly', False)]})
    voided_ids = fields.One2many(
        "account.move", "pa_voided_id", string="Voided Invoices")
    is_voided = fields.Boolean("Is Boided")

    response = fields.Char("Response", readonly=True)
    response_code = fields.Char("Response Code", readonly=True)

    authorization_protocol = fields.Char(
        "Nro Authorization Protocol", readonly=True)
    cufe = fields.Char("CUFE", readonly=True)
    dateReceptionDGI = fields.Char("Date Reception DGI", readonly=True)
    deadline = fields.Char("Deadline", readonly=True)

    _order = 'date desc, name desc'

    def unlink(self):
        for batch in self:
            if batch.name != "/" and batch.state != "draft":
                raise Warning(_('You can only delete sent documents.'))
        return super(PeruSunatCpe, self).unlink()

    def action_draft(self):
        if not self.pa_edocument and self.type == "sync":
            self._prepare_cpe()
        self.state = 'draft'

    def action_generate(self):
        if self.type in ['rc', 'ra']:
            if self.response:
                self.response = ''
            if not self.send_date:
                record = self.with_context(tz="America/Panama")
                self.send_date = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(record, datetime.now()))
            if self.type == "sync" and self.name == "/":
                self.name = self.invoice_ids[0].number

        if not self.pa_edocument:
            self._prepare_cpe()
            self.name =  self.get_document_name()
        elif self.name != "/" and self.type in ["rc", "ra"]:
            if self.get_document_name() != self.name:
                self._prepare_cpe()
        self.state = 'generate'

    def action_send(self):
        state = self.send_cpe()
        if state:
            self.state = state

    def action_verify(self):
        self.state = 'verify'

    def action_cancel(self):
        self.state = 'cancel'

    @api.model
    def create_from_invoice(self, invoice_id):
        vals = {}
        vals['invoice_ids'] = [(4, invoice_id.id)]
        vals['type'] = 'sync'
        vals['company_id'] = invoice_id.company_id.id
        res = self.create(vals)
        return res

    @api.model
    def get_cpe_async(self, type, invoice_id, is_voided=False):
        res = None
        company_id = invoice_id.company_id.id
        date_invoice = invoice_id.invoice_date
        if not res:
            vals = {}
            vals['type'] = type
            vals['date'] = date_invoice
            vals['company_id'] = company_id
            vals['is_voided'] = is_voided
            res = self.create(vals)
        return res

    def get_document_name(self):
        self.ensure_one()
        name = False
        if self.type == "sync":
            name = self.invoice_ids[0].name
        elif self.type == "ra":
            name = self.voided_ids[0].name + " [Anulación]"
        return name

    def get_document_name_manual(self):
        self.ensure_one()
        ruc = self.company_id.partner_id.vat
        if self.type == "sync":
            number = self.name
            doc_code = "-%s" % (self.l10n_latam_document_type_id.code or '01')
        else:
            doc_code = ""
            number = self.name or ""
        return "%s%s-%s" % (ruc, doc_code, number)

    def prepare_pac_auth(self):
        self.ensure_one()
        res = {}
        if self.company_id.type_env:
            url = self.company_id.url and self.company_id.url or "https://emision.ebi-pac.com/ws/obj/v1.0/Service.svc?singleWsdl"
        else:
            url = self.company_id.url_dev and self.company_id.url_dev or "https://demointegracion.ebi-pac.com/ws/obj/v1.0/Service.svc?singleWsdl"
        res['ruc'] = self.company_id.partner_id.vat
        res['username'] = self.company_id.user
        res['password'] = self.company_id.password
        res['url'] = url
        res["server"] = self.company_id.server_type
        return res

    def _prepare_cpe(self):
        if not self.pa_edocument:
            self.name = self.get_document_name()
            pa_edocument = get_document(self)
            self.pa_edocument = pa_edocument

    def send_cpe(self):
        res = None
        self.ensure_one()
        if not self.send_date:
            record = self.with_context(tz=self.env.user.tz)
            self.send_date = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(record, datetime.now()))
        local_date = datetime.strptime(
            str(self.send_date), "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
        if self.type == "sync" and self.name == "/":
            self.name = self.invoice_ids[0].number
        elif self.type == "ra" and self.name == "/":
            self.name = self.voided_ids[0].name + " [Anulación]"
        file_name = self.get_document_name()

        client = self.prepare_pac_auth()
        document = {}
        document['document_name'] = file_name
        document['type'] = self.type
        document['xml'] = self.pa_edocument
        response = send_dgi_cpe(client, document)
        if response:
            response_dict = dict(serialize_object(response))
            self.response = "{} - {}".format(response_dict.get(
                "codigo"), response_dict.get("mensaje"))
            self.note = response_dict.get("qr")
            self.response_code = response_dict.get("resultado")
            self.authorization_protocol = response_dict.get(
                "nroProtocoloAutorizacion")
            self.cufe = response_dict.get("cufe")
            self.deadline = response_dict.get("fechaLimite")
            self.error_code = False
            new_state = self.get_response_details()
            res = "send"
            res = new_state or res

        return res

    @api.depends('response_code')
    def get_response_details(self):
        self.ensure_one()
        state = self.state
        if self.response_code:
            if self.response_code == "procesado":
                state = "done"
        return state

    def generate_cpe(self):
        self._prepare_cpe()
        self.state = "generate"

    def action_document_status(self):
        client = self.prepare_pac_auth()
        response = get_status_pac(client, self)
        res = self.state
        if response:
            response_dict = dict(serialize_object(response))
            self.response = "{} - {}".format(response_dict.get(
                "codigo"), response_dict.get("mensajeDocumento"))
            self.response_code = response_dict.get("resultado")
            self.cufe = response_dict.get("cufe")
            new_state = self.get_response_details()
            res = new_state or res
        self.state = res
        return res

    def send_async_cpe(self):
        cpe_ids = self.search(
            [('state', 'in', ['generate', 'send']), ('type', 'in', ['sync'])])
        for cpe_id in cpe_ids:
            if cpe_id.invoice_ids:
                if cpe_id.invoice_ids[0].l10n_latam_document_type_id.code not in ["03", "07"]:
                    try:
                        cpe_id.action_document_status()
                    except Exception:
                        pass
                if cpe_id.state != 'done':
                    if cpe_id.invoice_ids[0].l10n_latam_document_type_id.code not in ["03", "07"]:
                        try:
                            cpe_id.action_generate()
                            cpe_id.action_send()
                        except Exception:
                            pass
