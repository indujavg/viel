import time
import unittest
from fastapi.testclient import TestClient
from PIL import Image
from backend.face_app import create_face_app
from backend.images import png_bytes

TOKEN='test-fixture-only-'+'x'*40
HEADERS={'Authorization':'Bearer '+TOKEN,'Content-Type':'image/png'}
class Runner:
    def protect(self,image,mode,cancel):return png_bytes(image),{'method':'test-fixture'}
class FailedRunner:
    def protect(self,*args):raise ValueError('No face detected.')

class FaceApiTest(unittest.TestCase):
    def wait(self,client,identifier):
        for _ in range(100):
            result=client.get('/face/jobs/'+identifier,headers=HEADERS).json()
            if result['status']!='running':return result
            time.sleep(.02)
        self.fail('Job did not finish')

    def test_authenticated_job_and_deletion(self):
        with TestClient(create_face_app(Runner(),token=TOKEN)) as client:
            self.assertEqual(client.get('/face/health').status_code,401)
            response=client.post('/face/jobs',headers=HEADERS,content=png_bytes(Image.new('RGB',(64,64))))
            self.assertEqual(response.status_code,202)
            identifier=response.json()['id']
            self.assertEqual(self.wait(client,identifier)['status'],'done')
            self.assertEqual(client.get('/face/jobs/'+identifier+'/result',headers=HEADERS).headers['content-type'],'image/png')
            client.delete('/face/jobs/'+identifier,headers=HEADERS)
            self.assertEqual(client.get('/face/jobs/'+identifier+'/result',headers=HEADERS).status_code,404)

    def test_failure_produces_no_result(self):
        with TestClient(create_face_app(FailedRunner(),token=TOKEN)) as client:
            response=client.post('/face/jobs',headers=HEADERS,content=png_bytes(Image.new('RGB',(64,64))))
            identifier=response.json()['id']
            result=self.wait(client,identifier)
            self.assertEqual(result['status'],'failed');self.assertIn('No face',result['message'])
            self.assertEqual(client.get('/face/jobs/'+identifier+'/result',headers=HEADERS).status_code,404)

    def test_offline_and_bad_content_type(self):
        with TestClient(create_face_app(token=TOKEN,load_runner=False)) as client:
            self.assertEqual(client.post('/face/jobs',headers=HEADERS,content=b'x').status_code,503)
        with TestClient(create_face_app(Runner(),token=TOKEN)) as client:
            self.assertEqual(client.post('/face/jobs',headers={**HEADERS,'Content-Type':'text/plain'},content=b'x').status_code,415)

if __name__=='__main__':unittest.main()
