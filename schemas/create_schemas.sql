drop schema if exists dox_agent; 

create schema dox_agent;

create table dox_agent.contract_versions(
    contract_version_id VARCHAR,
    file_name VARCHAR,
    check_sum VARCHAR,
    processed_doc BOOLEAN,
    updated_at TIMESTAMP,
);


create table dox_agent.contract_revisions(
    revision_id VARCHAR,
    contract_version_id VARCHAR, -- foreign key
    contract_meta VARCHAR,
    contract_clause_uuid VARCHAR,
    processed_paragraph BOOLEAN, 
    updated_at TIMESTAMP,
);


create table dox_agent.revision_analyses(
    analysis_id VARCHAR,
    revision_id VARCHAR, -- foreign key
    contract_version_id VARCHAR, -- foreign key
    analysis_summary VARCHAR,
    risk_assessment VARCHAR, -- "L", "M", "H"
    recommended_action VARCHAR, -- "A", "R", or "P"
    suggested_response VARCHAR,
    updated_at TIMESTAMP,
);
