--
-- PostgreSQL database dump
--

-- Dumped from database version 13.6
-- Dumped by pg_dump version 13.6

CREATE ROLE tagbase WITH SUPERUSER LOGIN;

CREATE DATABASE tagbase WITH ENCODING = 'UTF8' OWNER = 'tagbase';

ALTER USER tagbase PASSWORD 'tagbase';

\connect tagbase

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
-- SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_table_access_method = heap;

SET default_with_oids = false;

--
-- Name: data_histogram_bin_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE data_histogram_bin_data (
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    bin_id bigint NOT NULL,
    bin_class integer NOT NULL,
    date_time timestamp(6) with time zone NOT NULL,
    variable_value character varying(30) NOT NULL,
    position_date_time timestamp(6) with time zone,
    variable_id bigint NOT NULL
);


ALTER TABLE data_histogram_bin_data OWNER TO postgres;

--
-- Name: TABLE data_histogram_bin_data; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE data_histogram_bin_data IS 'Contains the frequency for corresponding summary data binning schemes (migrated from proc_observations)';


--
-- Name: COLUMN data_histogram_bin_data.submission_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_data.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- Name: COLUMN data_histogram_bin_data.tag_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_data.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- Name: COLUMN data_histogram_bin_data.bin_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_data.bin_id IS 'Unique bin ID for the summary bin-frequency class';


--
-- Name: COLUMN data_histogram_bin_data.bin_class; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_data.bin_class IS 'Sequential numeric bin class identifier related to either Depth or Temperature. Usually there are 12 (1-12) bin ranges (Min and Max Depth or Temperature respectively), however there are times the bin ranges will not be 12, but instead 14 or 16. The larger the number, the more recent the tag models are from tag manufacturers, as they make more bytes available for storage.';


--
-- Name: COLUMN data_histogram_bin_data.date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_data.date_time IS 'Date/time stamp of the tag summarized bin-frequency data record';


--
-- Name: COLUMN data_histogram_bin_data.variable_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_data.variable_value IS 'Aggregate measure for the given bin-interval of the geophysical value of the observed tag variable record';


--
-- Name: COLUMN data_histogram_bin_data.position_date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_data.position_date_time IS 'Date/time stamp of nearest matched associated positional record';


--
-- Name: COLUMN data_histogram_bin_data.variable_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_data.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested. The variable_id is based on observation or measurement variables listed in the observation_types table.  Note that records in this table are NOT expected to be equivalent to those in the variable_id column of the data_histogram_bin_info table';


--
-- Name: data_histogram_bin_info; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE data_histogram_bin_info (
    bin_id bigint NOT NULL,
    bin_class integer NOT NULL,
    min_value character varying(30) NOT NULL,
    max_value character varying(30) NOT NULL,
    variable_id bigint NOT NULL
);


ALTER TABLE data_histogram_bin_info OWNER TO postgres;

--
-- Name: TABLE data_histogram_bin_info; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE data_histogram_bin_info IS 'Contains definitions of binning schemes for summary tag data (migrated from proc_observations)';


--
-- Name: COLUMN data_histogram_bin_info.bin_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_info.bin_id IS 'Unique bin ID for the summary bin-frequency class';


--
-- Name: COLUMN data_histogram_bin_info.bin_class; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_info.bin_class IS 'Sequential numeric bin class identifier related to either Depth or Temperature. Usually there are 12 (1-12) bin ranges (Min and Max Depth or Temperature respectively), however there are times the bin ranges will not be 12, but instead 14 or 16. The larger the number, the more recent the tag models are from tag manufacturers, as they make more bytes available for storage.';


--
-- Name: COLUMN data_histogram_bin_info.min_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_info.min_value IS 'Value of minimum/lower bound of bin interval';


--
-- Name: COLUMN data_histogram_bin_info.max_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_info.max_value IS 'Value of maximum/upper bound of bin interval';


--
-- Name: COLUMN data_histogram_bin_info.variable_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_histogram_bin_info.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested. The variable_id is based on observation or measurement variables listed in the observation_types table. Note that records in this table are NOT expected to be equivalent to those in the variable_id column of the data_histogram_bin_data table';


--
-- Name: data_position; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE data_position (
    date_time timestamp(6) with time zone NOT NULL,
    lat character varying(30) NOT NULL,
    lon character varying(30) NOT NULL,
    lat_err character varying(30),
    lon_err character varying(30),
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    argos_location_class character varying(1),
    solution_id integer NOT NULL DEFAULT 1,
    flag_as_reference integer NOT NULL DEFAULT 0
);


ALTER TABLE data_position OWNER TO postgres;

--
-- Name: TABLE data_position; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE data_position IS 'Contains the tag positional data series with associated Lat/Lon error estimates where available (migrated from proc_observations)';


--
-- Name: COLUMN data_position.date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.date_time IS 'Date/time stamp of the tag positional data record';


--
-- Name: COLUMN data_position.lat; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.lat IS 'Latitude in decimal degrees of the positional data tag record';


--
-- Name: COLUMN data_position.lon; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.lon IS 'Longitude in decimal degrees of the positional data tag record';


--
-- Name: COLUMN data_position.lat_err; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.lat_err IS 'Error associated with the tag record Latitudinal positional estimate';


--
-- Name: COLUMN data_position.lon_err; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.lon_err IS 'Error associated with the tag record Longitudinal positional estimate';


--
-- Name: COLUMN data_position.submission_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- Name: COLUMN data_position.tag_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- Name: COLUMN data_position.argos_location_class; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.argos_location_class IS 'ARGOS Location Class code (G,3,2,1,0,A,B,Z)

https://www.argos-system.org/wp-content/uploads/2016/08/r363_9_argos_users_manual-v1.6.6.pdf  , page 13.';


--
-- Name: COLUMN data_position.solution_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.solution_id IS 'Unique numeric identifier for a given tag geolocation dataset solution. solution_id=1 is assigned to the primary or approved solution. Incremented solution_id''s assigned to other positional dataset solutions for a given tag_id and submission_id';


--
-- Name: COLUMN data_position.flag_as_reference; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_position.flag_as_reference IS 'Integer (representing psudo boolean value) flag field which identifies whether positional data associated with a given Tag and Track solution are considered to be coordinates of the "Reference" track (ie. best solution currently). Coordinate record takes 1 if it is part of the Reference track or 0 if it is not.';

--
-- Name: data_profile; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE data_profile (
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    variable_id bigint NOT NULL,
    date_time timestamp(6) with time zone NOT NULL,
    depth character varying(30) NOT NULL,
    variable_value character varying(30) DEFAULT '',
    position_date_time timestamp(6) with time zone
);


ALTER TABLE data_profile OWNER TO postgres;

--
-- Name: TABLE data_profile; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE data_profile IS 'Contains the summarized bin profile tag observations (migrated from proc_observations)';


--
-- Name: COLUMN data_profile.submission_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_profile.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- Name: COLUMN data_profile.tag_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_profile.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- Name: COLUMN data_profile.variable_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_profile.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested.  The variable_id is based on observation or measurement variables listed in the observation_types table';


--
-- Name: COLUMN data_profile.date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_profile.date_time IS 'Date/time stamp of the tag data record';


--
-- Name: COLUMN data_profile.depth; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_profile.depth IS 'Depth of the tag data record';


--
-- Name: COLUMN data_profile.variable_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_profile.variable_value IS 'Geophysical value of the observed tag variable record';


--
-- Name: COLUMN data_profile.position_date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_profile.position_date_time IS 'Date/time stamp of nearest matched associated positional record';


--
-- Name: data_time_series; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE data_time_series (
    date_time timestamp(6) with time zone NOT NULL,
    variable_id bigint NOT NULL,
    variable_value character varying(30) NOT NULL,
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    position_date_time timestamp(6) with time zone
);


ALTER TABLE data_time_series OWNER TO postgres;

--
-- Name: TABLE data_time_series; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE data_time_series IS 'Contains the continuous measurement archival time series of tag geophysical measurements (migrated from proc_observations)';


--
-- Name: COLUMN data_time_series.date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_time_series.date_time IS 'Date/time stamp of the tag data record';


--
-- Name: COLUMN data_time_series.variable_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_time_series.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested.  The variable_id is based on observation or measurement variables listed in the observation_types table';


--
-- Name: COLUMN data_time_series.variable_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_time_series.variable_value IS 'Geophysical value of the observed tag variable record';


--
-- Name: COLUMN data_time_series.submission_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_time_series.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- Name: COLUMN data_time_series.tag_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_time_series.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- Name: COLUMN data_time_series.position_date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN data_time_series.position_date_time IS 'Date/time stamp of nearest matched associated positional record';


--
-- Name: metadata; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE metadata (
    submission_id bigint NOT NULL,
    attribute_id bigint NOT NULL,
    attribute_value text NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE metadata OWNER TO postgres;

--
-- Name: TABLE metadata; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE metadata IS 'Contains the ingested tag metadata consistent with the eTUFF specification';


--
-- Name: COLUMN metadata.submission_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- Name: COLUMN metadata.attribute_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata.attribute_id IS 'Unique numeric metadata attribute ID based on the eTUFF metadata specification';


--
-- Name: COLUMN metadata.attribute_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata.attribute_value IS 'Value associated with the given eTUFF metadata attribute';


--
-- Name: COLUMN metadata.tag_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- Name: metadata_position; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE metadata_position (
    submission_id bigint NOT NULL,
    attribute_id bigint NOT NULL,
    attribute_value text NOT NULL,
    tag_id bigint NOT NULL,
    solution_id integer NOT NULL DEFAULT 1
);


ALTER TABLE metadata_position OWNER TO postgres;

--
-- Name: TABLE metadata_position; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE metadata_position IS 'Contains the ingested tag metadata consistent with the eTUFF specification';


--
-- Name: COLUMN metadata_position.submission_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_position.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- Name: COLUMN metadata_position.attribute_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_position.attribute_id IS 'Unique numeric metadata attribute ID based on the eTUFF metadata specification';


--
-- Name: COLUMN metadata_position.attribute_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_position.attribute_value IS 'Value associated with the given eTUFF metadata attribute';


--
-- Name: COLUMN metadata_position.tag_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_position.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- Name: COLUMN metadata_position.solution_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_position.solution_id IS 'Unique numeric identifier for a given tag geolocation dataset solution. solution_id=1 is assigned to the primary or approved solution. Incremented solution_id''s assigned to other positional dataset solutions for a given tag_id and submission_id';


--
-- Name: metadata_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE metadata_types (
    attribute_id bigint NOT NULL,
    category character varying(1024) NOT NULL,
    attribute_name character varying(1024) NOT NULL,
    description text NOT NULL,
    example text,
    comments text,
    necessity character varying(1024) NOT NULL
);


ALTER TABLE metadata_types OWNER TO postgres;

--
-- Name: TABLE metadata_types; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE metadata_types IS 'Contains descriptive information on tag metadata based on the eTUFF specification';


--
-- Name: COLUMN metadata_types.attribute_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_types.attribute_id IS 'Unique numeric metadata attribute ID based on the eTUFF metadata specification';


--
-- Name: COLUMN metadata_types.category; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_types.category IS 'Metadata attribute category or group based on the eTUFF metadata specification';


--
-- Name: COLUMN metadata_types.attribute_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_types.attribute_name IS 'Name of metadata attribute based on the eTUFF metadata specification';


--
-- Name: COLUMN metadata_types.description; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_types.description IS 'Description of metadata attribute based on the eTUFF metadata specification';


--
-- Name: COLUMN metadata_types.example; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_types.example IS 'Example value of metadata attribute on the eTUFF metadata specification';


--
-- Name: COLUMN metadata_types.comments; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_types.comments IS 'Comments or notes relating to the metadata attribute based on the eTUFF metadata specification';


--
-- Name: COLUMN metadata_types.necessity; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN metadata_types.necessity IS 'Designation of the metadata attribute as Required, Recommended, or Optional based on the eTUFF metadata specification';


--
-- Name: observation_types; Type: TABLE; Schema: public; Owner: postgres
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


ALTER TABLE observation_types OWNER TO postgres;

--
-- Name: TABLE observation_types; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE observation_types IS 'Contains listings and descriptions of observation variable types based on the eTUFF specification';


--
-- Name: COLUMN observation_types.variable_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN observation_types.variable_id IS 'Unique variable identifier based on the eTUFF tag data file specification';


--
-- Name: COLUMN observation_types.variable_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN observation_types.variable_name IS 'Variable name based on the eTUFF tag data file specification';


--
-- Name: COLUMN observation_types.standard_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN observation_types.standard_name IS 'CF Standard name for observation variable, if available';


--
-- Name: COLUMN observation_types.variable_source; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN observation_types.variable_source IS 'Source authority for the given variables';


--
-- Name: COLUMN observation_types.variable_units; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN observation_types.variable_units IS 'Units of the variable based on the eTUFF tag data file specification';


--
-- Name: COLUMN observation_types.notes; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN observation_types.notes IS 'Notes or comments relating to the variable';


--
-- Name: COLUMN observation_types.standard_unit; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN observation_types.standard_unit IS 'CF canonical standard unit for observation variable, if available';


--
-- Name: observation_types_variable_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE observation_types_variable_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE observation_types_variable_id_seq OWNER TO postgres;

--
-- Name: observation_types_variable_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE observation_types_variable_id_seq OWNED BY observation_types.variable_id;


--
-- Name: proc_observations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE UNLOGGED TABLE proc_observations (
    date_time timestamp(6) with time zone NOT NULL,
    variable_id bigint NOT NULL,
    variable_value character varying(30) NOT NULL,
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL
);


ALTER TABLE proc_observations OWNER TO postgres;

--
-- Name: TABLE proc_observations; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE proc_observations IS 'Contains staged source tag eTUFF data imported into Tagbase';


--
-- Name: COLUMN proc_observations.date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN proc_observations.date_time IS 'Date/time stamp of data record from source eTUFF file ingested';


--
-- Name: COLUMN proc_observations.variable_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN proc_observations.variable_id IS 'Unique variable identifier for the data record from the source eTUFF file ingested.  The variable_id is based on observation or measurement variables listed in the observation_types table';


--
-- Name: COLUMN proc_observations.variable_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN proc_observations.variable_value IS 'Value  of the given observation_type variable for the eTUFF data record';


--
-- Name: COLUMN proc_observations.submission_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN proc_observations.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- Name: COLUMN proc_observations.tag_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN proc_observations.tag_id IS 'Unique numeric Tag ID associated with the ingested tag data file';


--
-- Name: submission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE submission (
    submission_id bigint NOT NULL,
    tag_id bigint NOT NULL,
    date_time timestamp(6) with time zone DEFAULT now() NOT NULL,
    filename text NOT NULL,
    version character varying(50),
    notes text
);


ALTER TABLE submission OWNER TO postgres;

--
-- Name: TABLE submission; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE submission IS 'Contains information on source tag eTUFF files submitted for ingest into Tagbase';


--
-- Name: COLUMN submission.submission_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN submission.submission_id IS 'Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase';


--
-- Name: COLUMN submission.tag_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN submission.tag_id IS 'Unique numeric Tag ID associated with the ingested tag eTUFF data file';


--
-- Name: COLUMN submission.date_time; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN submission.date_time IS 'Local datetime stamp at the time of eTUFF tag data file ingestion';


--
-- Name: COLUMN submission.filename; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN submission.filename IS 'Full path, name and extension of the ingested eTUFF tag data file';


--
-- Name: COLUMN submission.version; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN submission.version IS 'Version identifier for the eTUFF tag data file ingested';


--
-- Name: COLUMN submission.notes; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN submission.notes IS 'Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just  secondary solutionpositional meta/data)';


--
-- Name: submission_submission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE submission_submission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE submission_submission_id_seq OWNER TO postgres;

--
-- Name: submission_submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE submission_submission_id_seq OWNED BY submission.submission_id;


--
-- Name: submission_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE submission_tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE submission_tag_id_seq OWNER TO postgres;

ALTER SEQUENCE submission_tag_id_seq OWNED BY submission.tag_id;

--
-- Name: observation_types variable_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY observation_types ALTER COLUMN variable_id SET DEFAULT nextval('observation_types_variable_id_seq'::regclass);


--
-- Name: submission submission_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY submission ALTER COLUMN submission_id SET DEFAULT nextval('submission_submission_id_seq'::regclass);


--
-- Data for Name: data_histogram_bin_data; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY data_histogram_bin_data (submission_id, tag_id, bin_id, bin_class, date_time, variable_value, position_date_time, variable_id) FROM stdin;
\.


--
-- Data for Name: data_histogram_bin_info; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY data_histogram_bin_info (bin_id, bin_class, min_value, max_value, variable_id) FROM stdin;
\.


--
-- Data for Name: data_position; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY data_position (date_time, lat, lon, lat_err, lon_err, submission_id, tag_id, argos_location_class, solution_id) FROM stdin;
\.


--
-- Data for Name: data_profile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY data_profile (submission_id, tag_id, variable_id, date_time, depth, variable_value, position_date_time) FROM stdin;
\.


--
-- Data for Name: data_time_series; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY data_time_series (date_time, variable_id, variable_value, submission_id, tag_id, position_date_time) FROM stdin;
\.


--
-- Data for Name: metadata; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY metadata (submission_id, attribute_id, attribute_value, tag_id) FROM stdin;
\.


--
-- Data for Name: metadata_position; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY metadata_position (submission_id, attribute_id, attribute_value, tag_id, solution_id) FROM stdin;
\.


--
-- Data for Name: proc_observations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY proc_observations (date_time, variable_id, variable_value, submission_id, tag_id) FROM stdin;
\.


--
-- Data for Name: submission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY submission (submission_id, tag_id, date_time, filename, version, notes) FROM stdin;
\.


--
-- Name: observation_types_variable_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('observation_types_variable_id_seq', 1, false);


--
-- Name: submission_submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('submission_submission_id_seq', 1, false);


--
-- Name: submission_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('submission_tag_id_seq', 1, false);


--
-- Name: data_histogram_bin_data data_histogram_bin_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT data_histogram_bin_data_pkey PRIMARY KEY (submission_id, tag_id, variable_id, bin_id, bin_class, date_time) WITH (fillfactor='100');


--
-- Name: data_histogram_bin_info data_histogram_bin_info_bin_id_bin_class_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_histogram_bin_info
    ADD CONSTRAINT data_histogram_bin_info_bin_id_bin_class_key UNIQUE (bin_id, bin_class);


--
-- Name: data_histogram_bin_info data_histogram_bin_info_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_histogram_bin_info
    ADD CONSTRAINT data_histogram_bin_info_pkey PRIMARY KEY (variable_id, bin_id, bin_class) WITH (fillfactor='100');


--
-- Name: data_position data_position_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_position
    ADD CONSTRAINT data_position_pkey PRIMARY KEY (submission_id, tag_id, solution_id, date_time) WITH (fillfactor='100');


--
-- Name: data_profile data_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_profile
    ADD CONSTRAINT data_profile_pkey PRIMARY KEY (submission_id, tag_id, date_time, depth, variable_id) WITH (fillfactor='100');


--
-- Name: data_time_series data_time_series_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_time_series
    ADD CONSTRAINT data_time_series_pkey PRIMARY KEY (submission_id, tag_id, variable_id, date_time) WITH (fillfactor='100');


--
-- Name: metadata metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (submission_id, attribute_id);


--
-- Name: metadata_position metadata_pkey01; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY metadata_position
    ADD CONSTRAINT metadata_pkey01 PRIMARY KEY (submission_id, attribute_id, tag_id, solution_id) WITH (fillfactor='100');


--
-- Name: metadata_types metadata_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY metadata_types
    ADD CONSTRAINT metadata_types_pkey PRIMARY KEY (attribute_id);


--
-- Name: observation_types observation_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY observation_types
    ADD CONSTRAINT observation_types_pkey PRIMARY KEY (variable_id);


--
-- Name: observation_types observation_types_variable_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY observation_types
    ADD CONSTRAINT observation_types_variable_name_key UNIQUE (variable_name);


--
-- Name: proc_observations proc_observations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY proc_observations
    ADD CONSTRAINT proc_observations_pkey PRIMARY KEY (date_time, variable_id, submission_id);


--
-- Name: submission submission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY submission
    ADD CONSTRAINT submission_pkey PRIMARY KEY (submission_id);


--
-- Name: data_histogram_bin_data_date_time_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX data_histogram_bin_data_date_time_index ON data_histogram_bin_data USING btree (date_time);


--
-- Name: data_histogram_bin_data_pos_date_time_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX data_histogram_bin_data_pos_date_time_index ON data_histogram_bin_data USING btree (position_date_time);


--
-- Name: data_position_date_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX data_position_date_time ON data_position USING btree (date_time);


--
-- Name: data_position_latlontime_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX data_position_latlontime_index ON data_position USING btree (submission_id, tag_id, solution_id, date_time, lat, lon, argos_location_class) WITH (fillfactor='100');


--
-- Name: data_profile_date_time_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX data_profile_date_time_index ON data_profile USING btree (date_time);


--
-- Name: data_profile_pos_date_time_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX data_profile_pos_date_time_index ON data_profile USING btree (position_date_time);


--
-- Name: data_time_series_date_time_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX data_time_series_date_time_index ON data_time_series USING btree (date_time);


--
-- Name: data_time_series_pos_date_time_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX data_time_series_pos_date_time_index ON data_time_series USING btree (position_date_time);


--
-- Name: data_histogram_bin_data data_histogram_bin_data_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT data_histogram_bin_data_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- Name: data_histogram_bin_info data_histogram_bin_info; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_histogram_bin_info
    ADD CONSTRAINT data_histogram_bin_info FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- Name: data_position data_position_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_position
    ADD CONSTRAINT data_position_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- Name: data_time_series data_time_series_data_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_time_series
    ADD CONSTRAINT data_time_series_data_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id);


--
-- Name: data_time_series data_time_series_variable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_time_series
    ADD CONSTRAINT data_time_series_variable_id_fkey FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- Name: data_histogram_bin_data datahistogrambindata_observationtypes_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT datahistogrambindata_observationtypes_fkey FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- Name: data_profile dataprofile_observationtypes_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_profile
    ADD CONSTRAINT dataprofile_observationtypes_fkey FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- Name: data_profile dataprofile_submission_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_profile
    ADD CONSTRAINT dataprofile_submission_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id);


--
-- Name: data_histogram_bin_data histogrambindata_histogrambininfo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY data_histogram_bin_data
    ADD CONSTRAINT histogrambindata_histogrambininfo_fkey FOREIGN KEY (bin_id, bin_class) REFERENCES data_histogram_bin_info(bin_id, bin_class);


--
-- Name: metadata metadata_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES metadata_types(attribute_id);


--
-- Name: metadata_position metadata_attribute_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY metadata_position
    ADD CONSTRAINT metadata_attribute_id_fkey FOREIGN KEY (attribute_id) REFERENCES metadata_types(attribute_id);


--
-- Name: metadata metadata_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- Name: metadata_position metadata_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY metadata_position
    ADD CONSTRAINT metadata_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- Name: proc_observations proc_observations_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY proc_observations
    ADD CONSTRAINT proc_observations_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES submission(submission_id) ON DELETE CASCADE;


--
-- Name: proc_observations proc_observations_variable_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY proc_observations
    ADD CONSTRAINT proc_observations_variable_id_fkey FOREIGN KEY (variable_id) REFERENCES observation_types(variable_id);


--
-- PostgreSQL database dump complete
--

--
-- The following TRIGGER ensures that upon ingestion of an eTUFF file into tagbase-server,
-- the data migration procedure is executed. The only remaining manual database administration
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
          AND b.variable_name LIKE 'HistDepthBinMin%'
          AND a.submission_id = c.submission_id RETURNING a.submission_id AS bin_id,
                                                   cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                                   a.variable_value AS min_value,
                                                   '',
                                                   a.variable_id AS variable_value)
     INSERT INTO data_histogram_bin_info
     SELECT *
     FROM moved_rows ON CONFLICT DO NOTHING;
     WITH moved_rows AS
       ( DELETE
        FROM proc_observations a USING observation_types b,
                                       submission c
        WHERE a.variable_id = b.variable_id
          AND b.variable_name LIKE 'HistDepthBinMax%'
          AND a.submission_id = c.submission_id RETURNING a.submission_id AS bin_id,
                                                   cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                                   a.variable_value AS max_value)
     UPDATE data_histogram_bin_info
     SET max_value = moved_rows.max_value
     FROM moved_rows
     WHERE data_histogram_bin_info.bin_id = moved_rows.bin_id
       AND data_histogram_bin_info.bin_class = moved_rows.bin_class;
     -- data_histogram_bin_data
     WITH moved_rows AS
       ( DELETE
        FROM proc_observations a USING observation_types b,
                                       submission c,
                                       data_time_series d
        WHERE a.variable_id = b.variable_id
          AND b.variable_name LIKE 'TimeAt%'
          AND a.submission_id = c.submission_id RETURNING a.submission_id,
                                                           c.tag_id,
                                                           a.submission_id AS bin_id,
                                                           cast(substring(variable_name, '(\d+)') AS int) AS bin_class,
                                                           a.date_time,
                                                           a.variable_value,
                                                           d.position_date_time,
                                                           a.variable_id)
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
          AND a.submission_id = c.submission_id RETURNING a.submission_id,
                                                          c.tag_id,
                                                          a.variable_id,
                                                          a.date_time,
                                                          a.variable_value)
     INSERT INTO data_profile (submission_id, tag_id, variable_id, date_time, depth)
     SELECT submission_id,
            tag_id,
            variable_id,
            date_time,
            variable_value
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
 CREATE TRIGGER data_migration AFTER INSERT OR UPDATE ON proc_observations FOR EACH STATEMENT
   EXECUTE PROCEDURE execute_data_migration();
