from core.network_gateway import gateway

def scan_database():
    print("Starting Deep Scan of Qdrant Database...\n")
    

    try:
        col_res = gateway.get("qdrant_admin", "/collections", timeout=(5, 10))
        collections = col_res.json().get("result", {}).get("collections", [])
    except Exception as e:
        print(f"Connection Failed: {e}")
        print("(Check if Docker is running and Port 6334 is mapped)")
        return

    if not collections:
        print("No collections found! Database is empty.")
        return

    print(f"Found {len(collections)} Collections: {[c['name'] for c in collections]}")

    
    for col in collections:
        name = col['name']
        print(f"Inspecting Collection: '{name}'")
        
        
        res = gateway.post("qdrant_admin", f"/collections/{name}/points/scroll", json={"limit": 10, "with_payload": True}, timeout=(5, 10))
        
        if res.status_code == 200:
            points = res.json().get("result", {}).get("points", [])
            if not points:
                print("      [Empty]")
            else:
                for p in points:
                    
                    payload = p.get("payload", {})
                    
                    content = payload.get("data") or payload.get("text") or payload.get("memory")
                    print(f"Found: {content}")
                    
                    if "Friday" in str(content) or "deadline" in str(content):
                        print("MATCH FOUND HERE!")
        else:
            print(f"Error reading collection: {res.status_code}")

if __name__ == "__main__":
    scan_database()