SET search_path TO dox_agent;





insert into "dox_agent.contract_versions" (
    file_id, 
    file_name, 
    summary_json,
    processed_doc, 
    created_at,
    updated_at) 
values (:file_id, :file_name, :summary_json, false, now(), NULL);