def reduce_graph(spec,history,project_status=None):
    node_status={n["id"]:"idle" for n in spec["nodes"]}
    node_message={}
    taken_edges=set()

    for event in history:
        node=event.get("node")
        typ=event.get("type")
        status=event.get("status")

        if node in node_status:
            if typ in ("node_start",):
                node_status[node]="running"
            elif typ in ("node_success","node_done"):
                node_status[node]="success"
            elif typ=="node_error":
                node_status[node]="failed"
            elif typ=="retry":
                node_status[node]="retrying"
            elif typ=="step" and status in ("running","success","failed","retrying"):
                node_status[node]=status

        if event.get("message") and node:
            node_message[node]=event["message"]

        if typ=="edge_taken":
            taken_edges.add((
                event.get("source"),
                event.get("target"),
                event.get("kind","normal")
            ))

        if typ=="project_completed" and "completed" in node_status:
            node_status["completed"]="success"

        if typ=="project_cancelled":
            # Keep the graph truthful after a force stop instead of leaving the
            # last active agent painted as if it were still running forever.
            for active_node,current_status in tuple(node_status.items()):
                if current_status in ("running","retrying"):
                    node_status[active_node]="cancelled"
                    node_message[active_node]=event.get("message") or "Project force-stopped by user"

    # A normal edge is considered traversed once its target actually ran.
    for ed in spec["edges"]:
        if ed["kind"]=="normal" and node_status.get(ed["target"])!="idle":
            taken_edges.add((ed["source"],ed["target"],ed["kind"]))

    if project_status=="completed" and "completed" in node_status:
        node_status["completed"]="success"

    return {
        "nodes":[{**n,"status":node_status[n["id"]],"message":node_message.get(n["id"],"")}
                 for n in spec["nodes"]],
        "edges":[{**e,"taken":(e["source"],e["target"],e["kind"]) in taken_edges}
                 for e in spec["edges"]],
    }
