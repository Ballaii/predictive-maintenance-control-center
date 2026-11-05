SELECT CAST(LEAST(FLOOR(failure_probability * 10), 9) AS INT64) AS probability_decile,
       COUNT(*) AS observations, AVG(machine_failure) AS observed_failure_rate
FROM `YOUR_PROJECT.maintenance_demo.observations`
GROUP BY probability_decile
ORDER BY probability_decile;
