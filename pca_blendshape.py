import numpy as np
from collections import defaultdict                                                                  
import hou      

node = hou.pwd()
geo  = node.geometry()
hda  = node.parent()

# --- agent definition setup ---
definition    = hou.crowds.findAgentDefinitions(geo)[0]
definitionNew = definition.freeze()
shape_lib     = definitionNew.shapeLibrary().freeze()
rig           = definitionNew.rig().freeze()

new_shape_lib = hou.AgentShapeLibrary()
shape_map     = {}
for shape in shape_lib.shapes():
  shape_map[shape.name()] = new_shape_lib.addShape(shape.name(), shape.geometry())

# --- read merged delta geometry ---
delta_geo      = node.inputs()[1].geometry()
tags_arr       = delta_geo.pointStringAttribValues("tag")
channels_arr   = delta_geo.pointStringAttribValues("channel_name")
baseshapes_arr = delta_geo.pointStringAttribValues("blendshape_baseshape")
positions_arr  = delta_geo.pointFloatAttribValues("P")

# group: delta_groups[tag][baseshape][channel_name] = [[dx,dy,dz], ...]
delta_groups = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for i in range(len(tags_arr)):
  delta_groups[tags_arr[i]][baseshapes_arr[i]][channels_arr[i]].append(
      [positions_arr[i*3], positions_arr[i*3+1], positions_arr[i*3+2]]
  )

# accumulate blendshape inputs per baseshape
# (multiple tags may share the same baseshape)
baseshape_inputs = defaultdict(lambda: {"shapes": [], "channels": []})

# pca results for fbuild_agent_info
pca_data = {}

# --- run PCA per (tag, baseshape) ---
for tag, baseshape_dict in delta_groups.items():
  pca_data[tag] = {}

  for baseshape, variation_dict in baseshape_dict.items():
      variation_names = sorted(variation_dict.keys())
      n_variations    = len(variation_names)
      n_points        = len(variation_dict[variation_names[0]])

      # build delta matrix: (n_variations, n_points * 3)
      X = np.zeros((n_variations, n_points * 3))
      for i, var_name in enumerate(variation_names):
          X[i] = np.array(variation_dict[var_name]).flatten()

      # SVD — same as what Houdini PCA SOP does internally
      U, S, Vt = np.linalg.svd(X, full_matrices=False)
      keep_n = min(n_variations, len(S))

      # base points from shape library
      base_ref = shape_map.get(baseshape)
      if not base_ref:
          raise hou.Error(f"Base shape '{baseshape}' not found in shape library")
      base_pts = np.array(base_ref.geometry().pointFloatAttribValues("P")).reshape(-1, 3)

      element_name = baseshape.split("/")[-1]
      tag_clean    = tag.replace(" ", "_")

      pca_shapes   = []
      pca_channels = []

      for j in range(keep_n):
          # component direction (unit vector in shape space)
          comp_delta = Vt[j].reshape(n_points, 3)
          comp_pts   = base_pts + comp_delta

          comp_geo = hou.Geometry()
          comp_geo = hou.Geometry()
          comp_geo.createPoints([                                                                              
              hou.Vector3(float(comp_pts[k, 0]), float(comp_pts[k, 1]), float(comp_pts[k, 2]))
              for k in range(n_points)
          ])

          comp_name    = f"{element_name}_{tag_clean}/pca_component_{j}"
          channel_name = f"{element_name}_{tag_clean}_pca_{j}"

          pca_shapes.append(new_shape_lib.addShape(comp_name, comp_geo))
          pca_channels.append(channel_name)

      for ch in pca_channels:
          rig.addChannel(ch, default_value=0.0)

      # accumulate — don't call addBlendshapeInputs yet
      baseshape_inputs[baseshape]["shapes"].extend(pca_shapes)
      baseshape_inputs[baseshape]["channels"].extend(pca_channels)

      # weights: U[i,j] * S[j] reconstructs variation i from component j
      variation_weights = {}
      for i, var_name in enumerate(variation_names):
          variation_weights[var_name] = [float(U[i, j] * S[j]) for j in range(keep_n)]

      pca_data[tag][baseshape] = {
          "channels":   pca_channels,
          "variations": variation_weights
      }

# --- wire blendshape inputs once per baseshape ---
for baseshape, inputs in baseshape_inputs.items():
  base_ref = shape_map.get(baseshape)
  base_ref.addBlendshapeInputs(inputs["shapes"], inputs["channels"])
  base_ref.setBlendshapeDeformerParms(attribs="P", point_id_attrib="id")

# --- store PCA data in fbuild_agent_info per agent point ---
for point in geo.points():
  info = dict(point.attribValue("fbuild_agent_info"))
  info["pca"] = pca_data
  point.setAttribValue("fbuild_agent_info", info)

# --- publish ---
definitionNew = definitionNew.freeze(new_shapelib=new_shape_lib, new_rig=rig)
hou.crowds.replaceAgentDefinitions(geo, {definition: definitionNew})
