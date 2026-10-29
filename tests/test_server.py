import http.client
import json
import tempfile
import threading
import unittest
from tests.helpers import write_package
from review_workbench.server import make_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();write_package(self.tmp.name)
        self.server=make_server(self.tmp.name,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.origin=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()

    def request(self,method,path,body=None,authorized=True,origin=True):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        headers={'Content-Type':'application/json'}
        if authorized:headers['X-Review-Token']=self.server.token
        if origin:headers['Origin']=self.origin
        conn.request(method,path,json.dumps(body) if body is not None else None,headers)
        result=conn.getresponse();data=result.read();status=result.status;ctype=result.getheader('Content-Type');conn.close()
        return status,data,ctype

    def test_read_write_and_stale_revision(self):
        code,raw,_=self.request('GET','/api/state');self.assertEqual(code,200)
        state=json.loads(raw);draft=state['drafts'];draft['items']['one']={'mode':'accept'}
        self.assertEqual(self.request('PUT','/api/drafts',{'drafts':draft,'expected_revision':0})[0],200)
        self.assertEqual(self.request('PUT','/api/drafts',{'drafts':draft,'expected_revision':0})[0],409)
        self.assertEqual(self.request('POST','/api/submit',{'item_ids':['one'],'expected_revision':1})[0],200)

    def test_auth_origin_and_traversal(self):
        self.assertEqual(self.request('GET','/api/state',authorized=False)[0],403)
        self.assertEqual(self.request('PUT','/api/drafts',{},origin=False)[0],403)
        self.assertEqual(self.request('GET','/static/../../requirements.txt')[0],400)
        self.assertEqual(self.request('GET','/assets/package.json')[0],404)

    def test_index_and_exclusive_service(self):
        code,raw,mime=self.request('GET','/');self.assertEqual(code,200);self.assertIn('text/html',mime)
        self.assertIn('校对工作台'.encode(),raw)
        with self.assertRaises(Exception):make_server(self.tmp.name,0)

    def test_malformed_body_is_error(self):
        self.assertEqual(self.request('POST','/api/submit',[])[0],400)


if __name__=='__main__':unittest.main()
