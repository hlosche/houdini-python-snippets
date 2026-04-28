import crowdstoolutils

node = kwargs["node"]
inputs = node.inputs()
if not inputs or inputs[0] is None:
  return []

geo = inputs[0].geometry()
if not geo or not geo.points():
  return []

info = geo.points()[0].attribValue("fbuild_agent_info")
if not info:
  return []

pca  = info.get("pca", {})
tags = sorted(pca.keys())
return crowdstoolutils.buildMenuStringList(tags)
