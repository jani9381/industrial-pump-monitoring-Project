import sqlite3
import networkx as nx
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "industrial_monitoring.db"

conn = sqlite3.connect(DB_PATH)

facilities = conn.execute("""
    SELECT facility_id FROM facilities
""").fetchall()

all_passed = True

for (facility_id,) in facilities:

    G = nx.Graph()

    nodes = conn.execute("""
        SELECT node_id
        FROM network_nodes
        WHERE facility_id = ?
    """, (facility_id,)).fetchall()

    pipes = conn.execute("""
        SELECT source_node_id, target_node_id
        FROM pipes
        WHERE facility_id = ?
    """, (facility_id,)).fetchall()

    G.add_nodes_from([node[0] for node in nodes])
    G.add_edges_from(pipes)

    components = list(nx.connected_components(G))

    connected = (
        len(components) == 1
        and len(nodes) > 0
    )

    print(f"\nFacility: {facility_id}")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total pipes: {len(pipes)}")
    print(f"Connected components: {len(components)}")
    print(f"Network connected: {connected}")

    if not connected:
        all_passed = False

print("\nFINAL RESULT:", "PASSED" if all_passed else "FAILED")

conn.close()