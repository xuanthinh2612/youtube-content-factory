def edge(source,target,kind="normal",label=""):
    return {"source":source,"target":target,"kind":kind,"label":label}


def graph_for(niche):
    nodes=[
        {"id":"director","label":"Director","group":"content"},
        {"id":"writer","label":"Writer","group":"content"},
        {"id":"editor","label":"Editor","group":"content"},
        {"id":"export","label":"Export","group":"system"},
        {"id":"completed","label":"Completed","group":"system"},
    ]
    return {"nodes":nodes,"edges":[
        edge("director","writer"),
        edge("writer","editor"),
        edge("editor","export"),
        edge("export","completed"),
    ]}
