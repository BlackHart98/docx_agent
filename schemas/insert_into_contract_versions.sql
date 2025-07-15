insert into docx_agent.contract_versions (
    file_id, 
    file_name, 
    processed_doc, 
    created_at,
    updated_at) 
values (:file_id, :file_name, true, now(), NULL);