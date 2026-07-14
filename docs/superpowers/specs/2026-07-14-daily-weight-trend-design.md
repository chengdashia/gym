# Daily Weight Trend Design

## Goal

Keep every same-day weight entry in the record list while making the trend chart show one meaningful value per recorded day.

## Confirmed rules

- The record list keeps every non-deleted `WeightRecord`, ordered newest first.
- The chart uses the last record of each calendar day, determined by the API's descending `record_date` and `record_time` order.
- The chart shows at most seven recorded dates, displayed oldest to newest.
- The chart title is `近 7 天趋势`.
- One recorded day renders one point or bar and keeps the existing prompt that more days make the trend clearer.
- The existing day-to-day change remains unavailable until two different recorded days exist.

## Scope

Frontend-only: derive the chart series from the existing `/weight/records` response. No API, schema, or historical data migration is required.
