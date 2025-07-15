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
    file_id TEXT REFERENCES "dox_agent.contract_versions"(file_id), -- foreign key
    analysis_json TEXT,
    created_at TIMESTAMP
);


create or replace function mark_contract_version_processed()
returns trigger
language plpgsql
as
$$
begin
    update "dox_agent.contract_versions"
    set processed_doc = true, updated_at = now()
    where file_id = NEW.file_id;

    return NEW;
end;
$$;

drop trigger if exists set_processed_doc_to_true_trigger
on "dox_agent.revision_analyses";

create trigger set_processed_doc_to_true_trigger
after insert
on "dox_agent.revision_analyses"
for each row
execute procedure mark_contract_version_processed();