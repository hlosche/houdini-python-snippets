import hou
import json
from collections import defaultdict

node = hou.pwd()
geo  = node.geometry()  # output — starts empty

project_geo     = node.inputs()[0].geometry()
base_geo        = node.inputs()[1].geometry()
pca_analyse_geo = node.inputs()[2].geometry()

baseshape_label = base_geo.prims()[0].attribValue("name")
baseshape_name   = base_geo.prims()[0].attribValue("path")
tag_name         = base_geo.prims()[0].attribValue("tag")

# --- read Analyse output (evals only — positions stay as geometry) ---
components = pca_analyse_geo.pointIntAttribValues("component")
evals      = pca_analyse_geo.pointFloatAttribValues("eval")

component_evals = {}
for i, comp_idx in enumerate(components):
    component_evals[comp_idx] = evals[i]

# --- 99% variance threshold ---
evals_sorted = sorted(component_evals.items())
total  = sum(val for _, val in evals_sorted)
cumsum = 0
keep_n = 0
for idx, val in evals_sorted:
    cumsum += val
    keep_n += 1
    if cumsum / total >= 0.2:
        break

kept_indices = sorted(component_evals.keys())[:keep_n]

# --- read Project output weights ---
names       = project_geo.pointStringAttribValues("channel_name")
weights_raw = project_geo.pointFloatAttribValues("weight")

variation_weights = defaultdict(list)
for i, name in enumerate(names):
    variation_weights[name].append(weights_raw[i])

# --- build channel names and flat weights ---
pca_channels = [f"pca_{baseshape_label}_{comp_idx}" for comp_idx in kept_indices]
names_list   = list(variation_weights.keys())
weights_flat = []
for name in names_list:
    for comp_idx in kept_indices:
        weights_flat.append(variation_weights[name][comp_idx])

# --- output single lightweight metadata point ---
metadata = {
    "tag":                   tag_name,
    "baseshape":             baseshape_name,
    "pca_channel_names":     pca_channels,
    "pca_variation_names":   names_list,
    "pca_variation_weights": weights_flat,
    "pca_num_channels":      len(pca_channels),
    "kept_indices":          kept_indices
}

pt          = geo.createPoint()
meta_attrib = geo.addAttrib(hou.attribType.Point, "pca_metadata", "")
pt.setAttribValue(meta_attrib, json.dumps(metadata))
