# eo-protocol-extensions

Official protocol extensions and the `eolib-ext` tool for the
[Endless Online](https://github.com/Cirras/eo-protocol) library ecosystem.

---

## What are protocol extensions?

The [eo-protocol](https://github.com/Cirras/eo-protocol) repository defines the binary
protocol used by Endless Online servers and clients. The official protocol only covers
the vanilla 0.0.28 version of the game.

**Protocol extensions** are a standard, structured way for custom server projects to add
new packets, modify existing enums, or extend structs — without permanently forking the
base protocol.

Each extension is a small directory of `protocol.xml` files that declare new or modified
protocol definitions. A CLI tool (`eolib-ext`) merges those extensions into a copy of the
eolib implementation of your choice before you build it.

---

## This repository

This repo serves two purposes:

1. **Official extension registry** — the `extensions/` directory contains publicly
   available protocol extensions. Any project can reference them by name.

2. **`eolib-ext` CLI tool** — the Python tool that automates cloning an eolib
   implementation, fetching extensions from any source, merging the XML, and producing
   a ready-to-build fork directory.

---

## eolib-ext CLI

### Installation

```bash
pip install eolib-ext
```

Requires Python 3.9+.

### Commands

| Command | Description |
|---|---|
| `eolib-ext apply` | Merge extensions into an eolib fork directory |
| `eolib-ext validate` | Fetch extensions and dry-run merge without cloning the full eolib |

---

### `eolib-ext apply`

The main command. Reads an `extensions.xml` config, clones/fetches extension sources,
merges the XML into the eolib protocol files, and outputs a ready-to-build directory.

```bash
eolib-ext apply --language=rs --config=extensions.xml --output=./eolib-rs-extended
```

**Options:**

| Flag | Default | Description |
|---|---|---|
| `--language` | *(required)* | Target eolib implementation (`rs`, `ts`, `java`, `python`, `php`, `go`, `dotnet`, `c`, `pas`) |
| `--config` | `extensions.xml` | Path to your `extensions.xml` file |
| `--output` | `./eolib-<language>-extended` | Output directory for the merged fork |

**Happy path output:**

```
eolib-ext v0.1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Cloning eolib-rs...                  ✔ done
 Initializing submodules...           ✔ done

 Resolving extensions...
  ✔  deep       (official registry)

 Merging extensions...
  ✔  deep
     + 3 new  · 7 appended  · 0 replaced

 Writing output to ./eolib-rs-extended... ✔ done

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ✔  Success! Build your extended eolib-rs from:
      ./eolib-rs-extended
```

**Extension not found:**

```
 ✘  Extension 'blah' not found in https://github.com/cirras/eo-protocol-extensions
    Available extensions:
      deep
      custom-quest
      example
```

**Merge conflict:**

```
 ✘  Merge conflict in extension 'something'
    Extension 'something' defines a new <enum> 'PacketFamily' but it already exists.
    Use extend="replace" to intentionally override it.
```

---

### `eolib-ext validate`

Fetches the base `eo-protocol` and all extensions to the local cache, then performs a
dry-run merge to check for conflicts — without cloning the full eolib implementation.
Useful for quickly catching merge errors during extension development.

```bash
eolib-ext validate --config=extensions.xml
```

---

## `extensions.xml` format

Create an `extensions.xml` file in your project to declare which extensions to apply:

```xml
<extensions>
  <!-- Official registry extension (git, default repo) -->
  <extension type="git" name="deep"/>

  <!-- Extension from a custom repository -->
  <extension type="git"
             name="my-feature"
             repo="https://github.com/my-org/eo-protocol-extensions"/>

  <!-- Local file-based extension (good for development) -->
  <extension type="file" name="local-test" path="../my-extension"/>
</extensions>
```

Extensions are applied in the order they appear. Later extensions can append to or replace
definitions introduced by earlier ones.

---

## How to make your own extension repository

You can host your own registry of extensions on GitHub (or anywhere git is accessible).

**Repository layout:**

```
your-eo-protocol-extensions/
  extensions/
    my-feature/
      protocol.xml
      net/
        client/protocol.xml
        server/protocol.xml
    another-feature/
      protocol.xml
```

Reference extensions from your repo with the `repo` attribute:

```xml
<extension type="git"
           name="my-feature"
           repo="https://github.com/your-org/your-eo-protocol-extensions"/>
```

Pin to a release tag with `ref`:

```xml
<extension type="git" name="my-feature" ref="v2.0.0"
           repo="https://github.com/your-org/your-eo-protocol-extensions"/>
```

See [`extensions/README.md`](extensions/README.md) for the full authoring guide,
including how to submit extensions to the official registry.

---

## Using a single extension without a repository

For local development or private extensions, use `type="file"` and point to a directory:

```xml
<extensions>
  <extension type="file" name="my-local-feature" path="../my-local-feature"/>
</extensions>
```

The `path` can be relative (resolved from the `extensions.xml` location) or absolute.

The directory must follow the same structure as a git-hosted extension:

```
my-local-feature/
  protocol.xml              ← optional: top-level definitions
  net/
    client/protocol.xml     ← optional: client-to-server packets
    server/protocol.xml     ← optional: server-to-client packets
  pub/
    protocol.xml            ← optional: pub file type definitions
```

---

## Extension XML format reference

Extension `protocol.xml` files mirror the structure of the base
[eo-protocol XML files](https://github.com/Cirras/eo-protocol).

### The `extend` attribute

`extend` can be used on top-level elements (`<enum>`, `<struct>`, `<packet>`) to control
the merge behavior:

| Value | Behavior |
|---|---|
| *(absent)* | **New** — definition must not already exist. Error if it does. |
| `"append"` | **Append** — push child elements onto an existing definition. |
| `"replace"` | **Replace** — completely swap out an existing definition. |

`extend="replace"` can also be used on individual `<value>` children inside an
`extend="append"` enum block to rename a specific existing value by its numeric position,
without replacing the whole enum:

```xml
<!-- Rename Reserved7 to Spell while leaving all other values intact -->
<enum name="ItemType" extend="append">
    <value name="Spell" extend="replace">7</value>
</enum>
```

### Element identification

- `<enum>` and `<struct>` are identified by their `name` attribute.
- `<packet>` is identified by the combination of `family` and `action` attributes.

### Appending switch cases

When appending to a struct or packet that contains a `<switch>`, use `extend="append"` on the
`<switch>` child to add new `<case>` elements without replacing the whole definition:

```xml
<struct name="AvatarChange" extend="append">
    <switch field="change_type" extend="append">
        <case value="Skin">
            <field name="skin" type="char"/>
        </case>
    </switch>
</struct>
```

The merger locates the target `<switch>` by its `field` attribute, searching recursively — so
it works whether the switch is a direct child of the struct/packet or nested inside a `<chunked>`
block. You do not need to know or replicate the surrounding structure.

### Conflict rules

| Situation | Behavior |
|---|---|
| New definition with duplicate name | **Error** — use `extend="replace"` to override |
| Append to nonexistent target | **Error** — check name and extension order |
| Replace nonexistent target | **Error** |
| Enum append with duplicate numeric value | **Error** — numeric conflicts corrupt generated code |
| Enum value replace with nonexistent numeric value | **Error** — check the numeric value |
| Switch append with no matching `field` | **Error** — check the field name |

### Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<protocol>
    <!-- Add a brand-new enum -->
    <enum name="Rarity" type="char">
        <value name="Common">0</value>
        <value name="Rare">1</value>
    </enum>

    <!-- Add a new value to an existing enum -->
    <enum name="PacketFamily" extend="append">
        <value name="Rarity">200</value>
    </enum>

    <!-- Rename an existing reserved value by numeric position -->
    <enum name="ItemType" extend="append">
        <value name="Spell" extend="replace">7</value>
    </enum>

    <!-- Completely replace an existing struct -->
    <struct name="Coords" extend="replace">
        <field name="x" type="short"/>
        <field name="y" type="short"/>
        <field name="layer" type="char"/>
    </struct>

    <!-- Add new cases to a switch inside an existing struct -->
    <struct name="AvatarChange" extend="append">
        <switch field="change_type" extend="append">
            <case value="Skin">
                <field name="skin" type="char"/>
            </case>
        </switch>
    </struct>

    <!-- Add a new client-to-server packet -->
    <packet family="Rarity" action="Request">
        <field name="item_id" type="short"/>
    </packet>
</protocol>
```

---

## Contributing

Pull requests welcome for:
- New official extensions under `extensions/`
- Bug fixes or improvements to `eolib-ext`
- Documentation improvements

See [`extensions/README.md`](extensions/README.md) for extension submission guidelines.

## License

MIT
