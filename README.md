# Polymarket attribution replication

Data and code that reproduce the price, trade, account and transfer calculations
reported in a study of anomalous trading and blockchain attribution on
decentralised prediction markets.

---


## Purpose
Reproduce the Ukrainian price and trade calculations, the frequency of the
observed price pattern over the life of that market and how it compares with a
volume rule and a participant-count rule, the later trading of the
Ukrainian focal buyers, the Iranian account totals, the Hungarian position, trade cash flow and transfer totals, the
funding chain of the Hungarian account, and the Venezuelan account totals
reported in the manuscript.
Market metadata documents the contract wording and the identified case
markets. The package contains no copies of journal articles or news reports.

## Run
Clone the repository and run: python3 reproduce.py
Python 3.10 or later; standard library only; no network access required.
The script checks the SHA-256 hash of every input listed in
source_manifest.json and compares its results with expected_results.json.
Any mismatch raises an error. A successful run writes results.json and four
derived CSV files: ukraine_prices.csv, ukraine_focal_trades.csv,
ukraine_wallets.csv and hungary_position.csv. These contain the data plotted
in Figures 2 and 3.

## Inputs and Provenance
source_manifest.json lists, for each input, its source, the exact request
URL and parameters, and its SHA-256 hash. Gamma records carry the label v1
(field "version"); the CLOB, Data API and JSON-RPC endpoints publish no
version identifier; the Relay request endpoint is versioned in its path (v2),
and a later Relay version may be needed to repeat those requests. All
analytical timestamps are UTC.
data/ contains the historical API extracts and contract metadata.
data/venezuela_activity.json holds the public activity of the Polymarket
account whose address matches the truncated address 0x31a5...8ed9 given in
the CFTC complaint against the defendant (p. 12). The link between this
account and a person rests on the legal filings, not on these data.
data/iran_accounts_activity.json holds the public activity of the five
accounts that were reported by Bubblemaps, cited in the manuscript through
The Block, and matched here to public account records; the sixth reported
account was not matched. The file is keyed by address, one request per
account. Only records of the focal condition ID are used.
data/ukraine_market_trades.json holds every trade record the endpoint returns
for the Ukrainian contract, not only the four pages used for the focal filter.
Its records are single-sided, so they support counts of traded size and of
participating addresses, but not a reconstructed position for each address.
data/ukraine_market_price_history.json holds the whole price series of the
Ukrainian contract, from 24 February 2026 to resolution, and supports the count
of windows in which the observed pattern would have triggered an alert.
data/iran_price_history.json holds the price series of the focal market on
28 February 2026 and documents the repricing that followed the purchases.
data/ukraine_focal_wallet_markets.json and data/ukraine_focal_wallet_records.json
condense the public activity of all 28 addresses that bought in the Ukrainian
focal interval, covering 1 February to 1 April 2026, one request per
address. These are not selected examples: they are every address the focal
filter returns. The first file gives the number of trades each address made in
each condition ID; the second holds its records of the Ukrainian contract in
full. The endpoint yields at most 5,500 records per account and window, so five
accounts are truncated and four of those do not reach back to 6 March; their
focal purchases are therefore absent and they are excluded from the outcome
counts, though not from the count of markets traded.
market_identifiers.csv lists market questions, condition IDs and the case
to which each market belongs, including the first Paris temperature contracts
of 18 and 19 April 2026, whose resolution text names the Charles de Gaulle
station and the Le Bourget station respectively.
wallet_identifiers.csv gives the analysed public addresses and the addresses
of the funding chain. transfer_ledger.csv lists the four Polygon transactions
between the funding chain and the trading account by hash, with direction,
amount, time and explorer label; each can be checked on the public ledger at
the URL given. data/relay_requests.json gives the Relay request record of
each transfer: all four are swaps within Polygon (chain 137), USDC to USDC.e
on entry and USDC.e to USDC on exit.
data/funding_chain_usdc_transfers.json lists every native USDC transfer of
the two funding-chain addresses, read from the Transfer logs of the USDC
contract itself, so that imitation tokens which copy the USDC name cannot
appear and no address index is relied upon. The address
0x46E53b77c9c483832DFfd2040bef0F8E9C5dD234 carries no public label; the
Polygonscan public name tags label 0xEe7aE85f2Fe2239E27D9c1E23fFFe168D63b4055
as Binance: Hot Wallet 34.
Display names, pseudonyms, profile biographies and profile images of platform
users have been removed from the trade and activity extracts, and metadata
files retain contract fields only. None of the removed fields is used in any
calculation.

## Analytical Rules
Ukraine: use the price observations for 6 March 2026, 00:00-20:00 UTC,
without interpolation. Collapse records identical in transaction hash, proxy
wallet, asset, side, size, price and timestamp. Select the specified condition
ID, BUY, Yes, and 16:05:00 inclusive to 16:11:00 exclusive. Count records and
unique proxy addresses. Four 500-record pages are concatenated in the input.
Ukrainian alert rule: over the whole price series, for every observation take
the last quote no later than six minutes afterwards and record a window when the
increase reaches the stated threshold. Merge windows less than six minutes apart
into one episode. This counts how often the pattern occurs in one contract; it
is not an error rate, because a single contract has no denominator and the
outcome of each episode is not classified.
Simpler rules: over the same market, score every six-minute window by traded
size and by the number of distinct addresses, and record where the focal window
ranks under each. A rank on one contract compares the rules on one event; it
does not measure their accuracy.
Ukrainian focal buyers: for each address count the distinct condition IDs
traded, and for the focal condition ID sum purchase expenditure against sale
proceeds and redemptions. Report the minimum, median and maximum number of
markets, the accounts that ended below cost or gained less than a tenth of
what they spent, and the return of the largest position. A count of markets
from a truncated extract is a lower bound.
Iran: select purchases of the Yes outcome and redemptions of the focal
condition ID across the five accounts, and sum size and usdcSize by type.
Report proceeds minus purchase cost. Count the accounts whose earliest record
in the extract falls on or after 24 February 2026, and locate the first
increase of at least 0.05 in the price series. An earliest record in the
extract is not proof of the date an account was created.
Hungary: select TRADE records for the specified condition ID, apply the same
rule for identical records, order by timestamp and accumulate purchases minus
sales. Sum usdcSize separately by side. Keep the platform closed-position
profit separate from trade cash flow. Compare the largest purchase timestamp
with scheduled polling closure on 12 April 2026 at 17:00 UTC. This is a
retrospective interval, not a validated alert lead time. Sum inbound and
outbound transfers separately; withdrawal totals are not trading profit. In
the funding chain, transfers of 1,000 USDC or more are treated as tranches
and the smaller ones as test transfers.
Venezuela: sum purchase records (usdcSize) and, separately, sale and
redemption records; report proceeds minus purchase cost.

## Scope
The package reproduces arithmetic from the supplied historical extracts.
It does not establish that the extracts contain all market activity, identify
natural persons, generalise the Ukrainian contrast beyond that one interval, establish common control of the Iranian accounts or the
origin of any information they may have used, establish responsibility for
map or sensor interference, or validate prospective warning performance.
An exchange label identifies the service, not the customer. The Russian
market identifier could not be recovered. The French contracts resolved to
the 21 C (6 April) and 22 C (15 April) bands; the traders of those bands are
not analysed. Metadata-only markets are not represented as independently
analysed trades. Public service, exchange or bridge labels do not establish
common beneficial ownership.

## Licensing

The data files (`data/`, `*.csv`, `expected_results.json`, `source_manifest.json`) are released under CC-BY-4.0 (`LICENSE`). The analysis script `reproduce.py` is released under the MIT licence (`LICENSE-CODE`).
