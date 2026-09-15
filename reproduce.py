"""Reproduce the calculations for SDQ-00582-2026-01 using the standard library; no network calls."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
import bisect
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent

def read(name):
    return json.loads((ROOT / 'data' / name).read_text(), parse_float=Decimal)

def emit(value):
    if isinstance(value, Decimal):
        return format(value, 'f')
    raise TypeError(type(value).__name__)

def unique(records):
    fields = ('transactionHash','proxyWallet','asset','side','size','price','timestamp')
    return list({tuple(row.get(f) for f in fields): row for row in records}.values())

def write_csv(name, rows, fields):
    with (ROOT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)

def main():
    manifest = json.loads((ROOT/'source_manifest.json').read_text())
    for item in manifest:
        p = ROOT/item['path']
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != item['sha256']:
            raise ValueError('Input hash mismatch: '+str(p))

    prices = [r for r in read('ukraine_price_history.json')['history']
              if 1772755200 <= r['t'] <= 1772827200]
    focal_prices = [r for r in prices if r['t'] in (1772813124,1772813423)]
    assert len(focal_prices)==2
    raw = read('ukraine_trades.json')
    trades = unique(raw)
    condition = '0xac74a0513cccc90d458bca3fa754470952f8571e81ee67a1b316ad70c1cbaa52'
    focal = [r for r in trades if r['conditionId']==condition and r['side']=='BUY'
             and r['outcome']=='Yes' and 1772813100 <= r['timestamp'] < 1772813460]
    wallets = sorted({r['proxyWallet'] for r in focal})
    write_csv('ukraine_focal_trades.csv', sorted(focal,key=lambda r:r['timestamp']),
              ['timestamp','transactionHash','proxyWallet','asset','side','outcome','size','price'])
    write_csv('ukraine_wallets.csv',[{'proxyWallet':w} for w in wallets],['proxyWallet'])
    write_csv('ukraine_prices.csv',prices,['t','p'])

    activity = read('pcpc_april_activity.json')
    hungary = '0x5ec80dc407457301f282a2b44341947afc700dfaa7923d14c8894e04bc63b03f'
    ht = sorted(unique([r for r in activity if r['type']=='TRADE' and r['conditionId']==hungary]),
                key=lambda r:r['timestamp'])
    buys=[r for r in ht if r['side']=='BUY']; sells=[r for r in ht if r['side']=='SELL']
    total=lambda rows,key:sum((Decimal(str(r[key])) for r in rows),Decimal(0))
    cash=total(sells,'usdcSize')-total(buys,'usdcSize')
    platform=read('pcpc_closed_positions.json')[0]['realizedPnl']
    largest=max(buys,key=lambda r:r['size'])
    close=int(datetime(2026,4,12,17,tzinfo=timezone.utc).timestamp())
    position=Decimal(0); series=[]
    for r in ht:
        position += r['size'] if r['side']=='BUY' else -r['size']
        series.append({'timestamp':r['timestamp'],'side':r['side'],'shares':r['size'],
                       'position':position,'price':r['price'],'usdcSize':r['usdcSize'],
                       'transactionHash':r['transactionHash']})
    write_csv('hungary_position.csv',series,list(series[0]))
    transfers=list(csv.DictReader((ROOT/'transfer_ledger.csv').open()))
    inbound=sum((Decimal(r['amount_usdc_e']) for r in transfers if r['direction']=='in'),Decimal(0))
    outbound=sum((Decimal(r['amount_usdc_e']) for r in transfers if r['direction']=='out'),Decimal(0))
    results={
      'ukraine':{'price_observations':len(prices),'raw_trade_records':len(raw),
        'unique_trade_records':len(trades),'focal_trade_records':len(focal),'focal_wallets':len(wallets),
        'highlighted_prices':focal_prices,
        'price_increase_percent':(focal_prices[1]['p']/focal_prices[0]['p']-1)*100},
      'hungary':{'raw_activity_records':len(activity),'trade_records':len(ht),'buy_records':len(buys),
        'sell_records':len(sells),'bought_shares':total(buys,'size'),'sold_shares':total(sells,'size'),
        'purchase_expenditure':total(buys,'usdcSize'),'sale_proceeds':total(sells,'usdcSize'),
        'trade_cash_flow_difference':cash,'platform_realized_pnl':platform,
        'pnl_difference':platform-cash,'residual_observed_shares':position,
        'largest_execution_shares':largest['size'],'largest_execution_price':largest['price'],
        'largest_execution_timestamp':largest['timestamp'],'scheduled_polling_close_timestamp':close,
        'seconds_to_scheduled_polling_close':close-largest['timestamp'],
        'inbound_transfer_total':inbound,'outbound_transfer_total':outbound}}

    va = read('venezuela_activity.json')
    vb = [r for r in va if r['type']=='TRADE' and r['side']=='BUY']
    vs = [r for r in va if r['type']=='TRADE' and r['side']=='SELL']
    vr = [r for r in va if r['type']=='REDEEM']
    v_cost = total(vb,'usdcSize'); v_proceeds = total(vs,'usdcSize') + total(vr,'usdcSize')
    results['venezuela'] = {'activity_records':len(va),'purchase_records':len(vb),'purchase_cost':v_cost,
        'sale_records':len(vs),'redemption_records':len(vr),'proceeds':v_proceeds,
        'proceeds_minus_cost':v_proceeds-v_cost,'markets':sorted({r['title'] for r in vb}),
        'first_purchase_timestamp':min(r['timestamp'] for r in vb),'last_purchase_timestamp':max(r['timestamp'] for r in vb)}

    ia = read('iran_accounts_activity.json')
    iran_condition = '0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20'
    ib, ir = [], []
    for records in ia.values():
        ib += [r for r in records if r['type']=='TRADE' and r['side']=='BUY'
               and r['conditionId']==iran_condition and r['outcome']=='Yes']
        ir += [r for r in records if r['type']=='REDEEM' and r['conditionId']==iran_condition]
    i_cost = total(ib,'usdcSize'); i_proceeds = total(ir,'usdcSize')
    new_accounts = sum(1 for records in ia.values()
                       if min(r['timestamp'] for r in records) >= 1771891200)
    px = [r for r in read('iran_price_history.json')['history'] if 1772236800 <= r['t'] <= 1772323200]
    jump = next(b for a,b in zip(px,px[1:]) if b['p']-a['p'] >= Decimal('0.05'))
    results['iran'] = {'accounts':len(ia),'focal_purchases':len(ib),'shares_bought':total(ib,'size'),
        'purchase_cost':i_cost,'redemption_records':len(ir),'redemption_proceeds':i_proceeds,
        'net_gain':i_proceeds-i_cost,
        'first_purchase_timestamp':min(r['timestamp'] for r in ib),
        'last_purchase_timestamp':max(r['timestamp'] for r in ib),
        'accounts_first_active_from_24_february':new_accounts,
        'price_jump_timestamp':jump['t'],'price_before_jump':px[px.index(jump)-1]['p'],'price_after_jump':jump['p']}

    chain = read('funding_chain_usdc_transfers.json')
    common = '0x46e53b77c9c483832dffd2040bef0f8e9c5dd234'
    tranches = [r for r in chain if r['to']==common and Decimal(str(r['amount'])) >= 1000]
    results['hungary_funding'] = {'transfer_records':len(chain),
        'inbound_to_common_address':total([r for r in chain if r['to']==common],'amount'),
        'tranche_senders':[r['from'] for r in tranches],
        'tranche_amounts':[Decimal(str(r['amount'])) for r in tranches],
        'tranche_timestamps':[r['timestamp'] for r in tranches]}

    traded = read('ukraine_focal_wallet_markets.json')
    own = read('ukraine_focal_wallet_records.json')
    per = {}
    for addr, counts in traded.items():
        rows = own[addr]
        spent = total([r for r in rows if r['type']=='TRADE' and r['side']=='BUY'],'usdcSize')
        back  = total([r for r in rows if (r['type']=='TRADE' and r['side']=='SELL') or r['type']=='REDEEM'],'usdcSize')
        per[addr] = {'distinct_markets':len(counts),'focal_records':len(rows),'focal_spent':spent,
                     'focal_returned':back,'focal_net':back-spent}
    covered = {a:v for a,v in per.items() if v['focal_spent']>0}
    counts = sorted(v['distinct_markets'] for v in per.values())
    mid = len(counts)//2
    median = counts[mid] if len(counts)%2 else (counts[mid-1]+counts[mid])/2
    largest = max(covered.values(), key=lambda v: v['focal_spent'])
    write_csv('ukraine_focal_wallet_contrast.csv',
              [dict(proxyWallet=a, **per[a]) for a in sorted(per)],
              ['proxyWallet','distinct_markets','focal_records','focal_spent','focal_returned','focal_net'])
    results['ukraine_focal_wallets'] = {'wallets':len(per),'wallets_with_focal_purchases':len(covered),
        'distinct_markets_min':counts[0],'distinct_markets_median':median,'distinct_markets_max':counts[-1],
        'wallets_below_cost':sum(1 for v in covered.values() if v['focal_net']<0),
        'wallets_below_ten_percent':sum(1 for v in covered.values() if v['focal_net']/v['focal_spent'] < Decimal('0.10')),
        'largest_focal_spent':largest['focal_spent'],'largest_focal_returned':largest['focal_returned'],
        'largest_focal_return_percent':largest['focal_net']/largest['focal_spent']*100}

    life = read('ukraine_market_price_history.json')
    stamps = [r['t'] for r in life]; quotes = [r['p'] for r in life]
    def episodes(threshold, span=360):
        windows = []
        for i, start in enumerate(stamps):
            j = bisect.bisect_right(stamps, start + span) - 1
            if j <= i or quotes[i] <= 0:
                continue
            if (quotes[j] / quotes[i] - 1) * 100 >= threshold:
                windows.append(start)
        merged = []
        for w in windows:
            if merged and w - merged[-1][-1] <= span:
                merged[-1].append(w)
            else:
                merged.append([w])
        return len(windows), len(merged), [m[0] for m in merged]
    results['ukraine_alert_rule'] = {'observations':len(life),
        'first_observation':stamps[0],'last_observation':stamps[-1],
        'windows_evaluated':sum(1 for i,s in enumerate(stamps) if bisect.bisect_right(stamps,s+360)-1>i)}
    for threshold in (100, 75, 50, 30, 20):
        hits, eps, starts = episodes(threshold)
        results['ukraine_alert_rule']['threshold_%d_percent' % threshold] = {
            'windows':hits,'episodes':eps,'episode_starts':starts}

    life_trades = sorted(read('ukraine_market_trades.json'), key=lambda r: r['timestamp'])
    stamps_t = [r['timestamp'] for r in life_trades]
    def window(start, span=360):
        i = bisect.bisect_left(stamps_t, start); j = bisect.bisect_left(stamps_t, start+span)
        chunk = life_trades[i:j]
        return (sum((Decimal(str(r['size'])) for r in chunk), Decimal(0)),
                len({r['proxyWallet'] for r in chunk}), len(chunk))
    scored = [(window(t), t) for t in sorted(set(stamps_t))]
    by_volume = sorted(scored, key=lambda x: (-x[0][0], x[1]))
    by_addresses = sorted(scored, key=lambda x: (-x[0][1], x[1]))
    focal_start = 1772813100
    def rank(order):
        return next(i for i, (_, t) in enumerate(order) if focal_start <= t < focal_start+360) + 1
    results['ukraine_simpler_rules'] = {'trade_records':len(life_trades),'windows':len(scored),
        'focal_rank_by_volume':rank(by_volume),'focal_rank_by_addresses':rank(by_addresses),
        'largest_volume_window':by_volume[0][1],'largest_volume':by_volume[0][0][0],
        'most_addresses_window':by_addresses[0][1],'most_addresses':by_addresses[0][0][1],
        'addresses_in_best_window_outside_6_march':max(
            v[1] for v, t in scored if not 1772755200 <= t < 1772841600)}
    output=json.dumps(results,indent=2,default=emit)+'\n'
    (ROOT/'results.json').write_text(output)
    expected=ROOT/'expected_results.json'
    if expected.exists() and json.loads(expected.read_text()) != json.loads(output):
        raise ValueError('Calculated results differ from expected_results.json')
    print(output)

if __name__=='__main__':
    main()
