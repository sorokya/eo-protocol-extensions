# Authoring Extensions

This guide explains how to create a protocol extension for use with `eolib-ext`.

---

## What is an extension?

An extension is a directory containing one or more `protocol.xml` files that add to or
modify the base [eo-protocol](https://github.com/Cirras/eo-protocol) definitions.

Extensions are applied in order using the `eolib-ext apply` command. Each extension can:
- **Add** new enums, structs, or packets
- **Append** new values or fields to existing definitions
- **Replace** existing definitions entirely

---

## Directory structure

An extension mirrors the layout of `eo-protocol/xml/`:

```
my-extension/
  protocol.xml              ← top-level definitions (enums, structs, misc packets)
  net/
    client/
      protocol.xml          ← client-to-server packets
    server/
      protocol.xml          ← server-to-client packets
```

Not all files are required — include only what your extension touches.

---

## The `extend` attribute

Each top-level element in an extension `protocol.xml` may include an `extend` attribute
that controls the merge behavior:

| `extend` value | Meaning |
|---|---|
| *(absent)* | **New** — the definition must not exist yet. Error if it does. |
| `"append"` | **Append** — push child elements (values/fields/etc.) onto an existing definition. |
| `"replace"` | **Replace** — completely swap out an existing definition with this one. |

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

<!-- Replace an existing struct entirely -->
<struct name="Coords" extend="replace">
    <field name="x" type="short"/>
    <field name="y" type="short"/>
    <field name="layer" type="char"/>
</struct>
```

---

## Conflict rules

- **New with duplicate name** → error. Use `extend="replace"` if intentional.
- **Append to nonexistent target** → error. Check name spelling and extension order.
- **Replace nonexistent target** → error.
- **Append enum with duplicate numeric value** → error (numeric conflicts corrupt generated code).

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
eolib-ext apply --language=rs --config=extensions.xml
```

### As part of a custom repository

Host your extensions in a GitHub repo following the layout:

```
your-eo-protocol-extensions/
  extensions/
    my-feature/
      protocol.xml
      net/client/protocol.xml
      net/server/protocol.xml
```

Reference it in `extensions.xml`:

```xml
<extensions>
  <extension type="git" name="my-feature" repo="https://github.com/your-org/your-eo-protocol-extensions"/>
</extensions>
```

You can pin to a specific tag or commit with `ref`:

```xml
<extension type="git" name="my-feature" ref="v1.2.0"
           repo="https://github.com/your-org/your-eo-protocol-extensions"/>
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
> extensions in your own repository instead. See
> [As part of a custom repository](#as-part-of-a-custom-repository) above — it's just as easy
> and gives you full control.

To submit an extension to this repository for others to use:

1. Fork this repo
2. Create a directory under `extensions/<your-extension-name>/`
3. Add your `protocol.xml` files following the structure above
4. Open a pull request with a description of what your extension does and why

Extension names should be lowercase, hyphen-separated, and descriptive (e.g. `deep-sea`, `custom-trade`).

---

## See also

- [`extensions/example/`](./example/) — a minimal reference extension
- [`extensions.xml` format](../README.md#extensionsxml-format) in the main README
- [eolib-ext CLI reference](../README.md#eolib-ext-cli)
