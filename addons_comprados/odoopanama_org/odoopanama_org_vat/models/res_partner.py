# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .library.cedula import validate as CDL
import requests

import logging

_logger = logging.getLogger(__name__)

			
class Partner(models.Model):
	_inherit = 'res.partner'

	commercial_name = fields.Char("Nombre commercial", default="-")
	is_validate = fields.Boolean("Es Validado")
	l10n_pa_corregimiento = fields.Many2one(
        'l10n_pa.res.city.corregimiento', string='Corregimiento')
	pa_dv = fields.Char("Digito Verificador")
	pa_type_client = fields.Selection(
        selection=[
            ('taxpayer', 'Empresa contribuyente'),
            ('consumer', 'Consumidor Final'),
            ('foreign', 'Extranjero'),
        ],
        string="Tipo de Cliente para FE",
        store=False,
        compute='_compute_customer_type')
	
	@api.depends("l10n_latam_identification_type_id")
	def _compute_customer_type(self):
		for partner in self:
			# import pdb; pdb.set_trace()
			# partner.country_id
			doc_type= partner.l10n_latam_identification_type_id.l10n_pa_vat_code
			if doc_type:
				if partner.country_id and partner.country_id.code != "PA":
					partner.pa_type_client = "foreign"
				else:			
					if doc_type in ("01","03"):
						partner.pa_type_client = "taxpayer"
					else:
						if doc_type == ("02"):
							partner.pa_type_client = "consumer"
						else:
							partner.pa_type_client = "foreign"
			else:
				if partner.country_id and partner.country_id.code != "PA":
					partner.pa_type_client = "foreign"
				else:
					partner.pa_type_client = "consumer"
				

	@api.onchange('l10n_pa_corregimiento')
	def _onchange_l10n_pa_corregimiento(self):
		if self.l10n_pa_corregimiento:
			self.city_id = self.l10n_pa_corregimiento.city_id

	@api.onchange('city_id')
	def _onchange_l10n_pa_city_id(self):
		if self.city_id and self.l10n_pa_corregimiento.city_id and self.l10n_pa_corregimiento.city_id != self.city_id:
			self.l10n_pa_corregimiento = False


	@api.constrains("vat")
	def check_vat(self):
		if not self.parent_id:
			for partner in self:
				doc_type = partner.l10n_latam_identification_type_id.l10n_pa_vat_code
				if not doc_type and not partner.vat or doc_type == '99' or doc_type == '02':
					continue
				elif doc_type and not partner.vat:
					raise UserError("Enter the document number")
				if self.search_count([('company_id', '=', partner.company_id.id),
									  ('l10n_latam_identification_type_id.l10n_pa_vat_code',
									   '=', doc_type),
									  ('vat', '=', partner.vat)]) > 1:
					raise UserError('The document number already exists and violates the unique field restriction')


	@api.onchange("vat", "l10n_latam_identification_type_id")
	@api.depends("l10n_latam_identification_type_id", "vat")
	def _vat_change(self):
		if self.vat:
			vat = self.vat
			if vat and self.l10n_latam_identification_type_id:
				doc_type = self.l10n_latam_identification_type_id.l10n_pa_vat_code
				if doc_type in ('01','02','03'):
					if doc_type == '02':
						response = CDL(self.vat)
						if not response['is_valid']:
							raise UserError(_('The identification number (Cédula) is incorrect.'))
					if self.AppLink(doc_type):
						response_api =  requests.get('{}{}'.format(self.AppLink(doc_type), vat.strip()))
						if response_api:
							response = response_api.json()
							if response and not response.get('error'):
								self.name= response.get('ruc').strip()
								self.pa_dv= response.get('dv').strip()
								self.name= response.get('name').strip()
		
	
	@api.onchange("company_type")
	def _company_type(self):
		for res in self:
			type_doc = res.env["l10n_latam.identification.type"].search([('l10n_pa_vat_code', '=', '01')], limit=1).id
			if res.l10n_latam_identification_type_id.l10n_pa_vat_code in ("01","03"):
				continue
			else:
				if res.company_type == 'company':
					res.l10n_latam_identification_type_id = type_doc
			res.country_id = self.env.ref("base.pa").id


	@api.onchange('l10n_latam_identification_type_id')
	def onchange_company_type(self):
		doc_type = self.l10n_latam_identification_type_id.l10n_pa_vat_code
		if doc_type == "01" or doc_type == "03":
			self.company_type = 'company'
		else:
			self.company_type = 'person'
		super(Partner, self).onchange_company_type()	

		
	def AppLink(self,doc_type):
		Applink = False
		if doc_type in ('01','02','03'):
			LinkSudo = self.env['ir.config_parameter'].sudo()
			consulta = LinkSudo.get_param('token') or "public"
			dniruc = LinkSudo.get_param('web.base.url').replace(
				'http://', '').replace('https://', '').replace('wwww', '').replace('.', '_')
			apiserver = dniruc.split(':')[0]
			url = 'https://api.odoopanama.org/api'
			Applink = "{}?url={}&token={}&type={}&ruc=".format(
				url, apiserver, consulta, doc_type)
		return Applink


	
