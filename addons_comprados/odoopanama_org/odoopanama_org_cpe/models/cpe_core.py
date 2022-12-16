# -*- coding: utf-8 -*-

from odoo import _
from datetime import datetime
import zeep
import pytz

import logging
log = logging.getLogger(__name__)


class CPE:

    def _getCompany21(self, invoice_id):
        pass

    def _format_phone(self, phone):
        res = ''
        if not phone:
            res = ''
        else:
            phone = phone.replace(" ", "").replace("-", "")
            if len(phone) >= 8:
                res = phone[-8:][:4] + '-' + phone[-8:][-4:]
            elif len(phone) == 7:
                res = phone[-8:][:3] + '-' + phone[-8:][-4:]
        return res

    def _set_tax(self, val):
        rateTax = '00'
        if val == 7.0:
            rateTax = '01'
        elif val == 10.0:
            rateTax = '02'
        elif val == 15.0:
            rateTax = '03'
        return rateTax

    def getCreditNote(self, invoice_id):
        zone = pytz.timezone('America/Panama')
        date_reversed = invoice_id.reversed_entry_id.invoice_date
        name_reversed = (invoice_id.reversed_entry_id.name).split("-")[0]
        formatDate = datetime(
            date_reversed.year, date_reversed.month, date_reversed.day, tzinfo=zone)
        formatDate = formatDate.isoformat()
        fechaEmision = formatDate[:23] + '00'
        cufeFEReferenciada = invoice_id.reversed_entry_id.pa_edocument_id.cufe
        datosTransaccion = self._getDataTransaction(invoice_id),
        datosTransaccion[0]["puntoFacturacionFiscal"] = name_reversed
        datosTransaccion[0]['listaDocsFiscalReferenciados'] = dict(
            {'docFiscalReferenciado': {
                "fechaEmisionDocFiscalReferenciado": fechaEmision,
                "cufeFEReferenciada": cufeFEReferenciada,
                "nroFacturaPapel": "",
                "nroFacturaImpFiscal": "",
            }})
        codigoSucursalEmisor = invoice_id.company_id.l10n_pa_edi_address_type_code or "0000"
        datos = dict(
            codigoSucursalEmisor=codigoSucursalEmisor,
            tipoSucursal="1",
            datosTransaccion=datosTransaccion[0],
            listaItems=dict(
                item=self._getLinesInvoice(invoice_id)
            ),
            totalesSubTotales=dict(
                self._getTotal(invoice_id),
                listaFormaPago=dict(
                    formaPago=self._getPaymentList(invoice_id)
                )
            )
        )
        return datos
    
    def _get_DataExportation(self, invoice_id):
        data = {
        "condicionesEntrega" : invoice_id.invoice_incoterm_id.code,
        "monedaOperExportacion" : invoice_id.currency_id.name,
        "puertoEmbarque" : "",
        }
        return data

    def _getDataTransaction(self, invoice_id):
        tipoDocumento = invoice_id.pa_document_type.code
        informacionInteres = invoice_id.pa_document_type.report_name
        if invoice_id.pa_document_type.code == '04' and not invoice_id.reversed_entry_id:
            tipoDocumento = '06'
            informacionInteres = "Factura de nota de credito"
        DocFiscal = invoice_id.name.split("-")[-1]
        puntoFacturacionFiscal = invoice_id.name.split("-")[0]
        tipoEmision = invoice_id.pa_dgi_type_emission
        naturalezaOperacion = invoice_id.pa_dgi_nature_operation
        tipoOperacion = invoice_id.pa_dgi_type_operation
        destinoOperacion = invoice_id.pa_dgi_destiny_operation
        tipoVenta = invoice_id.pa_dgi_type_sale
        zone = pytz.timezone('America/Panama')
        dateInput = datetime(invoice_id.invoice_date.year,
                             invoice_id.invoice_date.month, invoice_id.invoice_date.day, tzinfo=zone)
        formatDate = dateInput.isoformat()
        fechaEmision = formatDate[:23] + '00'
        datos = dict({
            "tipoEmision": tipoEmision,
            "tipoDocumento": tipoDocumento,
            "numeroDocumentoFiscal": DocFiscal,
            "puntoFacturacionFiscal": puntoFacturacionFiscal,
            "naturalezaOperacion": naturalezaOperacion,
            "tipoOperacion": tipoOperacion,
            "destinoOperacion": destinoOperacion,
            "formatoCAFE": 1,
            "entregaCAFE": 1,
            "envioContenedor": 1,
            "procesoGeneracion": 1,
            "tipoVenta": tipoVenta,
            "informacionInteres": informacionInteres,
            "fechaEmision": fechaEmision,
            "cliente": self._getPartner(invoice_id)
        })
        if invoice_id.pa_dgi_destiny_operation == "2":
            DataExportation = {"datosFacturaExportacion" : self._get_DataExportation(invoice_id)}
            datos.update(DataExportation)
        return datos

    def _getPartner(self, invoice_id):
        vat_code_parter = tipoClienteFE = (invoice_id.partner_id.l10n_latam_identification_type_id.l10n_pa_vat_code)
        if not vat_code_parter and invoice_id.partner_id.country_id != "PA":
            tipoClienteFE = "04"
        else:
            tipoClienteFE = tipoClienteFE[:2]
        tipoContribuyente = int(
            "1" if invoice_id.partner_id.company_type == 'person' else "2")
        if not invoice_id.partner_id.vat and tipoClienteFE in ('99','02'):
            numeroRUC = '0-000-0000'
        else:
            numeroRUC = invoice_id.partner_id.vat
        digitoVerificadorRUC = invoice_id.partner_id.pa_dv or ''
        razonSocial = invoice_id.partner_id.name
        direccion = invoice_id.partner_id.street
        codigoUbicacion = invoice_id.partner_id.l10n_pa_corregimiento.code or ''
        provincia = invoice_id.partner_id.state_id.name or ''
        distrito = invoice_id.partner_id.city_id.name or ''
        corregimiento = invoice_id.partner_id.l10n_pa_corregimiento.name or ''
        paisExtranjero = ''
        telefono1 = self._format_phone(invoice_id.partner_id.phone) or ''
        telefono2 = self._format_phone(invoice_id.partner_id.mobile) or ''
        telefono3 = ''
        correoElectronico1 = invoice_id.partner_id.email or ''
        correoElectronico2 = ''
        correoElectronico3 = ''
        pais = invoice_id.partner_id.country_id.code
        paisOtro = ''

        partner_data = dict({
            "tipoClienteFE": tipoClienteFE,
            "tipoContribuyente": tipoContribuyente,
            "numeroRUC": numeroRUC,
            "razonSocial": razonSocial,
            "direccion": direccion,
            "codigoUbicacion": codigoUbicacion,
            "provincia": provincia,
            "distrito": distrito,
            "corregimiento": corregimiento,
            "paisExtranjero": paisExtranjero,
        })
        phone_email = dict(
            {
                "telefono1": telefono1,
                "telefono2": telefono2,
                "telefono3": telefono3,
                "correoElectronico1": correoElectronico1,
                "correoElectronico2": correoElectronico2,
                "correoElectronico3": correoElectronico3,
                "pais": pais,
                "paisOtro": paisOtro,
            }
        )

        if tipoClienteFE[:2] != '04':
            partner_data["digitoVerificadorRUC"] = digitoVerificadorRUC

        if tipoClienteFE[:2] == '04':
            [partner_data.pop(key, None) for key in [
                'tipoContribuyente', 'numeroRUC', 'codigoUbicacion']]
            foreign_partner_data = dict(
                {
                    'tipoIdentificacion': tipoClienteFE[-2:] if tipoClienteFE[-2:] != "04" else "99",
                    'nroIdentificacionExtranjero': invoice_id.partner_id.vat
                }
            )
            partner_data.update(foreign_partner_data)
        partner_data.update(phone_email)
        return partner_data

    def _getLinesInvoice(self, invoice_id):
        list_item = []
        decimal_currency = '.{}f'.format(invoice_id.currency_id.decimal_places)
        invoices_line_ids = invoice_id.invoice_line_ids.filtered(lambda line: not line.display_type)
        for item in invoices_line_ids:
            unspsc_code = item.product_id.pa_unspsc_code_id.code if item.product_id.pa_unspsc_code_id else ""
            list_item.append({
                "descripcion": item.name,
                "cantidad": format(item.quantity, '.2f'),
                "codigoCPBSAbrev":unspsc_code[0:2],
                "codigoCPBS":unspsc_code,
                "precioUnitario": format((item.price_subtotal/item.quantity)+item.amount_discount, '.5f'),
                "precioUnitarioDescuento": format(item.amount_discount, '.2f'),
                "precioItem": format(item.price_subtotal, '.2f'),
                "valorTotal": format(item.price_total, '.2f'),
                "codigoGTIN": "",
                "cantGTINCom": "",
                "codigoGTINInv": "",
                "tasaITBMS": self._set_tax(item.tax_ids.amount) or "",
                "valorITBMS": format(item.price_subtotal * item.tax_ids.amount / 100, decimal_currency),
                "cantGTINComInv": ""
            })
        return list_item

    def _getPaymentList(self, invoice_id):
        formaPagoList = []
        if len(invoice_id.pe_payment_lines) != 0:
            for line in invoice_id.pe_payment_lines:
                formaPagoList.append({
                    'formaPagoFact': line.pa_payment_method,
                    "descFormaPago": " ",
                    "valorCuotaPagada": format(line.amount, '.2f')}
                )
        else:
            formaPagoList.append({
                'formaPagoFact': invoice_id.pa_payment_method,
                "descFormaPago": " ",
                "valorCuotaPagada": format(invoice_id.amount_total, '.2f')
            }
            )
        return formaPagoList

    def _getTotal(self, invoice_id):
        amount_untaxed = invoice_id.amount_untaxed
        taxes = []
        taxes.append(
            {'amount_tax_line': 0,   'tax_description': 'ITBMS 7%',  'percent': 7.0})
        ctx = dict(invoice_id._context)
        ctx.update({'params': {'view_type': 'form'}})
        invoice_id = invoice_id.with_context(ctx)
        for group_tax in invoice_id.amount_by_group:
            group_id = group_tax[(-1)]
            tax_id = invoice_id.line_ids.mapped('tax_ids').filtered(
                lambda x: x.tax_group_id.id == group_id)
            tax_id = tax_id and tax_id[0]
            amount_tax_line = group_tax[1]
            for i in range(len(taxes)):
                if taxes[i]['percent'] == tax_id.amount:
                    taxes[i]['amount_tax_line'] += amount_tax_line
        totalITBMS = 0
        for tax in taxes:
            if tax['percent'] == 7.0:
                totalITBMS += tax['amount_tax_line']
        # totalDescuento = invoice_id.pe_amount_discount or 0.00
        amount_total = invoice_id.amount_total
        nroItems = len(invoice_id.invoice_line_ids.filtered(
            lambda line: not line.display_type))
        data = dict(
            {
                "totalPrecioNeto": format(amount_untaxed, '.2f'),
                "totalITBMS": format(totalITBMS, '.2f'),
                "totalMontoGravado": format(totalITBMS, '.2f'),
                "totalDescuento": '0.00',
                "totalAcarreoCobrado": "",
                "valorSeguroCobrado": "",
                "totalFactura": format(amount_total, '.2f'),
                "totalValorRecibido": format(amount_total, '.2f'),
                "vuelto": "0.00",
                "tiempoPago": "1",
                "nroItems": nroItems,
                "totalTodosItems": format(amount_total, '.2f')}
        )
        return data

    def getVoidedDocuments(self, batch):
        for batch_id in batch:
            DocFiscal = batch_id.name.split("-")[-1]
            puntoFacturacionFiscal = batch_id.name.split("-")[0]
            codigoSucursalEmisor = batch_id.company_id.l10n_pa_edi_address_type_code or "0000"
            tipoDocumento = batch_id.l10n_latam_document_type_id.code
            tipoEmision = batch_id.pa_dgi_type_emission
            cancellation_reason = batch_id.cancellation_reason
            datos = dict({
                "motivoAnulacion": cancellation_reason,
                "datosDocumento": {
                    "codigoSucursalEmisor": codigoSucursalEmisor,
                    "numeroDocumentoFiscal": DocFiscal,
                    "puntoFacturacionFiscal": puntoFacturacionFiscal,
                    "tipoDocumento": tipoDocumento,
                    "tipoEmision": tipoEmision
                }
            })
            return datos

    def getDocumentStatus(self, invoice_id):
        datas = self.getVoidedDocuments(invoice_id)
        datas.pop('motivoAnulacion', None)
        return datas

    def getInvoice(self, invoice_id):
        codigoSucursalEmisor = invoice_id.company_id.l10n_pa_edi_address_type_code or "0000"
        SubTotales = dict(
                self._getTotal(invoice_id),
            )
        # if invoice_id.pe_amount_discount > 0:
        #     SubTotales.update(dict(listaDescBonificacio = dict(descuentoBonificacion=[{'descDescuento':'Descuento','montoDescuento':format(invoice_id.pe_amount_discount, '.2f') }])))
        SubTotales.update(dict(listaFormaPago=dict(formaPago=self._getPaymentList(invoice_id))))
        datos = dict(
            codigoSucursalEmisor=codigoSucursalEmisor,
            tipoSucursal="1",
            datosTransaccion=self._getDataTransaction(invoice_id),
            listaItems=dict(
                item=self._getLinesInvoice(invoice_id)
            ),
            totalesSubTotales = SubTotales
        )
        return datos


class Document(object):

    def __init__(self):
        self._xml = None
        self._type = None
        self._document_name = None
        self._client = None
        self._response = None
        self._response_status = None
        self._response_data = None

    def send(self):
        if self._type in ('sync', 'ra'):
            self._response = self._client.send_bill(self._xml)
        else:
            if self._type == 'status':
                self._response = self._client.get_status_pac(self._xml)

    def process_response(self):
        if self._response is not None:
            if self._type == 'sync':
                self._response_data = self._response
                return

    def process(self, document_name, type, xml, client):
        self._xml = xml
        self._type = type
        self._document_name = document_name
        self._client = client
        self.send()
        self.process_response()
        return (self._response)

    def get_status_pac(self, type, xml, client):
        self._type = 'status'
        self._xml = xml
        self._client = client
        self.send()
        self.process_response()
        return (self._response)


class Client(object):

    def __init__(self, ruc, username, password, url, debug=False, type=None, server=None):
        self._type = type
        self._username = username
        self._password = password
        self._head_data = {'tokenEmpresa': username, 'tokenPassword': password}
        self._debug = debug
        self._url = url
        self._method = 'getstatusPac'
        level = logging.DEBUG
        logging.basicConfig(level=level)
        log.setLevel(level)
        self._connect()

    def _connect(self):
        self._client = zeep.Client(wsdl=self._url)

    def _call_ws(self, content_file):
        datos = self._head_data
        if self._type == 'status':
            datos['datosDocumento'] = content_file['datosDocumento']
            datos_response = self._client.service.EstadoDocumento(**datos)
        else:
            if eval(content_file).get('motivoAnulacion'):
                # eval(content_file).get('motivoAnulacion')
                datos['motivoAnulacion'] = 'Motivo de la Anulación de FE'
                datos['datosDocumento'] = eval(
                    content_file).get('datosDocumento')
                datos_response = (
                    self._client.service.AnulacionDocumento(**datos))
            else:
                datos['documento'] = eval(content_file)
                datos_response = (self._client.service.Enviar(**datos))

        return datos_response

    def _call_service(self, content_file):
        try:
            return self._call_ws(content_file)
        except Exception as e:
            return (False, {})

    def send_bill(self, content_file):
        return self._call_service(content_file)

    def get_status_pac(self, document):
        self._type = 'status'
        return self._call_service(document)


def get_document(self):
    xml = None
    if self.type == 'sync':
        if self.invoice_ids[0].l10n_latam_document_type_id.code == '04' and self.invoice_ids[0].reversed_entry_id:
            xml = CPE().getCreditNote(self.invoice_ids[0])
        else:
            xml = CPE().getInvoice(self.invoice_ids[0])
    else:
        if self.type == 'ra':
            xml = CPE().getVoidedDocuments(self.voided_ids[0])
    return xml


def get_status_pac(client, invoice_id):
    xml = None
    if invoice_id.type == 'sync':
        xml = CPE().getDocumentStatus(invoice_id.invoice_ids[0])
    else:
        if invoice_id.type == 'rc':
            xml = CPE().getDocumentStatus(invoice_id.voided_ids[0])
    document = {}
    document['type'] = 'statusPac'
    document['xml'] = xml
    client = Client(**client)
    document['client'] = client
    return Document().get_status_pac(**document)


def get_response(data):
    return (Document().get_response)(**data)


def send_dgi_cpe(client, document):
    client['type'] = 'send'
    client = Client(**client)
    document['client'] = client
    return (Document().process)(**document)
