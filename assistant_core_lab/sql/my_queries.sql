-- Lab 5 Part F: write your queries for the assistant database here.
-- Q1 requests per intent
SELECT intent, COUNT(*) AS requests
FROM interaction
GROUP BY intent
ORDER BY requests DESC;
 
-- Q2 average latency per intent
SELECT intent, ROUND(AVG(latency_ms), 1) AS avg_latency_ms
FROM interaction
GROUP BY intent
ORDER BY avg_latency_ms DESC;
 
-- Q3 topics with the most thumbs-down (JOIN feedback with interaction)
-- NOTE: tên cột trong feedback (interaction_id, rating) và interaction (id, topic) là đoán, cần đối chiếu với schema của lab
SELECT i.topic, COUNT(*) AS thumbs_down
FROM feedback AS f
JOIN interaction AS i ON i.request_id = f.request_id
WHERE f.rating = -1
  AND i.topic IS NOT NULL
GROUP BY i.topic
ORDER BY thumbs_down DESC;