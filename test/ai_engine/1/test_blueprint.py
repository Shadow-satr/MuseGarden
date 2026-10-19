"""
测试 Music Blueprint 数据结构
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3] 
if str(PROJECT_ROOT) not in sys.path: 
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from test.output_format import format_record


blueprint = MusicBlueprint(

    primary_emotion="relief",

    secondary_emotions=[
        "fatigue",
        "achievement"
    ],

    energy=0.55,

    valence=0.72,

    tempo=92,

    key="C Major",

    instruments=[
        "acoustic_guitar",
        "soft_piano"
    ],

    texture="warm",

    scene="night",

    progression="restrained_to_open"
)

print(format_record(blueprint.model_dump()))
