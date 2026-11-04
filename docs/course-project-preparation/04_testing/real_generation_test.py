import os,sys,time,traceback
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root))
os.environ['MUSEGARDEN_DATA_ROOT']=str(root/'development/test_artifacts/course-real-generation')
os.environ['MUSEGARDEN_TEST_TERRAIN_GARDEN']='1'
from scripts.run_garden_preview_api import seed_preview_service,DATA_ROOT
from application.creation_service import CreationService
from music_engine import AudioStore,MusicGenerationService
from music_engine.providers import AceStepClient
start=time.monotonic()
try:
 _,garden_id=seed_preview_service()
 service=CreationService(data_root=DATA_ROOT,music_service=MusicGenerationService(AceStepClient(),AudioStore(DATA_ROOT)),flower_size_roll=lambda:1.0)
 result=service.create_memory('今天我完成了一件期待已久的小事，感到平静而开心。',garden_id,(22,18))
 print('PASS: real Ollama and ACE-Step creation; elapsed_seconds=%.2f; music_version=%s; flower=%s; position=(%s,%s)'%(time.monotonic()-start,result['music']['version'],result['flower']['species'],result['planting']['x'],result['planting']['y']))
except Exception:
 print('FAIL: real creation; elapsed_seconds=%.2f'%(time.monotonic()-start));traceback.print_exc();sys.exit(1)
