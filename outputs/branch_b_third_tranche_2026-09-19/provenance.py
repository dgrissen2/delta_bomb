"""Conservative publication-label checks for both saved-note metadata formats."""
from __future__ import annotations

from datetime import datetime, time
import re
from zoneinfo import ZoneInfo

STAMP = re.compile(r'([A-Za-z]+\s+\d{1,2},\s+\d{4}\s+at\s+\d{1,2}:\d{2}\s+[AP]M)'
                   r'(?:\s+(ET|EST|EDT))?\b', re.I)
ET = ZoneInfo('America/New_York')


def publication_timing(text: str, day: str) -> dict:
    """Require all publication labels to be same-day and strictly before09:30 ET.

    Older captures use Published and can have different preopen wrapper/content
    times. Preserve that discrepancy, conservatively using the latest label.
    A dated explicit Eastern heading is mandatory; scraped-at never establishes
    historical availability. These labels cannot prove absence of later revisions.
    """
    result = {'preopen': False, 'labels': [], 'latest_labeled_time': None,
              'time_labels_differ': False, 'issue': None}
    labels, explicit = [], 0
    try:
        for line in text.splitlines()[:14]:
            stripped = line.strip()
            metadata = stripped.startswith(('**Date:**', '**Published:**'))
            if not metadata and not stripped.startswith('#'):
                continue
            match = STAMP.search(stripped)
            if not match:
                if metadata:
                    raise ValueError('Malformed publication metadata')
                # A non-dated article heading marks the end of publication labels.
                if stripped.startswith('#') and labels:
                    break
                continue
            stamp = datetime.strptime(match[1].upper(), '%B %d, %Y at %I:%M %p').replace(tzinfo=ET)
            zone = match[2].upper() if match[2] else None
            if not metadata and zone is None:
                raise ValueError('Publication heading lacks explicit Eastern timezone')
            explicit += int(not metadata and zone is not None)
            if zone in {'EST', 'EDT'} and zone != stamp.tzname():
                raise ValueError('Eastern DST label conflicts with date')
            if stamp.date().isoformat() != day:
                raise ValueError('Publication date differs from session')
            labels.append(stamp)
            result['labels'].append({'extract': stripped, 'timestamp': stamp.isoformat()})
        if not labels or not explicit:
            raise ValueError('No explicit Eastern publication heading')
        latest = max(labels)
        result.update(latest_labeled_time=latest.isoformat(),
                      time_labels_differ=len(set(labels)) > 1,
                      preopen=latest.time() < time(9, 30))
        if not result['preopen']:
            result['issue'] = 'At least one publication label is at/after open'
    except ValueError as error:
        result['issue'] = str(error)
    return result


def assign_cohort(day: str, original: set[str], added: set[str], development: set[str]) -> str:
    """Keep earlier research dates out of the third-tranche evidence."""
    if original & added or original & development or added & development:
        raise ValueError('Prior cohort sets overlap')
    for name, dates in [('original_50', original), ('additional_100', added),
                        ('development_10', development)]:
        if day in dates:
            return name
    return 'third_tranche'
