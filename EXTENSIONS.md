# Authoring Extensions

This guide explains how to create a protocol extension for use with `protomerge`.

---

## What is an extension?

An extension is a directory containing one or more `protocol.xml` files that add to or
modify the base [eo-protocol](https://github.com/Cirras/eo-protocol) definitions.

Extensions are applied in order using the `protomerge apply` command. Each extension can:
- **Add** new enums, structs, or packets
- **Append** new values or fields to existing definitions
- **Replace** existing definitions entirely

---

## Directory structure

An extension mirrors the layout of `eo-protocol/xml/`. For a git-hosted extension, the
extension directory is a **named subdirectory at the root of the repository** — the `name`
attribute in `extensions.xml` determines which subdirectory is used:

```
your-extension-repo/
  my-extension/
    protocol.xml              ← top-level definitions (enums, structs, misc packets)
    net/
      client/
        protocol.xml          ← client-to-server packets
      server/
        protocol.xml          ← server-to-client packets
    pub/
      protocol.xml            ← pub file type definitions (EIF, ENF, ESF, ECF)
```

For a `type="file"` extension, the same structure applies inside the directory you point
`path` at. Not all files are required — include only what your extension touches.

---

## The `extend` attribute

Each top-level element in an extension `protocol.xml` may include an `extend` attribute
that controls the merge behavior:

| `extend` value | Meaning |
|---|---|
| *(absent)* | **New** — the definition must not exist yet. Error if it does. |
| `"append"` | **Append** — push child elements (values/fields/etc.) onto an existing definition. |
| `"replace"` | **Replace** — completely swap out an existing definition with this one. |

`extend="replace"` may also be used on individual `<value>` children inside an
`extend="append"` enum block to rename a specific existing value by its numeric position,
without replacing the whole enum:

```xml
<!-- Rename the "Reserved7" placeholder to "Spell" while leaving all other values alone -->
<enum name="ItemType" extend="append">
    <value name="Spell" extend="replace">7</value>
</enum>
```

The merger finds the child `<value>` with text content `7`, replaces it in-place with the
new element (stripping the `extend` attribute from the result), and raises an error if no
value with that number exists.

### Examples

```xml
<!-- New enum — must not already exist anywhere in the base or prior extensions -->
<enum name="Rarity" type="char">
    <value name="Common">0</value>
    <value name="Rare">1</value>
</enum>

<!-- Append a new value to an existing PacketFamily enum -->
<enum name="PacketFamily" extend="append">
    <value name="Rarity">200</value>
</enum>

<!-- Rename an existing reserved value by its numeric position -->
<enum name="ItemType" extend="append">
    <value name="Spell" extend="replace">7</value>
    <value name="Transformation" extend="replace">5</value>
</enum>

<!-- Replace an existing struct entirely -->
<struct name="Coords" extend="replace">
    <field name="x" type="short"/>
    <field name="y" type="short"/>
    <field name="layer" type="char"/>
</struct>

<!-- Add new cases to a switch inside an existing struct or packet -->
<struct name="AvatarChange" extend="append">
    <switch field="change_type" extend="append">
        <case value="Skin">
            <field name="skin" type="char"/>
        </case>
    </switch>
</struct>
```

The merger locates the target `<switch>` by its `field` attribute, searching recursively —
it works whether the switch is a direct child or nested inside a `<chunked>` block.

---

## Conflict rules

- **New with duplicate name** → error. Use `extend="replace"` if intentional.
- **Append to nonexistent target** → error. Check name spelling and extension order.
- **Replace nonexistent target** → error.
- **Append enum with duplicate numeric value** → error (numeric conflicts corrupt generated code).
- **Child value replace with nonexistent numeric value** → error. Check the number is correct.
- **Switch append with no matching `field`** → error. Check the field name.

---

## Using your extension

### As a file extension (local development)

Reference your extension directory directly in `extensions.xml`:

```xml
<extensions>
  <extension type="file" name="my-feature" path="../my-extension"/>
</extensions>
```

Then apply:

```
protomerge apply --config=extensions.xml
```

### As a git repository

A git extension repository contains named extension subdirectories at its root. The `name`
attribute in `extensions.xml` determines which subdirectory is used:

```
your-extension-repo/
  my-feature/
    protocol.xml
    net/client/protocol.xml
    net/server/protocol.xml
```

Reference it in `extensions.xml`:

```xml
<extensions>
  <extension type="git" name="my-feature" repo="https://github.com/your-org/your-extension-repo"/>
</extensions>
```

You can pin to a specific tag or commit with `ref`:

```xml
<extension type="git" name="my-feature" ref="v1.2.0"
           repo="https://github.com/your-org/your-extension-repo"/>
```

---

## Submitting to the official registry

> [!IMPORTANT]
> **The official registry has strict acceptance criteria — most submissions will not be accepted.**
>
> This repository is primarily intended to host protocol extensions created by the original
> game developer (Vult-r), such as the official "deep" protocol extensions. Extensions from
> third parties will only be considered in exceptional circumstances and must be very carefully
> evaluated for compatibility, stability, and value to the broader community.
>
> If you're building a custom server or client, we strongly encourage you to host your
> extension in its own repository instead. See
> [As a git repository](#as-a-git-repository) above — it's just as easy
> and gives you full control.

To submit an extension to this repository for others to use:

1. Fork this repo
2. Create a top-level directory named after your extension (e.g. `my-extension/`)
3. Add your `protocol.xml` files following the structure above
4. Open a pull request with a description of what your extension does and why

Extension names should be lowercase, hyphen-separated, and descriptive (e.g. `deep-sea`, `custom-trade`).

---

## See also

- [protomerge CLI reference](https://github.com/sorokya/protomerge)
- [`extensions.xml` format](README.md#using-extensions-with-protomerge) in the main README
