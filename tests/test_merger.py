import pytest
import xml.etree.ElementTree as ET
from pathlib import Path

from eolib_ext.merger import merge_protocol_file, load_base_elements, MergeError

FIXTURES = Path(__file__).parent / "fixtures"
BASE_FILES = [FIXTURES / "base" / "protocol.xml"]


def fresh_base() -> list[ET.Element]:
    return load_base_elements(BASE_FILES)


def element_ids(elements: list[ET.Element], tag: str) -> list[str]:
    out = []
    for el in elements:
        if el.tag != tag:
            continue
        if tag == "packet":
            out.append(f"{el.get('family')}::{el.get('action')}")
        else:
            out.append(el.get("name", ""))
    return out


def find_enum(elements: list[ET.Element], name: str) -> ET.Element | None:
    for el in elements:
        if el.tag == "enum" and el.get("name") == name:
            return el
    return None


def find_struct(elements: list[ET.Element], name: str) -> ET.Element | None:
    for el in elements:
        if el.tag == "struct" and el.get("name") == name:
            return el
    return None


def find_packet(elements: list[ET.Element], family: str, action: str) -> ET.Element | None:
    for el in elements:
        if el.tag == "packet" and el.get("family") == family and el.get("action") == action:
            return el
    return None


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

class TestNew:
    def test_adds_new_enum(self):
        elements = fresh_base()
        result = merge_protocol_file(elements, FIXTURES / "ext_new" / "protocol.xml", "ext_new")
        assert "Rarity" in element_ids(elements, "enum")
        assert result.new_count == 1
        assert result.append_count == 0
        assert result.replace_count == 0

    def test_does_not_alter_existing(self):
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_new" / "protocol.xml", "ext_new")
        pf = find_enum(elements, "PacketFamily")
        assert pf is not None
        values = [v.get("name") for v in pf if v.tag == "value"]
        assert "Rarity" not in values  # Rarity is a separate enum, not a value


class TestAppend:
    def test_appends_enum_value(self):
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_append" / "protocol.xml", "ext_append")
        pf = find_enum(elements, "PacketFamily")
        values = [v.get("name") for v in pf if v.tag == "value"]
        assert "Custom" in values

    def test_appends_packet_field(self):
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_append" / "protocol.xml", "ext_append")
        pkt = find_packet(elements, "Walk", "Player")
        fields = [f.get("name") for f in pkt if f.tag == "field"]
        assert "custom_data" in fields

    def test_result_counts(self):
        elements = fresh_base()
        result = merge_protocol_file(elements, FIXTURES / "ext_append" / "protocol.xml", "ext_append")
        assert result.append_count == 2
        assert result.new_count == 0
        assert result.replace_count == 0

    def test_does_not_duplicate_existing_values(self):
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_append" / "protocol.xml", "ext_append")
        pf = find_enum(elements, "PacketFamily")
        values = [v.get("name") for v in pf if v.tag == "value"]
        assert values.count("Connection") == 1


class TestReplace:
    def test_replaces_struct(self):
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_replace" / "protocol.xml", "ext_replace")
        coords = find_struct(elements, "Coords")
        fields = {f.get("name"): f.get("type") for f in coords if f.tag == "field"}
        assert fields == {"x": "short", "y": "short", "layer": "char"}

    def test_only_one_coords_after_replace(self):
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_replace" / "protocol.xml", "ext_replace")
        structs = [el for el in elements if el.tag == "struct" and el.get("name") == "Coords"]
        assert len(structs) == 1

    def test_result_counts(self):
        elements = fresh_base()
        result = merge_protocol_file(elements, FIXTURES / "ext_replace" / "protocol.xml", "ext_replace")
        assert result.replace_count == 1
        assert result.new_count == 0
        assert result.append_count == 0


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestConflicts:
    def test_new_duplicate_raises(self):
        elements = fresh_base()
        with pytest.raises(MergeError, match="already exists"):
            merge_protocol_file(
                elements,
                FIXTURES / "ext_conflict" / "protocol.xml",
                "ext_conflict",
            )

    def test_append_missing_target_raises(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="NoSuchEnum" extend="append">
        <value name="Foo">99</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        with pytest.raises(MergeError, match="does not exist"):
            merge_protocol_file(elements, f, "test")

    def test_replace_missing_target_raises(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <struct name="NoSuchStruct" extend="replace">
        <field name="x" type="int"/>
    </struct>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        with pytest.raises(MergeError, match="does not exist"):
            merge_protocol_file(elements, f, "test")

    def test_numeric_enum_value_conflict_raises(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="PacketFamily" extend="append">
        <value name="OtherName">1</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        with pytest.raises(MergeError, match="enum value conflict"):
            merge_protocol_file(elements, f, "test")

    def test_unknown_extend_value_raises(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="PacketFamily" extend="mutate">
        <value name="Foo">99</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        with pytest.raises(MergeError, match="unknown extend value"):
            merge_protocol_file(elements, f, "test")

    def test_invalid_xml_raises(self, tmp_path):
        f = tmp_path / "protocol.xml"
        f.write_text("this is not xml <<<")
        elements = fresh_base()
        with pytest.raises(MergeError, match="Failed to parse"):
            merge_protocol_file(elements, f, "test")
