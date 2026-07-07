import requests
from datetime import datetime as dt
from time import sleep
import json
import mimetypes
from os import mkdir, listdir
from os.path import exists

__version__ = "1.0.0"

folder='Downloads/trtest'
src_lang='ja'
out_lang='en'


ua={'User-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36'}


uid={}
def getUserId():
  if uid.get('cr',0)>0:
    return uid['user_id']
  user_id=f'temp_fp_{md5(str(dt.now().timestamp()).encode()).hexdigest()[:24]}'
  print(f'**Session {user_id}')
  uid['user_id']=user_id
  uid['cr']=3
  return user_id

def translate(imagePath, slang='ja', tlang='en'):
  base,fn=imagePath.rsplit('/',maxsplit=1)
  mime=mimetypes.guess_type(imagePath)[0]
  # make sure it's an image'
  if not mime.startswith('image'): return

  print(fn)
  # check already exists, if you want to redo just delete
  if not exists(f'{base}/tr/'):
    mkdir(f'{base}/tr/')
  if exists(f'{base}/tr/{fn}'):
    print('  Done')
    return

  ses=requests.Session()
  headers=ua.copy()
  r=ses.get('https://www.mangatranslate.com', headers=headers)

  user_id=getUserId()
  csrf=f'{int(user_id[-24:],16)}'

  r=ses.get(f'https://www.mangatranslate.com/api/v1/credits/get_credits/{user_id}', headers=headers, cookies={'csrftoken':csrf})
  cr=r.json()['data']['total_credits']
  print(f'  Credits {cr}')
  uid['cr']=cr
  if not cr:
    uid.clear()
    raise Exception('No credits on create')
  with open(imagePath,'rb') as fh:
    idat={
      'user_id':user_id,
      'task_name':dt.now().strftime('task-%Y-%m-%d-%H-%M-%S'),
      'source_language':slang, 'target_language':tlang, 'recognition_model':'CTD',
      'font_style':'auto', 'font_weight':'normal', 'spacing_x':'0', 'spacing_y':'0.15',
      'text_direction_preference':'auto', 'expected_total':'1',
      'files':json.dumps([{"index":0, "filename":fn, "content_type":mime, "size":len(fh.read())}]),
    }
    files=dict((k,(None,v)) for k,v in idat.items())
    headers.update({'x-csrf-token':csrf})

    # initialize upload, get submission URL and task
    r=ses.post('https://www.mangatranslate.com/api/v1/manga/translation/init', files=files, headers=headers, cookies={'csrftoken':csrf})
    r=r.json()
    if r.get('error'):
      try:
        e=r['error']['message']
      except TypeError:
        e=r['error']
      raise Exception(e)
    uurl=f"https://www.mangatranslate.com{r['upload_plan']['providers'][1]['url']}"
    task=r['task_id']

    udat={
      'user_id':user_id, 'index':0,
      'source_language':slang, 'target_language':tlang
    }
    fh.seek(0)

    # Upload
    uid['cr']-=1
    print('  Uploading', end=' ', flush=True)
    u=ses.post(uurl, data=udat,files={'file':fh}, headers=headers, cookies={'csrftoken':csrf})
    c=ses.post(f"https://www.mangatranslate.com/api/v1/manga/translation/{task}/upload-complete", headers=headers, cookies={'csrftoken':csrf})
    print('Done')
  status=''
  sc=0
  while status != 'completed':
    sleep(1)
    print(f'\r  Status ', end='', flush=True)
    stat=ses.get(f'https://www.mangatranslate.com/api/v1/manga/translation-tasks/{task}/images?_={dt.now().timestamp()}')
    stat=stat.json()
    cs=stat['items'][0]['status']
    if cs==status: sc+=1
    else: sc=0
    print(f'{cs}{"."*(sc%4):3}', end='')
    status=cs
    if stat['items'][0]['error']:
      raise Exception(stat['items'][0]['error'])
  print()
  print("  Downloading", end=' ', flush=True)
  for x in range(5):
    try:
      tri=ses.get(stat['items'][0]['translated_url'], headers=headers, timeout=30)
    except KeyboardInterrupt: raise
    except:
      if x==4: raise
      print(f"\r  Downloading {x+1}", end=' ', flush=True)
    else: break
  with open(f'{base}/tr/{fn}','wb') as fh:
    fh.write(tri.content)
  print('Done')

for f in listdir(folder):
  if not '.' in f: continue
  folder_path = folder if folder.endswith('/') else folder + '/'
  translate(folder_path + f, src_lang, out_lang)






