import crowdstoolutils

node   = kwargs["node"]
inputs = node.inputs()
if not inputs or inputs[0] is None:
    return []

geo = inputs[0].geometry()
if not geo or not geo.points():
    return []

info = geo.points()[0].attribValue("fbuild_agent_info")
if not info:
    return []

selected_tags = node.evalParm("selected_tag").split()
pca           = info.get("pca", {})

variations = set()
for selected_tag in selected_tags:
    if selected_tag not in pca:
        continue
    for bs_data in pca[selected_tag].values():
        variations.update(bs_data["variations"].keys())

return crowdstoolutils.buildMenuStringList(sorted(variations))
