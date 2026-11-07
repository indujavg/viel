"""Authenticated, asynchronous face-cloaking and held-out evaluation API."""
import asyncio
from contextlib import asynccontextmanager
import hmac
import io
import json
import logging
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from .faces.dataset import MAX_ARCHIVE, prepare_dataset
from .faces.fawkes import FawkesRunner, MODES
from .images import MAX_BYTES, decode_image


def create_face_app(runner=None, evaluator_factory=None, token=None, load_runner=True):
    secret = token if token is not None else os.environ.get('VIEL_API_TOKEN','')
    state={'runner':runner,'evaluator':None,'busy':False,'jobs':{}}

    @asynccontextmanager
    async def lifespan(app):
        if len(secret)<32:raise RuntimeError('Set VIEL_API_TOKEN to a private random token of at least 32 characters.')
        if state['runner'] is None and load_runner:
            try:state['runner']=await asyncio.to_thread(FawkesRunner)
            except Exception:logging.getLogger('viel').exception('Fawkes startup failed')
        yield
        tasks=[]
        for job in state['jobs'].values():
            job['cancel'].set()
            if job.get('task'):tasks.append(job['task'])
        if tasks:await asyncio.gather(*tasks,return_exceptions=True)

    app=FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
    def fail(status,message):
        return JSONResponse({'error':{'message':message}},status_code=status,headers={'Cache-Control':'no-store'})

    @app.middleware('http')
    async def auth(request,call_next):
        if not secret or not hmac.compare_digest(request.headers.get('authorization',''),f'Bearer {secret}'):
            return fail(401,'Missing or invalid server-side credentials.')
        response=await call_next(request);response.headers['Cache-Control']='no-store';return response

    @app.get('/face/health')
    async def health():
        return {'ready':state['runner'] is not None,'busy':state['busy'],'method':'upstream-fawkes',
                'purpose':'facial-recognition-training','modes':list(MODES)}

    def execute(job,data,kind,mode,target):
        def progress(message):job['message']=message
        try:
            if job['cancel'].is_set():raise RuntimeError('Cancelled.')
            if kind=='cloak':
                progress('Running Fawkes face cloaking')
                image=decode_image(data)
                result,report=state['runner'].protect(image,mode,job['cancel'])
                job.update(result=result,report=report,content_type='image/png',filename='viel-cloaked.png')
            else:
                with tempfile.TemporaryDirectory(prefix='viel-proof-') as folder:
                    rows=prepare_dataset(data,Path(folder))
                    if state['evaluator'] is None:
                        progress('Loading the independent face-recognition evaluator')
                        if evaluator_factory:
                            state['evaluator']=evaluator_factory()
                        else:
                            from .faces.evaluator import FaceEvaluator
                            state['evaluator']=FaceEvaluator()
                    report=state['evaluator'].evaluate(rows,target,state['runner'],mode,job['cancel'],progress)
                    job.update(result=json.dumps(report,indent=2).encode(),report=report,
                               content_type='application/json',filename='viel-proof.json')
            if job['cancel'].is_set():raise RuntimeError('Cancelled.')
            job.update(status='done',message='Completed')
        except ValueError as error:
            job.update(status='failed',message=str(error))
        except Exception:
            logging.getLogger('viel').exception('Face experiment failed')
            job.update(status='failed',message='Experiment cancelled or failed. Check the backend output; no success claim is available.')
        finally:
            job['finished']=time.monotonic()
            if job['cancel'].is_set():
                job.pop('result',None);job.pop('report',None);job.update(status='cancelled',message='Cancelled')

    async def run(job,data,kind,mode,target):
        try:await asyncio.to_thread(execute,job,data,kind,mode,target)
        finally:state['busy']=False

    @app.post('/face/jobs')
    async def start(request:Request,kind:str='cloak',mode:str='mid',target:str=''):
        if kind not in ('cloak','proof') or mode not in MODES:return fail(422,'Choose cloak/proof and low/mid/high.')
        if state['runner'] is None:return fail(503,'The Fawkes service is not configured. Use the face-cloaking notebook.')
        if state['busy']:return fail(429,'Another face experiment is running.')
        if kind=='proof' and (not target or len(target)>32):return fail(422,'Provide the target identity folder name.')
        expected=('image/png','image/jpeg') if kind=='cloak' else ('application/zip','application/x-zip-compressed')
        if request.headers.get('content-type','').split(';')[0] not in expected:return fail(415,'Send a PNG/JPEG for cloaking or ZIP for proof.')
        state['busy']=True
        queued=False
        try:
            data=bytearray();limit=MAX_BYTES if kind=='cloak' else MAX_ARCHIVE
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data)>limit:return fail(413,'The uploaded file is too large.')
            if not data:return fail(422,'The uploaded file is empty.')
            # Completed records expire after 30 minutes; cap memory to four records.
            now=time.monotonic()
            for key in list(state['jobs']):
                if now-state['jobs'][key].get('finished',now)>1800:del state['jobs'][key]
            while len(state['jobs'])>=4:del state['jobs'][next(iter(state['jobs']))]
            identifier=secrets.token_urlsafe(24)
            job={'status':'running','message':'Starting','cancel':threading.Event(),'created':now}
            state['jobs'][identifier]=job
            job['task']=asyncio.create_task(run(job,bytes(data),kind,mode,target))
            queued=True
            return JSONResponse({'id':identifier},status_code=202)
        finally:
            if not queued:state['busy']=False

    def find_job(identifier):
        job=state['jobs'].get(identifier)
        if job and time.monotonic()-job.get('finished',time.monotonic())>1800:
            del state['jobs'][identifier]
            return None
        return job

    @app.get('/face/jobs/{identifier}')
    async def status(identifier:str):
        job=find_job(identifier)
        if not job:return fail(404,'Experiment expired or not found.')
        return {'status':job['status'],'message':job['message'],'report':job.get('report')}

    @app.get('/face/jobs/{identifier}/result')
    async def result(identifier:str):
        job=find_job(identifier)
        if not job or job['status']!='done':return fail(404,'No completed result is available.')
        return Response(job['result'],media_type=job['content_type'],headers={
            'Content-Disposition':f'attachment; filename="{job["filename"]}"'})

    @app.delete('/face/jobs/{identifier}')
    async def cancel(identifier:str):
        job=find_job(identifier)
        if not job:return fail(404,'Experiment not found.')
        job['cancel'].set()
        if job['status']=='done':
            job.pop('result',None);job.pop('report',None);job.update(status='cancelled',message='Deleted')
        return {'cancel_requested':True}
    return app

app=create_face_app()
