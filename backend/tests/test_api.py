import unittest
from fastapi.testclient import TestClient
from PIL import Image
from backend.app import create_app
from backend.images import png_bytes

TOKEN='test-only-not-a-real-secret-'+'x'*32
HEADERS={'Authorization':f'Bearer {TOKEN}','Content-Type':'image/png'}

class TestEngine:
    def protect(self,image,profile,seed,cancel):
        return png_bytes(image),{'status':'experimental-unverified'}

class FailedEngine:
    def protect(self,*args):raise RuntimeError('private error detail')

class ApiTest(unittest.TestCase):
    def setUp(self):self.image=png_bytes(Image.new('RGB',(64,64)))

    def test_auth_and_success(self):
        with TestClient(create_app(TestEngine(),TOKEN)) as client:
            self.assertEqual(client.get('/health').status_code,401)
            self.assertTrue(client.get('/health',headers=HEADERS).json()['ready'])
            response=client.post('/protect',headers=HEADERS,content=self.image)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers['content-type'],'image/png')
            self.assertEqual(response.headers['cache-control'],'no-store')
            self.assertIn('experimental-unverified',response.headers['x-viel-report'])

    def test_validation(self):
        with TestClient(create_app(TestEngine(),TOKEN)) as client:
            self.assertEqual(client.post('/protect?profile=unknown',headers=HEADERS,content=self.image).status_code,422)
            self.assertEqual(client.post('/protect',headers=HEADERS,content=b'bad').status_code,422)
            self.assertEqual(client.post('/protect',headers={**HEADERS,'Content-Type':'text/plain'},content=b'bad').status_code,415)
            self.assertEqual(client.post('/protect',headers=HEADERS,content=b'x'*(10*1024*1024+1)).status_code,413)

    def test_unavailable_and_failure_never_return_image(self):
        with TestClient(create_app(token=TOKEN,load_engine=False)) as client:
            self.assertFalse(client.get('/health',headers=HEADERS).json()['ready'])
            self.assertEqual(client.post('/protect',headers=HEADERS,content=self.image).status_code,503)
        with TestClient(create_app(FailedEngine(),TOKEN)) as client:
            response=client.post('/protect',headers=HEADERS,content=self.image)
            self.assertEqual(response.status_code,500)
            self.assertNotIn('private error detail',response.text)

if __name__=='__main__':unittest.main()
