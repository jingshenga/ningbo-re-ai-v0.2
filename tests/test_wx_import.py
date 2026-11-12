from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

script=Path(__file__).resolve().parents[1]/'scripts'/'import_channels_export.py'
spec=spec_from_file_location('wximport',script)
module=module_from_spec(spec)
spec.loader.exec_module(module)


def test_map_channel_rows_and_skip_missing_ids():
    x,missing=module.map_rows([{'id':'v1','title':'房产视频','author':'中介A'},
                               {'title':'no-id'}],account_id='abc')
    assert len(x['items'])==1
    assert x['items'][0]['platform']=='wechat_channels'
    assert x['items'][0]['account_id']=='abc'
    assert missing==[1]
