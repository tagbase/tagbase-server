--
-- PostgreSQL database dump
--

-- Dumped from database version 10.4
-- Dumped by pg_dump version 10.1

-- Started on 2019-12-10 13:35:30

CREATE ROLE tagbase WITH SUPERUSER LOGIN;

CREATE DATABASE tagbase WITH OWNER = 'tagbase';

ALTER USER tagbase PASSWORD 'tagbase';

\connect tagbase

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 196 (class 1259 OID 16574)
-- Name: data_histogram_bin_data; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE data_histogram_bin_data (
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    bin_id bigint NOT NULL,
    bin_class integer NOT NULL,
    date_time timestamp(6) with time zone NOT NULL,
    variable_value double precision NOT NULL,
    position_date_time timestamp(6) with time zone,
    variable_id bigint NOT NULL
);


ALTER TABLE data_histogram_bin_data OWNER TO tagbase;

--
-- TOC entry 2903 (class 0 OID 0)
-- Dependencies: 196
-- Name: TABLE data_histogram_bin_data; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE data_histogram_bin_data IS 'Conatins the frequency for corresponding summary data binning schemes (migrated from proc_observations)';


--
-- TOC entry 2904 (class 0 OID 0)
-- Dependencies: 196
-- Name: COLUMN data_histogram_bin_data.submission_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_data.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- TOC entry 2905 (class 0 OID 0)
-- Dependencies: 196
-- Name: COLUMN data_histogram_bin_data.tag_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_data.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- TOC entry 2906 (class 0 OID 0)
-- Dependencies: 196
-- Name: COLUMN data_histogram_bin_data.bin_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_data.bin_id IS 'Unique bin ID for the summary bin-frequency class';


--
-- TOC entry 2907 (class 0 OID 0)
-- Dependencies: 196
-- Name: COLUMN data_histogram_bin_data.bin_class; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_data.bin_class IS 'Sequential numeric bin class identifier';


--
-- TOC entry 2908 (class 0 OID 0)
-- Dependencies: 196
-- Name: COLUMN data_histogram_bin_data.date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_data.date_time IS 'Date/time stamp of the tag summarized bin-frequency data record';


--
-- TOC entry 2909 (class 0 OID 0)
-- Dependencies: 196
-- Name: COLUMN data_histogram_bin_data.variable_value; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_data.variable_value IS 'Aggregate measure for the given bin-interval of the geophysical value of the observed tag variable record';


--
-- TOC entry 2910 (class 0 OID 0)
-- Dependencies: 196
-- Name: COLUMN data_histogram_bin_data.position_date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_data.position_date_time IS 'Date/time stamp of nearest matched associated positional record';


--
-- TOC entry 2911 (class 0 OID 0)
-- Dependencies: 196
-- Name: COLUMN data_histogram_bin_data.variable_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_data.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested.  The variable_id is based on observation or measurment variables listed in the observation_types table.  Note that records in this table are NOT expected to be equivalent to those in the variable_id column of the data_histogram_bin_info table';


--
-- TOC entry 197 (class 1259 OID 16577)
-- Name: data_histogram_bin_info; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE data_histogram_bin_info (
    bin_id bigint NOT NULL,
    bin_class integer NOT NULL,
    min_value double precision NOT NULL,
    max_value double precision NOT NULL,
    variable_id bigint NOT NULL
);


ALTER TABLE data_histogram_bin_info OWNER TO tagbase;

--
-- TOC entry 2912 (class 0 OID 0)
-- Dependencies: 197
-- Name: TABLE data_histogram_bin_info; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE data_histogram_bin_info IS 'Contains definitions of binning schemes for summary tag data (migrated from proc_observations)';


--
-- TOC entry 2913 (class 0 OID 0)
-- Dependencies: 197
-- Name: COLUMN data_histogram_bin_info.bin_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_info.bin_id IS 'Unique bin ID for the summary bin-frequency class';


--
-- TOC entry 2914 (class 0 OID 0)
-- Dependencies: 197
-- Name: COLUMN data_histogram_bin_info.bin_class; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_info.bin_class IS 'Sequential numeric bin class identifier';


--
-- TOC entry 2915 (class 0 OID 0)
-- Dependencies: 197
-- Name: COLUMN data_histogram_bin_info.min_value; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_info.min_value IS 'Value of minimum/lower bound of bin interval';


--
-- TOC entry 2916 (class 0 OID 0)
-- Dependencies: 197
-- Name: COLUMN data_histogram_bin_info.max_value; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_info.max_value IS 'Value of maximum/upper bound of bin interval';


--
-- TOC entry 2917 (class 0 OID 0)
-- Dependencies: 197
-- Name: COLUMN data_histogram_bin_info.variable_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_histogram_bin_info.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested.  The variable_id is based on observation or measurment variables listed in the observation_types table.  Note that records in this table are NOT expected to be equivalent to those in the variable_id column of the data_histogram_bin_data table';


--
-- TOC entry 198 (class 1259 OID 16580)
-- Name: data_position; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE data_position (
    date_time timestamp(6) with time zone NOT NULL,
    lat double precision NOT NULL,
    lon double precision NOT NULL,
    lat_err double precision,
    lon_err double precision,
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    "argosLC" character(1)
);


ALTER TABLE data_position OWNER TO tagbase;

--
-- TOC entry 2918 (class 0 OID 0)
-- Dependencies: 198
-- Name: TABLE data_position; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE data_position IS 'Contains the tag positional data series with associated Lat/Lon error estimates where available (migrated from proc_observations)';


--
-- TOC entry 2919 (class 0 OID 0)
-- Dependencies: 198
-- Name: COLUMN data_position.date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_position.date_time IS 'Date/time stamp of the tag positional data record';


--
-- TOC entry 2920 (class 0 OID 0)
-- Dependencies: 198
-- Name: COLUMN data_position.lat; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_position.lat IS 'Latitude in decimal degrees of the positional data tag record';


--
-- TOC entry 2921 (class 0 OID 0)
-- Dependencies: 198
-- Name: COLUMN data_position.lon; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_position.lon IS 'Longitude in decimal degrees of the positional data tag record';


--
-- TOC entry 2922 (class 0 OID 0)
-- Dependencies: 198
-- Name: COLUMN data_position.lat_err; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_position.lat_err IS 'Error associated with the tag record Laitudiinal positional estimate';


--
-- TOC entry 2923 (class 0 OID 0)
-- Dependencies: 198
-- Name: COLUMN data_position.lon_err; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_position.lon_err IS 'Error associated with the tag record Longitudinal positional estimate';


--
-- TOC entry 2924 (class 0 OID 0)
-- Dependencies: 198
-- Name: COLUMN data_position.submission_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_position.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- TOC entry 2925 (class 0 OID 0)
-- Dependencies: 198
-- Name: COLUMN data_position.tag_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_position.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- TOC entry 2926 (class 0 OID 0)
-- Dependencies: 198
-- Name: COLUMN data_position."argosLC"; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_position."argosLC" IS 'Single character Argos Location Class positional quality code based on argosLC scheme defined by Argos System
';


--
-- TOC entry 199 (class 1259 OID 16583)
-- Name: data_profile; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE data_profile (
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    variable_id bigint NOT NULL,
    date_time timestamp(6) with time zone NOT NULL,
    depth double precision NOT NULL,
    variable_value double precision NOT NULL,
    position_date_time timestamp(6) with time zone
);


ALTER TABLE data_profile OWNER TO tagbase;

--
-- TOC entry 2927 (class 0 OID 0)
-- Dependencies: 199
-- Name: TABLE data_profile; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE data_profile IS 'Contains the summarized bin profile tag observations (migrated from proc_observations)';


--
-- TOC entry 2928 (class 0 OID 0)
-- Dependencies: 199
-- Name: COLUMN data_profile.submission_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_profile.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- TOC entry 2929 (class 0 OID 0)
-- Dependencies: 199
-- Name: COLUMN data_profile.tag_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_profile.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- TOC entry 2930 (class 0 OID 0)
-- Dependencies: 199
-- Name: COLUMN data_profile.variable_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_profile.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested.  The variable_id is based on observation or measurment variables listed in the observation_types table';


--
-- TOC entry 2931 (class 0 OID 0)
-- Dependencies: 199
-- Name: COLUMN data_profile.date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_profile.date_time IS 'Date/time stamp of the tag data record';


--
-- TOC entry 2932 (class 0 OID 0)
-- Dependencies: 199
-- Name: COLUMN data_profile.depth; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_profile.depth IS 'Depth of the tag data record';


--
-- TOC entry 2933 (class 0 OID 0)
-- Dependencies: 199
-- Name: COLUMN data_profile.variable_value; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_profile.variable_value IS 'Geophysical value of the observed tag variable record';


--
-- TOC entry 2934 (class 0 OID 0)
-- Dependencies: 199
-- Name: COLUMN data_profile.position_date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_profile.position_date_time IS 'Date/time stamp of nearest matched associated positional record';


--
-- TOC entry 200 (class 1259 OID 16586)
-- Name: data_time_series; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE data_time_series (
    date_time timestamp(6) with time zone NOT NULL,
    variable_id bigint NOT NULL,
    variable_value double precision NOT NULL,
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    position_date_time timestamp(6) with time zone
);


ALTER TABLE data_time_series OWNER TO tagbase;

--
-- TOC entry 2935 (class 0 OID 0)
-- Dependencies: 200
-- Name: TABLE data_time_series; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE data_time_series IS 'Contains the continuous measurement archival time series of tag geophysical measurments (migrated from proc_observations)';


--
-- TOC entry 2936 (class 0 OID 0)
-- Dependencies: 200
-- Name: COLUMN data_time_series.date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_time_series.date_time IS 'Date/time stamp of the tag data record';


--
-- TOC entry 2937 (class 0 OID 0)
-- Dependencies: 200
-- Name: COLUMN data_time_series.variable_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_time_series.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested.  The variable_id is based on observation or measurment variables listed in the observation_types table';


--
-- TOC entry 2938 (class 0 OID 0)
-- Dependencies: 200
-- Name: COLUMN data_time_series.variable_value; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_time_series.variable_value IS 'Geophysical value of the observed tag variable record';


--
-- TOC entry 2939 (class 0 OID 0)
-- Dependencies: 200
-- Name: COLUMN data_time_series.submission_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_time_series.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- TOC entry 2940 (class 0 OID 0)
-- Dependencies: 200
-- Name: COLUMN data_time_series.tag_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_time_series.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- TOC entry 2941 (class 0 OID 0)
-- Dependencies: 200
-- Name: COLUMN data_time_series.position_date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN data_time_series.position_date_time IS 'Date/time stamp of nearest matched associated positional record';


--
-- TOC entry 201 (class 1259 OID 16589)
-- Name: metadata; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE metadata (
    submission_id bigint NOT NULL,
    attribute_id bigint NOT NULL,
    attribute_value text NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE metadata OWNER TO tagbase;

--
-- TOC entry 2942 (class 0 OID 0)
-- Dependencies: 201
-- Name: TABLE metadata; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE metadata IS 'Contains the ingested tag metadata consistent with the eTUFF specification';


--
-- TOC entry 2943 (class 0 OID 0)
-- Dependencies: 201
-- Name: COLUMN metadata.submission_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- TOC entry 2944 (class 0 OID 0)
-- Dependencies: 201
-- Name: COLUMN metadata.attribute_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata.attribute_id IS 'Unique numeric metadata atttribute ID based on the eTUFF metadata specification';


--
-- TOC entry 2945 (class 0 OID 0)
-- Dependencies: 201
-- Name: COLUMN metadata.attribute_value; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata.attribute_value IS 'Value associated with the given eTUFF metadata attribute';


--
-- TOC entry 2946 (class 0 OID 0)
-- Dependencies: 201
-- Name: COLUMN metadata.tag_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- TOC entry 202 (class 1259 OID 16595)
-- Name: metadata_types; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE metadata_types (
    attribute_id bigint NOT NULL,
    category character varying(1024) NOT NULL,
    attribute_name character varying(1024) NOT NULL,
    type character varying(1024) NOT NULL,
    description text NOT NULL,
    example text,
    comments text,
    necessity character varying(1024) NOT NULL
);


ALTER TABLE metadata_types OWNER TO tagbase;

--
-- TOC entry 2947 (class 0 OID 0)
-- Dependencies: 202
-- Name: TABLE metadata_types; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE metadata_types IS 'Contains descriptive information on tag metadata based on the eTUFF specification';


--
-- TOC entry 2948 (class 0 OID 0)
-- Dependencies: 202
-- Name: COLUMN metadata_types.attribute_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata_types.attribute_id IS 'Unique numeric metadata atttribute ID based on the eTUFF metadata specification';


--
-- TOC entry 2949 (class 0 OID 0)
-- Dependencies: 202
-- Name: COLUMN metadata_types.category; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata_types.category IS 'Metadata attribute category or group based on the eTUFF metadata specification';


--
-- TOC entry 2950 (class 0 OID 0)
-- Dependencies: 202
-- Name: COLUMN metadata_types.attribute_name; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata_types.attribute_name IS 'Name of metadata attribute based on the eTUFF metadata specification';


--
-- TOC entry 2951 (class 0 OID 0)
-- Dependencies: 202
-- Name: COLUMN metadata_types.type; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata_types.type IS 'Metadata attribute format type based on the eTUFF metadata specification';


--
-- TOC entry 2952 (class 0 OID 0)
-- Dependencies: 202
-- Name: COLUMN metadata_types.description; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata_types.description IS 'Description of metadata attribute  based on the eTUFF metadata specification';


--
-- TOC entry 2953 (class 0 OID 0)
-- Dependencies: 202
-- Name: COLUMN metadata_types.example; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata_types.example IS 'Example value of metadata attribute on the eTUFF metadata specification';


--
-- TOC entry 2954 (class 0 OID 0)
-- Dependencies: 202
-- Name: COLUMN metadata_types.comments; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata_types.comments IS 'Comments or notes relating to the metadata attribute based on the eTUFF metadata specification';


--
-- TOC entry 2955 (class 0 OID 0)
-- Dependencies: 202
-- Name: COLUMN metadata_types.necessity; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN metadata_types.necessity IS 'Deisgnation of the metadata attribute as Required, Recommended, or Optional based on the eTUFF metadata specification';


--
-- TOC entry 203 (class 1259 OID 16601)
-- Name: observation_types; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE observation_types (
    variable_id bigint NOT NULL,
    variable_name character varying(255) NOT NULL,
    standard_name character varying(255),
    variable_source character varying(255),
    variable_units character varying(255),
    notes text,
    standard_unit character varying(255)
);


ALTER TABLE observation_types OWNER TO tagbase;

--
-- TOC entry 2956 (class 0 OID 0)
-- Dependencies: 203
-- Name: TABLE observation_types; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE observation_types IS 'Contains listings and descriptions of observation variable types based on the eTUFF specification';


--
-- TOC entry 2957 (class 0 OID 0)
-- Dependencies: 203
-- Name: COLUMN observation_types.variable_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN observation_types.variable_id IS 'Unique variable identifier based on the eTUFF tag data file specification';


--
-- TOC entry 2958 (class 0 OID 0)
-- Dependencies: 203
-- Name: COLUMN observation_types.variable_name; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN observation_types.variable_name IS 'Variable name based on the eTUFF tag data file specification';


--
-- TOC entry 2959 (class 0 OID 0)
-- Dependencies: 203
-- Name: COLUMN observation_types.standard_name; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN observation_types.standard_name IS 'CF Standard name for observation variable, if available';


--
-- TOC entry 2960 (class 0 OID 0)
-- Dependencies: 203
-- Name: COLUMN observation_types.variable_source; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN observation_types.variable_source IS 'Source authority for the given variables';


--
-- TOC entry 2961 (class 0 OID 0)
-- Dependencies: 203
-- Name: COLUMN observation_types.variable_units; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN observation_types.variable_units IS 'Units of the variable based on the eTUFF tag data file specification';


--
-- TOC entry 2962 (class 0 OID 0)
-- Dependencies: 203
-- Name: COLUMN observation_types.notes; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN observation_types.notes IS 'Notes or comments relating to the variable';


--
-- TOC entry 2963 (class 0 OID 0)
-- Dependencies: 203
-- Name: COLUMN observation_types.standard_unit; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN observation_types.standard_unit IS 'CF canonical standard unit for observation variable, if available';


--
-- TOC entry 204 (class 1259 OID 16607)
-- Name: observation_types_variable_id_seq; Type: SEQUENCE; Schema: public; Owner: tagbase
--

CREATE SEQUENCE observation_types_variable_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE observation_types_variable_id_seq OWNER TO tagbase;

--
-- TOC entry 2964 (class 0 OID 0)
-- Dependencies: 204
-- Name: observation_types_variable_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tagbase
--

ALTER SEQUENCE observation_types_variable_id_seq OWNED BY observation_types.variable_id;


--
-- TOC entry 205 (class 1259 OID 16609)
-- Name: proc_observations; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE proc_observations (
    date_time timestamp(6) with time zone NOT NULL,
    variable_id bigint NOT NULL,
    variable_value double precision NOT NULL,
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    final_value boolean NOT NULL
);


ALTER TABLE proc_observations OWNER TO tagbase;

--
-- TOC entry 2965 (class 0 OID 0)
-- Dependencies: 205
-- Name: TABLE proc_observations; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE proc_observations IS 'Contains staged source tag eTUFF data imported into Tagbase';


--
-- TOC entry 2966 (class 0 OID 0)
-- Dependencies: 205
-- Name: COLUMN proc_observations.date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN proc_observations.date_time IS 'Date/time stamp of data record from source eTUFF file ingested';


--
-- TOC entry 2967 (class 0 OID 0)
-- Dependencies: 205
-- Name: COLUMN proc_observations.variable_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN proc_observations.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested.  The variable_id is based on observation or measurment variables listed in the observation_types table';


--
-- TOC entry 2968 (class 0 OID 0)
-- Dependencies: 205
-- Name: COLUMN proc_observations.variable_value; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN proc_observations.variable_value IS 'Geophysical value of the given measured variable for the eTUFF data record';


--
-- TOC entry 2969 (class 0 OID 0)
-- Dependencies: 205
-- Name: COLUMN proc_observations.submission_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN proc_observations.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- TOC entry 2970 (class 0 OID 0)
-- Dependencies: 205
-- Name: COLUMN proc_observations.tag_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN proc_observations.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';

COMMENT ON COLUMN proc_observations.final_value IS 'Boolean flag used to trigger data migration after a batch ingest. Whenever a TRUE value is encountered, the data_migration TRIGGER is executed meaning that the data migration task is initiated';

--
-- TOC entry 206 (class 1259 OID 16612)
-- Name: submission; Type: TABLE; Schema: public; Owner: tagbase
--

CREATE TABLE submission (
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    dmas_granule_id bigint,
    date_time timestamp(6) with time zone DEFAULT now() NOT NULL,
    filename character varying(255) NOT NULL,
    version character varying(50)
);


ALTER TABLE submission OWNER TO tagbase;

--
-- TOC entry 2971 (class 0 OID 0)
-- Dependencies: 206
-- Name: TABLE submission; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON TABLE submission IS 'Contains information on source tag eTUFF files submitted for ingest into Tagbase';


--
-- TOC entry 2972 (class 0 OID 0)
-- Dependencies: 206
-- Name: COLUMN submission.submission_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN submission.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- TOC entry 2973 (class 0 OID 0)
-- Dependencies: 206
-- Name: COLUMN submission.tag_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN submission.tag_id IS 'Unique numeric Tag ID associated with the ingested tag eTUFF data file';


--
-- TOC entry 2974 (class 0 OID 0)
-- Dependencies: 206
-- Name: COLUMN submission.dmas_granule_id; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN submission.dmas_granule_id IS 'Unique numeric file identifier in the PODAAC DMAS catalog for the ingested tag eTUFF data file';


--
-- TOC entry 2975 (class 0 OID 0)
-- Dependencies: 206
-- Name: COLUMN submission.date_time; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN submission.date_time IS 'Local datetime stamp at the time of eTUFF tag data file ingestion';


--
-- TOC entry 2976 (class 0 OID 0)
-- Dependencies: 206
-- Name: COLUMN submission.filename; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN submission.filename IS 'Full name and extension of the ingested eTUFF tag data file';


--
-- TOC entry 2977 (class 0 OID 0)
-- Dependencies: 206
-- Name: COLUMN submission.version; Type: COMMENT; Schema: public; Owner: tagbase
--

COMMENT ON COLUMN submission.version IS 'Version identifier for the eTUFF tag data file ingested';


--
-- TOC entry 207 (class 1259 OID 16616)
-- Name: submission_submission_id_seq; Type: SEQUENCE; Schema: public; Owner: tagbase
--

CREATE SEQUENCE submission_submission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE submission_submission_id_seq OWNER TO tagbase;

--
-- TOC entry 2978 (class 0 OID 0)
-- Dependencies: 207
-- Name: submission_submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tagbase
--

ALTER SEQUENCE submission_submission_id_seq OWNED BY submission.submission_id;


--
-- TOC entry 208 (class 1259 OID 16618)
-- Name: submission_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: tagbase
--

CREATE SEQUENCE submission_tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE submission_tag_id_seq OWNER TO tagbase;

--
-- TOC entry 2713 (class 2604 OID 16620)
-- Name: observation_types variable_id; Type: DEFAULT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY observation_types ALTER COLUMN variable_id SET DEFAULT nextval('observation_types_variable_id_seq'::regclass);


--
-- TOC entry 2715 (class 2604 OID 16621)
-- Name: submission submission_id; Type: DEFAULT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY submission ALTER COLUMN submission_id SET DEFAULT nextval('submission_submission_id_seq'::regclass);


--
-- TOC entry 2885 (class 0 OID 16574)
-- Dependencies: 196
-- Data for Name: data_histogram_bin_data; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY data_histogram_bin_data (submission_id, tag_id, bin_id, bin_class, date_time, variable_value, position_date_time, variable_id) FROM stdin;
\.


--
-- TOC entry 2886 (class 0 OID 16577)
-- Dependencies: 197
-- Data for Name: data_histogram_bin_info; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY data_histogram_bin_info (bin_id, bin_class, min_value, max_value, variable_id) FROM stdin;
\.


--
-- TOC entry 2887 (class 0 OID 16580)
-- Dependencies: 198
-- Data for Name: data_position; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY data_position (date_time, lat, lon, lat_err, lon_err, submission_id, tag_id, "argosLC") FROM stdin;
\.


--
-- TOC entry 2888 (class 0 OID 16583)
-- Dependencies: 199
-- Data for Name: data_profile; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY data_profile (submission_id, tag_id, variable_id, date_time, depth, variable_value, position_date_time) FROM stdin;
\.


--
-- TOC entry 2889 (class 0 OID 16586)
-- Dependencies: 200
-- Data for Name: data_time_series; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY data_time_series (date_time, variable_id, variable_value, submission_id, tag_id, position_date_time) FROM stdin;
\.


--
-- TOC entry 2890 (class 0 OID 16589)
-- Dependencies: 201
-- Data for Name: metadata; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY metadata (submission_id, attribute_id, attribute_value, tag_id) FROM stdin;
\.


--
-- TOC entry 2891 (class 0 OID 16595)
-- Dependencies: 202
-- Data for Name: metadata_types; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY metadata_types (attribute_id, category, attribute_name, type, description, example, comments, necessity) FROM stdin;
1	instrument	instrument_name	string	Append an identifer that is unique within your organization. This is essential if a device is recycled.	16P0100-Refurb2	Devices might be reused, so the serial number will be the same. The only way to distinguish is by providing a unique name for the recycled product. 	required
2	instrument	instrument_type	string	Type of instrument	archival, popup, satellite, acoustic tag, or acoustic receiver	Should be restricted to the examples provided.	required
3	instrument	firmware	string	Version number of the firmware used to build the device	\N	\N	required
4	instrument	manufacturer	string	Name of manufacturer	Wildlife Computers, Microwave Telemetry, Lotek Wireless, Desert Star Systems, CEFAS, StarOddi, Sea Mammal Research Unit, Vemco, Loggerhead Instruments, Biologging Solutions, Little Leonardo, Teleonics etc.	\N	required
5	instrument	model	string	Model name	MiniPAT	\N	required
6	instrument	owner_contact	string	Contact email/ telephone/ address	\N	\N	required
7	instrument	person_owner	string	Researcher/ organization owning the device	\N	PI/scientist/organization is used interchargably here. But best to have a first-last name specified here.	required
8	instrument	serial_number	string	Serial number	16P0100	\N	required
9	instrument	date_shipment	string	Date (yyyy-mm-dd) of receiving the device from manufacturer	2017-07-11T18:24:23+00:00	The device can be fresh off the production line or refurnished with some parts replaced.	recommended
10	instrument	project	string	Name or identifer for project/ grant number	\N	\N	recommended
11	instrument	ptt	string	Platform Transmitting Terminal (PTT) number for Argos transmission.	\N	\N	recommended
12	instrument	ptt_hex	string	PTT in hexadecimal	\N	\N	recommended
13	instrument	specs	string	Specification document name/ URL/ file (e.g., in xml)	\N	Need input from manufacturer. May allow attachment or upload. Or grab it from an online archive.	recommended
14	instrument	code_map	string	Placeholder for acoustic tags	\N	Refer to ATN spec.	no
15	instrument	ping_code	string	Placeholder for acoustic tags	\N	Refer to ATN spec.	no
100	programming	programming_report	string	File/ URL to a report listing the details of programming	\N	Need input from manufacturer. May allow attachment or upload. Or grab it from an online archive.	required
101	programming	programming_software	string	Programming software with version number	\N	\N	required
102	programming	days_constantdepth	string	Days at a constant depth before release is initiated 	1	This represents a time lag in days after the tag is  floating/ detached/ sunk before the release procedure will be initiated. 	recommended
103	programming	days_mission	string	Programmed mission length in days	365	\N	recommended
104	programming	minutes_summary	string	Interval in minutes during when data are summarized for that period	1440	Data are summarized because of Argos transmission constraint.	recommended
105	programming	person_programmer	string	Person responsible for the programming	\N	\N	recommended
106	programming	seconds_sampling	string	Sampling rate (seconds) for sensor sampling	15	For basic sensors,  e.g., pressure, temperature, light	recommended
107	programming	seconds_writingdata	string	Time interval in seconds when sampled data are written to onboard storage memory	300	This specifies how frequent data will be stored, and subsequently available for download or summarizing.	recommended
108	programming	seconds_sampling_highfreq	string	Sampling rate (seconds) for sensor sampling at a higher frequency	\N	For sensors that sample in Hertz (Hz),  e.g., accelerometer, magnetometer	optional
200	attachment	attachment_method	string	Method used to put the tag on/ in the animal	tow, glue, suction, anchor, mount, implant, harness, backpack	Should be restricted to the examples provided. Tow includes tethered for popup or towed for satellite tags . Glue is using adhensive or epoxy. Mount is using screw, bolt, button, sleeve or backpack. Anchor is equivalent to applying a conventional tag or using a gun (air, spear etc.). Implant implies surgery, ingestion or insertion.	required
201	attachment	anchor_depth_cm	string	How deep (centimeter) should the anchor be in the animal?	8	May be used for cetacean tagging.	recommended
202	attachment	anchor_dimensions_mm	string	Dimensions (millimeter) as length, width, thichkness or diameter.	20 L x 14 W	Can be used loosely as size: small, medium and large.	recommended
203	attachment	anchor_material	string	Material of anchor	nylon, urethane, stainless steel, titanium	\N	recommended
204	attachment	anchor_type	string	Type of anchor	Domeier, Wilton, Titanium	\N	recommended
205	attachment	attachment_product	string	Brand name and/ product for attachment materials used	VetBond, Peel Ply, tesaÃƒâ€šÃ‚Â®	Brand and product name of suture, stainless steel wire, monofilament, bolt, tape, adhesive, epoxy, suction cup, air gun, speargun, pole, applicator and tip.	recommended
206	attachment	mount_type	string	Type of mount	Fin, tail, carapacial ridge	\N	recommended
207	attachment	release_method	string	Method to get a tag detached from the animal/ anchor	corrosive burn wire, oxidative/ explosive, galavanizing metal, acoustic release	\N	recommended
208	attachment	tether_assembly	string	Materials and methods in constructing a tether	heat-shrink or silicon tubing	Use brand name and/ product when possible.	recommended
209	attachment	tether_length_cm	string	End to end length (centimeter) of a tether	\N	\N	recommended
210	attachment	tether_material	string	Tether material for a towed tag	stainless steel wire, monofilament	Use brand name and/ product when possible.	recommended
211	attachment	anesthetic_product	string	Brand name and/ product of anesthesia used during the attachment	metomidate, Aqua-S	\N	optional
212	attachment	antifouling_product	string	Brand name and/ product of antifoluling paint or coating applied 	PropSpeed	\N	optional
213	attachment	antiseptic_product	string	Brand name and/ product of antiseptic or sterilizing agent used during the attachment	Iodine, Cicatrin	\N	optional
214	attachment	float_additional	string	Specify any additional floation used	\N	Float might be added to archival tags for external use.	optional
215	attachment	release_forced	string	If a mechanical release is engaged at depth (too avoid crushing the tag), specify the mechanism and depth at which the release is engaged.	Wildlife Computers RD1800	\N	optional
300	deployment	geospatial_lat_start	string	Latitude (decimal degree) of release/ deployment	\N	\N	required
301	deployment	geospatial_lon_start	string	Longitude (decimal degree) of release/ deployment	\N	\N	required
302	deployment	person_tagger_capture	string	Person responsible for tagging or surgery	\N	Can be the name of vet, observer, crew, spear fisherman or scientist	required
303	deployment	time_coverage_start	string	Local date time (yyyy-mm-dd hh:mm:ss) of release/ deployment	2017-07-11T18:24:23+00:00	http://en.wikipedia.org/wiki/ISO_8601	required
304	deployment	location_capture	string	Name or standard identifer of location	\N	\N	recommended
305	deployment	method_capture	string	Type of gear used to catch the animal	Longline, purse seine, troll, trawl, rod and reel, handline, set net, trap, gillnet, harpoon, hoop net, anesthesia, tangle net, dip net, vertical line entanglement (commercial fisheries, aquaculture, mooring), dredge, pound net/weir (for turtles)	\N	recommended
306	deployment	baitlure_capture	string	Bait, chum, lure or decoy used	sardine	Use brand name and/ product when possible.	optional
307	deployment	cruise_capture	string	Name or standard identifer of cruise	\N	\N	optional
308	deployment	depth_m_capture	string	Depth (meters) at which the animal was caught	\N	Can use estimated depth from hook number on longline	optional
310	deployment	hook_capture	string	Type of hook used	18/0 circle	Use brand name and/ product when possible.	optional
311	deployment	method_aboard	string	how was animal put aboard the vessel	net, sling, lifted	\N	optional
312	deployment	othertags_capture	string	List tag IDs for conventional, acoustic, PIT, band or satellite tags for multi-tagged situation, photoID, photo/video footage file names	Hallprint PAR007007	\N	optional
313	deployment	person_angler_capture	string	Person responsible for angling	\N	\N	optional
314	deployment	school_capture	string	Type of school in which the animal was caught	Free school, log, anchored FAD, drifting FAD	Include FAD number if possible.	optional
315	deployment	seastate_capture	string	World Meteorological Organization sea state code (0-9)	\N	Similar to Douglas Sea Scale 	optional
317	deployment	station_capture	string	Name or standard identifer of station	\N	\N	optional
318	deployment	temp_degC_capture	string	Air or sea surface temperature (Celcius) when the animal was caught	\N	\N	optional
319	deployment	vessel_capture	string	Name or standard identifer of vessel	\N	\N	optional
320	deployment	wind_knots_capture	string	Wind speed (knots) when the animal was caught	\N	\N	optional
401	animal	length_capture	string	Length of the animal	300	\N	required
403	animal	length_type_capture	string	Type of length measurement	 Curved fork length, Straight fork length, total length.  for turtle the standard measurements are Curved Carapace Length (CCL), Straight Carapace Length (SCL), Curved Carapace Width (CCW) and Straight Carapace Width (SCW), and researchers occasionally measure girth as well. 	May need to compile a list of types and abbreviations	required
404	animal	length_unit_capture	string	Unit of length measurement	centimeter	May need to compile a list of types and abbreviations	required
405	animal	platform	string	Common name(s) or FAO code for species name	\N	Refer to www.itis.gov or FAO species list	required
406	animal	taxonomic_serial_number	string	Taxononomic Serial Number (TSN) from Integrated Taxonomic Information System	\N	https://www.itis.gov	required
501	animal	fate_recapture	string	Fate of the animal upon recapture	harvested, released, tag and release, missing, unknown; observed/ photo ID	\N	recommended
503	animal	length_recapture	string	Length of the animal	\N	\N	recommended
505	animal	length_unit_recapture	string	Unit of length measurement	\N	May need to compile a list of types and abbreviations	recommended
407	animal	lifestage_capture	string	Life stage of the animal	adult, juvenile, subadult, weaner	\N	recommended
506	animal	lifestage_recapture	string	Life stage of the animal	\N	\N	recommended
408	animal	tag_placement	string	Description of where the tag was placed.	second dorsal fin	\N	recommended
507	animal	age_recapture	string	Age from direct aging methods if available	year-of-young, 3 y.o. etc.	Can be used to back calculate age of the individual at capture	optional
409	animal	hours_soaktime_capture	string	If caught on longline, specify soak time In hours	\N	\N	optional
508	animal	hours_soaktime_recapture	string	If caught on longline, specify soak time In hours	\N	\N	optional
410	animal	implant_numsuture	string	Number of suture used to close the wound	\N	Internal archival only	optional
411	animal	minutes_fighttime_capture	string	If caught on rod and wheel or handline, specify fight time	\N	\N	optional
509	animal	minutes_fighttime_recapture	string	If caught on rod and wheel or handline, specify fight time	\N	\N	optional
412	animal	minutes_operation	string	Time used (minutes) in carrying out the attachment or surgical procedure.	\N	\N	optional
413	animal	minutes_revival	string	If the animal is revived, specify revival time in minutes	\N	Can be time used in swimming the animal before release	optional
504	animal	length_type_recapture	string	Type of length measurement	SFL, CFL, TL, etc	May need to compile a list of types and abbreviations	recommended
316	deployment	set_float_capture	string	If caught on longline, include set number and float number	\N	It is very unlikely to tag turtle, bird/ mammal off longline.	optional
402	animal	length_method_capture	string	Method used to obtain the measurement	measured caliper, measured tape,  estimated, calculated	Calculated means calculated from length-weight relationships or other conversions.	required
502	animal	length_method_recapture	string	Method used to obtain the measurement	measured Caliper, measured tape, estimated, calculated	Calculated means calculated from length-weight relationships or other conversions	recommended
500	animal	condition_recapture	string	Description of condition/ injury. Or specify scoring system and a score.	\N	Can be generic: good, bad, gut hooked, eye hooked, bleeding. Scoring system fof fish/ shark:  reflex action mortality predictor (RAMP), Kerstetters lab ACES.  Measurement: Bioelectrical Impedance Analysis (BIA) gives phase angle and composition index. Fat: Distell Fatmeter	recommended
414	animal	mount_numbolts	string	Number of bolts used for mounting	\N	\N	optional
415	animal	sex	string	Sex of the animal	male, female, unknown	Likely only applicable to sharks upon visual confirmation	optional
416	animal	stock	string	Stock origin if known	East, West, unknown etc.	\N	optional
417	animal	tissue_sample_capture	string	List other sample types and sample IDs if collected	Blood-ID02101	Tissue can be any issue: fin clip, blood, scale, biopsy etc.	optional
510	animal	tissue_sample_recapture	string	List other sample types and sample IDs if collected	\N	Tissue can be any issue: fin clip, blood, scale, hard parts, stomach, muscle, biopsy etc.	optional
418	animal	weight_capture	string	Weight of the animal	1200	\N	optional
512	animal	weight_recapture	string	Weight of the animal	\N	\N	optional
420	animal	weight_type_capture	string	Type of weight measurement	whole	May need to compile a list of types and abbreviations: whole, dressed, gilled & gutted	optional
513	animal	weight_type_recapture	string	Type of weight measurement	\N	May need to compile a list of types and abbreviations: whole, dressed, gilled & gutted	optional
421	animal	weight_unit_capture	string	Unit of weight measurement	pound	\N	optional
514	animal	weight_unit_recapture	string	Unit of weight measurement	\N	\N	optional
600	end_of_mission	time_coverage_end	string	End date time (yyyy-mm-dd hh:mm:ss) or date range (BETWEEN yyyy-mm-dd AND yyyy-mm-dd) if estimated/ guessed.	2017-07-11T18:24:23+00:00	http://en.wikipedia.org/wiki/ISO_8601	required
602	end_of_mission	end_type	string	Description of how the end point is derived for the device.	first reported, recaptured, last transmission, recovered	\N	required
603	end_of_mission	geospatial_lat_end	string	End latitude	\N	\N	required
604	end_of_mission	geospatial_lon_end	string	End longitude	\N	\N	required
605	end_of_mission	locationclass_end	string	Argos location class for popup location or satellite transmission	\N	\N	recommended
606	end_of_mission	datetime_death	string	If mortality occurs before end datetime, specify date time (yyyy-mm-dd hh:mm:ss)	2017-07-11T18:24:23+00:00	http://en.wikipedia.org/wiki/ISO_8601	optional
700	recovery	location_recapture	string	Name or standard identifer of location	\N	\N	recommended
701	recovery	method_recapture	string	Type of gear used to catch the animal	Longline, purse seine, troll, trawl, rod and reel, handline, set net, trap, gillnet, harpoon, hoop net, anesthesia, tangle net, dip net, vertical line entanglement (commercial fisheries, aquaculture, mooring), dredge, pound net/weir (for turtles)	\N	recommended
702	recovery	person_recapture	string	Person responsible for the recapture	\N	Name of angler, observer, scientist, fisher, beach comber etc.	recommended
703	recovery	baitlure_recapture	string	Bait, chum, lure or decoy used	\N	Use brand name and/ product when possible	optional
704	recovery	cruise_recapture	string	Name or standard identifer of cruise	\N	\N	optional
705	recovery	depth_m_recapture	string	Depth (meters) at which the animal was caught	\N	Can use estimated depth from hook number on longline	optional
707	recovery	hook_recapture	string	Type of hook used	\N	Use brand name and/ product when possible.	optional
708	recovery	person_tagger_recapture	string	Person responsible for tag-and-release	\N	Very unlikely to re-tag turtle or mammal	optional
709	recovery	retagged_recapture	string	List tag IDs for conventional, acoustic, PIT, band or satellite tags for multi-tagged situation, photoID, photo/video footage file names	\N	\N	optional
710	recovery	school_recapture	string	Type of school in which the animal was caught	Free school, log, anchored FAD, drifting FAD	Include FAD number if possible	optional
711	recovery	seastate_recapture	string	World Meteorological Organization sea state code (0-9)	\N	Similar to Douglas Sea Scale 	optional
712	recovery	set_float_recapture	string	If caught on longline, include set number and float number	\N	\N	optional
713	recovery	station_recapture	string	Name or standard identifer of station	\N	\N	optional
714	recovery	temp_degC_recapture	string	Air or sea surface temperature (Celcius) when the animal was caught	\N	\N	optional
715	recovery	vessel_recapture	string	Name or standard identifer of vessel	\N	\N	optional
716	recovery	wind_knots_recapture	string	Wind speed (knots) when the animal was caught	\N	\N	optional
1000	waypoints	waypoints_source	string	State the source for waypoints	Argos, GPS, acoustic detections, manufacturer, modeled	Waypoints are 'points'" along the trajectory of the tagged animal between the start and end dates."	required
1002	waypoints	interpolation_method	string	None if no interpolation. Otherwise, specify method/ software used.	None, crawl, BÃƒÆ’Ã‚Â©zier curves, Hermite splines and cubic splines	\N	recommended
1003	waypoints	interpolation_time	string	Specify the time interval for interpolation	0, 1 hour, gap filling	Use 0 for no interpolation or gap filling for data points without any coordinates.	recommended
1004	waypoints	waypoints_method	string	If 'waypoints_source'" = '"modeled'"	 specify the method used to estimate the positions. Include citation/ reference/ url if available"	kftrack, ukfsst, trackit, tripEstimation, SSM, GPE3, Track & Loc, GeoLight, BASTrack, IKNOS	recommended
1005	waypoints	waypoints_software	string	Software packages used with version number	\N	\N	recommended
706	recovery	flag_capture	string	The vessel's country of registration	\N	\N	optional
1001	waypoints	geolocation_parameters	string	List of Geocorrection Parameters and associated values implemented. Comma seperated list in format ''parameter1:value'', ''parameter2:value'',..	eg. ''diffusion_coefficien:0.3'', ''satellite_sst'': https://podaac.jpl.nasa.gov/dataset/NCDC-L4LRblend-GLOB-AVHRR_OI''	Assuming only 1 set of waypoints per tag data file.	recommended
511	animal	weight_method_recapture	string	Method used to obtain the measurement	measured, estimated, calculated	Calculated means calculated from length-weight relationships or other conversions	optional
419	animal	weight_method_capture	string	Method used to obtain the measurement	measured, estimated, calculated	Calculated means calculated from length-weight relationships or other conversions	optional
1006	waypoints	geolocation_output	string	URL/URI to any relevant geocorrection output file(s) produced	eg. ftp://myserver/myfiles.zip	\N	optional
1100	ancillary_positions	ancillary_position_source	string	List available source(s) for other known position(s)	Acoustic detections	If an animal is tagged and then released again, this can be included here as well	optional
1101	ancillary_positions	ancillary_position_instrumentid	string	List chronologically the instruments collecting the ancillary position(s)	receiverID1003, receiverID1008, receiverID1121	\N	optional
1102	ancillary_positions	datetime_ancillary_position	string	List chronologically the datetime (yyyy-mm-dd hh:mm:ss) for ancillary position(s)	2016-01-04 22:32:21, 2016-02-01 02:41:11, 2016-03-29 09:15:31	http://en.wikipedia.org/wiki/ISO_8601	optional
1103	ancillary_positions	ancillary_position_lon	string	List chronologically the longitude for ancillary position(s)	-153.42,-152.42,-152.49	\N	optional
1104	ancillary_positions	ancillary_position_lat	string	List chronologically the latitude for ancillary position(s)	42.131,41.135,42.422	\N	optional
1105	ancillary_positions	ancillary_position_quality	string	List chronologically the quality (location class/ accuracy/ range etc.) for ancillary position(s). Can be qualitative.	LC0,LC1,LCA	Can be Argos location class or general descriptions	optional
1200	quality	found_problem	string	Is there any problem found in this dataset? One of 3 responses: yes, no, unexamined.	yes	\N	required
1201	quality	person_qc	string	Person responsible for quality control	\N	\N	required
1202	quality	problem_affecteddates	string	Date range (BETWEEN yyyy-mm-dd AND yyyy-mm-dd) in which data quality is in doubt	\N	\N	recommended
1203	quality	problem_details	string	Provide details for the problem(s)	Daily drift after sunset by 1.5 degC	\N	recommended
1204	quality	problem_numof	string	Number of problems found	1	Hard to cover all problems here, e.g., date of post-release mortality/ predation, broken light stalk, broken hardware, tag failure modes	recommended
1205	quality	problem_summary	string	List short description(s) for the problem(s)	Temperature sensor drift	\N	recommended
1206	quality	calibration_file	string	 Files/ URLs used for calibration of sensors	\N	\N	optional
309	deployment	flag_capture	string	The vessel's country of registration	\N	\N	optional
601	end_of_mission	end_details	string	Description of the cause for the end of the tag deployment mission	GPS, Argos, estimated, calculated, modeled, recovered on animal, floater at sea, animal died and sank, recovered on land, recovered by fishing fleet, recovered in port, transfer in transshipment, found in well number X, recovered in processing plant	\N	required
400	animal	condition_capture	string	Description of condition/ injury. Or specify scoring system and a score.	good	Can be generic: good, bad, gut hooked, eye hooked, bleeding. Scoring system fof fish/ shark:  reflex action mortality predictor (RAMP), Kerstetters lab ACES.  Measurement: Bioelectrical Impedance Analysis (BIA) gives phase angle and composition index. Fat: Distell Fatmeter	required
\.


--
-- TOC entry 2892 (class 0 OID 16601)
-- Dependencies: 203
-- Data for Name: observation_types; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY observation_types (variable_id, variable_name, standard_name, variable_source, variable_units, notes, standard_unit) FROM stdin;
1	datetime	\N	common	time	Date time stamp, usually understood to be in GMT time zone when time zone is not specified. Ideally, format after ISO8601 as yyyy-mm-dd hh:mm:ss	\N
2	longitude	longitude	common	degree	Decimical degree	degree_east
3	latitude	latitude	common	degree	Decimical degree	degree_north
4	pressure	sea_water_pressure	common	psi	Pressure expressed as pound-force per square inch	dbar
5	depth	depth	common	meter	Depth in meter, usually converted from pressure measurements	meter
6	temperature	sea_water_temperature	common	Celsius	External sensor temperature, usually water temperature in Celsius	K
7	internal temperature	\N	common	Celsius	Internal sesnor temperature, usually body cavity temperature in Celsius	\N
8	light	\N	common	unitless	Measured blue or green light on a logarithmic scale. Usually expressed as unitless by Wildlife Computers (light sensor in W cm-2), Lotek and Microwave Telemetry (light sensor in Lux) tags. Also termed as relative light levels.	\N
9	accelX	\N	common	G	Acceleration in the X-axis expressed as gravitational force (1 G ~ 9.8 ms-2)	\N
10	accelY	\N	common	G	Acceleration in the Y-axis expressed as gravitational force (1 G ~ 9.8 ms-2)	\N
11	accelZ	\N	common	G	Acceleration in the Z-axis expressed as gravitational force (1 G ~ 9.8 ms-2)	\N
12	accelM	\N	common	G	Magnitude of acceleration expressed as gravitational force (1 G ~ 9.8 ms-2)	\N
13	accelMdelta	\N	common	G	Change in magnitude of acceleration	\N
14	magX	\N	common	nT	Magnetic field strength in the X-axis as nanotesla	\N
15	magY	\N	common	nT	Magnetic field strength in the Y-axis as nanotesla	\N
16	magZ	\N	common	nT	Magnetic field strength in the Z-axis as nanotesla	\N
17	oxygen	mole_concentration_of_dissolved_molecular_oxygen_in_sea_water	common	ml L-1	Dissolved oxygen expressed in milliter per liter	mol m-3
18	OxySat	fractional_saturation_of_oxygen_in_sea_water	common	Percent	Oxygen saturation in percent	1
19	longitudeError	\N	common	degree	Confidence interval is bound by +/- this number	\N
20	latitudeError	\N	common	degree	Confidence interval is bound by +/- this number	\N
21	salinity	\N	common	PSU	Salinity expressed as Practical Salinity Unit, which is  is equivalent to per thousand or (o/00) or to  g/kg	\N
22	conductivity	\N	common	S m-1	Conductivity expresed as Siemens (S) per meter, which is equivalent to mS/cm	\N
23	sst	sea_surface_temperature	common	Celsius	Sea surface temperature	K
24	solarVoltage	\N	Desert Star	volts	For Desert Star tags, mean Solar Panel Voltage in SDPT_3DSN2 packet. (light intensity ~100 Lux/V)	\N
25	heartrate	\N	Star Oddi	BPM	Heart rate measured as beats per minute, BPM	\N
26	tiltX	\N	Star Oddi	degree	Tilt in the X-axis	\N
27	tiltY	\N	Star Oddi	degree	Tilt in the Y-axis	\N
28	tiltZ	\N	Star Oddi	degree	Tilt in the Z-axis	\N
29	pitch	\N	Wildlife Computers	degree	Counterclockwise rotation of the tag about its Y axis. This value is given in degrees from -90 to +90 (where a horizontal tag reads 0 degrees).	\N
30	roll	\N	Wildlife Computers	degree	Counterclockwise rotation of the tag about its X axis. This value is given in degrees from -180 to +180 (where a tag flat on its base reads 0 degrees).	\N
31	heading	\N	Wildlife Computers	degree	Direction in which the nose of the tag is pointing. The value is expressed in degrees on a scale from 0 to 360. Magnetic North corresponds to a reading of 0 with a clockwise rotation increasing the value (consistent with navigational headings).	\N
32	magDip	\N	Wildlife Computers	degree	angle at which the earthÃ¢â‚¬â„¢s magnetic flux lines enter the earthÃ¢â‚¬â„¢s surface. This value is given in degrees, from -90 to +90 with 0 being completely horizontal to the earthÃ¢â‚¬â„¢s surface. +90 corresponds to the tag resting directly over the magnetic north pole while a -90 reading means the tag is over the magnetic south pole.	\N
33	stomach temperature	\N	Wildlife Computers	Celsius	Stomach temperature, usually measured by an ingested logger	\N
1001	frequency	\N	aggregation	unitless	Frequency takes only a value between 0 and 1	\N
1002	percentage	\N	aggregation	percent	Takes a value between 0 and 100	\N
1003	count	\N	aggregation	number	Total number of times this particular data item was received, verified, or successfully decoded.	\N
1004	depthMin	\N	aggregation	meter	Mean depth in a series of measurements	\N
1005	depthMax	\N	aggregation	meter	Maximum depth in a series of measurements	\N
1006	depthMean	\N	aggregation	meter	Minimum depth in a series of measurements	\N
1007	depthMedian	\N	aggregation	meter	Median depth in a series of measurements	\N
1008	depthStDev	\N	aggregation	meter	Standard deviation of depth measurements	\N
1009	depthSunrise	\N	Microwave Telemetry	meter	Depth occupied at sunset.  Light levels are analyzed onboard the tag with manufacturer algorithm to determine the time of sunrise and sunset each day.	\N
1010	depthSunset	\N	Microwave Telemetry	meter	Depth occupied at sunrise.  Light levels are analyzed onboard the tag with manufacturer algorithm to determine the time of sunrise and sunset each day.	\N
1011	depthDelta	\N	Microwave Telemetry	meter	Delta value represents the resolution of a transmitted depth measurement after applying data compression. See manufacturer's website for details.	\N
1012	lightMin	\N	Microwave Telemetry	unitless	Minimum light level recorded in a given day. Useful for detecting a mortality event.	\N
1013	lightMax	\N	Microwave Telemetry	unitless	Maximum light level recorded in a given day. Useful for detecting a mortality event.	\N
1014	tempDelta	\N	Microwave Telemetry	Celsius	Delta value represents the resolution of a transmitted temperature measurement after applying data compression. See manufacturer's website for details.	\N
1015	tempMin	\N	aggregation	Celsius	Mean temperature in a series of measurements	\N
1016	tempMax	\N	aggregation	Celsius	Maximum temperature in a series of measurements	\N
1017	tempMean	\N	aggregation	Celsius	Mean temperature in a series of measurements	\N
1018	tempMedian	\N	aggregation	Celsius	Median temperature in a series of measurements	\N
1019	tempStDev	\N	aggregation	Celsius	Standard deviation of temperature measurements	\N
1020	sstMin	\N	aggregation	Celsius	Mean sea surface temperature in a series of measurements	\N
1021	sstMax	\N	aggregation	Celsius	Maximumsea surface  temperature in a series of measurements	\N
1022	sstMean	\N	aggregation	Celsius	Mean sea surface temperature in a series of measurements	\N
1023	sstMedian	\N	aggregation	Celsius	Median sea surface temperature in a series of measurements	\N
1024	sstStDev	\N	aggregation	Celsius	Standard deviation of sea surface temperature measurements	\N
1025	sstDepth	\N	Wildlife Computers	meter	Depth, in meters, when the sea surface temperature was sampled. This value needs to be doubled for a 2000 meter instrument.	\N
1026	sstDateTime	\N	Wildlife Computers	time	Time of day when the sea surface temperature was sampled	\N
101	PdtDepth01	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
102	PdtTempMin01	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
103	PdtTempMax01	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
104	PdtDepth02	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
105	PdtTempMin02	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
106	PdtTempMax02	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
107	PdtDepth03	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
108	PdtTempMin03	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
109	PdtTempMax03	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
110	PdtDepth04	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
111	PdtTempMin04	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
112	PdtTempMax04	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
113	PdtDepth05	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
114	PdtTempMin05	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
115	PdtTempMax05	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
116	PdtDepth06	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
117	PdtTempMin06	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
118	PdtTempMax06	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
119	PdtDepth07	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
120	PdtTempMin07	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
121	PdtTempMax07	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
122	PdtDepth08	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
123	PdtTempMin08	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
124	PdtTempMax08	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
125	PdtDepth09	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
126	PdtTempMin09	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
127	PdtTempMax09	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
128	PdtDepth10	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
129	PdtTempMin10	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
130	PdtTempMax10	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
131	PdtDepth11	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
132	PdtTempMin11	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
133	PdtTempMax11	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
134	PdtDepth12	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
135	PdtTempMin12	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
136	PdtTempMax12	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
137	PdtDepth13	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
138	PdtTempMin13	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
139	PdtTempMax13	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
140	PdtDepth14	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
141	PdtTempMin14	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
142	PdtTempMax14	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
143	PdtDepth15	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
144	PdtTempMin15	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
145	PdtTempMax15	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
146	PdtDepth16	\N	Wildlife Computers	meter	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
147	PdtTempMin16	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
148	PdtTempMax16	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, profile-depth-temperature (PDT) output in PDTs.csv	\N
301	HistDepthBinMin01	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
302	HistDepthBinMax01	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
303	HistDepthBinMin02	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
304	HistDepthBinMax02	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
305	HistDepthBinMin03	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
306	HistDepthBinMax03	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
307	HistDepthBinMin04	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
308	HistDepthBinMax04	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
309	HistDepthBinMin05	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
310	HistDepthBinMax05	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
311	HistDepthBinMin06	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
312	HistDepthBinMax06	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
313	HistDepthBinMin07	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
314	HistDepthBinMax07	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
315	HistDepthBinMin08	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
316	HistDepthBinMax08	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
317	HistDepthBinMin09	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
318	HistDepthBinMax09	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
319	HistDepthBinMin10	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
320	HistDepthBinMax10	\N	Wildlife Computers, Desert Star	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
321	HistDepthBinMin11	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
322	HistDepthBinMax11	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
323	HistDepthBinMin12	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
324	HistDepthBinMax12	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
325	HistDepthBinMin13	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
326	HistDepthBinMax13	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
327	HistDepthBinMin14	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
328	HistDepthBinMax14	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
329	HistDepthBinMin15	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
330	HistDepthBinMax15	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
331	HistDepthBinMin16	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
332	HistDepthBinMax16	\N	Wildlife Computers	meter	For Wildlife Computers tags, bin definition for time-at-depth output in Histos.csv	\N
333	HistTempBinMin01	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
334	HistTempBinMax01	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
335	HistTempBinMin02	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
336	HistTempBinMax02	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
337	HistTempBinMin03	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
338	HistTempBinMax03	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
339	HistTempBinMin04	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
340	HistTempBinMax04	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
341	HistTempBinMin05	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
342	HistTempBinMax05	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
343	HistTempBinMin06	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
344	HistTempBinMax06	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
345	HistTempBinMin07	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
346	HistTempBinMax07	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
347	HistTempBinMin08	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
348	HistTempBinMax08	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
349	HistTempBinMin09	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
350	HistTempBinMax09	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
351	HistTempBinMin10	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
352	HistTempBinMax10	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
353	HistTempBinMin11	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
354	HistTempBinMax11	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
355	HistTempBinMin12	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
356	HistTempBinMax12	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
357	HistTempBinMin13	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
358	HistTempBinMax13	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
359	HistTempBinMin14	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
360	HistTempBinMax14	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
361	HistTempBinMin15	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
362	HistTempBinMax15	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
363	HistTempBinMin16	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
364	HistTempBinMax16	\N	Wildlife Computers	Celsius	For Wildlife Computers tags, bin definition for time-at-temperature output in Histos.csv	\N
365	TimeAtDepthBin01	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
366	TimeAtDepthBin02	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
367	TimeAtDepthBin03	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
368	TimeAtDepthBin04	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
369	TimeAtDepthBin05	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
370	TimeAtDepthBin06	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
371	TimeAtDepthBin07	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
372	TimeAtDepthBin08	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
373	TimeAtDepthBin09	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
374	TimeAtDepthBin10	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
375	TimeAtDepthBin11	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
376	TimeAtDepthBin12	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
377	TimeAtDepthBin13	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
378	TimeAtDepthBin14	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
379	TimeAtDepthBin15	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
380	TimeAtDepthBin16	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
381	TimeAtTempBin01	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
382	TimeAtTempBin02	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
383	TimeAtTempBin03	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
384	TimeAtTempBin04	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
385	TimeAtTempBin05	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
386	TimeAtTempBin06	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
387	TimeAtTempBin07	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
388	TimeAtTempBin08	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
389	TimeAtTempBin09	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
390	TimeAtTempBin10	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
391	TimeAtTempBin11	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
392	TimeAtTempBin12	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
393	TimeAtTempBin13	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
394	TimeAtTempBin14	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
395	TimeAtTempBin15	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
396	TimeAtTempBin16	\N	Wildlife Computers	frequency	Time spent at bin during a sampling period (e.g., 1-24 hours), expressed as a value between 0 and 1 in Histos.csv	\N
34	argosLC	\N	common	unitless	Argos Location Class positional single character quality codes based on the scheme defined by the Argos System (http://www.argos-system.org/manual/3-location/34_location_classes.htm)	\N
\.


--
-- TOC entry 2894 (class 0 OID 16609)
-- Dependencies: 205
-- Data for Name: proc_observations; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY proc_observations (date_time, variable_id, variable_value, submission_id, tag_id) FROM stdin;
\.


--
-- TOC entry 2895 (class 0 OID 16612)
-- Dependencies: 206
-- Data for Name: submission; Type: TABLE DATA; Schema: public; Owner: tagbase
--

COPY submission (submission_id, tag_id, dmas_granule_id, date_time, filename, version) FROM stdin;
\.


--
-- TOC entry 2979 (class 0 OID 0)
-- Dependencies: 204
-- Name: observation_types_variable_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tagbase
--

SELECT pg_catalog.setval('observation_types_variable_id_seq', 1, false);


--
-- TOC entry 2980 (class 0 OID 0)
-- Dependencies: 207
-- Name: submission_submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tagbase
--

SELECT pg_catalog.setval('submission_submission_id_seq', 1, false);


--
-- TOC entry 2981 (class 0 OID 0)
-- Dependencies: 208
-- Name: submission_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tagbase
--

SELECT pg_catalog.setval('submission_tag_id_seq', 1, false);


--
-- TOC entry 2718 (class 2606 OID 16623)
-- Name: data_histogram_bin_data data_histogram_bin_data_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT data_histogram_bin_data_pkey PRIMARY KEY (submission_id, tag_id, bin_id, bin_class, date_time, variable_id) WITH (fillfactor='100');


--
-- TOC entry 2721 (class 2606 OID 16625)
-- Name: data_histogram_bin_info data_histogram_bin_info_bin_id_bin_class_key; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_histogram_bin_info
    ADD CONSTRAINT data_histogram_bin_info_bin_id_bin_class_key UNIQUE (bin_id, bin_class);


--
-- TOC entry 2723 (class 2606 OID 16627)
-- Name: data_histogram_bin_info data_histogram_bin_info_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_histogram_bin_info
    ADD CONSTRAINT data_histogram_bin_info_pkey PRIMARY KEY (variable_id, bin_id, bin_class) WITH (fillfactor='100');


--
-- TOC entry 2727 (class 2606 OID 16629)
-- Name: data_position data_position_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_position
    ADD CONSTRAINT data_position_pkey PRIMARY KEY (submission_id, tag_id, date_time);


--
-- TOC entry 2730 (class 2606 OID 16631)
-- Name: data_profile data_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_profile
    ADD CONSTRAINT data_profile_pkey PRIMARY KEY (submission_id, tag_id, date_time, depth, variable_id) WITH (fillfactor='100');


--
-- TOC entry 2734 (class 2606 OID 16633)
-- Name: data_time_series data_time_series_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_time_series
    ADD CONSTRAINT data_time_series_pkey PRIMARY KEY (submission_id, tag_id, variable_id, date_time);


--
-- TOC entry 2737 (class 2606 OID 16635)
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (submission_id, attribute_id);


--
-- TOC entry 2739 (class 2606 OID 16637)
-- Name: metadata_types metadata_types_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY metadata_types
    ADD CONSTRAINT metadata_types_pkey PRIMARY KEY (attribute_id);


--
-- TOC entry 2741 (class 2606 OID 16639)
-- Name: observation_types observation_types_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY observation_types
    ADD CONSTRAINT observation_types_pkey PRIMARY KEY (variable_id);


--
-- TOC entry 2743 (class 2606 OID 16641)
-- Name: observation_types observation_types_variable_name_key; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY observation_types
    ADD CONSTRAINT observation_types_variable_name_key UNIQUE (variable_name);


--
-- TOC entry 2745 (class 2606 OID 16643)
-- Name: proc_observations proc_observations_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY proc_observations
    ADD CONSTRAINT proc_observations_pkey PRIMARY KEY (date_time, variable_id, submission_id);


--
-- TOC entry 2747 (class 2606 OID 16645)
-- Name: submission submission_pkey; Type: CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY submission
    ADD CONSTRAINT submission_pkey PRIMARY KEY (submission_id);


--
-- TOC entry 2716 (class 1259 OID 16646)
-- Name: data_histogram_bin_data_date_time_index; Type: INDEX; Schema: public; Owner: tagbase
--

CREATE INDEX data_histogram_bin_data_date_time_index ON public.data_histogram_bin_data USING btree (date_time);


--
-- TOC entry 2719 (class 1259 OID 16647)
-- Name: data_histogram_bin_data_pos_date_time_index; Type: INDEX; Schema: public; Owner: tagbase
--

CREATE INDEX data_histogram_bin_data_pos_date_time_index ON public.data_histogram_bin_data USING btree (position_date_time);


--
-- TOC entry 2724 (class 1259 OID 16648)
-- Name: data_position_date_time_index; Type: INDEX; Schema: public; Owner: tagbase
--

CREATE INDEX data_position_date_time_index ON public.data_position USING btree (date_time);


--
-- TOC entry 2725 (class 1259 OID 16649)
-- Name: data_position_latlontime_index; Type: INDEX; Schema: public; Owner: tagbase
--

CREATE INDEX data_position_latlontime_index ON public.data_position USING btree (date_time, lat, lon, submission_id, tag_id);


--
-- TOC entry 2728 (class 1259 OID 16650)
-- Name: data_profile_date_time_index; Type: INDEX; Schema: public; Owner: tagbase
--

CREATE INDEX data_profile_date_time_index ON public.data_profile USING btree (date_time);


--
-- TOC entry 2731 (class 1259 OID 16651)
-- Name: data_profile_pos_date_time_index; Type: INDEX; Schema: public; Owner: tagbase
--

CREATE INDEX data_profile_pos_date_time_index ON public.data_profile USING btree (position_date_time);


--
-- TOC entry 2732 (class 1259 OID 16652)
-- Name: data_time_series_date_time_index; Type: INDEX; Schema: public; Owner: tagbase
--

CREATE INDEX data_time_series_date_time_index ON public.data_time_series USING btree (date_time);


--
-- TOC entry 2735 (class 1259 OID 16653)
-- Name: data_time_series_pos_date_time_index; Type: INDEX; Schema: public; Owner: tagbase
--

CREATE INDEX data_time_series_pos_date_time_index ON public.data_time_series USING btree (position_date_time);


--
-- TOC entry 2748 (class 2606 OID 16654)
-- Name: data_histogram_bin_data data_histogram_bin_data_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT data_histogram_bin_data_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- TOC entry 2752 (class 2606 OID 16659)
-- Name: data_histogram_bin_info data_histogram_bin_info; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_histogram_bin_info
    ADD CONSTRAINT data_histogram_bin_info FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- TOC entry 2753 (class 2606 OID 16664)
-- Name: data_position data_position_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_position
    ADD CONSTRAINT data_position_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- TOC entry 2757 (class 2606 OID 16669)
-- Name: data_time_series data_time_series_data_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_time_series
    ADD CONSTRAINT data_time_series_data_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id);


--
-- TOC entry 2758 (class 2606 OID 16674)
-- Name: data_time_series data_time_series_variable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_time_series
    ADD CONSTRAINT data_time_series_variable_id_fkey FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- TOC entry 2749 (class 2606 OID 16679)
-- Name: data_histogram_bin_data datahistogrambindata_observationtypes_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT datahistogrambindata_observationtypes_fkey FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- TOC entry 2754 (class 2606 OID 16684)
-- Name: data_profile dataprofile_dataposition_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_profile
    ADD CONSTRAINT dataprofile_dataposition_fkey FOREIGN KEY (submission_id, tag_id, position_date_time) REFERENCES data_position(submission_id, tag_id, date_time);


--
-- TOC entry 2755 (class 2606 OID 16689)
-- Name: data_profile dataprofile_observationtypes_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_profile
    ADD CONSTRAINT dataprofile_observationtypes_fkey FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- TOC entry 2756 (class 2606 OID 16694)
-- Name: data_profile dataprofile_submission_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_profile
    ADD CONSTRAINT dataprofile_submission_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id);


--
-- TOC entry 2759 (class 2606 OID 16699)
-- Name: data_time_series datetimeseries_datapositions_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_time_series
    ADD CONSTRAINT datetimeseries_datapositions_fkey FOREIGN KEY (submission_id, tag_id, position_date_time) REFERENCES data_position(submission_id, tag_id, date_time);


--
-- TOC entry 2750 (class 2606 OID 16704)
-- Name: data_histogram_bin_data histogrambindata_dataposition_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT histogrambindata_dataposition_fkey FOREIGN KEY (submission_id, tag_id, position_date_time) REFERENCES data_position(submission_id, tag_id, date_time);


--
-- TOC entry 2751 (class 2606 OID 16709)
-- Name: data_histogram_bin_data histogrambindata_histogrambininfo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT histogrambindata_histogrambininfo_fkey FOREIGN KEY (bin_id, bin_class) REFERENCES data_histogram_bin_info(bin_id, bin_class);


--
-- TOC entry 2760 (class 2606 OID 16714)
-- Name: metadata metadata_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES metadata_types(attribute_id);


--
-- TOC entry 2761 (class 2606 OID 16719)
-- Name: metadata metadata_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- TOC entry 2762 (class 2606 OID 16724)
-- Name: proc_observations proc_observations_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY proc_observations
    ADD CONSTRAINT proc_observations_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- TOC entry 2763 (class 2606 OID 16729)
-- Name: proc_observations proc_observations_variable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: tagbase
--

ALTER TABLE ONLY proc_observations
    ADD CONSTRAINT proc_observations_variable_id_fkey FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


-- Completed on 2019-12-10 13:35:32

--
-- PostgreSQL database dump complete
--

--
-- The following TRIGGER ensures that upon ingestion of an arbitary eTUFF file into tagbase-server,
-- the data migration phase is auotmated. This means that the only manual database administration
-- involves the creation of the materialized views. This can simply be done by executing
-- 'tagbase-materialized-view.sql' in the pgAdmin4 Web application Query Tool.
CREATE OR REPLACE FUNCTION execute_data_migration() RETURNS trigger AS $BODY$
  BEGIN
    --\connect tagbase
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
         AND a.variable_id = c.variable_id RETURNING a.date_time,
                                                     a.variable_id,
                                                     a.variable_value,
                                                     a.submission_id,
                                                     b.tag_id)
    INSERT INTO data_time_series
    SELECT *
    FROM moved_rows;
    -- -- data_position
    WITH moved_rows AS
      ( DELETE
       FROM proc_observations a USING submission b,
                                      observation_types c
       WHERE c.variable_name = 'longitude'
         AND a.submission_id = b.submission_id
         AND a.variable_id = c.variable_id RETURNING a.date_time,
                                                     a.variable_id,
                                                     a.variable_value,
                                                     a.submission_id,
                                                     b.tag_id,
                                                     cast(('0.0') AS double precision) AS initial_lat)
    INSERT INTO data_position (date_time, lat, lon, submission_id, tag_id)
    SELECT date_time,
           initial_lat,
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
         AND c.variable_name = 'latitude' RETURNING a.date_time,
                                                    a.variable_id,
                                                    a.variable_value,
                                                    a.submission_id)
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
         AND c.variable_name = 'longitudeError' RETURNING a.date_time,
                                                    a.variable_id,
                                                    a.variable_value,
                                                    a.submission_id)
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
         AND c.variable_name = 'latitudeError' RETURNING a.date_time,
                                                    a.variable_id,
                                                    a.variable_value,
                                                    a.submission_id)
    UPDATE data_position
    SET lat_err = moved_rows.variable_value
    FROM moved_rows
    WHERE data_position.date_time = moved_rows.date_time
      AND data_position.submission_id = moved_rows.submission_id;
    -- -- data_histogram_bin_info
    WITH moved_rows AS
      ( DELETE
       FROM proc_observations a USING observation_types b,
                                      submission c
       WHERE a.variable_id = b.variable_id
         AND b.variable_name LIKE 'Hist%'
         AND a.submission_id = c.submission_id RETURNING a.submission_id AS bin_id,
                                                  cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                                  variable_value)
    INSERT INTO data_histogram_bin_info
    SELECT *
    FROM moved_rows ON CONFLICT DO NOTHING;
    WITH moved_rows AS
      ( DELETE
       FROM proc_observations a USING observation_types b,
                                      submission c
       WHERE a.variable_id = b.variable_id
         AND b.variable_name LIKE 'Hist%'
         AND a.submission_id = c.submission_id RETURNING a.submission_id AS bin_id,
                                                  cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                                  variable_value)
    UPDATE data_histogram_bin_info
    SET max_value = moved_rows.variable_value
    FROM moved_rows
    WHERE data_histogram_bin_info.bin_id = moved_rows.bin_id
      AND data_histogram_bin_info.bin_class = moved_rows.bin_class;
    -- data_histogram_bin_data
    WITH moved_rows AS
      ( DELETE
       FROM proc_observations a USING observation_types b,
                                      submission c
       WHERE a.variable_id = b.variable_id
         AND b.variable_name LIKE 'TimeAt%'
         AND a.submission_id = c.submission_id RETURNING a.submission_id,
                                                          c.tag_id,
                                                          a.submission_id AS bin_id,
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
         AND a.submission_id = c.submission_id RETURNING a.date_time,
                                                         a.variable_id,
                                                         a.variable_value,
                                                         a.submission_id,
                                                         variable_name,
                                                         c.tag_id)
    INSERT INTO data_profile (date_time, depth, submission_id, tag_id)
    SELECT date_time,
           variable_value,
           submission_id,
           tag_id
    FROM moved_rows;
    WITH moved_rows AS
      ( DELETE
       FROM proc_observations a USING observation_types b,
                                      data_profile c,
                                      submission e
       WHERE a.variable_id = b.variable_id
         AND b.variable_name LIKE 'PdtTempMin%'
         AND a.submission_id = c.submission_id
         AND a.date_time = c.date_time
         AND e.submission_id = a.submission_id RETURNING a.date_time,
                                                         a.variable_id,
                                                         a.variable_value AS variable_value,
                                                         a.submission_id)
    UPDATE data_profile
    SET variable_value = moved_rows.variable_value
    FROM moved_rows
    WHERE data_profile.date_time = moved_rows.date_time
      AND data_profile.submission_id = moved_rows.submission_id;
    WITH moved_rows AS
      ( DELETE
       FROM proc_observations a USING observation_types b,
                                      data_profile c,
                                      submission e
       WHERE a.variable_id = b.variable_id
         AND b.variable_name LIKE 'PdtTempMax%'
         AND a.submission_id = c.submission_id
         AND a.date_time = c.date_time
         AND e.submission_id = a.submission_id RETURNING a.date_time,
                                                         a.variable_id,
                                                         a.variable_value,
                                                         a.submission_id)
    UPDATE data_profile
    SET variable_value = moved_rows.variable_value
    FROM moved_rows
    WHERE data_profile.date_time = moved_rows.date_time
      AND data_profile.submission_id = moved_rows.submission_id;
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
    RETURN NULL;
  END;
$BODY$ LANGUAGE plpgsql;
CREATE TRIGGER data_migration AFTER INSERT ON proc_observations FOR EACH ROW WHEN (NEW.final_value)
  EXECUTE PROCEDURE execute_data_migration();
