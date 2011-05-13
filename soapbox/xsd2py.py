import sys
from jinja2 import Template,Environment
from xsdspec import *
from utils import removens, classyfiy, get_get_type, use, find_xsd_namepsace

    
environment = Environment()
environment.filters["class"] = classyfiy
environment.filters["removens"] = removens
environment.filters["use"] = use


TEMPLATE = """from soapbox import xsd
{# ------------------ SimpleType Generation ---------------------#}
{% for st in schema.simpleTypes %}
    {%- if st.restriction %}
class {{st.name|class}}({{st.restriction.base|type}}):
        {%- if st.restriction.enumerations %}    
    enumeration = [{% for enum in st.restriction.enumerations %} "{{enum.value}}", {% endfor %}]
        {%- elif st.restriction.pattern %}
    pattern = r"{{st.restriction.pattern.value}}"
        {%- endif %}
    {% endif %}

    {%- if st.list %}
class {{st.name|class}}(xsd.List):
    pass
    {%- endif %}
{%- endfor %}
{# ---------------End of SimpleType Generation -----------------#}

{# ------------------------- GROUOPS ----------------------------------------#}
{%- for attrGroup in schema.attributeGroups %}
class {{attrGroup.name|class}}(xsd.AttributeGroup):
    {%- for attribute in attrGroup.attributes %}
    {{attribute.name}} = xsd.Attribute({{attribute.type|type}}{% if attribute.use %}, use={{attribute.use|use}}{% endif %})
    {%- endfor %}
{% endfor %}

{%- for group in schema.groups %}
class {{group.name|class}}(xsd.Group):
    {%- for element in group.sequence.elements %}
        {%- if element.ref %}
    {{element.ref|removens}} = xsd.Element({{element.ref|type}})
        {%- else %}
    {{element.name}} = xsd.Element({{element.type|type}})
        {%- endif %}
    {%- endfor %}
{% endfor %}

{# ---------------------------------------------------------------------------#}

{# -------------------------- ComplexTypes -----------------------------------#}
{% for ct in schema.complexTypes %}
{% set content = ct %}

{%- if not ct.sequence and not ct.complexContent %}
class {{ct.name|class}}(xsd.ComplexType):
{%- endif %}

{%- if ct.complexContent %}
    {%- if ct.complexContent.restriction %}
class {{ct.name|class}}({{ct.complexContent.restriction.base|type}}):
    INHERITANCE = xsd.Inheritance.RESTRICTION
    {%- set content = ct.complexContent.restriction %}
    {%- else %}
class {{ct.name|class}}({{ct.complexContent.extension.base|type}}):
    INHERITANCE = xsd.Inheritance.EXTENSION
    {%- set content = ct.complexContent.extension %}
    {%- endif %}
{%- elif ct.sequence %}
class {{ct.name|class}}(xsd.ComplexType):
    INHERITANCE = None
    {%- set content = ct %}
{%- endif %}

{%- if content.sequence %}
    INDICATOR = xsd.Sequence
    {%- set elements = content.sequence.elements %}
{%- elif content.all %}
    INDICATOR = xsd.All
    {%- set elements = content.all.elements %}
{%- elif content.choice %}
    INDICATOR = xsd.Choice
    {%- set elements = content.choice.elements %}
{%- endif %} 

{%- for attribute in content.attributes %}
    {%- if attribute.ref %}
    {{attribute.ref|removens}} = xsd.Attribute({{attribute.ref|type}})
    {%- else %}
    {{attribute.name}} = xsd.Attribute({{attribute.type|type}}{% if attribute.use %}, use={{attribute.use|use}}{% endif %})
    {%- endif %} 
{%- endfor %}

{%- for attrGroupRef in content.attributeGroups %}
    {{attrGroupRef.ref|removens}} = xsd.Ref({{attrGroupRef.ref|type}})
{%- endfor %}

{%- for element in elements %}
    {%- if element.type %}
    {{element.name}} = xsd.Element({{element.type|type}}{% if element.minOccurs == 0 %}, minOccurs=0{% endif %})
    {%- endif %}
    {%- if element.simpleType %}
    {{element.name}} = xsd.Element({{element.simpleType.restriction.base|type}}( enumeration = 
    [{% for enum in element.simpleType.restriction.enumerations %} "{{enum.value}}",{% endfor %}]) )
    {%- endif %}
    {%- if element.ref %}
    {{element.ref|removens}} = xsd.Ref({{element.ref|type}})
    {%- endif %}
{%- endfor %}
{% endfor %}
{# ------------------------ End of ComplexTypes -------------------------------#}

Schema = xsd.Schema(
    targetNamespace = "{{schema.targetNamespace}}",
    elementFormDefault = "{{schema.elementFormDefault}}",
    simpleTypes = [{% for st in schema.simpleTypes %} {{st.name|class}},{% endfor %}],
    attributeGroups = [{% for ag in schema.attributeGroups %} {{ag.name|class}},{% endfor %}],
    groups = [{% for g in schema.groups %} {{g.name|class}},{% endfor %}],
    complexTypes = [{% for ct in schema.complexTypes %} {{ct.name|class}},{% endfor %}],
    elements = { {% for e in schema.elements %} "{{e.name}}":xsd.Element({{e.type|type}}),{% endfor %}})
"""
        
XSD_NAMESPACE = None
    
if __name__ == "__main__":
    xml = open(sys.argv[1]).read()
    xmlelement = etree.fromstring(xml)
    XSD_NAMESPACE = find_xsd_namepsace(xmlelement.nsmap)
    environment.filters["type"] = get_get_type(XSD_NAMESPACE)
    schema = Schema.parse_xmlelement(etree.fromstring(xml))
    print environment.from_string(TEMPLATE).render(schema=schema)