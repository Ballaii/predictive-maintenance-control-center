-- Only held-out observations are appropriate for reporting independent performance.
SELECT machine_failure AS observed_failure, elevated_risk AS predicted_failure,
       COUNT(*) AS observations
FROM `YOUR_PROJECT.maintenance_demo.observations`
WHERE split = 'test'
GROUP BY machine_failure, elevated_risk;
