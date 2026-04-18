from __future__ import annotations

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


class TestChildValueReplace:
    def test_renames_reserved_value(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="Direction" extend="append">
        <value name="Sideways" extend="replace">1</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        merge_protocol_file(elements, f, "test")
        direction = find_enum(elements, "Direction")
        names = [v.get("name") for v in direction if v.tag == "value"]
        assert "Sideways" in names
        assert "Left" not in names  # was value 1, now replaced

    def test_preserves_other_values(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="Direction" extend="append">
        <value name="Sideways" extend="replace">1</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        merge_protocol_file(elements, f, "test")
        direction = find_enum(elements, "Direction")
        names = [v.get("name") for v in direction if v.tag == "value"]
        assert "Down" in names
        assert "Up" in names
        assert "Right" in names

    def test_preserves_position(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="Direction" extend="append">
        <value name="Sideways" extend="replace">1</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        merge_protocol_file(elements, f, "test")
        direction = find_enum(elements, "Direction")
        values = [(v.get("name"), (v.text or "").strip()) for v in direction if v.tag == "value"]
        idx = next(i for i, (_, num) in enumerate(values) if num == "1")
        assert values[idx][0] == "Sideways"

    def test_strips_extend_attr_from_result(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="Direction" extend="append">
        <value name="Sideways" extend="replace">1</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        merge_protocol_file(elements, f, "test")
        direction = find_enum(elements, "Direction")
        for v in direction:
            if v.tag == "value" and (v.text or "").strip() == "1":
                assert "extend" not in v.attrib

    def test_missing_numeric_value_raises(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="Direction" extend="append">
        <value name="Sideways" extend="replace">99</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        with pytest.raises(MergeError, match="no <value> with numeric value"):
            merge_protocol_file(elements, f, "test")

    def test_no_conflict_for_replaced_values(self, tmp_path):
        """A value with extend="replace" should not trigger the numeric conflict error."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <enum name="Direction" extend="append">
        <value name="Sideways" extend="replace">1</value>
        <value name="Extra">10</value>
    </enum>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        # Should not raise
        merge_protocol_file(elements, f, "test")


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestAppendSwitch:
    def _get_switch_cases(self, el: ET.Element, field: str) -> list[str] | None:
        """Recursively find a switch by field name and return its case values, or None if not found."""
        for child in el:
            if child.tag == "switch" and child.get("field") == field:
                return [c.get("value") for c in child if c.tag == "case"]
            result = self._get_switch_cases(child, field)
            if result is not None:
                return result
        return None

    def test_appends_case_to_direct_switch(self):
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_append_switch" / "protocol.xml", "ext_switch")
        shape = find_struct(elements, "Shape")
        cases = self._get_switch_cases(shape, "type")
        assert "Triangle" in cases
        assert "Circle" in cases  # original preserved

    def test_appends_case_to_switch_inside_chunked(self):
        """The merger auto-detects the switch regardless of chunked nesting."""
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_append_switch" / "protocol.xml", "ext_switch")
        msg = find_struct(elements, "ShapeMessage")
        cases = self._get_switch_cases(msg, "type")
        assert "Square" in cases
        assert "Circle" in cases  # original preserved

    def test_appends_case_to_switch_in_packet_chunked(self):
        """Works the same way for packets with a chunked-nested switch."""
        elements = fresh_base()
        merge_protocol_file(elements, FIXTURES / "ext_append_switch" / "protocol.xml", "ext_switch")
        pkt = find_packet(elements, "Walk", "Player")
        cases = self._get_switch_cases(pkt, "direction")
        assert "Left" in cases
        assert "Down" in cases  # original preserved

    def test_result_counts(self):
        elements = fresh_base()
        result = merge_protocol_file(elements, FIXTURES / "ext_append_switch" / "protocol.xml", "ext_switch")
        assert result.append_count == 4  # ShapeType enum + Shape + ShapeMessage + Walk::Player
        assert result.new_count == 0
        assert result.replace_count == 0

    def test_missing_switch_raises(self, tmp_path):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <struct name="Shape" extend="append">
        <switch field="no_such_field" extend="append">
            <case value="Foo"><field name="x" type="char"/></case>
        </switch>
    </struct>
</protocol>"""
        f = tmp_path / "protocol.xml"
        f.write_text(xml)
        elements = fresh_base()
        with pytest.raises(MergeError, match="no such switch"):
            merge_protocol_file(elements, f, "test")

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
