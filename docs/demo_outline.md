# Assessment demonstration (approximately 7 minutes)

1. Explain the synthetic dataset and condition-based binary target. Show the official source,
   10,000 observations, 339 failures and six allowed predictors. State no future forecast.
2. Show overview filters and test partition. Search a UDI, sort risk and distinguish recorded
   failure from model score. Explain that each row is an observation, not a live machine feed.
3. Submit a manual observation; show estimated failure probability, threshold category and input units. Demonstrate
   an out-of-training-range warning and explain why Lower does not mean safe.
4. Download the example CSV, upload it, inspect predictions, and download results. Show one
   invalid CSV and its actionable error without crashing the app.
5. Show the sidebar policies. The calibrated High precision policy catches 16/68 held-out failures
   with 2 false alarms; Balanced F1 catches 40/68 with 15 false alarms. Probabilities stay the same.
   Compare majority, LR and RF; identify the original uncalibrated winner separately (25 caught,
   43 missed, 2 false alarms). Explain why accuracy alone is insufficient and disclose holdout reuse.
6. Explain the reference reproduction and its test-selected threshold limitation. Show
   calibration, global importance and the limits of synthetic generalization.
7. If deployed, open the real Cloud Run URL and perform a prediction. Show BigQuery/Looker
   integration only when actually configured. Otherwise identify deployment as pending.
8. Show test-results.xml, environment locks, architecture and cleanup plan. Disclose AI assistance.
