-- Uncomment the line below if you run this from the terminal.
--\connect tagbase

-- MATERIALIZED VIEW

CREATE MATERIALIZED VIEW mview_vis_data AS
WITH var_rows AS (
  SELECT
    x.variable_value,
    y.variable_name,
    x.date_time,
    x.submission_id,
    y.variable_units,
    x.position_date_time
  FROM data_time_series AS x
  INNER JOIN observation_types AS y
    ON x.variable_id = y.variable_id
  WHERE
    y.variable_name <> 'depth'
    AND y.variable_name <> 'datetime'
),

depth_rows AS (
  SELECT
    x.variable_value AS depth_value,
    x.date_time,
    x.submission_id
  FROM data_time_series AS x
  INNER JOIN observation_types AS y
    ON x.variable_id = y.variable_id
  WHERE y.variable_name = 'depth'
)

SELECT
  var_rows.submission_id AS source_id,
  var_rows.variable_value AS measurement_value,
  var_rows.variable_name AS measurement_name,
  var_rows.variable_units AS measurement_units,
  depth_rows.depth_value AS depth,
  var_rows.date_time AS measurement_date_time,
  data_position.date_time AS position_date_time,
  data_position.lat,
  CASE
    WHEN data_position.lon::double precision > 180
      THEN data_position.lon::double precision - 360
    ELSE data_position.lon::double precision
  END AS lon,
  data_position.lat_err,
  data_position.lon_err
FROM var_rows
INNER JOIN data_position
  ON var_rows.submission_id = data_position.submission_id
  AND var_rows.position_date_time = data_position.date_time
INNER JOIN depth_rows
  ON var_rows.submission_id = depth_rows.submission_id
  AND var_rows.date_time = depth_rows.date_time
WITH DATA;


CREATE MATERIALIZED VIEW mview_vis_data_histogram AS
WITH hist_rows AS (
  SELECT
    data_histogram_bin_info.min_value,
    data_histogram_bin_data.submission_id,
    data_histogram_bin_data.date_time,
    data_histogram_bin_data.variable_value,
    data_histogram_bin_data.position_date_time
  FROM data_histogram_bin_info
  INNER JOIN data_histogram_bin_data
    ON data_histogram_bin_info.bin_id = data_histogram_bin_data.bin_id
    AND data_histogram_bin_info.bin_class = data_histogram_bin_data.bin_class
)

SELECT
  hist_rows.submission_id AS source_id,
  hist_rows.min_value AS bin_class,
  hist_rows.variable_value AS measurement_value,
  hist_rows.date_time AS measurement_date_time,
  data_position.date_time AS position_date_time,
  data_position.lat,
  CASE
    WHEN data_position.lon::double precision > 180
      THEN data_position.lon::double precision - 360
    ELSE data_position.lon::double precision
  END AS lon,
  data_position.lat_err,
  data_position.lon_err
FROM hist_rows
INNER JOIN data_position
  ON hist_rows.submission_id = data_position.submission_id
  AND hist_rows.position_date_time = data_position.date_time
WITH DATA;


CREATE MATERIALIZED VIEW mview_vis_data_profile AS
WITH profile_rows AS (
  SELECT
    data_profile.submission_id,
    data_profile.date_time,
    data_profile.depth,
    data_profile.variable_value,
    data_profile.position_date_time
  FROM data_profile
)

SELECT
  profile_rows.submission_id AS source_id,
  profile_rows.depth,
  profile_rows.variable_value AS measurement_value,
  profile_rows.date_time AS measurement_date_time,
  data_position.date_time AS position_date_time,
  data_position.lat,
  CASE
    WHEN data_position.lon::double precision > 180
      THEN data_position.lon::double precision - 360
    ELSE data_position.lon::double precision
  END AS lon,
  data_position.lat_err,
  data_position.lon_err
FROM profile_rows
INNER JOIN data_position
  ON profile_rows.submission_id = data_position.submission_id
  AND profile_rows.position_date_time = data_position.date_time
WITH DATA;


CREATE MATERIALIZED VIEW mview_vis_metadata AS
WITH dts AS (
  SELECT
    data_time_series_1.variable_id,
    data_time_series_1.submission_id
  FROM data_time_series AS data_time_series_1
  GROUP BY data_time_series_1.variable_id, data_time_series_1.submission_id
)

SELECT
  metadata.submission_id AS source_id,
  'Global Attributes'::text AS attribute_type,
  NULL::character varying AS variable,
  metadata_types.category,
  metadata_types.attribute_name,
  left(
    right(metadata.attribute_value, length(metadata.attribute_value) - 1),
    -1
  ) AS attribute_value
FROM metadata_types
INNER JOIN metadata
  ON metadata_types.attribute_id = metadata.attribute_id
WHERE
  (
    (
      metadata_types.category::text = 'instrument'::text
      AND metadata_types.attribute_name::text IN (
        'instrument_name',
        'instrument_type',
        'firmware',
        'manufacturer',
        'model',
        'owner_contact',
        'person_owner',
        'serial_number'
      )
    )
    OR (
      metadata_types.category::text = 'programming'::text
      AND metadata_types.attribute_name::text IN (
        'programming_report',
        'programming_software'
      )
    )
    OR (
      metadata_types.category::text = 'attachment'::text
      AND metadata_types.attribute_name::text = 'attachment_method'::text
    )
    OR (
      metadata_types.category::text = 'deployment'::text
      AND metadata_types.attribute_name::text IN (
        'geospatial_lat_start',
        'geospatial_lon_start',
        'person_tagger_capture',
        'time_coverage_start'
      )
    )
    OR (
      metadata_types.category::text = 'animal'::text
      AND metadata_types.attribute_name::text IN (
        'condition_capture',
        'length_capture',
        'length_method_capture',
        'length_type_capture',
        'length_unit_capture',
        'platform',
        'taxonomic_serial_number'
      )
    )
    OR (
      metadata_types.category::text = 'end_of_mission'::text
      AND metadata_types.attribute_name::text IN (
        'time_coverage_end',
        'end_details',
        'end_type',
        'geospatial_lat_end',
        'geospatial_lon_end'
      )
    )
    OR (
      metadata_types.category::text = 'waypoints'::text
      AND metadata_types.attribute_name::text = 'waypoints_source'::text
    )
    OR (
      metadata_types.category::text = 'quality'::text
      AND metadata_types.attribute_name::text IN (
        'found_problem',
        'person_qc'
      )
    )
  )
UNION
SELECT
  dts.submission_id AS source_id,
  'Variable Attributes'::text AS attribute_type,
  observation_types.standard_name AS variable,
  NULL::character varying AS category,
  'units'::character varying AS attribute_name,
  observation_types.variable_units AS attribute_value
FROM observation_types
INNER JOIN dts
  ON observation_types.variable_id = dts.variable_id
WHERE observation_types.standard_name IS NOT NULL
UNION
SELECT
  dts.submission_id AS source_id,
  'Variable Attributes'::text AS attribute_type,
  observation_types.standard_name AS variable,
  NULL::character varying AS category,
  'standard_name'::character varying AS attribute_name,
  observation_types.standard_name AS attribute_value
FROM observation_types
INNER JOIN dts
  ON observation_types.variable_id = dts.variable_id
WHERE observation_types.standard_name IS NOT NULL
UNION
SELECT
  dts.submission_id AS source_id,
  'Variable Attributes'::text AS attribute_type,
  observation_types.standard_name AS variable,
  NULL::character varying AS category,
  'long_name'::character varying AS attribute_name,
  observation_types.variable_name AS attribute_value
FROM observation_types
INNER JOIN dts
  ON observation_types.variable_id = dts.variable_id
WHERE observation_types.standard_name IS NOT NULL
WITH DATA;
