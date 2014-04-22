CREATE TABLE clinical_study (
    NCT_ID VARCHAR(50), 
    PRIMARY KEY (NCT_ID), 
    DOWNLOAD_DATE VARCHAR(200), 
    DOWNLOAD_DATE_DT DATE, 
    ORG_STUDY_ID VARCHAR(100), 
    BRIEF_TITLE VARCHAR(1000), 
    OFFICIAL_TITLE VARCHAR(1000), 
    ACRONYM VARCHAR(50), 
    SOURCE VARCHAR(200), 
    HAS_DMC VARCHAR(10), 
    BRIEF_SUMMARY TEXT, 
    DETAILED_DESCRIPTION TEXT, 
    OVERALL_STATUS VARCHAR(200), 
    START_DATE VARCHAR(50), 
    COMPLETION_DATE VARCHAR(50), 
    COMPLETION_DATE_TYPE VARCHAR(50), 
    PRIMARY_COMPLETION_DATE VARCHAR(50), 
    PRIMARY_COMPLETION_DATE_TYPE VARCHAR(50), 
    PHASE VARCHAR(50), 
    STUDY_TYPE VARCHAR(100), 
    STUDY_DESIGN VARCHAR(2000), 
    NUMBER_OF_ARMS INT, 
    NUMBER_OF_GROUPS INT, 
    ENROLLMENT_TYPE VARCHAR(50), 
    ENROLLMENT INT, 
    BIOSPEC_RETENTION VARCHAR(50), 
    BIOSPEC_DESCR VARCHAR(2000), 
    CRITERIA TEXT, 
    GENDER VARCHAR(50), 
    MINIMUM_AGE VARCHAR(50), 
    MAXIMUM_AGE VARCHAR(50), 
    HEALTHY_VOLUNTEERS VARCHAR(50), 
    SAMPLING_METHOD VARCHAR(100), 
    STUDY_POP VARCHAR(2000), 
    VERIFICATION_DATE VARCHAR(50), 
    LASTCHANGED_DATE VARCHAR(50), 
    FIRSTRECEIVED_DATE VARCHAR(50), 
    IS_SECTION_801 VARCHAR(50), 
    IS_FDA_REGULATED VARCHAR(50), 
    WHY_STOPPED VARCHAR(1000), 
    HAS_EXPANDED_ACCESS VARCHAR(50), 
    FIRSTRECEIVED_RESULTS_DATE VARCHAR(50), 
    URL VARCHAR(250), 
    TARGET_DURATION VARCHAR(250), 
    STUDY_RANK VARCHAR(50), 
    LIMITATIONS_AND_CAVEATS VARCHAR(2000)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE arm_groups (
    ARM_GROUP_ID INT, 
    PRIMARY KEY (ARM_GROUP_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    ARM_GROUP_LABEL VARCHAR(100), 
    ARM_GROUP_TYPE VARCHAR(50), 
    DESCRIPTION VARCHAR(2000), 
    GROUP_ID VARCHAR(20)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE authorities (
    AUTHORITY_ID INT, 
    PRIMARY KEY (AUTHORITY_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    AUTHORITY VARCHAR(300)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE central_contacts (
    CENTRAL_CONTACT_ID INT, 
    PRIMARY KEY (CENTRAL_CONTACT_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    CONTACT_TYPE VARCHAR(100), 
    NAME_DEGREE VARCHAR(150), 
    PHONE VARCHAR(50), 
    PHONE_EXT VARCHAR(50), 
    EMAIL VARCHAR(200)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE condition_browse (
    MESH_CONDITION_ID INT, 
    PRIMARY KEY (MESH_CONDITION_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    MESH_TERM VARCHAR(200)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE conditions (
    CONDITION_ID INT, 
    PRIMARY KEY (CONDITION_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    CONDITION_NAME VARCHAR(200)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE designs (
    DESIGN_ID INT, 
    PRIMARY KEY (DESIGN_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    DESIGN_NAME VARCHAR(500), 
    DESIGN_VALUE VARCHAR(500), 
    MASKED_ROLE VARCHAR(100)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE facilities (
    FACILITY_ID INT, 
    PRIMARY KEY (FACILITY_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    STATUS VARCHAR(50), 
    FACILITY_NAME VARCHAR(500), 
    CITY VARCHAR(100), 
    STATE VARCHAR(100), 
    ZIP VARCHAR(50), 
    COUNTRY VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE facility_contacts (
    FACILITY_CONTACT_ID INT, 
    PRIMARY KEY (FACILITY_CONTACT_ID), 
    FACILITY_ID INT, 
    FOREIGN KEY (FACILITY_ID) REFERENCES facilities(FACILITY_ID), 
    NCT_ID VARCHAR(50), 
    CONTACT_TYPE VARCHAR(100), 
    NAME_DEGREE VARCHAR(150), 
    PHONE VARCHAR(50), 
    PHONE_EXT VARCHAR(50), 
    EMAIL VARCHAR(200)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE interventions (
    INTERVENTION_ID INT, 
    PRIMARY KEY (INTERVENTION_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    INTERVENTION_TYPE VARCHAR(100), 
    INTERVENTION_NAME VARCHAR(500), 
    DESCRIPTION VARCHAR(2000)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE intervention_arm_groups (
    INT_ARM_GROUP_ID INT, 
    PRIMARY KEY (INT_ARM_GROUP_ID), 
    INTERVENTION_ID INT, 
    FOREIGN KEY (INTERVENTION_ID) REFERENCES interventions(INTERVENTION_ID), 
    NCT_ID VARCHAR(50), 
    ARM_GROUP_LABEL VARCHAR(100)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE intervention_browse (
    MESH_INTERVENTION_ID INT, 
    PRIMARY KEY (MESH_INTERVENTION_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    MESH_TERM VARCHAR(200)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE intervention_other_names (
    INT_OTHER_NAME_ID INT, 
    PRIMARY KEY (INT_OTHER_NAME_ID), 
    NCT_ID VARCHAR(50), 
    INTERVENTION_ID INT, 
    FOREIGN KEY (INTERVENTION_ID) REFERENCES interventions(INTERVENTION_ID), 
    OTHER_NAME VARCHAR(500)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE investigators (
    INVESTIGATOR_ID INT, 
    PRIMARY KEY (INVESTIGATOR_ID), 
    FACILITY_ID INT, 
    FOREIGN KEY (FACILITY_ID) REFERENCES facilities(FACILITY_ID), 
    NCT_ID VARCHAR(50), 
    NAME_DEGREE VARCHAR(150), 
    ROLE VARCHAR(100), 
    AFFILIATION VARCHAR(500)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE keywords (
    KEYWORD_ID INT, 
    PRIMARY KEY (KEYWORD_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    KEYWORD VARCHAR(200)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE links (
    LINK_ID INT, 
    PRIMARY KEY (LINK_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    URL VARCHAR(500), 
    DESCRIPTION VARCHAR(300)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE location_countries (
    LOCATION_COUNTRIES_ID INT, 
    PRIMARY KEY (LOCATION_COUNTRIES_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    COUNTRY VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE mesh_thesaurus (
    MESH_SEQID INT, 
    PRIMARY KEY (MESH_SEQID), 
    MESH_ID VARCHAR(50), 
    MESH_TERM VARCHAR(200)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE nct_aliases (
    NCT_ALIAS_ID INT, 
    PRIMARY KEY (NCT_ALIAS_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    NCT_ALIAS VARCHAR(200)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE overall_officials (
    OVERALL_OFFICIAL_ID INT, 
    PRIMARY KEY (OVERALL_OFFICIAL_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    ROLE VARCHAR(100), 
    NAME_DEGREE VARCHAR(150), 
    AFFILIATION VARCHAR(300)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE reference (
    REFERENCE_ID INT, 
    PRIMARY KEY (REFERENCE_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    REFERENCE_TYPE VARCHAR(50), 
    CITATION TEXT, 
    PMID VARCHAR(20)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE removed_countries (
    REMOVED_COUNTRIES_ID INT, 
    PRIMARY KEY (REMOVED_COUNTRIES_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    COUNTRY VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE reported_events (
    REPORTED_EVENT_ID INT, 
    PRIMARY KEY (REPORTED_EVENT_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    EVENT_TYPE VARCHAR(50), 
    TIME_FRAME VARCHAR(300), 
    DESCRIPTION VARCHAR(1000), 
    FREQUENCY_THRESHOLD VARCHAR(50), 
    DEFAULT_VOCAB VARCHAR(100), 
    DEFAULT_ASSESSMENT VARCHAR(300)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE reported_event_ctgy (
    REPORTED_EVENT_CATEGORY_ID INT, 
    PRIMARY KEY (REPORTED_EVENT_CATEGORY_ID), 
    REPORTED_EVENT_ID INT, 
    FOREIGN KEY (REPORTED_EVENT_ID) REFERENCES reported_events(REPORTED_EVENT_ID), 
    CATEGORY_TITLE VARCHAR(300), 
    CATEGORY_SUB_TITLE VARCHAR(1000), 
    CATEGORY_DESCRIPTION VARCHAR(1000), 
    CATEGORY_ASSESSMENT VARCHAR(300)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE reported_event_ctgy_grp (
    REPORTED_EVENT_CATGY_GRP_ID INT, 
    PRIMARY KEY (REPORTED_EVENT_CATGY_GRP_ID), 
    REPORTED_EVENT_CATEGORY_ID INT, 
    FOREIGN KEY (REPORTED_EVENT_CATEGORY_ID) REFERENCES reported_event_ctgy(REPORTED_EVENT_CATEGORY_ID), 
    ARM_GROUP_ID INT, 
    FOREIGN KEY (ARM_GROUP_ID) REFERENCES arm_groups(ARM_GROUP_ID), 
    SUBJECTS_AFFECTED VARCHAR(50), 
    SUBJECTS_AT_RISK VARCHAR(50), 
    EVENTS VARCHAR(2000)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE responsible_parties (
    RESPONSIBLE_PARTY_ID INT, 
    PRIMARY KEY (RESPONSIBLE_PARTY_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    NAME_TITLE VARCHAR(300), 
    ORGANIZATION VARCHAR(250), 
    RESPONSIBLE_PARTY_TYPE VARCHAR(50), 
    INVESTIGATOR_AFFILIATION VARCHAR(300), 
    INVESTIGATOR_FULL_NAME VARCHAR(300), 
    INVESTIGATOR_TITLE VARCHAR(300)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_baseline (
    RSLTS_BASELINE_ID INT, 
    PRIMARY KEY (RSLTS_BASELINE_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    POPULATION VARCHAR(500)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_baseline_measures (
    BASELINE_ID INT, 
    PRIMARY KEY (BASELINE_ID), 
    RSLTS_BASELINE_ID INT, 
    FOREIGN KEY (RSLTS_BASELINE_ID) REFERENCES results_baseline(RSLTS_BASELINE_ID), 
    BASELINE_MEASURE_TITLE VARCHAR(300), 
    DESCRIPTION VARCHAR(2000), 
    UNITS_OF_MEASURE VARCHAR(50), 
    MEASURE_TYPE VARCHAR(50), 
    DISPERSION VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_baseline_measure_catgy (
    BASELINE_MEASURE_CATGY_ID INT, 
    PRIMARY KEY (BASELINE_MEASURE_CATGY_ID), 
    BASELINE_ID INT, 
    FOREIGN KEY (BASELINE_ID) REFERENCES results_baseline_measures(BASELINE_ID), 
    CATEGORY_TITLE VARCHAR(300), 
    ARM_GROUP_ID INT, 
    FOREIGN KEY (ARM_GROUP_ID) REFERENCES arm_groups(ARM_GROUP_ID), 
    BASELINE_VALUE VARCHAR(50), 
    SPREAD VARCHAR(50), 
    LOWER_LIMIT VARCHAR(50), 
    UPPER_LIMIT VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_outcomes (
    OUTCOME_ID INT, 
    PRIMARY KEY (OUTCOME_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    OUTCOME_TYPE VARCHAR(50), 
    OUTCOME_TITLE VARCHAR(300), 
    TIME_FRAME VARCHAR(300), 
    SAFETY_ISSUE VARCHAR(50), 
    OUTCOME_DESCRIPTION VARCHAR(2000), 
    POPULATION VARCHAR(500), 
    POSTING_DATE VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_outcome_analysis (
    RESULTS_OUTCOME_ANALYSIS_ID INT, 
    PRIMARY KEY (RESULTS_OUTCOME_ANALYSIS_ID), 
    OUTCOME_ID INT, 
    FOREIGN KEY (OUTCOME_ID) REFERENCES results_outcomes(OUTCOME_ID), 
    PARAM_TYPE VARCHAR(50), 
    DISPERSION_TYPE VARCHAR(50), 
    CI_PERCENT INT, 
    CI_LOWER_LIMIT VARCHAR(50), 
    CI_UPPER_LIMIT VARCHAR(50), 
    GROUPS_DESC VARCHAR(1000), 
    NON_INFERIORITY VARCHAR(50), 
    NON_INFERIORITY_DESC VARCHAR(1000), 
    P_VALUE VARCHAR(50), 
    P_VALUE_DESC VARCHAR(1000), 
    METHOD VARCHAR(100), 
    METHOD_DESC VARCHAR(500), 
    PARAM_VALUE VARCHAR(50), 
    ESTIMATE_DESC VARCHAR(2000), 
    DISPERSION_VALUE VARCHAR(50), 
    CI_N_SIDES VARCHAR(50), 
    CI_UPPER_LIMIT_NA_COMMENT VARCHAR(500)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_outcome_analysis_grp (
    RESULTS_OUTCOME_ANAL_GRP_ID INT, 
    PRIMARY KEY (RESULTS_OUTCOME_ANAL_GRP_ID), 
    RESULTS_OUTCOME_ANALYSIS_ID INT, 
    FOREIGN KEY (RESULTS_OUTCOME_ANALYSIS_ID) REFERENCES results_outcome_analysis(RESULTS_OUTCOME_ANALYSIS_ID), 
    ARM_GROUP_ID INT, 
    FOREIGN KEY (ARM_GROUP_ID) REFERENCES arm_groups(ARM_GROUP_ID)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_outcome_measure (
    OUTCOME_MEASURE_ID INT, 
    PRIMARY KEY (OUTCOME_MEASURE_ID), 
    OUTCOME_ID INT, 
    FOREIGN KEY (OUTCOME_ID) REFERENCES results_outcomes(OUTCOME_ID), 
    OUTCOME_MEASURE_TITLE VARCHAR(300), 
    MEASURE_DESCRIPTION VARCHAR(2000), 
    UNIT_OF_MEASURE VARCHAR(50), 
    MEASURE_TYPE VARCHAR(50), 
    DISPERSION VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_outcome_measure_ctgy (
    OUTCOME_MEASURE_CATGY_ID INT, 
    PRIMARY KEY (OUTCOME_MEASURE_CATGY_ID), 
    OUTCOME_MEASURE_ID INT, 
    FOREIGN KEY (OUTCOME_MEASURE_ID) REFERENCES results_outcome_measure(OUTCOME_MEASURE_ID), 
    CATEGORY_TITLE VARCHAR(300), 
    ARM_GROUP_ID INT, 
    FOREIGN KEY (ARM_GROUP_ID) REFERENCES arm_groups(ARM_GROUP_ID), 
    OUTCOME_VALUE VARCHAR(50), 
    SPREAD VARCHAR(50), 
    LOWER_LIMIT VARCHAR(50), 
    UPPER_LIMIT VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_partic_flows (
    PARTICIPANT_FLOW_ID INT, 
    PRIMARY KEY (PARTICIPANT_FLOW_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    PERIOD_TITLE VARCHAR(300), 
    RECRUITMENT_DETAILS VARCHAR(1000), 
    PRE_ASSIGNMENT_DETAILS VARCHAR(1000)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_partflow_mlstn (
    MILESTONE_ID INT, 
    PRIMARY KEY (MILESTONE_ID), 
    PARTICIPANT_FLOW_ID INT, 
    FOREIGN KEY (PARTICIPANT_FLOW_ID) REFERENCES results_partic_flows(PARTICIPANT_FLOW_ID), 
    MILESTONE_TYPE VARCHAR(50), 
    MILESTONE_TITLE VARCHAR(300)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_partflow_mlstn_grp (
    MILESTONE_GROUP_ID INT, 
    PRIMARY KEY (MILESTONE_GROUP_ID), 
    MILESTONE_ID INT, 
    FOREIGN KEY (MILESTONE_ID) REFERENCES results_partflow_mlstn(MILESTONE_ID), 
    ARM_GROUP_ID INT, 
    FOREIGN KEY (ARM_GROUP_ID) REFERENCES arm_groups(ARM_GROUP_ID), 
    PARTFLOW_COUNT VARCHAR(20), 
    PARTICIPANT_DESCRIPTION VARCHAR(1000)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_point_of_contact (
    POINT_OF_CONTACT_ID INT, 
    PRIMARY KEY (POINT_OF_CONTACT_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    NAME_OR_TITLE VARCHAR(300), 
    ORGANIZATION VARCHAR(300), 
    PHONE VARCHAR(50), 
    EMAIL VARCHAR(300)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE results_restriction_agreements (
    AGREEMENT_ID INT, 
    PRIMARY KEY (AGREEMENT_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    PI_EMPLOYEE VARCHAR(500), 
    RESTRICTIVE_AGREEMENT VARCHAR(1000)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE secondary_ids (
    SEC_ID INT, 
    PRIMARY KEY (SEC_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    SECONDARY_ID VARCHAR(100)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE sponsors (
    SPONSOR_ID INT, 
    PRIMARY KEY (SPONSOR_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    SPONSOR_TYPE VARCHAR(50), 
    AGENCY VARCHAR(200), 
    AGENCY_CLASS VARCHAR(50)
) DEFAULT CHARACTER SET=utf8;
CREATE TABLE study_outcome (
    OUTCOME_ID INT, 
    PRIMARY KEY (OUTCOME_ID), 
    NCT_ID VARCHAR(50), 
    FOREIGN KEY (NCT_ID) REFERENCES clinical_study(NCT_ID), 
    STUDY_OUTCOMES_TYPE VARCHAR(50), 
    MEASURE VARCHAR(300), 
    SAFETY_ISSUE VARCHAR(50), 
    TIME_FRAME VARCHAR(300), 
    DESCRIPTION VARCHAR(2000)
) DEFAULT CHARACTER SET=utf8;