 # coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from os.path import join, dirname, realpath
from odoo import tools

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _load_unspsc_codes(cr, registry)


def uninstall_hook(cr, registry):
    cr.execute("DELETE FROM panama_unspsc_code;")
    cr.execute("DELETE FROM ir_model_data WHERE model='panama_unspsc_code';")

def _load_unspsc_codes(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv
    Even with the faster CSVs, it would take +30 seconds to load it with
    the regular ORM methods, while here, it is under 3 seconds
    """
    csv_path = join(dirname(realpath(__file__)), 'data',
                    'panama.unspsc.code.csv')
    csv_file = open(csv_path, 'rb')
    csv_file.readline() # Read the header, so we avoid copying it to the db
    cr.copy_expert(
        """COPY panama_unspsc_code (code, name, applies_to, active)
           FROM STDIN WITH DELIMITER '|'""", csv_file)
    # Create xml_id, to allow make reference to this data
    cr.execute(
        """INSERT INTO ir_model_data
           (name, res_id, module, model, noupdate)
           SELECT concat('unspsc_code_', code), id, 'odoopanama_org_unspsc', 'panama.unspsc.code', 't'
           FROM panama_unspsc_code""")

