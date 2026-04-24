import hou                                                                                                                       

node = hou.pwd()                                                                                                                 
geo  = node.geometry()
hda  = node.parent()

selected_tag       = node.evalParm("selected_tag")
selected_variation = node.evalParm("selected_variation")

all_ch_names = []
all_weights  = []
tag_layers   = []  # NEW

for point in geo.points():
  info = point.attribValue("fbuild_agent_info")
  pca  = info.get("pca", {})

  if selected_tag not in pca:
      continue

  for baseshape, bs_data in pca[selected_tag].items():
      if selected_variation in bs_data["variations"]:
          all_ch_names.extend(bs_data["channels"])
          all_weights.extend(bs_data["variations"][selected_variation])

  # NEW — extract layers once from first valid point
  if not tag_layers:
      layers_info = info.get("layers", {})
      tag_layers  = [
          layer_name
          for layer_name, layer_data in layers_info.items()
          if selected_tag in layer_data.get("tag", [])
      ]

geo.addArrayAttrib(hou.attribType.Global, "pca_channel_names",     hou.attribData.String, 1)
geo.addArrayAttrib(hou.attribType.Global, "pca_variation_weights", hou.attribData.Float,  1)
geo.addAttrib(     hou.attribType.Global, "pca_num_channels", 0)
geo.addArrayAttrib(hou.attribType.Global, "pca_tag_layers",        hou.attribData.String, 1)  # NEW

geo.setGlobalAttribValue("pca_channel_names",     all_ch_names)
geo.setGlobalAttribValue("pca_variation_weights", all_weights)
geo.setGlobalAttribValue("pca_num_channels",      len(all_ch_names))
geo.setGlobalAttribValue("pca_tag_layers",        tag_layers)  # NEW
