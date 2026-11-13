"""Offline validation of real-video quality tooling with synthetic records."""
import csv
import json

from scripts import quality_pilot_run as runner
from scripts import quality_pilot_report as report


COLUMNS = [
    'video_id', 'source_note', 'orientation', 'community_truth',
    'area_truth_sqm', 'bedroom_truth', 'price_truth_wan',
    'other_prices_truth', 'floor_truth', 'on_screen_text_truth',
    'oral_price_truth', 'notes',
]


def write_rows(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def truth(video_id='sample_01'):
    return dict(video_id=video_id, source_note='self filmed - permission retained',
                orientation='vertical', community_truth='东湖花园', area_truth_sqm='160',
                bedroom_truth='4', price_truth_wan='365',
                other_prices_truth='380:historical;100:deposit', floor_truth='',
                on_screen_text_truth='东湖花园|报价365万|建面160㎡',
                oral_price_truth='', notes='')


def result(*, valid=True):
    return dict(ok=True, hints={
        'price_mentions_wan': [380.0, 365.0, 100.0],
        'area_mentions_sqm': [160.0], 'bedroom_mentions': [4],
        'community_mentions': ['东湖花园']},
        ocr={'engine': 'rapidocr' if valid else 'mock',
             'status': 'ok', 'items': [
                 {'text': '东湖花园'}, {'text': '报价365万'},
                 {'text': '建面160m²'}]})


def test_runner_rejects_unsafe_video_ids(tmp_path):
    for value in ('../hidden', 'nested/video', 'abc;echo', '.hidden', 'x\\y'):
        try:
            runner._video_path(tmp_path, value)
        except ValueError:
            pass
        else:
            raise AssertionError('accepted unsafe video_id: ' + value)


def test_runner_rejects_duplicate_and_symlink_media(tmp_path):
    (tmp_path / 'one.mp4').write_bytes(b'data')
    (tmp_path / 'one.mov').write_bytes(b'data')
    try:
        runner._video_path(tmp_path, 'one')
    except ValueError as exc:
        assert 'ambiguous' in str(exc)
    else:
        raise AssertionError('ambiguity not detected')
    (tmp_path / 'one.mov').unlink()
    assert runner._video_path(tmp_path, 'one').name == 'one.mp4'
    (tmp_path / 'link.mp4').symlink_to(tmp_path / 'one.mp4')
    try:
        runner._video_path(tmp_path, 'link')
    except ValueError:
        pass
    else:
        raise AssertionError('media symlink accepted')


def test_report_normalizes_equivalent_area_units():
    assert report.normalize(' 建面 160㎡ ') == report.normalize('建面160m²')
    assert report.parse_time('980600000 maximum resident set size\nreal 0.56\n')['max_rss_mb'] == 935.2
    assert report.parse_time('Maximum resident set size (kbytes): 491520\nreal 0.7\n')['max_rss_mb'] == 480.0


def test_report_price_inclusion_and_other_price_check():
    checks, missing, line_hits = report._field_checks(truth(), result())
    assert all(checks.values()), (checks, missing)
    assert missing == []
    assert line_hits == (3, 3)
    with_extra = result()
    with_extra['hints']['price_mentions_wan'].remove(380.0)
    checks, missing, _ = report._field_checks(truth(), with_extra)
    assert checks['price'] is True
    assert checks['other_prices'] is False
    assert missing == [380.0]
    mocked, _, _ = report._field_checks(truth(), result(valid=False))
    assert not any(mocked.values())


def test_report_missing_video_counts_as_failure_not_skipped(tmp_path, capsys):
    csv_file = tmp_path / 'truth.csv'
    write_rows(csv_file, [truth('first'), truth('second')])
    (tmp_path / 'first.result.json').write_text(json.dumps(result()), encoding='utf-8')
    (tmp_path / 'first.time.log').write_text('real 0.6\n', encoding='utf-8')
    assert report.main(['--csv', str(csv_file), '--dir', str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert 'second | price=FAIL' in out
    assert 'price 1/2' in out
    assert 'failed_videos 1/2' in out


def test_runner_uses_only_real_ocr_and_rejects_missing_rights(tmp_path, monkeypatch):
    csv_file = tmp_path / 'truth.csv'
    row = truth()
    missing_rights = truth('missing_rights')
    missing_rights['source_note'] = ''
    write_rows(csv_file, [row, missing_rights])
    (tmp_path / 'sample_01.mp4').write_bytes(b'synthetic video placeholder')
    known = tmp_path / 'communities.txt'
    known.write_text('东湖花园\n', encoding='utf-8')

    def fake_execute(args, timeout):
        output = args[args.index('--json-out') + 1]
        with open(output, 'w', encoding='utf-8') as handle:
            json.dump(result(), handle)
        return 0, '', '', 0.01

    monkeypatch.setattr(runner, '_execute', fake_execute)
    assert runner.main(['--csv', str(csv_file), '--dir', str(tmp_path),
                        '--known-communities', str(known)]) == 1
    assert (tmp_path / 'sample_01.result.json').exists()
    assert not (tmp_path / 'missing_rights.result.json').exists()


def test_runner_fails_if_real_ocr_unavailable(tmp_path, monkeypatch):
    csv_file = tmp_path / 'truth.csv'
    write_rows(csv_file, [truth()])
    (tmp_path / 'sample_01.mp4').write_bytes(b'synthetic video placeholder')
    known = tmp_path / 'communities.txt'
    known.write_text('东湖花园\n', encoding='utf-8')

    def fake_execute(args, timeout):
        output = args[args.index('--json-out') + 1]
        with open(output, 'w', encoding='utf-8') as handle:
            json.dump(result(valid=False), handle)
        return 0, '', '', 0.01

    monkeypatch.setattr(runner, '_execute', fake_execute)
    assert runner.main(['--csv', str(csv_file), '--dir', str(tmp_path),
                        '--known-communities', str(known)]) == 1


def test_runner_removes_stale_output_when_media_disappears(tmp_path, monkeypatch):
    csv_file = tmp_path / 'truth.csv'
    write_rows(csv_file, [truth('missing')])
    (tmp_path / 'missing.result.json').write_text(json.dumps(result()), encoding='utf-8')
    (tmp_path / 'missing.time.log').write_text('real 0.5', encoding='utf-8')
    known = tmp_path / 'communities.txt'
    known.write_text('东湖花园\n', encoding='utf-8')
    monkeypatch.setattr(runner, '_execute', lambda *a: (_ for _ in ()).throw(
        AssertionError('missing video should never execute')))
    assert runner.main(['--csv', str(csv_file), '--dir', str(tmp_path),
                        '--known-communities', str(known)]) == 1
    assert not (tmp_path / 'missing.result.json').exists()
    assert not (tmp_path / 'missing.time.log').exists()
