# eo-protocol-extensions

[![Validate Extensions](https://github.com/sorokya/eo-protocol-extensions/actions/workflows/validate-extensions.yml/badge.svg)](https://github.com/sorokya/eo-protocol-extensions/actions/workflows/validate-extensions.yml)

Official protocol extensions for the [Endless Online](https://github.com/Cirras/eo-protocol)
library ecosystem.

---

## Official extensions

| Name | Description |
|------|-------------|
| [`deep`](deep/) | The "Deep" protocol extensions created by Vult-r. Adds and extends packets for features of the 0.3.x client version |

---

## What are protocol extensions?

The [eo-protocol](https://github.com/Cirras/eo-protocol) repository defines the binary
protocol used by Endless Online servers and clients. The official protocol only covers
the vanilla 0.0.28 version of the game.

**Protocol extensions** are a standard, structured way for custom server projects to add
new packets, modify existing enums, or extend structs — without permanently forking the
base protocol.

Each extension is a directory of `protocol.xml` files. The
[protomerge](https://github.com/sorokya/protomerge) CLI tool merges them into a complete
copy of the eo-protocol XML, ready to pass to an eolib code generator.

---

## Using extensions with `protomerge`

Install [protomerge](https://github.com/sorokya/protomerge):

```bash
pip install git+https://github.com/sorokya/protomerge.git
```

Create an `extensions.xml` in your project:

```xml
<extensions>
  <!-- Extension from a git repository (files at the repo root) -->
  <extension type="git" name="deep"
             repo="https://github.com/sorokya/eo-protocol-extensions"/>

  <!-- Local file-based extension -->
  <extension type="file" name="local-test" path="../my-extension"/>
</extensions>
```

Then apply:

```bash
protomerge apply --config=extensions.xml --output=./eo-protocol
```

This writes a merged `eo-protocol/` directory you can point your eolib code generator at.
See the [protomerge README](https://github.com/sorokya/protomerge) for the full CLI reference.

---

## How to host your own extension

Each git extension repository contains one or more named extension subdirectories at its
root. The `name` attribute in `extensions.xml` selects which subdirectory to use:

```
your-extension-repo/
  my-feature/
    protocol.xml              ← top-level definitions
    net/
      client/protocol.xml     ← client-to-server packets
      server/protocol.xml     ← server-to-client packets
    pub/
      protocol.xml            ← pub file type definitions
```

Reference it in your `extensions.xml`:

```xml
<extension type="git" name="my-feature"
           repo="https://github.com/your-org/your-extension-repo"/>
```

Pin to a release tag or commit with `ref`:

```xml
<extension type="git" name="my-feature" ref="v1.0.0"
           repo="https://github.com/your-org/your-extension-repo"/>
```

See [`EXTENSIONS.md`](EXTENSIONS.md) for the full extension authoring guide,
including how to submit extensions to this registry.

---

## Contributing

Pull requests welcome for:
- New official extensions (as top-level directories in this repo)
- Documentation improvements

See [`EXTENSIONS.md`](EXTENSIONS.md) for extension submission guidelines.

## License

MIT
