from __future__ import annotations

"""
XML merge engine.

Applies extension protocol.xml files onto a base set of protocol elements.
Each element in an extension file may carry an optional 'extend' attribute:

  absent   → new:     Add as a brand-new definition. Error if name already exists.
  append   → append:  Push child elements (values/fields) onto an existing definition.
  replace  → replace: Completely swap out an existing definition.

Packets are identified by (direction, family, action) where direction is "client",
"server", or "" derived from the file path. Enums and structs are identified by name.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from .models import ElementChange, MergeResult


class MergeError(Exception):
    pass


# Internal attribute used to tag packet elements with their client/server direction.
_DIR_ATTR = "_eoext_direction"


def _direction_from_path(path: Path) -> str:
    parts = set(path.parts)
    if "client" in parts:
        return "client"
    if "server" in parts:
        return "server"
    return ""


def _packet_id(el: ET.Element) -> str:
    direction = el.get(_DIR_ATTR, "")
    prefix = f"{direction}:" if direction else ""
    return f"{prefix}{el.get('family')}{el.get('action')}"


def _element_id(el: ET.Element) -> str:
    tag = el.tag
    if tag == "packet":
        return _packet_id(el)
    return el.get("name", "")


def _find_existing(
    pool: list[ET.Element], tag: str, el_id: str
) -> Optional[ET.Element]:
    for existing in pool:
        if existing.tag != tag:
            continue
        if _element_id(existing) == el_id:
            return existing
    return None


def _tag_packet(el: ET.Element, path: Path) -> None:
    """Attach direction metadata to a packet element derived from its file path."""
    if el.tag == "packet":
        el.set(_DIR_ATTR, _direction_from_path(path))


def merge_protocol_file(
    base_elements: list[ET.Element],
    extension_file: Path,
    extension_name: str,
) -> MergeResult:
    """
    Parse one extension protocol.xml and merge its elements into base_elements in-place.
    Returns a MergeResult describing what changed.
    Raises MergeError on conflicts.
    """
    result = MergeResult(extension_name=extension_name)

    try:
        tree = ET.parse(extension_file)
    except ET.ParseError as e:
        raise MergeError(f"Failed to parse {extension_file}: {e}") from e

    root = tree.getroot()
    if root.tag != "protocol":
        raise MergeError(
            f"{extension_file}: root element must be <protocol>, got <{root.tag}>"
        )

    for el in root:
        if el.tag in ("comment", ET.Comment):
            continue

        _tag_packet(el, extension_file)
        extend = el.get("extend")
        el_id = _element_id(el)
        tag = el.tag

        if extend is None:
            # New definition — must not already exist
            existing = _find_existing(base_elements, tag, el_id)
            if existing is not None:
                raise MergeError(
                    f"Extension '{extension_name}' ({extension_file}) defines a new "
                    f"<{tag}> '{el_id}' but it already exists in the base protocol or "
                    f"a previously-applied extension.\n"
                    f"  Use extend=\"replace\" to intentionally override it."
                )
            new_el = _strip_extend(el)
            base_elements.append(new_el)
            result.changes.append(ElementChange("new", tag, el_id))

        elif extend == "append":
            existing = _find_existing(base_elements, tag, el_id)
            if existing is None:
                raise MergeError(
                    f"Extension '{extension_name}' ({extension_file}) tries to append "
                    f"to <{tag}> '{el_id}' but it does not exist in the base protocol "
                    f"or any previously-applied extension.\n"
                    f"  Check the extension name and the order of extensions."
                )
            _check_no_numeric_conflicts(existing, el, extension_name, extension_file)
            for child in el:
                if child.tag in ("comment", ET.Comment):
                    continue
                if child.get("extend") == "replace":
                    _replace_child_value(existing, child, extension_name, extension_file)
                elif child.tag == "switch" and child.get("extend") == "append":
                    _append_switch_cases(existing, child, extension_name, extension_file)
                else:
                    existing.append(child)
            result.changes.append(ElementChange("append", tag, el_id))

        elif extend == "replace":
            existing = _find_existing(base_elements, tag, el_id)
            if existing is None:
                raise MergeError(
                    f"Extension '{extension_name}' ({extension_file}) tries to replace "
                    f"<{tag}> '{el_id}' but it does not exist in the base protocol or "
                    f"any previously-applied extension."
                )
            idx = base_elements.index(existing)
            new_el = _strip_extend(el)
            base_elements[idx] = new_el
            result.changes.append(ElementChange("replace", tag, el_id))

        else:
            raise MergeError(
                f"Extension '{extension_name}' ({extension_file}): "
                f"unknown extend value '{extend}' on <{tag}> '{el_id}'. "
                f"Valid values: append, replace (or omit for new)."
            )

    return result


def _strip_extend(el: ET.Element) -> ET.Element:
    """Return a copy of the element with the 'extend' attribute removed."""
    new_el = ET.Element(el.tag, {k: v for k, v in el.attrib.items() if k != "extend"})
    new_el.text = el.text
    new_el.tail = el.tail
    for child in el:
        new_el.append(child)
    return new_el


def _find_switch(el: ET.Element, field: str) -> Optional[ET.Element]:
    """Recursively find the first <switch> with the given field attribute."""
    for child in el:
        if child.tag == "switch" and child.get("field") == field:
            return child
        result = _find_switch(child, field)
        if result is not None:
            return result
    return None


def _append_switch_cases(
    existing: ET.Element,
    switch_el: ET.Element,
    extension_name: str,
    extension_file: Path,
) -> None:
    """Append <case> children from switch_el into the matching <switch> inside existing."""
    field = switch_el.get("field")
    target_switch = _find_switch(existing, field)
    if target_switch is None:
        raise MergeError(
            f"Extension '{extension_name}' ({extension_file}) tries to append cases "
            f"to <switch field=\"{field}\"> in '{_element_id(existing)}' "
            f"but no such switch exists."
        )
    for case in switch_el:
        if case.tag not in ("comment", ET.Comment):
            target_switch.append(case)


def _replace_child_value(
    parent: ET.Element,
    replacement: ET.Element,
    extension_name: str,
    extension_file: Path,
) -> None:
    """
    Replace an existing child <value> in parent whose numeric value matches replacement's.
    The replacement element should carry extend="replace"; it is stripped before insertion.
    """
    target_num = (replacement.text or "").strip()
    for i, child in enumerate(parent):
        if child.tag == "value" and (child.text or "").strip() == target_num:
            new_child = _strip_extend(replacement)
            parent.remove(child)
            parent.insert(i, new_child)
            return
    raise MergeError(
        f"Extension '{extension_name}' ({extension_file}): "
        f"<{parent.tag}> '{_element_id(parent)}' has no <value> with numeric value "
        f"'{target_num}' to replace."
    )


def _check_no_numeric_conflicts(
    existing: ET.Element,
    extension_el: ET.Element,
    extension_name: str,
    extension_file: Path,
) -> None:
    """For enum appends, check that no numeric value is duplicated."""
    if existing.tag != "enum":
        return

    existing_values: dict[str, str] = {}  # numeric_value -> name
    for child in existing:
        if child.tag == "value":
            num = (child.text or "").strip()
            existing_values[num] = child.get("name", "?")

    for child in extension_el:
        if child.tag == "value":
            num = (child.text or "").strip()
            name = child.get("name", "?")
            if child.get("extend") == "replace":
                continue  # intentional replacement of an existing value — not a conflict
            if num in existing_values:
                raise MergeError(
                    f"Extension '{extension_name}' ({extension_file}): "
                    f"enum value conflict in '{_element_id(existing)}':\n"
                    f"  Value {num} (name '{name}') conflicts with "
                    f"value {num} (name '{existing_values[num]}') already defined."
                )


def load_base_elements(base_protocol_files: list[Path]) -> list[ET.Element]:
    """Parse all base protocol.xml files and return their combined top-level elements."""
    elements: list[ET.Element] = []
    for f in base_protocol_files:
        tree = ET.parse(f)
        root = tree.getroot()
        for el in root:
            if el.tag not in ("comment", ET.Comment):
                _tag_packet(el, f)
                elements.append(el)
    return elements
