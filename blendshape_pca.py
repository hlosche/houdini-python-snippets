from collections import defaultdict

node = hou.pwd()                                                                                    
geo  = node.geometry()                                                                              
                                                                                              
definition    = hou.crowds.findAgentDefinitions(geo)[0]                                             
definitionNew = definition.freeze()                                                                 
          
shape_lib = definitionNew.shapeLibrary().freeze()
rig       = definitionNew.rig().freeze()

new_shape_lib = hou.AgentShapeLibrary()
shape_map = {}
for shape in shape_lib.shapes():
    shape_map[shape.name()] = new_shape_lib.addShape(shape.name(), shape.geometry())

variation_geo   = node.inputs()[1].geometry()
pca_analyse_geo = node.inputs()[2].geometry()
pca_project_geo = node.inputs()[3].geometry()


selected_layer_name = node.parent().evalParm("layername")
layer = next((l for l in definitionNew.layers() if l.name() == selected_layer_name), None)
if layer is None:
    raise hou.Error(f"Layer'{selected_layer_name}' not found")
    
baseshape        = node.parent().evalParm("baseshape_attrib")
baseshape_name   = variation_geo.prim(0).attribValue(baseshape)    
    
base_points = None
for binding in layer.bindings():
    if binding.shape().name() == baseshape_name:
        base_points = binding.shape().geometry().pointFloatAttribValues("P")
        break

if base_points is None:
    raise hou.Error(f"Shape '{baseshape_name}' not found in layer'{selected_layer_name}'")
        
components  = pca_analyse_geo.pointIntAttribValues("component")
evals       = pca_analyse_geo.pointFloatAttribValues("eval")
positions   = pca_analyse_geo.pointFloatAttribValues("P")


component_points = defaultdict(list)
component_evals  = {}

for i, comp_idx in enumerate(components):
    pos = hou.Vector3(positions[i*3], positions[i*3+1], positions[i*3+2])
    component_points[comp_idx].append(pos)
    component_evals[comp_idx] = evals[i]

    
variance_threshold = node.parent().parm("variance_threshold") 

# --- 95% variance threshold ---
evals_sorted = [(idx, val) for idx, val in sorted(component_evals.items())]
total        = sum(val for _, val in evals_sorted)
cumsum       = 0
keep_n       = 0
for idx, val in evals_sorted:
  cumsum += val
  keep_n += 1
  if cumsum / total >= variance_threshold.eval():
      break
      
# --- register PCA components as shapes ---
pca_shapes   = []
pca_channels = []
kept_indices = sorted(component_points.keys())[:keep_n]

for comp_idx in kept_indices:
    comp_geo = hou.Geometry()
    for j, pos in enumerate(component_points[comp_idx]):
        base_pos = hou.Vector3(base_points[j*3], base_points[j*3+1], base_points[j*3+2])
        pt = comp_geo.createPoint()
        pt.setPosition(base_pos + pos)

    comp_name = f"element/pca_component_{comp_idx}"
    pca_shapes.append(new_shape_lib.addShape(comp_name, comp_geo))
    pca_channels.append(f"pca_{comp_idx}")

# --- build variation -> weights lookup from all projected bodies
names   = pca_project_geo.pointStringAttribValues("name")
weights = pca_project_geo.pointFloatAttribValues("weight")


variation_weights = defaultdict(list)
for i, name in enumerate(names):
    variation_weights[name].append(weights[i])
        
# register PCA channel with neutral default
for i, channel in enumerate(pca_channels):
    rig.addChannel(channel, default_value=0.0)


# -- wire PCA component as blendshape targets ---
base_shape = shape_map.get(baseshape_name)
if base_shape:
    base_shape.addBlendshapeInputs(pca_shapes, pca_channels)
    base_shape.setBlendshapeDeformerParms(attribs="P", point_id_attrib="id")

# --- store lookup as Vex flat arrays --
names_list = list(variation_weights.keys())
weights_flat = []
for name in names_list:
    for comp_idx in kept_indices:
        weights_flat.append(variation_weights[name][comp_idx])
    
num_channels = len(pca_channels)

geo.addArrayAttrib(hou.attribType.Global, "pca_variation_names", hou.attribData.String, 1)
geo.addArrayAttrib(hou.attribType.Global, "pca_variation_weights", hou.attribData.Float, 1)
geo.addArrayAttrib(hou.attribType.Global, "pca_channel_names", hou.attribData.String, 1)
geo.addAttrib(hou.attribType.Global, "pca_num_channels", 0)

geo.setGlobalAttribValue("pca_variation_names", names_list)
geo.setGlobalAttribValue("pca_variation_weights", weights_flat)
geo.setGlobalAttribValue("pca_channel_names", pca_channels)
geo.setGlobalAttribValue("pca_num_channels", num_channels)



definitionNew = definitionNew.freeze(new_shapelib=new_shape_lib, new_rig=rig)
hou.crowds.replaceAgentDefinitions(geo, {definition: definitionNew})
    






    
