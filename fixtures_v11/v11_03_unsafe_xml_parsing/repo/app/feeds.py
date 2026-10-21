import xml.etree.ElementTree as ET

def parse_feed(raw):
    return ET.fromstring(raw)
