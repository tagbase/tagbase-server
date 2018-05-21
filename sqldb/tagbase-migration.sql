\connect tagbase
-- data_time_series

WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING submission b,
                                  observation_types c
   WHERE c.variable_name IN ('datetime',
                             'depth',
                             'temperature',
                             'light',
                             'internal temperature')
     AND a.submission_id = b.submission_id
     AND a.variable_id = c.variable_id RETURNING a.*,
                                                 b.tag_id)
INSERT INTO data_time_series
SELECT *
FROM moved_rows;


-- data_position

WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING submission b,
                                  observation_types c
   WHERE c.variable_name = 'longitude'
     AND a.submission_id = b.submission_id
     AND a.variable_id = c.variable_id RETURNING a.*,
                                                 b.tag_id)
INSERT INTO data_position (date_time, lon, submission_id, tag_id)
SELECT date_time,
       variable_value,
       submission_id,
       tag_id
FROM moved_rows;


WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING data_position b,
                                  observation_types c
   WHERE a.submission_id = b.submission_id
     AND a.date_time = b.date_time
     AND a.variable_id = c.variable_id
     AND c.variable_name = 'latitude' RETURNING a.*)
UPDATE data_position
SET lat = moved_rows.variable_value
FROM moved_rows
WHERE data_position.date_time = moved_rows.date_time
  AND data_position.submission_id = moved_rows.submission_id;


WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING data_position b,
                                  observation_types c
   WHERE a.submission_id = b.submission_id
     AND a.date_time = b.date_time
     AND a.variable_id = c.variable_id
     AND c.variable_name = 'longitudeError' RETURNING a.*)
UPDATE data_position
SET lon_err = moved_rows.variable_value
FROM moved_rows
WHERE data_position.date_time = moved_rows.date_time
  AND data_position.submission_id = moved_rows.submission_id;


WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING data_position b,
                                  observation_types c
   WHERE a.submission_id = b.submission_id
     AND a.date_time = b.date_time
     AND a.variable_id = c.variable_id
     AND c.variable_name = 'latitudeError' RETURNING a.*)
UPDATE data_position
SET lat_err = moved_rows.variable_value
FROM moved_rows
WHERE data_position.date_time = moved_rows.date_time
  AND data_position.submission_id = moved_rows.submission_id;


-- data_histogram_*

INSERT INTO data_histogram_bin_unit (tag_id, TYPE, units)
SELECT *
FROM
  (SELECT tag_id,
          substring(variable_name, 'Hist(.+)Bin') AS TYPE,
          variable_units
   FROM proc_observations,
        observation_types,
        submission
   WHERE submission.submission_id = proc_observations.submission_id
     AND proc_observations.variable_id = observation_types.variable_id
     AND variable_name LIKE 'Hist%') AS a
GROUP BY tag_id,
         TYPE,
         variable_units;


WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING observation_types b,
                                  submission c,
                                  data_histogram_bin_unit d
   WHERE a.variable_id = b.variable_id
     AND b.variable_name LIKE 'Hist%'
     AND a.submission_id = c.submission_id
     AND c.tag_id = d.tag_id
     AND d.type = substring(b.variable_name, 'Hist(.+)BinMin') RETURNING bin_id,
                                                                         cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                                                         variable_value)
INSERT INTO data_histogram_bin_info
SELECT *
FROM moved_rows ON CONFLICT DO NOTHING;

WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING observation_types b,
                                  submission c,
                                  data_histogram_bin_unit d
   WHERE a.variable_id = b.variable_id
     AND b.variable_name LIKE 'Hist%'
     AND a.submission_id = c.submission_id
     AND c.tag_id = d.tag_id
     AND d.type = substring(b.variable_name, 'Hist(.+)BinMax') RETURNING bin_id,
                                                                         cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                                                         variable_value)
UPDATE data_histogram_bin_info
SET max_value = moved_rows.variable_value
FROM moved_rows
WHERE data_histogram_bin_info.bin_id = moved_rows.bin_id
  AND data_histogram_bin_info.bin_class = moved_rows.bin_class;


WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING observation_types b,
                                  submission c,
                                  data_histogram_bin_unit d
   WHERE a.variable_id = b.variable_id
     AND b.variable_name LIKE 'TimeAt%'
     AND a.submission_id = c.submission_id
     AND c.tag_id = d.tag_id
     AND d.type = substring(b.variable_name, 'TimeAt(.+)Bin') RETURNING a.submission_id,
                                                                        c.tag_id,
                                                                        bin_id,
                                                                        cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                                                        a.date_time,
                                                                        variable_value)
INSERT INTO data_histogram_bin_data
SELECT *
FROM moved_rows;


-- data_profile

WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING observation_types b,
                                  submission c
   WHERE a.variable_id = b.variable_id
     AND b.variable_name LIKE 'PdtDepth%'
     AND a.submission_id = c.submission_id RETURNING a.*,
                                                     variable_name,
                                                     tag_id)
INSERT INTO data_profile (date_time, bin_class, depth, submission_id, tag_id)
SELECT date_time,
       cast(substring(variable_name, '(\d+)') AS int),
       variable_value,
       submission_id,
       tag_id
FROM moved_rows;


WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING observation_types b,
                                  data_profile c,
                                  data_histogram_bin_unit d,
                                  submission e
   WHERE a.variable_id = b.variable_id
     AND b.variable_name LIKE 'PdtTempMin%'
     AND a.submission_id = c.submission_id
     AND a.date_time = c.date_time
     AND d.type = 'Temp'
     AND e.submission_id = a.submission_id
     AND e.tag_id = d.tag_id RETURNING a.*,
                                       cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                       d.bin_id)
UPDATE data_profile
SET min_value = moved_rows.variable_value,
    bin_id = moved_rows.bin_id
FROM moved_rows
WHERE data_profile.date_time = moved_rows.date_time
  AND data_profile.submission_id = moved_rows.submission_id
  AND data_profile.bin_class = moved_rows.bin_class;


WITH moved_rows AS
  ( DELETE
   FROM proc_observations a USING observation_types b,
                                  data_profile c,
                                  data_histogram_bin_unit d,
                                  submission e
   WHERE a.variable_id = b.variable_id
     AND b.variable_name LIKE 'PdtTempMax%'
     AND a.submission_id = c.submission_id
     AND a.date_time = c.date_time
     AND d.type = 'Temp'
     AND e.submission_id = a.submission_id
     AND e.tag_id = d.tag_id RETURNING a.*,
                                       cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                       d.bin_id)
UPDATE data_profile
SET max_value = moved_rows.variable_value
FROM moved_rows
WHERE data_profile.date_time = moved_rows.date_time
  AND data_profile.submission_id = moved_rows.submission_id
  AND data_profile.bin_class = moved_rows.bin_class
  AND data_profile.bin_id = moved_rows.bin_id;


-- SQL update statements to link measurement date time with position date time

UPDATE data_time_series
SET position_date_time =
  (SELECT date_time
   FROM data_position
   WHERE data_time_series.submission_id = data_position.submission_id
     AND data_time_series.date_time >= data_position.date_time
   ORDER BY data_position.date_time DESC
   LIMIT 1)
WHERE position_date_time IS NULL;

UPDATE data_histogram_bin_data
SET position_date_time =
  (SELECT date_time
   FROM data_position
   WHERE data_histogram_bin_data.submission_id = data_position.submission_id
     AND data_histogram_bin_data.date_time >= data_position.date_time
   ORDER BY data_position.date_time DESC
   LIMIT 1)
WHERE position_date_time IS NULL;

UPDATE data_profile
SET position_date_time =
  (SELECT date_time
   FROM data_position
   WHERE data_profile.submission_id = data_position.submission_id
     AND data_profile.date_time >= data_position.date_time
   ORDER BY data_position.date_time DESC
   LIMIT 1)
WHERE position_date_time IS NULL;
