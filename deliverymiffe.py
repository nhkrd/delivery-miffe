#
# Delivery Miffe(MTE Inserter for Fmp4 as Emsg box)
#
from socketserver import ThreadingTCPServer
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler
import time
import datetime
import os
import configparser

inifile = configparser.ConfigParser()
inifile.read('settings.ini')

q_chunk = {}
get_chunk = {}
get_chunk_seq = 0
LogFlag = False

FileDelete = (inifile.get('SERVER', 'FileDelete').lower() == 'true')

class HandleRequests(ThreadingMixIn, BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.1"


#
# readBody
#
    def readBody(self,size):
        self.bodySize = (-1)
        self.bodyData = bytearray()
        if 0 < size:
            self.bodyData = self.rfile.read( size )
        else:
            self._size = self.rfile.readline()
            self.bodyEnd = (0 == self._size.find(b'\r\n'))
            if not self.bodyEnd:
                self.bodySize = int(self._size, 16)
                if 0 < self.bodySize:
                    self.bodyData = self.rfile.read( self.bodySize )
        return self.bodySize, self.bodyData


#
# readFile
#
    def readFile(self,fpath):
        wholedata = ""
        with open(fpath) as f:
            wholedata = f.read()
        return wholedata


#
# readFile Binary
#
    def readFileBin(self,fpath):
        wholedata = ""
        with open(fpath, 'rb') as f:
            wholedata = f.read()
        return wholedata


#
# Transfer Chunked Data
#
    def transferChunkedData(self, fpath, fpath_seq):
        get_chunk[fpath_seq]['chunkdata'] = b''
        get_chunk[fpath_seq]['datalen'] = 0
        get_chunk[fpath_seq]['filesize'] = os.path.getsize(fpath)

        if 0 < get_chunk[fpath_seq]['filesize']:
            get_chunk[fpath_seq]['chunkdata'] = get_chunk[fpath_seq]['fd'].read()
            get_chunk[fpath_seq]['datalen'] = len(get_chunk[fpath_seq]['chunkdata'])

        if 0 < get_chunk[fpath_seq]['datalen']:
            while True:
                get_chunk[fpath_seq]['readsize'] = get_chunk[fpath_seq]['readsize'] + get_chunk[fpath_seq]['datalen']
                if (0 < get_chunk[fpath_seq]['datalen']) and (get_chunk[fpath_seq]['chunkdata'][(get_chunk[fpath_seq]['datalen']-10):] == b"xxxxxxxxxx"):
                    if 10 < get_chunk[fpath_seq]['datalen']:
                        get_chunk[fpath_seq]['wfile'].write(b"%X\r\n" % (len(get_chunk[fpath_seq]['chunkdata'][:-10])))
                        get_chunk[fpath_seq]['wfile'].write(get_chunk[fpath_seq]['chunkdata'][:-10])
                        get_chunk[fpath_seq]['wfile'].write(b"\r\n")
                    get_chunk[fpath_seq]['wfile'].write(b"0\r\n\r\n")
                    print( datetime.datetime.now(), '    GET End', fpath )
                    get_chunk[fpath_seq]['fd'].close()
                    get_chunk[fpath_seq]['chunkdata'] = b''
                    get_chunk[fpath_seq]['datalen'] = 0
                    del get_chunk[fpath_seq]
                    break
                else:
                    if fpath_seq in get_chunk:
                        if 0 < get_chunk[fpath_seq]['datalen']:
                            get_chunk[fpath_seq]['wfile'].write(b"%X\r\n" % (get_chunk[fpath_seq]['datalen']))
                            get_chunk[fpath_seq]['wfile'].write(get_chunk[fpath_seq]['chunkdata'])
                            get_chunk[fpath_seq]['wfile'].write(b"\r\n")
                        get_chunk[fpath_seq]['chunkdata'] = b''
                        get_chunk[fpath_seq]['datalen'] = 0
                        if get_chunk[fpath_seq]['readsize'] < get_chunk[fpath_seq]['filesize']:
                            get_chunk[fpath_seq]['chunkdata'] = get_chunk[fpath_seq]['fd'].read()
                            get_chunk[fpath_seq]['datalen'] = len(get_chunk[fpath_seq]['chunkdata'])
                        else:
                            time.sleep(0.05)
                            get_chunk[fpath_seq]['filesize'] = os.path.getsize(fpath)

        if fpath_seq in get_chunk:
            get_chunk[fpath_seq]['transfer'] = False


#
# _set_headers
#
    def _set_headers(self):
        self.send_response(200)
        self.end_headers()


#
# parseURLParams
#
    def parseURLParams(self, param):
        params = {}
        queryparams = param.split("?")[1]
        urlparams = queryparams.split("&")
        for i in range(0, len(urlparams)):
            element = urlparams[i].split("=")
            params[ element[0] ] = element[1] 
        return params


#
# httpPutTarget
#
    def httpPutTarget(self, targetpath, putdata, contFlag):
        if contFlag:
            if targetpath.find('m4s') < 0:
                q_chunk[targetpath]["fd"] = open(targetpath, 'wb')
            q_chunk[targetpath]["fd"].write(putdata)
            q_chunk[targetpath]["fd"].flush()
        else:
            if q_chunk[targetpath]:
                print( datetime.datetime.now(), 'Put End', targetpath )
                q_chunk[targetpath]["fd"].write(b"xxxxxxxxxx")
                q_chunk[targetpath]["fd"].close()
                del q_chunk[targetpath]


#
# httpDeleteTarget
#
    def httpDeleteTarget(self, targetpath, headers):
        self.elements = targetpath.split("/")
        self.hostport = self.elements[2].split(":")
        self.filepath = '/'.join(self.elements[3:])
        self.filepath = "/" + self.filepath
        if 1 == len(self.hostport):
            self.hostport.append(80)


#
# do_GET
#
    def do_GET(self):
        global Observer_Start
        global get_chunk_seq
        self.paths = self.path.split("/")
        self.fpath = "/".join(self.paths[1:])

        print( datetime.datetime.now(), '    GET Start', self.fpath )
        self.fpath_seq = self.fpath + '_' + str(get_chunk_seq)
        get_chunk_seq = get_chunk_seq + 1

        if False:
            Observer_Start = True
            self.elements = self.path.split("/")
            self.dirpath = '/'.join(self.elements[1:-1])
            print( 'Observer Path:', self.dirpath )
            observer = Observer()
            # 監視するフォルダを第２引数に指定
            observer.schedule(ChangeHandler(self), './' + self.dirpath, recursive=True)
            # 監視を開始する
            observer.start()        

        if self.fpath == 'status':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write( ('Hello delivery-miffe, version:' + delivery_miffe_version + ', FileDelete:' + ("True" if FileDelete else "False")).encode('utf-8') )

        elif 0 <= self.fpath.find('.mpd') or 0 <= self.fpath.find('.m3u8'):
            get_chunk[self.fpath_seq] = {}
            get_chunk[self.fpath_seq]['fd'] = open(self.fpath, mode='rb', buffering=0)
            get_chunk[self.fpath_seq]['filesize'] = 0
            get_chunk[self.fpath_seq]['readsize'] = 0
            get_chunk[self.fpath_seq]['chunkdata'] = b''
            get_chunk[self.fpath_seq]['datalen'] = 0
            get_chunk[self.fpath_seq]['wfile'] = self.wfile

            self.send_response(200)
            self.send_header("Content-type", "application/dash+xml")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
            self.send_header("Access-Control-Expose-Headers", "Date")
            self.send_header("Connection", "close")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            get_chunk[self.fpath_seq]['transfer'] = True
            self.transferChunkedData(self.fpath, self.fpath_seq)

        elif 0 <= self.fpath.find('.m3u8'):
            fdata = self.readFile(self.fpath)
            self.send_response(200)
            self.send_header("Content-type", "application/dash+xml")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(fdata.encode('utf-8'))

        elif 0 <= self.fpath.find('.m4s'):
            self.elements = self.path.split("/")
            self.filepath = '/'.join(self.elements[1:])
            if (os.path.isfile(self.fpath)) and ((not self.filepath in q_chunk) or ((self.filepath in q_chunk) and (q_chunk[self.filepath]["read"]))) :
                get_chunk[self.fpath_seq] = {}
                print( datetime.datetime.now(), '    GET OK', self.fpath )

                get_chunk[self.fpath_seq]['fd'] = open(self.fpath, mode='rb', buffering=0)
                get_chunk[self.fpath_seq]['fend'] = False
                get_chunk[self.fpath_seq]['filesize'] = 0
                get_chunk[self.fpath_seq]['readsize'] = 0
                get_chunk[self.fpath_seq]['chunkdata'] = b''
                get_chunk[self.fpath_seq]['datalen'] = 0
                get_chunk[self.fpath_seq]['wfile'] = self.wfile

                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
                self.send_header("Access-Control-Expose-Headers", "Date")
                self.send_header("Connection", "close")
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                get_chunk[self.fpath_seq]['transfer'] = True
                self.transferChunkedData(self.fpath, self.fpath_seq)

            else:
                print( datetime.datetime.now(), '    GET NG', self.fpath )
                self.send_response(404, 'File not found')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
                self.send_header("Access-Control-Expose-Headers", "Date")
                self.send_header("Connection", "close")
                self.end_headers()

        elif 0 <= self.fpath.find('.mp4'):
            get_chunk[self.fpath_seq] = {}
            get_chunk[self.fpath_seq]['fd'] = open(self.fpath, mode='rb')
            get_chunk[self.fpath_seq]['fend'] = False
            get_chunk[self.fpath_seq]['filesize'] = 0
            get_chunk[self.fpath_seq]['readsize'] = 0
            get_chunk[self.fpath_seq]['chunkdata'] = b''
            get_chunk[self.fpath_seq]['datalen'] = 0
            get_chunk[self.fpath_seq]['wfile'] = self.wfile

            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
            self.send_header("Access-Control-Expose-Headers", "Date")
            self.send_header("Connection", "close")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            get_chunk[self.fpath_seq]['transfer'] = True
            self.transferChunkedData(self.fpath, self.fpath_seq)

        else:
            self.send_response(404, 'File not found')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
            self.send_header("Access-Control-Expose-Headers", "Date")
            self.send_header("Connection", "close")
            self.end_headers()


#
# do_POST
#
    def do_POST(self):
        self.paths = self.path.split("/")
        self.fpath = "/".join(self.paths[1:])
        if self.fpath == 'emsg':
            self.send_response(200)
            self.end_headers()
            content_len = int(self.headers.get('content-length'))
            self.post_body = self.rfile.read(content_len)
            self.putQueue(self.post_body)
        else:
            self.send_response(404)
            self.end_headers()


#
# do_PUT
#
    def do_PUT(self):
        self._set_headers()
        dt_now = datetime.datetime.now()
        self.elements = self.path.split("/")
        self.filepath = '/'.join(self.elements[1:])
        self.dirpath = '/'.join(self.elements[1:-1])
        print( datetime.datetime.now(), 'Put Start 00', self.filepath )

        if 2 < len(self.elements):
            if not (os.path.isdir(self.dirpath)):
                os.makedirs( self.dirpath )

        if not (self.filepath in q_chunk):
            print( datetime.datetime.now(), 'Put Start 01', self.filepath )
            q_chunk[self.filepath] = {"fd":0, "read":False}
            if 0 <= self.filepath.find('m4s') :
                q_chunk[self.filepath]["fd"] = open(self.filepath, 'wb')

            print( datetime.datetime.now(), 'Put Start 02a', self.filepath )
            self.chunk_no = 0
            self.put_body = self.readBody(-1)
            self.readbytes = self.put_body[0]
            print( datetime.datetime.now(), 'Put Start 02b', self.filepath, self.readbytes )
            q_chunk[self.filepath]["read"] = True

            while 0 != self.readbytes :
                if 0 < self.readbytes:
                    self.httpPutTarget(self.filepath, self.put_body[1], True)
                self.put_body = self.readBody(-1)
                self.readbytes = self.put_body[0]
            self.httpPutTarget(self.filepath, b'', False)


#
# do_DELETE
#
    def do_DELETE(self):
        global FileDelete
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header("Connection", "close")
        self.end_headers()
        if FileDelete:
            print( datetime.datetime.now(), '*** DELETE *** ', self.path )
            os.remove( '.' + self.path )

#
# logMessage
#
    def log_message(self, format, *args):
        return


host = inifile.get('DEFAULT', 'host')
port = int( inifile.get('DEFAULT', 'port') )
delivery_miffe_version = inifile.get('DEFAULT', 'version')

Observer_Start = False

address = (host, port)
print( 'start delivery_miffe port: ', port )
print( 'relay_miffe_version: ', delivery_miffe_version )
print( 'FileDelete: ', FileDelete )

ThreadingTCPServer.allow_reuse_address = True
with ThreadingTCPServer(address, HandleRequests) as server:
    server.serve_forever()

