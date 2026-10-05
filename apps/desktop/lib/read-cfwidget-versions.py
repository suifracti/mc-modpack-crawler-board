"""Small-window cached metadata reader; no files are downloaded."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from curseforge_cfwidget import get_project, project_releases, WidgetRefusal


def read_versions(ident):
    project, observation = get_project(ident)
    versions = [{'id': row['id'], 'displayName': row['version_number'],
        'fileName': row['version_number'], 'fileDate': row['date_published'][:10],
        'gameVersions': row['game_versions'] + row['loaders'],
        'version_number': row['version_number'], 'date_published': row['date_published'],
        'files': row['files'],
        'sourceUrl': row['files'][0]['url'], 'downloadUrl': ''}
        for row in project_releases(project)]
    return {'versions': versions, 'fetchedAt': observation['fetchedAt'], 'provider': 'cfwidget',
        'providerLastFetch': observation.get('providerLastFetch'),
        'coverage': 'known-project-cached-metadata-only',
        'note': 'CFWidget公开缓存；上游抓取时间可能未知，未提供文件下载。'}


if __name__ == '__main__':
    try:
        result = read_versions(sys.argv[1])
    except Exception as error:
        result = {'error': str(error), 'sourceStopped': isinstance(error, WidgetRefusal)}
    print(json.dumps(result, ensure_ascii=False))
