# -*- coding: utf-8 -*-
{
  'name':'Pos Fprint',
  'description': "Fprint conexiune server casa de marcat",
  'version':'18.0.0.6',
  'author':'Dakai SOFT',
  'data': [
    'security/ir.model.access.csv',
    'view/pos_config.xml',
    'view/pos_order.xml',
    'view/pos_payment_method.xml',
    ],
  'assets': {
    'point_of_sale._assets_pos': [
      'pos_fprint/static/src/js/fprint.js',
      'pos_fprint/static/src/js/pos_chrome.js',
      'pos_fprint/static/src/js/PaymentScreen.js',
      'pos_fprint/static/src/js/ReportsButton.js',
      'pos_fprint/static/src/js/pos_order.js',
      'pos_fprint/static/src/js/pos_in_out.js',
      'pos_fprint/static/src/js/open_cash_in.js',
      'pos_fprint/static/src/js/reprint.js',
      'pos_fprint/static/src/xml/pos.xml',
      'pos_fprint/static/src/xml/ReportsButton.xml',
      'pos_fprint/static/src/xml/addReports.xml',
    ],
  },
  'category': 'Point of Sale',
  'depends': ['point_of_sale', 'common_fprint'],
}
