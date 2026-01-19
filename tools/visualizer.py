from fastapi import APIRouter
import random

router = APIRouter()

@router.get("/api/memory/graph")
async def get_memory_graph():
    """
    Returns the topology of the user's second brain.
    Currently a simulation, will eventually pull from Vector DB.
    """
    nodes = []
    links = []

    nodes.append({"id": "ENGRAM_CORE", "group": "core", "val": 20, "label": "Engram Core"})

    clusters = ["Project: Specter", "Personal", "Learning", "Email Logs", "Code Snippets"]
    
    for i, cluster in enumerate(clusters):
        hub_id = f"HUB_{i}"
        nodes.append({"id": hub_id, "group": "hub", "val": 10, "label": cluster})
        links.append({"source": "ENGRAM_CORE", "target": hub_id})

        for j in range(random.randint(5, 12)):
            leaf_id = f"NODE_{i}_{j}"
            nodes.append({
                "id": leaf_id, 
                "group": "memory", 
                "val": random.randint(3, 6),
                "label": f"Memory fragment {j}"
            })
            links.append({"source": hub_id, "target": leaf_id})
            
            if random.random() > 0.85:
                random_target = f"HUB_{random.randint(0, len(clusters)-1)}"
                links.append({"source": leaf_id, "target": random_target})

    return {"nodes": nodes, "links": links}