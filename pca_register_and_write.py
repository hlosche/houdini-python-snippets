import hou                                                                                   
import json                                                                                  
from collections import defaultdict                                                          
                                                                                           
node = hou.pwd()                                                                             
geo  = node.geometry()  # agent prim                                                         
              
combined_geo = node.inputs()[1].geometry()

# --- agent setup ---
definition    = hou.crowds.findAgentDefinitions(geo)[0]
definitionNew = definition.freeze()
shape_lib     = definitionNew.shapeLibrary().freeze()
rig           = definitionNew.rig().freeze()

new_shape_lib = hou.AgentShapeLibrary()
shape_map = {}
for shape in shape_lib.shapes():
  shape_map[shape.name()] = new_shape_lib.addShape(shape.name(), shape.geometry())

# --- separate metadata points from component geometry points ---
meta_vals      = combined_geo.pointStringAttribValues("pca_metadata")
bs_vals        = combined_geo.pointStringAttribValues("blendshape_baseshape")
components_arr = combined_geo.pointIntAttribValues("component")
positions_arr  = combined_geo.pointFloatAttribValues("P")

metadata_by_baseshape = {}
comp_pts_by_baseshape = defaultdict(lambda: defaultdict(list))

for i, meta_str in enumerate(meta_vals):
  if meta_str:  # metadata point
      meta = json.loads(meta_str)
      metadata_by_baseshape[meta["baseshape"]] = meta
  else:  # component geometry point
      comp_pts_by_baseshape[bs_vals[i]][components_arr[i]].append(
          [positions_arr[i*3], positions_arr[i*3+1], positions_arr[i*3+2]]
      )

pca_fbuild       = {}  # tag -> baseshape -> data
baseshape_inputs = {}  # baseshape -> {"shapes": [], "channels": []}

for baseshape_name, meta in metadata_by_baseshape.items():
  tag_name     = meta["tag"]
  kept_indices = meta["kept_indices"]
  pca_channels = meta["pca_channel_names"]
  names_list   = meta["pca_variation_names"]
  weights_flat = meta["pca_variation_weights"]
  num_channels = meta["pca_num_channels"]

  pca_shapes = []
  for j, comp_idx in enumerate(kept_indices):
      pts_list = comp_pts_by_baseshape[baseshape_name][comp_idx]
      comp_geo = hou.Geometry()
      for pos in pts_list:
          pt = comp_geo.createPoint()
          pt.setPosition(hou.Vector3(pos[0], pos[1], pos[2]))
      comp_name = f"{baseshape_name}/pca_component_{j}"
      pca_shapes.append(new_shape_lib.addShape(comp_name, comp_geo))

  for ch in pca_channels:
      rig.addChannel(ch, default_value=0.0)

  if baseshape_name not in baseshape_inputs:
      baseshape_inputs[baseshape_name] = {"shapes": [], "channels": []}
  baseshape_inputs[baseshape_name]["shapes"].extend(pca_shapes)
  baseshape_inputs[baseshape_name]["channels"].extend(pca_channels)

  variation_weights = {}
  for vi, var_name in enumerate(names_list):
      offset = vi * num_channels
      variation_weights[var_name] = weights_flat[offset:offset + num_channels]

  if tag_name not in pca_fbuild:
      pca_fbuild[tag_name] = {}
  pca_fbuild[tag_name][baseshape_name] = {
      "channels":   pca_channels,
      "variations": variation_weights
  }

# --- wire blendshape inputs once per baseshape ---
for baseshape_name, inputs_data in baseshape_inputs.items():
  base_ref = shape_map.get(baseshape_name)
  if base_ref:
      base_ref.addBlendshapeInputs(inputs_data["shapes"], inputs_data["channels"])
      base_ref.setBlendshapeDeformerParms(attribs="P", point_id_attrib="id")

# --- store in fbuild_agent_info ---
for point in geo.points():
  info = dict(point.attribValue("fbuild_agent_info"))
  info["pca"] = pca_fbuild
  point.setAttribValue("fbuild_agent_info", info)

# --- publish ---
definitionNew = definitionNew.freeze(new_shapelib=new_shape_lib, new_rig=rig)
hou.crowds.replaceAgentDefinitions(geo, {definition: definitionNew})
