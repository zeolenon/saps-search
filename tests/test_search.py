import unittest
from types import SimpleNamespace
from urllib.parse import parse_qs
import httpx
from saps_search.auth import SAPSCredentials
from saps_search.client import SAPSClient, SAPSAuthError, SAPSRequestError
from saps_search.legacy import ExistingSessionSearch
from saps_search.batch import search_rows

HTML = '''<table><thead><tr><th>Nome Fantasia</th><th>CNPJ/CPF</th></tr></thead>
<tbody><tr><td>EMPRESA FICTICIA</td><td>00.000.000/0000-00</td></tr>
<tr><td>FILIAL FICTICIA</td><td>00000000000000</td></tr></tbody></table>'''

class SearchTests(unittest.TestCase):
    def client(self, handler):
        client = SAPSClient(SAPSCredentials('fictional', 'fictional'))
        client._http.close()
        client._http = httpx.Client(transport=httpx.MockTransport(handler))
        client._authenticated = True
        self.addCleanup(client.close)
        return client

    def test_client_document_form_and_exact_matches(self):
        def handler(req):
            self.assertEqual(req.url.path, '/serten/clientes')
            form = parse_qs(req.content.decode())
            self.assertEqual(form['data[Cliente][num_cnpj]'], ['00000000000000'])
            self.assertEqual(form['data[Filter][filterFormId]'], ['Cliente'])
            return httpx.Response(200, text=HTML)
        result = self.client(handler).search_client(cnpj='00.000.000/0000-00')
        self.assertEqual(result['exact_document_matches'], 2)

    def test_building_fields_and_pagination(self):
        def handler(req):
            form = parse_qs(req.content.decode())
            self.assertEqual(req.url.path, '/serten/edificacoes')
            self.assertNotIn('data[Filter][filterFormId]', form)
            self.assertEqual(form['data[Edificacao][dsc_nomefantasia]'], ['EMPRESA'])
            self.assertEqual(form['data[Edificacao][dsc_cidade]'], ['CIDADE FICTICIA'])
            return httpx.Response(200, text=HTML + '<a rel="next" href="?page=2">Next</a>')
        result = self.client(handler).search_building(name='empresa', city='CIDADE FICTICIA')
        self.assertEqual(result['outcome'], 'incomplete')
        self.assertTrue(result['has_next_page'])

    def test_redesim(self):
        def handler(req):
            self.assertEqual(parse_qs(req.content.decode())['data[Cliente][prot_redesim]'], ['FICTICIO'])
            return httpx.Response(200, text=HTML)
        self.client(handler).search_client(redesim='FICTICIO')

    def test_timeout_no_retry(self):
        calls = []
        def handler(req):
            calls.append(req)
            raise httpx.ReadTimeout('fictional', request=req)
        with self.assertRaises(SAPSRequestError):
            self.client(handler).search_building(cnpj='00000000000000')
        self.assertEqual(len(calls), 1)

    def test_batch_deduplicates(self):
        calls = []
        def handler(req):
            calls.append(req)
            return httpx.Response(200, text=HTML)
        rows = [{'target': 'client', 'cnpj_cpf': '00000000000000'}] * 2
        self.assertEqual(len(search_rows(self.client(handler), rows)), 2)
        self.assertEqual(len(calls), 1)

    def test_existing_session_never_logs_in(self):
        calls = []
        def handler(req):
            calls.append(req)
            self.assertEqual(req.extensions['timeout']['read'], 90.0)
            return httpx.Response(302, headers={'location': '/serten/usuarios/login'})
        http = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(http.close)
        legacy = SimpleNamespace(_client=http, _cookies={'fictional': 'fictional'})
        adapter = ExistingSessionSearch(legacy)
        with self.assertRaises(SAPSAuthError):
            adapter.search_client(cnpj='00000000000000')
        self.assertEqual(len(calls), 1)
        self.assertIs(adapter._http, http)
        self.assertEqual(legacy._cookies, {'fictional': 'fictional'})

    def test_existing_session_success(self):
        http = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, text=HTML)))
        self.addCleanup(http.close)
        result = ExistingSessionSearch(SimpleNamespace(_client=http, _cookies={'fictional': 'fictional'})).search_building(cnpj='00000000000000')
        self.assertEqual(result['returned_rows'], 2)

    def test_missing_table_and_invalid_filters(self):
        client = self.client(lambda req: httpx.Response(200, text='<html></html>'))
        with self.assertRaises(SAPSRequestError):
            client.search_client(cnpj='00000000000000')
        with self.assertRaises(ValueError):
            client.search_client(cnpj='0', name='EMPRESA')

if __name__ == '__main__':
    unittest.main()
