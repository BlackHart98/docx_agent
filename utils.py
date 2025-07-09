import typing as t
import logging


# this is a simplisitic diffing to help me regenerate the original text
def get_paragragh_difflist( paragraph_meta: t.Dict[str, t.Any]) -> t.Optional[t.Tuple[int, t.List[t.Tuple[str, str]]]]:
    if len(paragraph_meta["track_changes"]) != 0:
        logging.info(paragraph_meta["track_changes"])
        sorted_track_change_list: t.List[t.Tuple[int, int, str, str]] = sorted([
            (track_changes["start"], track_changes["end"], track_changes["text"], track_changes["type"]) 
            for track_changes in paragraph_meta["track_changes"]])
        concat_chunk = []
        found_paragraph_start: bool = False
        last_index: int = 0
        for chunk in sorted_track_change_list:
            if chunk[0] != 0 and not found_paragraph_start:
                concat_chunk += [(paragraph_meta["paragraph"], "origin"), (chunk[2], chunk[3])]
                found_paragraph_start = True
            elif chunk[0] == 0 and not found_paragraph_start:
                concat_chunk += [(chunk[2], chunk[3])]
                last_index = chunk[1] 
            elif last_index > chunk[1]:
                concat_chunk += [(paragraph_meta["paragraph"], "origin"), (chunk[2], chunk[3])]
            else:
                concat_chunk += [(chunk[2], chunk[3])]
        return paragraph_meta["paragraph_index"], concat_chunk
    else:
        return None