"""Keep daily catalog coverage while rotating unchanged release detail checks."""
import json
from pathlib import Path


def load_previous(path):
    path=Path(path)
    if not path.is_file():return []
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,list):raise ValueError('Previous catalog must be a list')
    return value


def select_daily_versions(items,previous,standardize,rotation=50):
    old={str(row['project_id']):row for row in previous if row.get('project_id')}
    changed=[];unchanged=[]
    for item in items:
        current=standardize(item);ident=str(current.get('project_id') or '')
        prior=old.get(ident)
        # Absent source dates are unknown, not evidence that every old project
        # changed. They participate in the bounded oldest-attempt rotation.
        modified=str(current.get('date_modified') or '')
        version_id=str(current.get('catalog_version_id') or '')
        prior_version_id=str(prior.get('catalog_version_id') or '') if prior else ''
        if prior is None or prior.get('version_refresh_pending') is True or (modified and modified!=str(prior.get('date_modified') or '')) or (version_id and prior_version_id and version_id!=prior_version_id):
            changed.append(item)
        else:
            unchanged.append((str(prior.get('version_attempted_at') or prior.get('version_checked_at') or ''),ident,item))
    unchanged.sort(key=lambda row:(row[0],row[1]))
    return changed+[row[2] for row in unchanged[:max(0,int(rotation))]]


def retain_cached_versions(current,prior):
    if not prior:return
    fresh=any(current.get(field) for field in ('versions_data','releases_data','releases'))
    if not fresh:
        for field in ('versions_data','releases_data','releases','latest_version','version_checked_at','download_links'):
            if prior.get(field):current[field]=prior[field]
        if prior.get('has_server'):current['has_server']=True
    if not current.get('version_attempted_at') and prior.get('version_attempted_at'):
        current['version_attempted_at']=prior['version_attempted_at']
