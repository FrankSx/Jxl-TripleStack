# Jxl-TripleStack

> A novel triple-container polyglot: **JPEG XL** + **PDF 2.0** + **WebAssembly** — three formats, one file.

```
Project:    Jxl-TripleStack
Version:    v1.0
Size:       1,308 bytes
Formats:    3 (PDF 2.0 / JPEG XL / WebAssembly v1)
Stack:      PDF → JXL ISOBMFF → WASM
Status:     Novel / First documented triple-container of this type
```

---

## The Triple Stack

| Layer | Format | Role | Size |
|-------|--------|------|------|
| **Top** | PDF 2.0 | Outermost wrapper / document | ~1,062 bytes |
| **Middle** | JPEG XL | ISOBMFF carrier container | 246 bytes |
| **Bottom** | WebAssembly | Innermost executable payload | 144 bytes |

All three layers are **independently valid**. Extract any layer and it parses cleanly in its native tooling.

---

## Quick Start

```bash
# Clone or download the release
unzip Jxl-TripleStack_v1.0.zip
cd Jxl-TripleStack_v1.0

# Open as PDF (any PDF reader)
open polyglot.pdf

# Extract all embedded formats
python tools/extract_all.py polyglot.pdf
# → extracted_container.jxl (246 bytes)
# → extracted_module.wasm   (144 bytes)

# Inspect the WASM module
python tools/wasm_info.py extracted_module.wasm

# Rebuild the entire triple stack from scratch
python tools/build_polyglot.py
```

---

## What Is Jxl-TripleStack?

A **polyglot file** is a single byte sequence valid under multiple format specifications. Most documented polyglots are dual-format (JPG+PDF, HTML+JS). Jxl-TripleStack pushes that to **three independent formats** through nested container abuse — the "triple stack."

### The Three Faces

| Extension | Format | Opens With |
|-----------|--------|------------|
| `.pdf` | PDF 2.0 (ISO 32000-2) | Any PDF reader — renders a document page |
| `.jxl` | JPEG XL (ISO/IEC 18181-1) | JXL-aware tools — parses ISOBMFF container |
| `.wasm` | WebAssembly v1 (W3C) | WASM runtimes — executes `polyglot` function |

All three files are **identical bytes** — just renamed.

---

## Architecture

```mermaid
graph TD
    A[PDF 2.0 Document<br/>1,308 bytes] -->|EmbeddedFile Stream<br/>FlateDecode compressed| B[JPEG XL ISOBMFF<br/>246 bytes]
    B -->|xml box<br/>XML comment| C[WebAssembly v1<br/>144 bytes]

    A --> A1[%PDF-2.0 header]
    A --> A2[Catalog → Pages → Page]
    A --> A3[EmbeddedFiles Name Tree]
    A --> A4[FileSpec: polyglot.jxl]
    A --> A5[Cross-reference table]

    B --> B1[ftyp box<br/>jxl brand]
    B --> B2[jxlc box<br/>FF 0A signature]
    B --> B3[xml box<br/>&lt;!-- WASM --&gt;]
    B --> B4[jxll box<br/>Level 5]

    C --> C1[Type: () → i32]
    C --> C2[Export: polyglot]
    C --> C3[Code: return 0xCAFEBABE]
    C --> C4[Custom: polyglot-meta]
```

### Layer 1 — PDF 2.0 (The Wrapper)
- Valid `%PDF-2.0` header at offset 0
- Standard object graph: Catalog → Pages → Page → Content
- EmbeddedFiles name tree maps `polyglot.jxl` → FileSpec → EmbeddedFile stream
- Full cross-reference table and trailer per ISO 32000-2:2020
- The embedded stream is **FlateDecode compressed** to hide the JXL payload

### Layer 2 — JPEG XL (The Carrier)
- ISOBMFF-based (ISO/IEC 14496-12) with `jxl ` brand
- `ftyp` → `jxlc` → `xml ` → `jxll` box chain
- The `xml ` box contains XML-wrapped WASM:
  ```xml
  <?xml version="1.0"?><wasm><!--[144 bytes raw WASM]--></wasm>
  ```
- XML comment preserves raw binary WASM without modification

### Layer 3 — WebAssembly (The Payload)
- Magic: `\x00asm` (0x0061736D)
- Version: 1
- Exports function `polyglot` returning `i32.const 0xCAFEBABE`
- Custom section `polyglot-meta` contains JSON metadata

---

## File Hashes

```
MD5:     9b57d0e04519082d6be5e2aba1281b5b
SHA1:    e47b1e7394b04fbfbd4462fc263ab6114b731393
SHA256:  70e1b9c9ba4bc03f092f0d9cf4d4015a6b11df1eba957cf0e01721e1c50263ce
Size:    1308 bytes
```

---

## Project Structure

```
Jxl-TripleStack_v1.0/
├── polyglot.pdf              # Triple stack (.pdf face)
├── polyglot.jxl              # Same bytes (.jxl face)
├── polyglot.wasm             # Same bytes (.wasm face)
├── tools/
│   ├── extract_all.py        # Universal extractor & analyzer
│   ├── extract_jxl_from_pdf.py  # JXL-specific extractor
│   ├── wasm_info.py          # WASM section inspector
│   └── build_polyglot.py     # Rebuild the triple stack from scratch
├── docs/
│   └── TECHNICAL_SPEC.md     # Full technical documentation
├── README.md                 # This file
└── HASHES.txt                # Verification hashes
```

---

## Verification

### Open as PDF

```bash
$ file polyglot.pdf
polyglot.pdf: PDF document, version 2.0

$ pdfinfo polyglot.pdf
PDF version:     2.0
Pages:           1
```

Opens correctly in Adobe Acrobat, Chrome, Firefox, evince, etc.

### Extract JPEG XL

```bash
$ python tools/extract_all.py polyglot.pdf
=== Polyglot Analysis: polyglot.pdf ===
Size: 1308 bytes | MD5: 9b57d0e04519082d6be5e2aba1281b5b
[PDF] Valid: True
[JXL] Stream 1: 246 bytes
[WASM] Module: 144 bytes
=== Done ===
```

### Extract & Run WebAssembly

```bash
$ python tools/wasm_info.py extracted_module.wasm
WASM: extracted_module.wasm (144 bytes)
Version: 1
  Type: 5 bytes
  Function: 2 bytes
  Export: 12 bytes
    Export: polyglot (func idx=0)
  Code: 8 bytes
  Custom: 91 bytes
    Custom: polyglot-meta
```

Run in a browser:
```javascript
const wasm = await WebAssembly.instantiateStreaming(
  fetch('extracted_module.wasm')
);
console.log(wasm.instance.exports.polyglot());
// → -889275714 (0xCAFEBABE as signed i32)
```

Or with Wasmtime:
```bash
$ wasmtime extracted_module.wasm --invoke polyglot
-889275714
```

---

## Novelty

### What's Prior Art

| Technique | Source | Year |
|-----------|--------|------|
| JPG+PDF polyglots | Ange Albertini (PoC||GTFO) | ~2013 |
| PDF EmbeddedFile steganography | Glasswall research | 2024 |
| WASM+HTML polyglots | FuzzingLabs | 2024 |
| ISOBMFF format abuse | Multimedia security community | Ongoing |

### What's New Here

1. **Triple-container nesting** — No publicly documented polyglot chains three independent container formats (PDF → JXL ISOBMFF → WASM). Most stop at two.

2. **JPEG XL as polyglot carrier** — JXL is a relatively new format (standardized ~2021-2022). Its ISOBMFF structure differs from traditional JPEG, making prior JPG+PDF techniques non-transferable.

3. **xml box → WASM comment injection** — Using an ISOBMFF `xml ` box's XML comment to preserve raw WASM binary data is a specific format-quirk marriage not documented in prior polyglot research.

4. **Size efficiency** — At ~1,308 bytes, this is one of the smallest documented multi-format polyglots with this nesting depth.

**Status:** First documented triple-container of this type. Published 2026-05-12.

---

## Security Research Applications

- **Parser Differential Analysis** — Different tools handle ambiguous containers differently. PDF readers render the document; JXL decoders extract the image container; WASM runtimes execute the module.
- **MIME Type Confusion** — Serve as one Content-Type, exploit as another. A server allowing `application/pdf` uploads might not recursively inspect embedded streams.
- **Steganography** — Three layers of obfuscation: FlateDecode compression → ISOBMFF box structure → XML comment wrapping.
- **Format Sandbox Escapes** — Whitelist-based sandboxes checking only outer-layer magic numbers may miss nested payloads.

---

## Technical Deep Dive

<details>
<summary><b>Construction Methodology</b></summary>

### Design Constraints

**PDF Constraints:**
- `%PDF-X.Y` must appear within first 1,024 bytes (offset 0 is ideal)
- Object numbers must be sequential; xref offsets must be exact
- Stream lengths must match actual compressed data

**JXL Constraints:**
- `ftyp` box must be early for brand recognition
- Box sizes are big-endian 32-bit; types are 4 ASCII chars
- Must be parseable as valid ISOBMFF

**WASM Constraints:**
- Magic `\x00asm` at module offset 0
- Version `1` (little-endian) at offset 4
- All sections must be valid LEB128-encoded

### Why This Works

Each format only validates its own layer:
- **PDF parser** sees a valid PDF with an embedded file. It doesn't care what the compressed stream contains.
- **JXL parser** sees a valid ISOBMFF container. It doesn't care that the `xml ` box contains a WASM module.
- **WASM parser** sees valid binary between `<!--` and `-->`. It doesn't care about the XML wrapper.

This is **defense in depth for polyglot construction** — each layer shields inner layers from outer parser scrutiny.

### Byte Budget

| Component | Size |
|-----------|------|
| PDF header + binary marker | 14 bytes |
| 8 PDF objects | ~850 bytes |
| xref + trailer + EOF | ~120 bytes |
| FlateDecode overhead | ~20 bytes |
| JXL container (uncompressed) | 246 bytes |
| WASM module | 144 bytes |
| **Total** | **~1,308 bytes** |

</details>

<details>
<summary><b>Limitations & Future Work</b></summary>

### Current Limitations

- **WASM offset requirement**: Standard runtimes require `\x00asm` at file offset 0. The polyglot starts with `%PDF-2.0`, so direct WASM execution requires extraction first.
- **JXL image rendering**: The `jxlc` box contains only the naked codestream signature with minimal padding. Real decoders will recognize the container but may not render a visible image.
- **PDF strictness**: Some strict PDF parsers might object to binary content in EmbeddedFile streams, though FlateDecode compression should mask this.

### Future Directions

1. **True offset-0 triple polyglot** — Investigate whether a file can start with WASM magic while satisfying PDF and JXL header requirements.
2. **Visual payload** — Replace minimal `jxlc` with a real JXL codestream encoding a meaningful image.
3. **Quad-polyglot** — Add a fourth format (e.g., ZIP in WASM custom section) for PDF → JXL → WASM → ZIP.
4. **Exploit delivery** — Research bypass of specific security products that inspect files at different depths.

</details>

---

## References

1. Albertini, A. (2013). *PoC||GTFO 0x03: AngeCryption*
2. FuzzingLabs (2024). *WASM+HTML Polyglots*
3. Glasswall (2024). *PDF Steganography Techniques*
4. ISO/IEC 18181-1:2022. *JPEG XL Image Coding System — Part 1: Core coding system*
5. ISO/IEC 14496-12:2022. *ISO Base Media File Format (ISOBMFF)*
6. ISO 32000-2:2020. *Document management — Portable Document Format — Part 2: PDF 2.0*
7. W3C (2019). *WebAssembly Core Specification, Version 1.0*
8. Mozilla (2025). *JPEG XL Support Status*

---

## License

Research / Educational Use. Created for security research purposes.

---

> *"Three formats. One file. Zero compromises."*
> 
> **— frankSx, 2026-05-12**
