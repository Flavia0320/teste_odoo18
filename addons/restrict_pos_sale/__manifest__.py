# -*- coding: utf-8 -*-
{
  'name':'Restrict pos sale',
  'description': "Restricts sale in pos. It does not allow you to order having zero quantity or price zero on order line.",
  'version':'18.0.0.0',
  'author':'Dakai SOFT',
  'data': [
    ],
  'assets': {
    'point_of_sale._assets_pos': [
      'restrict_pos_sale/static/src/js/RestrictSalePopup.js',
      'restrict_pos_sale/static/src/js/OrderScreen.js',
      'restrict_pos_sale/static/src/xml/RestrictSalePopup.xml',
    ],
  },
  'category': 'Point of Sale',
  'depends': ['point_of_sale'],
}
