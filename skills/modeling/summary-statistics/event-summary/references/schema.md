# Event Summary Schema

Top-level fields:
- `status`
- `summary`
- `event`
- `metrics`
- `validation`
- `provenance`

`event` block:
- `event_id`
- `value_mode` (`flux` or `magnitude`)
- `units` object

`metrics` block (minimum):
- `n_points`
- `time_min`, `time_max`
- `value_median`
- `value_peak`
- `time_at_peak`
- `value_amplitude_proxy`
- `duration_proxy_90pct` (time span of central 90% samples)
