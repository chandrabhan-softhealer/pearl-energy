{
    'name': 'Auto Receipt and Vendor Bill on PO Confirm',
    'version': '20.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'On PO confirmation: validate the receipt with the demanded quantity and post the vendor bill',
    'description': """
After a Purchase Order is confirmed (and Odoo has finished creating the receipt),
this module:
  1. Sets each receipt move quantity = demand and runs the standard button_validate.
  2. Creates the vendor bill from the PO, dates it today and posts it.

Safety: the automation runs in a savepoint after the standard confirmation. If anything
fails, only the automation is rolled back, the PO stays confirmed and a note is
posted in the PO chatter. It can be switched off per company in Purchase settings.
""",
    'depends': ['purchase_stock', 'account'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
