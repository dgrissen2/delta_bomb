"""Prior-session issuer weights; exact dated failures remain explicit."""
from __future__ import annotations

from datetime import datetime, timezone
import json

import pandas as pd
import requests

from inputs import DATA, OUT, all_dates, digest, load, selected_dates, write_frame, write_json

legacy = load('full_issuer_weights',OUT.parent/'b06_sector_weighted_iv_2026-09-19/weights.py')
PRIOR = legacy.DATA


def validation_paths() -> tuple:
    """A changed parser gets a new derived version; raw receipts are never deleted."""
    parser_sha = digest(OUT.parent/'b06_sector_weighted_iv_2026-09-19/weights.py')
    directory = DATA/'weights'/'validation_runs'/parser_sha[:16]
    return directory/'sector_weights.parquet',directory/'validation_ledger.parquet'


def validate_cached(receipt: dict, source, day: str, prior: str) -> tuple:
    """Re-validate retrieved bytes even when an older parser rejected them."""
    row = dict(date=day,as_of_date=prior,raw_path=str(source),
               original_receipt_status=receipt['status'],retrieval_status='not_retrieved',
               validation_status='not_attempted',reason='')
    if not source.exists() or not receipt.get('sha256'):
        row['reason'] = receipt.get('reason','no_response_body')
        return None,row
    if digest(source) != receipt['sha256']:
        raise ValueError(f'Changed raw issuer response: {source}')
    row['raw_sha256'] = receipt['sha256']
    if receipt.get('http_status',200) != 200:
        row.update(retrieval_status='http_failure',reason=receipt.get('reason','HTTP error'))
        return None,row
    row['retrieval_status'] = 'retrieved'
    try:
        _,sectors,_ = legacy.parse_holdings(json.loads(source.read_text()),prior)
    except (ValueError,KeyError) as exc:
        row.update(validation_status='rejected',reason=str(exc))
        return None,row
    sectors.insert(0,'date',day)
    row['validation_status'] = 'accepted'
    return sectors,row


def combine_validated(rows: list[pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame(
        columns=['date','as_of_date','symbol','equity_weight'])


def main() -> None:
    sessions = all_dates()
    rows,receipts,validation = [],[],[]
    dest = DATA/'weights'
    (dest/'raw').mkdir(parents=True,exist_ok=True)
    with requests.Session() as session:
        session.headers.update({'Accept':'application/json','x-application-id':'pp-ui-csr'})
        for i,day in enumerate(selected_dates(),1):
            prior = sessions[sessions.index(day)-1]
            path = dest/'raw'/f'ivv_{prior}.json'
            cached = PRIOR/'raw'/path.name
            receipt_path = dest/'raw'/f'ivv_{prior}.receipt.json'
            if receipt_path.exists():
                receipt = json.loads(receipt_path.read_text())
                source = cached if receipt.get('reused') else path
                if source.exists() and receipt.get('sha256') and digest(source) != receipt['sha256']:
                    raise ValueError('Historical holdings changed')
            else:
                if cached.exists():
                    old_receipt = json.loads(cached.with_suffix('.receipt.json').read_text())
                    if digest(cached) != old_receipt['sha256']:
                        raise ValueError('Prior holdings cache changed')
                    source = cached
                    receipt = dict(date=day,as_of=prior,reused=True,status='ok',
                                   path=str(cached),sha256=digest(cached))
                else:
                    params = dict(appSubType='ISHARES',appType='PRODUCT_PAGE',component='holdings.all',
                        locale='en_US',portfolioId='239726',targetSite='us-ishares',userType='individual',
                        excludeContent='true',asOfDate=prior.replace('-',''),includeConfig='true')
                    receipt = dict(date=day,as_of=prior,reused=False,status='unknown',
                                   requested_utc=datetime.now(timezone.utc).isoformat())
                    try:
                        response = session.get(legacy.URL,params=params,timeout=30)
                        path.write_bytes(response.content)
                        receipt.update(path=str(path),sha256=digest(path),http_status=response.status_code)
                        response.raise_for_status()
                        legacy.parse_holdings(response.json(),prior)
                        receipt['status'] = 'ok'
                    except (requests.RequestException,ValueError,KeyError) as exc:
                        receipt.update(status='unavailable',reason=str(exc))
                    source = path
                write_json(receipt_path,receipt)
            sectors,checked = validate_cached(receipt,source,day,prior)
            validation.append(checked)
            if sectors is not None:
                rows.append(sectors)
            receipts.append(receipt)
            if i%25 == 0 or i == len(selected_dates()):
                print(json.dumps(dict(phase='weights',completed=i,available=len(rows))),flush=True)
    values_path,ledger_path = validation_paths()
    write_frame(values_path,combine_validated(rows))
    write_frame(ledger_path,pd.DataFrame(validation))
    write_json(values_path.parent/'manifest.json',dict(source_manifest=str(dest/'manifest.json'),
        code_sha256=digest(OUT/'weights.py'),output_hashes={str(p):digest(p) for p in [values_path,ledger_path]},
        semantics='Raw retrieval and validation are separate; rejected bodies retained for revalidation.'))
    write_json(dest/'manifest.json',dict(receipts=receipts,proxy='IVV_equity_sleeve',
        source_code_sha256=digest(OUT.parent/'b06_sector_weighted_iv_2026-09-19/weights.py')))


if __name__ == '__main__':
    main()
