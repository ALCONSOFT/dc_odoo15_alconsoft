# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class pa_dgi_server(models.Model):
    _inherit = 'res.company'
    _description = 'Panamanian Server'

    type_env = fields.Boolean("Tipo de Ambiente", default=False)
    server_type = fields.Selection([('ebi', 'EBI PAC')], "Servidor", default="ebi")
    url = fields.Char("Url Producción")
    url_dev = fields.Char("Url Desarrollo")
    user = fields.Char("User")
    password = fields.Char("Password")
    description = fields.Text("Description")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    pe_is_sync = fields.Boolean("Es sincrono", default=True)
    key = fields.Text(".key")
    crt = fields.Text(".crt")
    l10n_pa_edi_address_type_code = fields.Char(
            string="Address Type Code",
            default="0000",
            help="Code of the establishment that EBI has registered.")

    @api.onchange("type_env")
    def _onchange_type_evn(self):
        if self.type_env:
            if not self.user:
                self.type_env = False
                raise UserError(
                    'Debe configurar el usuario y contraseña para pasar a Porducción.')
            

