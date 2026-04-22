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
    return {
        "x": 0.05 if index % 2 == 0 else 0.3,
        "y": 0.05 + (index * 0.15),
        "w": 0.25,
        "h": 0.12,
        "zIndex": index + 1
    }

def to_int(value, default=0):
    try:
        return int(value)
    except:
        return default

def to_bool(value):
    return str(value).lower() == "true"

# -------------------------------
# COMPONENT BUILDERS
# -------------------------------

def create_component(tag, element, index, parent_id):
    tag = tag.lower()
    attributes = element.attrib

    mapping = {
        "textview": ("Label", "label", "app-label"),
        "inputfield": ("Input", "input-text", "app-input-text"),
        "textedit": ("Text area", "text-area", "app-text-area"),
        "dropdownlist": ("Dropdown", "dropdown", "app-dropdown"),
        "range": ("Range", "range", "app-range"),
        "invisibleelement": ("Invisible", "invisible", "app-invisible"),

        # REPORT
        "rlabel": ("Label", "label", "app-label"),
        "rinputfield": ("Input", "input-text", "app-input-text"),
        "rlink": ("Link", "link", "app-link"),
        "rline": ("Line", "line", "app-line"),
        "rlist": ("List", "list", "app-list"),
        "rchart": ("Chart", "chart", "app-chart"),

        # Containers 
        "transparentcontainer": None,
        "groupbox": None,
        "uiterator": None,
        "iteratortc": None,
        "rtransparentcontainer": None,
        "rgroupbox": None,
        "rinvisibleelement": None
    }

    if tag not in mapping or mapping[tag] is None:
        return None

    label, comp_type, selector = mapping[tag]

    component = {
        "id": generate_id(),
        "label": label,
        "type": comp_type,
        "selector": selector,
        "position": default_position(index),
        "input": base_style(),
        "parentId": parent_id
    }

    # -------------------------------
    # APPLY RULES
    # -------------------------------

    # TEXTVIEW / RLABEL
    if tag in ["textview", "rlabel"]:
        component.update({
            "text": attributes.get("text"),
            "colSpan": to_int(attributes.get("colSpan"), 1),
            "design": attributes.get("design"),
            "hAlign": attributes.get("hAlign") or attributes.get("textalign"),
            "color": attributes.get("semanticColor") or attributes.get("color"),
            "fontSize": attributes.get("fontsize"),
            "fontWeight": attributes.get("fontweight")
        })

    # INPUTFIELD / RINPUTFIELD
    elif tag in ["inputfield", "rinputfield"]:
        component.update({
            "tagName": attributes.get("tagName"),
            "frequency": attributes.get("frequency"),
            "decPlaces": to_int(attributes.get("decPlaces"), 0),
            "readOnly": to_bool(attributes.get("readOnly")),
            "colSpan": to_int(attributes.get("colSpan"), 1),
            "displayIfNull": attributes.get("displayIfNull"),
            "valueSpan": to_int(attributes.get("valueSpan"), 1),
            "spanType": attributes.get("spanType"),
            "offset": attributes.get("offset"),
            "operFacl": attributes.get("operFacl"),
            "textAlign": attributes.get("textalign")
        })

    # DROPDOWN
    elif tag == "dropdownlist":
        component.update({
            "tagName": attributes.get("tagName"),
            "valuesList": attributes.get("valuesList"),
            "frequency": attributes.get("frequency"),
            "colSpan": to_int(attributes.get("colSpan"), 1),
            "readOnly": to_bool(attributes.get("readOnly"))
        })

    # TEXTEDIT
    elif tag == "textedit":
        component.update({
            "rows": to_int(attributes.get("rows")),
            "cols": to_int(attributes.get("cols")),
            "tagName": attributes.get("tagName"),
            "frequency": attributes.get("frequency"),
            "colSpan": to_int(attributes.get("colSpan"), 1)
        })

    # RANGE
    elif tag == "range":
        component.update({
            "label": attributes.get("label"),
            "frequency": attributes.get("frequency"),
            "convFact": attributes.get("convFact"),
            "enabledAfter": attributes.get("enabledAfter"),
            "tagName": attributes.get("tagName")
        })

    # LINK
    elif tag == "rlink":
        component.update({
            "url": attributes.get("url"),
            "text": attributes.get("text"),
            "color": attributes.get("color"),
            "fontSize": attributes.get("font-size"),
            "textAlign": attributes.get("text-align")
        })

    # LINE
    elif tag == "rline":
        component.update({
            "color": attributes.get("color"),
            "pattern": attributes.get("leader-pattern"),
            "length": attributes.get("leader-length"),
            "thickness": attributes.get("rule-thickness")
        })

    # LIST
    elif tag == "rlist":
        items = []
        for item in element.findall("item"):
            label = item.find("label")
            body = item.find("body")

            items.append({
                "label": label.text if label is not None else "",
                "body": body.text if body is not None else ""
            })

        component["items"] = items

    return component

# -------------------------------
# RECURSION
# -------------------------------

def extract_components(xml_node, parent_id):
    components = []
    index = 0

    for elem in xml_node:
        tag = elem.tag.split('}')[-1]

        comp = create_component(tag, elem, index, parent_id)

        if comp:
            components.append(comp)
            index += 1

        # recursion
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