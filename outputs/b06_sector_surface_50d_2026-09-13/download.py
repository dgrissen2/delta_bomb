"""Bounded two-worker Theta SDK collector; immutable raw responses, no outcome inputs."""
from __future__ import annotations

import contextlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import logging
from pathlib import Path
import threading
from typing import Any, Callable

import pandas as pd

OUT = Path(__file__).resolve().parent
DATA = Path('/Users/dgrissen/Dev/central_trade_data/thetadata/sector_surface_b06_50d_2026-09-13-v1')
SYMBOLS = ['XLC','XLY','XLP','XLE','XLF','XLV','XLI','XLB','XLRE','XLK','XLU']
DATES = pd.read_csv(OUT / 'selected_days.csv')['date'].tolist()



def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Cache:
    """Reserve explicit requests under a lock; independent responses are additive."""
    def __init__(self, root: Path, limit: int = 2250) -> None:
        self.root, self.limit = root, limit
        root.mkdir(parents=True, exist_ok=True)
        self.log = root / 'requests.jsonl'
        self.lock = threading.Lock()
        self.used = sum(json.loads(line)['status']=='started' for line in
                        self.log.read_text().splitlines()) if self.log.exists() else 0
        self.inflight: set[str] = set()

    def record(self, record: dict[str, Any]) -> None:
        with self.log.open('a') as stream:
            stream.write(json.dumps({'at': now(), **record}, sort_keys=True) + '\n')

    def get(self, method: str, params: dict[str, Any], query: Callable[..., Any]
            ) -> tuple[pd.DataFrame, Path]:
        safe = json.loads(json.dumps(params, default=str))
        key = hashlib.sha256(json.dumps([method, safe], sort_keys=True).encode()).hexdigest()
        path = self.root / method / f'{key}.parquet'
        meta_path = path.with_suffix('.json')
        with self.lock:
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                if not path.exists() or digest(path) != meta['sha256']:
                    raise ValueError(f'cache digest mismatch: {path}')
                return pd.read_parquet(path), path
            if path.exists() or key in self.inflight:
                raise ValueError(f'incomplete or concurrent duplicate cache request: {key}')
            if self.used >= self.limit:
                raise RuntimeError('SDK data request budget exhausted')
            self.used += 1
            self.inflight.add(key)
            self.record({'status':'started','method':method,'params':safe,'key':key})
        try:
            response = query(**params)
            frame = response if isinstance(response, pd.DataFrame) else response.to_pandas()
        except Exception as exc:
            code = exc.code().name if callable(getattr(exc, 'code', None)) else type(exc).__name__
            with self.lock:
                self.record({'status':'error','method':method,'key':key,'code':code,
                             'error_type':type(exc).__name__})
                self.inflight.remove(key)
            raise RuntimeError(f'Theta {method}: {code}') from None
        path.parent.mkdir(parents=True, exist_ok=True)
        pending = path.with_suffix('.parquet.tmp')
        frame.to_parquet(pending, index=False)
        pending.replace(path)
        meta = {'method':method,'params':safe,'rows':len(frame),'received_at':now(),
                'schema':{col:str(dtype) for col,dtype in frame.dtypes.items()},
                'sha256':digest(path),'sdk_version':importlib.metadata.version('thetadata')}
        meta_path.write_text(json.dumps(meta, indent=2)+'\n')
        with self.lock:
            self.record({'status':'ok','method':method,'key':key,'rows':len(frame),
                         'path':str(path),'sha256':meta['sha256']})
            self.inflight.remove(key)
        return frame, path


def expiries(day: date, values: list[date]) -> list[date]:
    valid = sorted({e for e in values if 8 <= (e-day).days <= 65})
    front = [e for e in valid if (e-day).days <= 30]
    back = [e for e in valid if (e-day).days >= 30]
    return sorted({front[-1],back[0]}) if front and back else []


def freeze(path: Path, value: Any) -> None:
    if path.exists() and json.loads(path.read_text()) != value:
        raise ValueError(f'Frozen input changed: {path}')
    path.write_text(json.dumps(value, indent=2)+'\n')


def main() -> None:
    from thetadata import ThetaClient

    cache = Cache(DATA)
    freeze(DATA/'sampling_freeze.json', {'path':str(OUT/'selected_days.csv'), 'sha256':digest(OUT/'selected_days.csv')})
    protocol = {'path':str(OUT/'PROTOCOL.md'),'sha256':digest(OUT/'PROTOCOL.md')}
    freeze(DATA/'protocol_freeze.json', protocol)
    logging.getLogger('thetadata').setLevel(logging.CRITICAL)
    cache.record({'status':'authentication_started'})
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            client = ThetaClient(creds_file='/Users/dgrissen/Dev/ThetaData/creds.txt',
                                 dataframe_type='pandas')
    except Exception as exc:
        cache.record({'status':'authentication_error','error_type':type(exc).__name__})
        raise RuntimeError(f'Theta authentication: {type(exc).__name__}') from None
    cache.record({'status':'authentication_ok'})
    selections, listing_sources = [], []
    for day_string in DATES:
        day = date.fromisoformat(day_string)
        listing, path = cache.get('option_list_contracts',
            {'request_type':'quote','date':day,'symbol':SYMBOLS,'max_dte':65},
            client.option_list_contracts)
        listing_sources.append({'date':day_string,'path':str(path),'sha256':digest(path)})
        for symbol in SYMBOLS:
            values = pd.to_datetime(listing.loc[listing.symbol.eq(symbol),'expiration']).dt.date.tolist()
            selected = expiries(day,values)
            selections.append({'date':day_string,'symbol':symbol,
                'expirations':[str(e) for e in selected],
                'status':'selected' if selected else 'missing_tenor_bracket'})
        print(json.dumps({'phase':'listing','date':day_string,'rows':len(listing)}),flush=True)
    freeze(DATA/'selections.json',{'sources':listing_sources,'selections':selections})
    tasks = [(s['date'],s['symbol'],e) for s in selections for e in s['expirations']]
    if 2*len(tasks)+len(DATES)>2250:
        raise ValueError('Dataset exceeds frozen request ceiling')
    print(json.dumps({'phase':'planned','expiry_pairs':len(tasks),
                      'max_explicit_data_calls':2*len(tasks)+len(DATES)}),flush=True)

    def collect(task: tuple[str,str,str]) -> dict[str,Any]:
        day, symbol, expiry = task
        params = {'symbol':symbol,'expiration':date.fromisoformat(expiry),
                  'date':date.fromisoformat(day),'interval':'1m','strike':'*','right':'both',
                  'start_time':'09:30:00','end_time':'14:29:00','strike_range':30,
                  'rate_type':'sofr','version':'latest'}
        record: dict[str,Any] = {'date':day,'symbol':symbol,'expiration':expiry,'files':[]}
        for kind in ['implied_volatility','first_order']:
            method = 'option_history_greeks_'+kind
            try:
                frame,path = cache.get(method,params,getattr(client,method))
                if len(frame) and (not frame.symbol.eq(symbol).all() or
                    not pd.to_datetime(frame.expiration).dt.date.eq(date.fromisoformat(expiry)).all()):
                    raise ValueError('Response contract mismatch')
                record['files'].append({'kind':kind,'path':str(path),'rows':len(frame),
                                        'sha256':digest(path)})
            except (RuntimeError,ValueError) as exc:
                record['status']='error'
                record['error']=str(exc)
                return record
        record['status']='ok'
        return record

    records=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(collect,task) for task in tasks]
        for future in as_completed(futures):
            record=future.result()
            records.append(record)
            manifest={'at':now(),'protocol':protocol,'dates':DATES,'symbols':SYMBOLS,
                      'selections':selections,'listing_sources':listing_sources,
                      'planned_pairs':len(tasks),'pairs':records,'status':'collecting'}
            (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            (OUT/'collection_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            print(json.dumps({k:record[k] for k in ['date','symbol','expiration','status']}|
                             {'completed':len(records),'planned':len(tasks)}),flush=True)
    manifest['status']='complete' if all(r['status']=='ok' for r in records) else 'complete_with_errors'
    manifest['at']=now()
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'collection_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':
    main()
