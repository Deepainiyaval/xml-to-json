from flask import Flask, request, jsonify
import xml.etree.ElementTree as ET
from datetime import datetime
import random

app = Flask(__name__)

# -------------------------------
# CONFIG
# -------------------------------

CANVAS = {
    "width": 1200,
    "heightPx": 920.55,
    "minHeightPx": 920.55,
    "styles": {
        "backgroundColor": "",
        "backgroundMode": "color",
        "backgroundImageUrl": "",
        "backgroundSize": "cover",
        "backgroundPosition": "center center",
        "backgroundRepeat": "no-repeat",
        "gradientType": "linear",
        "gradientAngle": 90,
        "gradientStartColor": "#2196F3",
        "gradientEndColor": "#4CAF50",
        "width": "",
        "height": "",
        "borderRadius": 0
    }
}

# -------------------------------
# HELPERS
# -------------------------------

def generate_id():
    return f"w-{int(datetime.utcnow().timestamp() * 1000)}-{random.randint(100,999)}"

def base_style():
    return {
        "style": {
            "backgroundMode": "transparent",
            "backgroundColor": "transparent"
        }
    }

def default_position(index):
    """
    Simple vertical stacking (you said positioning later)
    """
    return {
        "x": 0.05 if index % 2 == 0 else 0.3,
        "y": 0.05 + (index * 0.15),
        "w": 0.25,
        "h": 0.12,
        "zIndex": index + 1
    }

# -------------------------------
# COMPONENT BUILDERS
# -------------------------------

def create_component(tag, element, index, parent_id):
    tag = tag.lower()

    mapping = {
        # MDE
        "textview": ("Label", "label", "app-label"),
        "inputfield": ("Input", "input-text", "app-input-text"),
        "textedit": ("Text area", "text-area", "app-text-area"),
        "dropdownlist": ("Dropdown", "dropdown", "app-dropdown"),
        "range": ("Range", "range", "app-range"),
        "invisibleelement": ("Invisible", "invisible", "app-invisible"),

        # REPORT
        "rlabel": ("Label", "label", "app-label"),
        "rinputfield": ("Input", "input-text", "app-input-text"),
        "rtransparentcontainer": None,  # skip container
        "rgroupbox": None,
        "rinvisibleelement": None,
        "rlink": ("Link", "link", "app-link"),
        "rline": ("Line", "line", "app-line"),
        "rlist": ("List", "list", "app-list"),
        "rchart": ("Chart", "chart", "app-chart")
    }

    if tag not in mapping:
        return None

    if mapping[tag] is None:
        return None  # skip container

    label, comp_type, selector = mapping[tag]

    return {
        "id": generate_id(),
        "label": label,
        "type": comp_type,
        "selector": selector,
        "position": default_position(index),
        "input": base_style(),
        "parentId": parent_id
    }

# -------------------------------
# CORE FLATTEN LOGIC
# -------------------------------

def extract_components(xml_node, parent_id):
    components = []
    index = 0

    for elem in xml_node:
        tag = elem.tag.split('}')[-1]  # remove namespace if exists

        comp = create_component(tag, elem, index, parent_id)

        if comp:
            components.append(comp)
            index += 1

        # 🔥 IMPORTANT: always go deeper (flatten)
        components.extend(extract_components(elem, parent_id))

    return components

# -------------------------------
# ROUTE
# -------------------------------

@app.route('/upload-xml', methods=['POST'])
def upload_xml():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Empty file"}), 400

    try:
        tree = ET.parse(file)
        root = tree.getroot()

        root_id = generate_id()

        root_section = {
            "id": root_id,
            "label": "Section",
            "type": "section",
            "selector": "app-designer-section-container",
            "position": {
                "x": 0.085,
                "y": 0.047,
                "w": 0.68,
                "h": 0.42,
                "zIndex": 1
            },
            "input": base_style(),
            "children": []
        }

        # 🔥 FLATTENED COMPONENTS
        components = extract_components(root, root_id)
        root_section["children"] = components

        response = {
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "canvas": CANVAS,
            "widgets": [root_section]
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# RUN
# -------------------------------

if __name__ == '__main__':
    app.run(debug=True)