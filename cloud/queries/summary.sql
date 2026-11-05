-- Replace YOUR_PROJECT and maintenance_demo with your selected project and dataset.
SELECT machine_type, COUNT(*) AS observations,
       SUM(machine_failure) AS observed_failures,
       AVG(machine_failure) AS observed_failure_rate,
       COUNTIF(elevated_risk) AS elevated_risk_observations,
       AVG(failure_probability) AS mean_failure_probability
FROM `YOUR_PROJECT.maintenance_demo.observations`
GROUP BY machine_type;
