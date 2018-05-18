-- MATERIALIZED VIEW

CREATE MATERIALIZED VIEW mview_vis_data
AS
 SELECT
    variable.submission_id AS source_id,
    variable.variable_value AS measurement_value,
    variable.variable_name AS measurement_name,
    variable.variable_units AS measurement_units,
    depth.depth,
    variable.date_time AS measurement_date_time,
    data_position.date_time AS position_date_time,
    data_position.lat,
    CASE WHEN data_position.lon > 180 THEN data_position.lon - 360 ELSE data_position.lon END,
    data_position.lat_err,
    data_position.lon_err
   FROM ( SELECT x.variable_value,
            y.variable_name,
            x.date_time,
            x.submission_id,
            y.variable_units,
            x.position_date_time
           FROM data_time_series x,
            observation_types y
          WHERE x.variable_id = y.variable_id AND y.variable_name <> 'depth' AND y.variable_name <> 'datetime') variable,
    data_position,
    ( SELECT x.variable_value AS depth,
            x.date_time,
            x.submission_id
           FROM data_time_series x,
            observation_types y
          WHERE x.variable_id = y.variable_id AND y.variable_name = 'depth') depth
  WHERE variable.submission_id = data_position.submission_id AND variable.submission_id = depth.submission_id AND variable.position_date_time = data_position.date_time AND depth.date_time = variable.date_time
WITH DATA;


CREATE MATERIALIZED VIEW mview_vis_data_histogram
AS
 SELECT
    data.submission_id AS source_id,
    data.min_value AS bin_class,
    data.frequency AS measurement_value,
    data.units AS measurement_units,
    data.type AS measurement_name,
    data.date_time AS measurement_date_time,
    data_position.date_time AS position_date_time,
    data_position.lat,
    CASE WHEN data_position.lon > 180 THEN data_position.lon - 360 ELSE data_position.lon END,
    data_position.lat_err,
    data_position.lon_err
   FROM ( SELECT data_histogram_bin_info.min_value,
            data_histogram_bin_unit.units,
            data_histogram_bin_unit.type,
            data_histogram_bin_data.submission_id,
            data_histogram_bin_data.date_time,
            data_histogram_bin_data.frequency,
            data_histogram_bin_data.position_date_time
           FROM data_histogram_bin_info,
            data_histogram_bin_unit,
            data_histogram_bin_data
          WHERE data_histogram_bin_info.bin_id = data_histogram_bin_unit.bin_id AND data_histogram_bin_info.bin_id = data_histogram_bin_data.bin_id AND data_histogram_bin_info.bin_class = data_histogram_bin_data.bin_class AND data_histogram_bin_data.tag_id = data_histogram_bin_unit.tag_id) data,
    data_position
  WHERE data.submission_id = data_position.submission_id AND data.position_date_time = data_position.date_time
WITH DATA;



CREATE MATERIALIZED VIEW mview_vis_data_profile
AS
 SELECT
    data.submission_id AS source_id,
    data.bin_class,
    data.depth,
    data.min_value AS measurement_value_min,
    data.max_value AS measurement_value_max,
    data.units AS measurement_units,
    data.type AS measurement_name,
    data.date_time AS measurement_date_time,
    data_position.date_time AS position_date_time,
    data_position.lat,
    CASE WHEN data_position.lon > 180 THEN data_position.lon - 360 ELSE data_position.lon END,
    data_position.lat_err,
    data_position.lon_err
   FROM ( SELECT data_profile.submission_id,
            data_profile.bin_class,
            data_profile.date_time,
            data_profile.depth,
            data_profile.min_value,
            data_profile.max_value,
            data_histogram_bin_unit.units,
            data_histogram_bin_unit.type,
            data_profile.position_date_time
           FROM data_profile,
            data_histogram_bin_unit
          WHERE data_profile.bin_id = data_histogram_bin_unit.bin_id AND data_histogram_bin_unit.tag_id = data_profile.tag_id) data,
    data_position
  WHERE data.submission_id = data_position.submission_id AND data.position_date_time = data_position.date_time
WITH DATA;


CREATE MATERIALIZED VIEW mview_vis_metadata
AS
 SELECT metadata.submission_id AS source_id,
    'Global Attributes'::text AS attribute_type,
    NULL::character varying AS variable,
    metadata_types.category,
    metadata_types.attribute_name,
    "left"("right"(metadata.attribute_value, length(metadata.attribute_value) - 1), '-1'::integer) AS attribute_value
   FROM metadata_types,
    metadata
  WHERE metadata_types.attribute_id = metadata.attribute_id AND (metadata_types.category::text = 'instrument'::text AND (metadata_types.attribute_name::text = ANY (ARRAY['instrument_name'::character varying, 'instrument_type'::character varying, 'firmware'::character varying, 'manufacturer'::character varying, 'model'::character varying, 'owner_contact'::character varying, 'person_owner'::character varying, 'serial_number'::character varying]::text[])) OR metadata_types.category::text = 'programming'::text AND (metadata_types.attribute_name::text = ANY (ARRAY['programming_report'::character varying, 'programming_software'::character varying]::text[])) OR metadata_types.category::text = 'attachment'::text AND metadata_types.attribute_name::text = 'attachment_method'::text OR metadata_types.category::text = 'deployment'::text AND (metadata_types.attribute_name::text = ANY (ARRAY['geospatial_lat_start'::character varying, 'geospatial_lon_start'::character varying, 'person_tagger_capture'::character varying, 'time_coverage_start'::character varying]::text[])) OR metadata_types.category::text = 'animal'::text AND (metadata_types.attribute_name::text = ANY (ARRAY['condition_capture'::character varying, 'length_capture'::character varying, 'length_method_capture'::character varying, 'length_type_capture'::character varying, 'length_unit_capture'::character varying, 'platform'::character varying, 'taxonomic_serial_number'::character varying]::text[])) OR metadata_types.category::text = 'end_of_mission'::text AND (metadata_types.attribute_name::text = ANY (ARRAY['time_coverage_end'::character varying, 'end_details'::character varying, 'end_type'::character varying, 'geospatial_lat_end'::character varying, 'geospatial_lon_end'::character varying]::text[])) OR metadata_types.category::text = 'waypoints'::text AND metadata_types.attribute_name::text = 'waypoints_source'::text OR metadata_types.category::text = 'quality'::text AND (metadata_types.attribute_name::text = ANY (ARRAY['found_problem'::character varying, 'person_qc'::character varying]::text[])))
UNION
 SELECT data_time_series.submission_id AS source_id,
    'Variable Attributes'::text AS attribute_type,
    observation_types.standard_name AS variable,
    NULL::character varying AS category,
    'units'::character varying AS attribute_name,
    observation_types.variable_units AS attribute_value
   FROM observation_types,
    ( SELECT data_time_series_1.variable_id,
            data_time_series_1.submission_id
           FROM data_time_series data_time_series_1
          GROUP BY data_time_series_1.variable_id, data_time_series_1.submission_id) data_time_series
  WHERE observation_types.standard_name IS NOT NULL AND observation_types.variable_id = data_time_series.variable_id
UNION
 SELECT data_time_series.submission_id AS source_id,
    'Variable Attributes'::text AS attribute_type,
    observation_types.standard_name AS variable,
    NULL::character varying AS category,
    'standard_name'::character varying AS attribute_name,
    observation_types.standard_name AS attribute_value
   FROM observation_types,
    ( SELECT data_time_series_1.variable_id,
            data_time_series_1.submission_id
           FROM data_time_series data_time_series_1
          GROUP BY data_time_series_1.variable_id, data_time_series_1.submission_id) data_time_series
  WHERE observation_types.standard_name IS NOT NULL AND observation_types.variable_id = data_time_series.variable_id
UNION
 SELECT data_time_series.submission_id AS source_id,
    'Variable Attributes'::text AS attribute_type,
    observation_types.standard_name AS variable,
    NULL::character varying AS category,
    'long_name'::character varying AS attribute_name,
    observation_types.variable_name AS attribute_value
   FROM observation_types,
    ( SELECT data_time_series_1.variable_id,
            data_time_series_1.submission_id
           FROM data_time_series data_time_series_1
          GROUP BY data_time_series_1.variable_id, data_time_series_1.submission_id) data_time_series
  WHERE observation_types.standard_name IS NOT NULL AND observation_types.variable_id = data_time_series.variable_id
WITH DATA;