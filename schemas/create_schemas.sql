drop schema if exists dox_agent cascade; 

create schema dox_agent;

SET search_path TO dox_agent;

create table "dox_agent.contract_versions"(
    file_id TEXT PRIMARY KEY,
    file_name TEXT,
    summary_json TEXT,
    processed_doc BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);



create table "dox_agent.revision_analyses"(
    analysis_id SERIAL,
    file_id TEXT, -- foreign key
    analysis_json TEXT,
    created_at TIMESTAMP
);