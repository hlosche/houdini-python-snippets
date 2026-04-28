import hou
import random

node = hou.pwd()
geo  = node.geometry()
hda  = node.parent()

selected_tags      = node.evalParm("selected_tag").split()
selected_variation = node.evalParm("selected_variation")

geo.addArrayAttrib(hou.attribType.Point, "pca_channel_names",     hou.attribData.String, 1)
geo.addArrayAttrib(hou.attribType.Point, "pca_variation_weights", hou.attribData.Float,  1)
geo.addArrayAttrib(hou.attribType.Point, "pca_tag_layers",        hou.attribData.String, 1)

for point in geo.points():
    info = point.attribValue("fbuild_agent_info")
    pca  = info.get("pca", {})

    available_tags = [t for t in selected_tags if t in pca]
    if not available_tags:
        continue

    if len(available_tags) > 1:
        random.seed(point.number())
        chosen_tag = random.choice(available_tags)

        variations = set()
        for bs_data in pca[chosen_tag].values():
            variations.update(bs_data["variations"].keys())

        if not variations:
            continue

        chosen_variation = random.choice(sorted(variations))

        ch_names = []
        weights  = []
        for bs_data in pca[chosen_tag].values():
            if chosen_variation in bs_data["variations"]:
                ch_names.extend(bs_data["channels"])
                weights.extend(bs_data["variations"][chosen_variation])

        layers_info = info.get("layers", {})
        tag_layers  = [
            layer_name
            for layer_name, layer_data in layers_info.items()
            if chosen_tag in layer_data.get("tag", [])
        ]

    else:
        chosen_tag = available_tags[0]
        ch_names   = []
        weights    = []
        tag_layers = []

        for bs_data in pca[chosen_tag].values():
            if selected_variation in bs_data["variations"]:
                ch_names.extend(bs_data["channels"])
                weights.extend(bs_data["variations"][selected_variation])

        layers_info = info.get("layers", {})
        tag_layers  = [
            layer_name
            for layer_name, layer_data in layers_info.items()
            if chosen_tag in layer_data.get("tag", [])
        ]

    point.setAttribValue("pca_channel_names",     ch_names)
    point.setAttribValue("pca_variation_weights", weights)
    point.setAttribValue("pca_tag_layers",        tag_layers)
