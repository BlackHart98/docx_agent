SET search_path TO dox_agent;

select *
from "dox_agent.revision_analyses"
where file_id = :file_id
limit 1;