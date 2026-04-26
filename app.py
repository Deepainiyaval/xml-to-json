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

#  STYLE HELPER
def apply_style(component, attributes, mapping):
    style = component["input"]["style"]

    for xml_key, json_key in mapping.items():
        value = attributes.get(xml_key)
        if value is not None:
            style[json_key] = value

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
        "transparentcontainer": ("Container", "container", "app-container"),
        "groupbox": ("GroupBox", "group", "app-group"),
        "uiterator": ("Iterator", "iterator", "app-iterator"),
        "iteratortc": ("IteratorContainer", "iterator-container", "app-iterator-container"),
        "rtransparentcontainer": ("Container", "container", "app-container"),
        "rgroupbox": ("GroupBox", "group", "app-group"),
        "rinvisibleelement": ("Invisible", "invisible", "app-invisible")
    }

    if tag not in mapping :
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
        component["text"] = attributes.get("text")

        apply_style(component, attributes, {
            "colSpan": "colSpan",
            "design": "design",
            "hAlign": "hAlign",
            "textalign": "hAlign",
            "semanticColor": "color",
            "color": "color",
            "fontsize": "fontSize",
            "fontweight": "fontWeight"
        })

    # INPUTFIELD / RINPUTFIELD
    elif tag in ["inputfield", "rinputfield"]:
        component.update({
            "tagName": attributes.get("tagName"),
            "frequency": attributes.get("frequency"),
            "decPlaces": to_int(attributes.get("decPlaces"), 0),
            "readOnly": to_bool(attributes.get("readOnly")),
            "displayIfNull": attributes.get("displayIfNull"),
            "valueSpan": to_int(attributes.get("valueSpan"), 1),
            "spanType": attributes.get("spanType"),
            "offset": attributes.get("offset"),
            "operFacl": attributes.get("operFacl")
        })

        apply_style(component, attributes, {
            "colSpan": "colSpan",
            "textalign": "textAlign",
            "fontsize": "fontSize",
            "fontweight": "fontWeight",
            "color": "color",
            "bgcolor": "backgroundColor"
        })

    # DROPDOWN
    elif tag == "dropdownlist":
        component.update({
            "tagName": attributes.get("tagName"),
            "valuesList": attributes.get("valuesList"),
            "frequency": attributes.get("frequency"),
            "readOnly": to_bool(attributes.get("readOnly"))
        })

        apply_style(component, attributes, {
            "colSpan": "colSpan"
        })

    # TEXTEDIT
    elif tag == "textedit":
        component.update({
            "rows": to_int(attributes.get("rows")),
            "cols": to_int(attributes.get("cols")),
            "tagName": attributes.get("tagName"),
            "frequency": attributes.get("frequency")
        })

        apply_style(component, attributes, {
            "colSpan": "colSpan"
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
            "text": attributes.get("text")
        })

        apply_style(component, attributes, {
            "color": "color",
            "font-size": "fontSize",
            "text-align": "textAlign"
        })

    # LINE
    elif tag == "rline":
        apply_style(component, attributes, {
            "color": "color"
        })

        component.update({
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
    if tag in [
        "transparentcontainer",
        "groupbox",
        "uiterator",
        "iteratortc",
        "rtransparentcontainer",
        "rgroupbox"
    ]:
        apply_style(component, attributes, {
            "colSpan": "colSpan",
            "colCount": "colCount",
            "width": "width",
            "height": "height",
            "layout": "layout",
            "cellPadding": "cellPadding",
            "cellSpacing": "cellSpacing",
            "design": "design",
            "header": "header",
            "hasContentPadding": "hasContentPadding"
        })
            

        component["rawAttributes"] = attributes   

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
            comp_id = comp["id"]

            # Recursively get children
            children = extract_components(elem, comp_id)

            if children:
                comp["children"] = children

            components.append(comp)
            index += 1

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