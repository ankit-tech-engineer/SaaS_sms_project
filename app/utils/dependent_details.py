from typing import List, Dict, Union, Any
from app.core.database import get_database

async def fetch_dependent_details(
    data: Union[List[Dict[str, Any]], Dict[str, Any]], 
    dependency_map: Dict[str, Dict[str, str]]
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Enriches data with details from dependent collections.
    
    Args:
        data: A dictionary or a list of dictionaries containing foreign keys.
        dependency_map: A mapping of foreign_key field names to configuration.
            Example:
            {
                "org_id": {
                    "collection": "organizations",
                    "name_field": "org_name"
                },
                "plan_id": {
                    "collection": "plans",
                    "name_field": "name"
                }
            }
            
    Returns:
        The enriched data with _{key}_details and _{key}_name fields.
    """
    if not data:
        return data

    is_single = False
    if isinstance(data, dict):
        items = [data]
        is_single = True
    else:
        items = data

    db = await get_database()
    
    # Pre-fetch all necessary IDs to minimize DB calls
    lookup_keys = {} # { "org_id": { "organizations": ["id1", "id2"] } } - actually simplify to { "field_key": set(ids) }
    
    # 1. Collect IDs
    for key, config in dependency_map.items():
        ids_to_fetch = set()
        for item in items:
            val = item.get(key)
            if val:
                ids_to_fetch.add(val)
        
        if ids_to_fetch:
            lookup_keys[key] = ids_to_fetch

    # 2. Fetch Data
    # fetched_data = { "org_id": { "id1": {doc}, "id2": {doc} } }
    fetched_map = {} 
    
    for key, ids in lookup_keys.items():
        collection_name = dependency_map[key]["collection"]
        fetched_map[key] = {}
        
        # Determine strict list of IDs to query
        id_list = list(ids)
        if not id_list:
            continue
            
        cursor = db[collection_name].find({"_id": {"$in": id_list}})
        async for doc in cursor:
            # Convert datetime objects to string if needed or handle by serializer
            # The user output example has { "$date": ... } which suggests raw MongoDB dump or specific serialization.
            # We will keep it as python objects for FastAPI to serialize, OR we can conform to the example strictly if asked.
            # The example output format `_org_id_details` containing `$date` suggests we might return raw dicts
            # usually FastAPI handles datetime -> ISO string. I will stick to returning dicts.
            fetched_map[key][doc["_id"]] = doc

    # 3. Enrich Items
    for item in items:
        for key, config in dependency_map.items():
            val = item.get(key)
            if val and key in fetched_map and val in fetched_map[key]:
                detail_doc = fetched_map[key][val]
                
                # Add _details
                item[f"_{key}_details"] = detail_doc
                
                # Add _name
                name_field = config.get("name_field")
                if name_field and name_field in detail_doc:
                     item[f"_{key}_name"] = detail_doc[name_field]
                else:
                    # Fallback or None? User example implies it should exist.
                    item[f"_{key}_name"] = None

    if is_single:
        return items[0]
    return items
