SET search_path TO dox_agent;

select *
from "dox_agent.contract_versions"
where file_id = :file_id
limit 1;