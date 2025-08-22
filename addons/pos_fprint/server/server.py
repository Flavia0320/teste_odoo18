#!/usr/bin/python
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule #, NotFound, RequestRedirect, HTTPException
from werkzeug import secure_filename
from datetime import datetime, timedelta
import os,json
import logging
from base64 import b64decode


from configparser import ConfigParser
config = ConfigParser.read('config.conf')

_logger = logging.getLogger(__name__)

url_map = Map([
    Rule('/', endpoint='index'),
    Rule('/fax', endpoint='faxGet'),
])

class Application(object):
    depou = {}

    def __init__(self):
        pass

    def index(self, **kwarg):
        return {'state':True, 'message': 'First Page, default route'}

#     def __call__(self, environ, start_response):
#         request = Request(environ)
#         res = {}
#         urls = url_map.bind_to_environ(environ)
#         try:
#             endpoint, args = urls.match()
#         except:
#             endpoint, args = ('index',{})
#         #print endpoint, args, urls.match()
# 
#         func = self.index
#         if hasattr(self, endpoint):
#             func = getattr(self, endpoint)
# 
#         args['request'] = request
#         #access:
#         block = self.restrict(request.values)
#         #print "TTS", dir(request), parse_form_data(environ)
#         if block[0] and 'index' not in endpoint:
#             res = block[1]
#         else:
#             res = func(**args)
#         #print "Params", request.data
#         response = Response(content_type="application/json")
#         if endpoint == 'html2pdf' and args.get('hstr',None):
#             response = Response(content_type="text/html")
#             response.data = res
#             return response(environ, start_response)
#         elif endpoint == 'download' and res:
#             response = Response(content_type="aplication/octet-stream")
#             response.data = res
#             response.data = res
#             return response(environ, start_response)
#         elif endpoint == 'downloadPDF' and res:
#             response = Response(content_type="aplication/octet-stream")
#             response.data = res
#             response.data = res
#             return response(environ, start_response)
#         elif endpoint == 'qr' and res:
#             response = Response(content_type="image/SVG+XML")
#             response.data = res
#             return response(environ, start_response)
#         elif res:
#             response.headers["Cache-Control"] = "no-cache"
#             response.headers["Pragma"] = "no-cache"
#             response.headers["Expires"] = "-1"
#             response.data = json.dumps(res)
#         return response(environ, start_response)
# 
#     def receiveFile(self, request):
#         if not request.files.get('courier',None):
#             return {'status':False, 'message':'No file uploaded'}
#         courierDict = {}
#         for key, f in request.files.items():
#             filename = secure_filename(f.filename)
#             fpath = os.path.join(_PATH_COURIER_FOLDER, filename)
#             f.save(fpath)
#             f.stream.seek(0)
#             courierDict = parseFile(f.stream.readlines())
#             uid = filename.split(".")[0]
#         if not courierDict:
#             return None
#         sender = courierDict.get('expeditor')
#         reciver = courierDict.get('destinatar')
#         s_id = checkforpartner(sender)
#         r_id = checkforpartner(reciver)
#         for item in courierDict.get('item'):
#             sql.anySql("INSERT INTO courier (sender, reciver, sender_id, reciver_id, item, quantity, value, weight, status, uid) VALUES ('%s','%s',%s,%s,'%s',%s,%s,%s,'%s','%s')" % (
#                     sender.get('nume')+' '+sender.get('prenume'),
#                     reciver.get('nume')+' '+reciver.get('prenume'),
#                     s_id,r_id,
#                     item.get('item'),
#                     item.get('cantitate'),
#                     item.get('valoare'),
#                     item.get('greutate'),
#                     'draft',
#                     uid))
#             courierlogger({
#                 'table':'courier',
#                 'tab_id':sql.anySql("SELECT LAST_INSERT_ID() as id")[0].get('id'),
#                 'log':dump(['Transport adaugat la %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
#                 })
# 
# ####################################################NEW###################################################################
#     def download(self, request, model=None, field=None, ids=None):
#         if not all([model, ids, field]):
#             return {'status': False, 'message': 'No id set'}
#         raw = sql.anySql("SELECT %s FROM %s WHERE id = %s" % (field, model, ids))
#         x = raw[0].get(field)
#         return b64decode(x)
# 
#     def downloadPDF(self,request,an,bpi):
#         out = None
#         if '.pdf' in bpi:
#             bpi = bpi.replace('.pdf', '')
#         if not all([an,bpi]):
#             return {'status': False, 'message': 'No id or year set'}
#         x = "/home/python_app/store_pdf/%s-%s.pdf" % (an, bpi)
# 
#         try:
#             file = open('%s' % x, 'rb')
#             out = file.read()
#         except:
#             pass
# 
#         if out:
#             return out
#         else:
#             return {'status':False,'message':'Nu s-a gasit buletinul'}
# 
# 
# ###################################################################################################################################
# 
# 
#     def smsmaster(self, request):
#         d = json.loads(request.get_data())
#         if 'id' in d:
#             id = d.get('id')
#             i = sql.anySql('SELECT alias,tel_destinatar,mesaj,date FROM SMS WHERE id=%d AND status=1' % id)
#             return [{"alias": b.get('alias'),
#                      "nrdest":b.get('tel_destinatar'),
#                      "sms":b.get('mesaj'),
#                      "message": "Sent",
#                      "at date":b.get('date').strftime('%Y-%m-%d %H:%M:%S')} for b in i]
#         elif 'alias' in d:
#             alias = d.get('alias')
#             x = sql.anySql('SELECT id,tel_destinatar,mesaj FROM SMS WHERE alias="%s" AND status=0' % alias)
#             return [{
#                 "id": a.get('id'),
#                 "number": a.get('tel_destinatar'),
#                 "sms": a.get('mesaj')} for a in x]
#         elif 'sms_id' in d:
#             id = d.get('sms_id')
#             sql.anySql('UPDATE SMS set status=1 WHERE id=%d' % id)


if __name__ == '__main__':
    application = Application()
    run_simple('0.0.0.0', 8000, application)