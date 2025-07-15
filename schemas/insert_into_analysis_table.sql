SET search_path TO dox_agent;


insert into "dox_agent.revision_analyses"(
    file_id, -- foreign key
    analysis_json,
    created_at)
values (:file_id, :analysis_json, now());;