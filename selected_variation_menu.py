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

selected_tag = node.evalParm("selected_tag")
pca          = info.get("pca", {})
if selected_tag not in pca:
    return []

variations = set()
for bs_data in pca[selected_tag].values():
    variations.update(bs_data["variations"].keys())
return crowdstoolutils.buildMenuStringList(sorted(variations))
