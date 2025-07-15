drop schema if exists dox_agent cascade; 

create schema dox_agent;

SET search_path TO dox_agent;

create table "dox_agent.contract_versions"(
    file_id TEXT UNIQUE,
    file_name TEXT,
    summary_json TEXT,
    processed_doc BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


create table "dox_agent.contract_revisions"(
    revision_id TEXT,
    file_id TEXT, -- foreign key
    contract_meta TEXT,
    contract_clause_uuid TEXT,
    processed_paragraph BOOLEAN, 
    updated_at TIMESTAMP
);


create table "dox_agent.revision_analyses"(
    analysis_id TEXT,
    file_id TEXT, -- foreign key
    analysis_summary TEXT,
    risk_assessment TEXT, -- "L", "M", "H"
    recommended_action TEXT, -- "A", "R", or "P"
    suggested_response TEXT,
    updated_at TIMESTAMP
);