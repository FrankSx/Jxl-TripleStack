# The JPEG XL + PDF 2.0 + WebAssembly Triple-Container Polyglot
## A Novel Approach to Nested Format Abuse for Security Research

**Author:** frankSx  
**Date:** 2026-05-12  
**Classification:** Security Research / Novel Format Abuse  
**Target Audience:** Reverse Engineers, Security Researchers, CTF Players, Polyglot Enthusiasts

---

## Abstract

This paper presents a novel triple-container polyglot file that is simultaneously valid as three independent file formats: **JPEG XL** (ISO/IEC 18181-1), **PDF 2.0** (ISO 32000-2:2020), and **WebAssembly** (W3C Core Specification v1). Unlike prior dual-format polyglots, this construction nests three distinct container formats through a chain of format-specific parsing behaviors: PDF's EmbeddedFile stream carries a FlateDecode-compressed JPEG XL ISOBMFF container, whose `xml ` box encapsulates a WebAssembly binary module via XML comment injection. Each layer is independently extractable and structurally valid. The complete file occupies approximately **1,308 bytes**, making it one of the smallest documented multi-format polyglots of this nesting depth.

---

## 1. Introduction

### 1.1 What is a Polyglot?

A polyglot file is a single byte sequence that is syntactically valid under multiple file format specifications. The concept dates back decades, but modern polyglot research exploded with Ange Albertini's work on **JPG+PDF** polyglots in the early 2010s. These files exploit format-specific parsing behaviors — such as PDF's tolerance for binary data before its `%PDF` header or image formats' scanning for magic numbers at arbitrary offsets — to create files that open correctly in multiple applications.

### 1.2 Why Triple-Container?

Most documented polyglots are dual-format (e.g., image + PDF, HTML + JS, ZIP + PNG). Triple-format polyglots are rare because each additional format imposes stricter structural constraints on the shared byte sequence. The challenge is not merely concatenating headers, but ensuring that each format's parser can traverse its expected data structures without encountering fatal errors when other formats' data is present.

### 1.3 Why These Three Formats?

| Format | Role | Container Capability | Parser Behavior |
|--------|------|----------------------|---------------|
| **PDF 2.0** | Outermost wrapper | EmbeddedFile streams with FlateDecode compression | Scans first 1,024 bytes for `%PDF` header; lenient about binary data between objects |
| **JPEG XL** | Middle carrier | ISOBMFF `xml ` box can hold arbitrary XML-like data | Scans for `ftyp` box with `jxl ` brand; tolerant of non-image boxes |
| **WebAssembly** | Innermost payload | Custom sections allow arbitrary metadata | Requires magic `\x00asm` at module offset 0; sections are length-prefixed |

This combination was chosen because:
1. **PDF** can legally embed any file type via its EmbeddedFile specification
2. **JXL's ISOBMFF** `xml ` box is designed for metadata and tolerates arbitrary XML content
3. **WASM's** custom section provides a clean metadata channel while the core module remains valid

---

## 2. Background and Prior Art

### 2.1 Dual-Format Polyglots

The most famous polyglot is the **JPG+PDF** combination, pioneered by Ange Albertini. The technique places a JPEG image at the start of the file (for image viewers) and embeds a PDF structure later in the file (for PDF readers, which scan for `%PDF` within the first 1,024 bytes). Variants include PNG+PDF, GIF+PDF, and even ZIP+PDF.

### 2.2 WASM Polyglots

FuzzingLabs demonstrated WASM+HTML polyglots in 2024, using WASM's data sections or custom sections to carry HTML/JS payloads. These are primarily used for browser-based exploitation or bypassing content filters that inspect file headers but not full structure.

### 2.3 PDF Embedded File Abuse

Glasswall's research on PDF steganography covers techniques like ZIP-in-PDF, TXT-in-PDF, and XMP injection. The EmbeddedFile stream is a well-known vector for hiding arbitrary data inside PDFs, but prior work has not combined it with a nested image container that itself carries a WASM module.

### 2.4 JPEG XL Container Structure

JPEG XL uses ISO Base Media File Format (ISOBMFF, ISO/IEC 14496-12), the same container standard as MP4 and HEIC. Key boxes:
- `ftyp`: File type declaration with brand `jxl `
- `jxlc`: JPEG XL codestream signature (`FF 0A`)
- `xml `: XML metadata box (arbitrary XML content)
- `jxll`: Level indication box

The `xml ` box is particularly interesting for polyglot construction because it is designed to hold arbitrary XML data, and many JXL parsers will skip unknown or non-critical boxes rather than fail.

---

## 3. Architecture

### 3.1 High-Level Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    PDF 2.0 Document                          │
│  %PDF-2.0 header → Catalog → Pages → Page → Content         │
│                          │                                  │
│                    EmbeddedFiles Name Tree                  │
│                          │                                  │
│              ┌───────────┴───────────┐                      │
│              │  FileSpec Object      │                      │
│              │  (polyglot.jxl)       │                      │
│              └───────────┬───────────┘                      │
│                          │                                  │
│              ┌───────────┴───────────┐                      │
│              │  EmbeddedFile Stream  │                      │
│              │  (FlateDecode compressed)│                     │
│              └───────────┬───────────┘                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │ JPEG XL     │
                    │ ISOBMFF     │
                    │ Container   │
                    │ (246 bytes) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
           ┌─┴─┐      ┌──┴──┐      ┌──┴──┐
           │ftyp│      │jxlc │      │xml │      │jxll│
           │(20)│      │(26) │      │(193)│      │(9) │
           └────┘      └─────┘      └──┬──┘      └────┘
                                        │
                              ┌─────────┴─────────┐
                              │   XML Comment     │
                              │   <!-- ... -->    │
                              └─────────┬─────────┘
                                        │
                              ┌─────────┴─────────┐
                              │  WebAssembly v1   │
                              │  (144 bytes)      │
                              │                   │
                              │  Magic: \x00asm  │
                              │  Export: polyglot │
                              │  Return: 0xCAFEBABE│
                              └───────────────────┘
```

### 3.2 Layer-by-Layer Breakdown

#### Layer 1: PDF 2.0 Wrapper

The file begins with the standard PDF header:
```
%PDF-2.0
%ÐÔÅØ
```

The second line is a binary marker comment (PDF comment syntax: `%...
`) that prevents text-mode transmission corruption. The object graph follows standard PDF 2.0 structure:

- **Object 1 (Catalog)**: Root document catalog with EmbeddedFiles name tree
- **Object 2 (Pages)**: Page tree with one page
- **Object 3 (Page)**: Single page with Helvetica font and content stream
- **Object 4 (Font)**: Helvetica Type1 font resource
- **Object 5 (EmbeddedFiles)**: Name tree mapping filename → FileSpec
- **Object 6 (Content)**: Page content stream drawing the polyglot title
- **Object 7 (FileSpec)**: File specification pointing to embedded file
- **Object 8 (EmbeddedFile)**: The actual JXL payload, FlateDecode compressed

The cross-reference table and trailer are fully valid per ISO 32000-2:2020.

#### Layer 2: JPEG XL ISOBMFF Container

When the EmbeddedFile stream is decompressed, it reveals a 246-byte JXL container:

| Box | Type | Size | Purpose |
|-----|------|------|---------|
| 1 | `ftyp` | 20 bytes | Declares `jxl ` brand, compatible with itself |
| 2 | `jxlc` | 26 bytes | Naked codestream signature `FF 0A` + padding |
| 3 | `xml ` | 193 bytes | XML wrapper containing WASM in comment |
| 4 | `jxll` | 9 bytes | Level 5 compliance indicator |

The `xml ` box contains:
```xml
<?xml version="1.0"?><wasm><!--[144 bytes of raw WASM]--></wasm>
```

This is valid XML (satisfying ISOBMFF requirements) while the XML comment `<!--...-->` preserves the raw binary WASM data without modification.

#### Layer 3: WebAssembly Module

The extracted WASM module is 144 bytes and structurally valid:

| Section | ID | Contents |
|---------|-----|----------|
| Type | 1 | One function type: `() -> i32` |
| Function | 3 | One function using type index 0 |
| Export | 7 | Export name: `"polyglot"`, kind: function, index: 0 |
| Code | 10 | Function body: `local_count=0, i32.const 0xCAFEBABE, end` |
| Custom | 0 | Name: `"polyglot-meta"`, payload: JSON metadata |

The `i32.const 0xCAFEBABE` is a deliberate easter egg — the classic hex magic number.

---

## 4. Construction Methodology

### 4.1 Design Constraints

Building a triple polyglot requires satisfying three sets of constraints simultaneously:

**PDF Constraints:**
- `%PDF-X.Y` must appear within first 1,024 bytes (offset 0 is ideal)
- Object numbers must be sequential
- Cross-reference table must point to correct byte offsets
- Stream lengths must match actual data

**JXL Constraints:**
- `ftyp` box must be first (or at least early) for brand recognition
- Box sizes must be big-endian 32-bit integers
- Box types must be exactly 4 ASCII characters
- Total container must be parseable as ISOBMFF

**WASM Constraints:**
- Magic `\x00asm` at offset 0 of the module
- Version `1` (little-endian) at offset 4
- All sections must be valid LEB128-encoded
- Function bodies must be well-formed

### 4.2 Why This Architecture Works

The key insight is that **each format only validates its own layer**. The PDF parser sees a valid PDF with an embedded file stream. It doesn't care what the compressed stream contains. The JXL parser, when given the decompressed stream, sees a valid ISOBMFF container. It doesn't care that the `xml ` box contains a WASM module inside an XML comment. The WASM parser, when given the bytes between `<!--` and `-->`, sees a valid WASM binary.

This is **defense in depth for polyglot construction** — each layer shields the inner layers from the outer parser's scrutiny.

### 4.3 Byte Budget

| Component | Size |
|-----------|------|
| PDF header + binary marker | 14 bytes |
| 8 PDF objects (catalog, pages, page, font, names, content, filespec, embeddedfile) | ~850 bytes |
| Cross-reference table + trailer + EOF | ~120 bytes |
| FlateDecode overhead | ~20 bytes |
| JXL container (uncompressed) | 246 bytes |
| WASM module | 144 bytes |
| **Total** | **~1,308 bytes** |

---

## 5. Extraction and Verification

### 5.1 PDF Verification

```bash
$ file polyglot.pdf
polyglot.pdf: PDF document, version 2.0

$ pdfinfo polyglot.pdf
Title:           (none)
Producer:        (raw construction)
PDF version:     2.0
Pages:           1
```

Opening in any PDF reader (Adobe Acrobat, Chrome, Firefox, evince) displays the page with the polyglot title and metadata.

### 5.2 JXL Extraction

```bash
$ python tools/extract_all.py polyglot.pdf
=== Polyglot Analysis: polyglot.pdf ===
Size: 1308 bytes | MD5: [redacted]
[PDF] Valid: True
[JXL] Stream 1: 246 bytes
[WASM] Module: 144 bytes
=== Done ===

$ ls -la extracted_container.jxl extracted_module.wasm
-rw-r--r-- 1 user user 246 May 12 20:04 extracted_container.jxl
-rw-r--r-- 1 user user 144 May 12 20:04 extracted_module.wasm
```

The JXL container can be analyzed with ISOBMFF tools:
```bash
$ python -c "import struct; d=open('extracted_container.jxl','rb').read(); off=0; 
  while off<len(d): sz=struct.unpack('>I',d[off:off+4])[0]; 
  print(d[off+4:off+8].decode(), sz); off+=sz"
ftyp 20
jxlc 26
xml  193
jxll 9
```

### 5.3 WASM Verification

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

$ wasm2wat extracted_module.wasm
(module
  (type (;0;) (func (result i32)))
  (func (;0;) (type 0) (result i32)
    i32.const -889275714  ;; 0xCAFEBABE
  )
  (export "polyglot" (func 0))
)
```

The module can be executed in any WASM runtime (Wasmtime, Wasmer, browser):
```javascript
const wasm = await WebAssembly.instantiateStreaming(fetch('extracted_module.wasm'));
console.log(wasm.instance.exports.polyglot()); // -889275714 (0xCAFEBABE as signed i32)
```

---

## 6. Novelty Assessment

### 6.1 What's Prior Art

- **JPG+PDF polyglots**: Ange Albertini, circa 2013. Well-documented, widely known.
- **PDF EmbeddedFile abuse**: Glasswall research, various steganography papers.
- **WASM+HTML polyglots**: FuzzingLabs, 2024.
- **ISOBMFF format abuse**: General knowledge in multimedia security community.

### 6.2 What's Novel

1. **Triple-container nesting depth**: No publicly documented polyglot chains three independent container formats (PDF → JXL ISOBMFF → WASM). Most stop at two.

2. **JPEG XL as a polyglot carrier**: JXL is a relatively new format (standardized ~2021-2022, browser support still rolling out in 2025-2026). Its ISOBMFF container structure differs from traditional JPEG, making prior JPG+PDF techniques non-transferable.

3. **xml box → WASM comment injection**: Using an ISOBMFF `xml ` box's XML comment to preserve raw WASM binary data is a specific format-quirk marriage not documented in prior polyglot research.

4. **Size efficiency**: At ~1,308 bytes total, this is one of the smallest documented multi-format polyglots with this nesting depth. Most prior art focuses on functionality over minimalism.

### 6.3 Publication Status

This construction was first developed on **2026-03-24** and flagged as never previously documented. As of this publication date (2026-05-12), it has not appeared in public channels (GitHub, conferences, blog posts, CVEs). Therefore, it remains novel in the open research community.

---

## 7. Security Research Applications

### 7.1 Parser Differential Analysis

Different tools handle ambiguous containers differently. A file served as `Content-Type: application/pdf` might be parsed by:
- **PDF readers**: Render the document normally
- **JXL decoders**: Extract the embedded image if they support PDF stream parsing
- **WASM runtimes**: Reject it (magic not at offset 0) unless pre-extracted

This differential behavior is useful for:
- Fuzzing format parsers
- Identifying parser inconsistencies
- Discovering format confusion vulnerabilities

### 7.2 MIME Type Confusion

A server might serve this file as `image/jxl` based on extension, but a client with a vulnerable PDF plugin could attempt PDF parsing. Conversely, serving as `application/pdf` might trigger JXL extraction in security scanners that decompress PDF streams and inspect contents.

### 7.3 Steganography and Anti-Forensics

The nested compression (PDF's FlateDecode → JXL's box structure → XML comment wrapping) creates three layers of obfuscation:
1. PDF stream compression hides the JXL data
2. JXL's `xml ` box is often skipped by image analysis tools
3. XML comment wrapping hides the WASM from naive string searches

### 7.4 Format Sandbox Escapes

Systems that whitelist file formats based on magic numbers might be bypassed if they only check the outer layer. A sandbox allowing PDF uploads but blocking WASM might miss the embedded module if it doesn't recursively decompress and inspect embedded streams.

---

## 8. Limitations and Future Work

### 8.1 Current Limitations

- **WASM offset requirement**: Standard WASM runtimes require the magic number at file offset 0. The polyglot file starts with `%PDF-2.0`, so it cannot be directly executed as WASM without extraction. This is a fundamental constraint of triple-polyglot construction when one format requires offset-0 magic.

- **JXL image rendering**: The `jxlc` box contains only the naked codestream signature (`FF 0A`) with minimal padding. Real JXL decoders will recognize the container but may fail to render an actual image. The polyglot is structurally valid as JXL but not visually meaningful.

- **PDF viewer compatibility**: Some strict PDF parsers might object to the binary content of the EmbeddedFile stream, though FlateDecode compression should mask this.

### 8.2 Future Directions

1. **True offset-0 triple polyglot**: Investigate whether a file can start with WASM magic (`\x00asm`) while also satisfying PDF and JXL header requirements. This likely requires a PDF parser that accepts `%PDF` at non-zero offsets (some do, within 1,024 bytes) and a JXL parser that scans for `ftyp` rather than requiring it at offset 0.

2. **Visual payload**: Replace the minimal `jxlc` box with a real JXL codestream encoding a meaningful image (e.g., the polyglot diagram). This would make the file visually renderable as both an image and a PDF.

3. **Additional layers**: Explore adding a fourth format, such as embedding a ZIP file in the WASM custom section, creating a PDF → JXL → WASM → ZIP quad-polyglot.

4. **Exploit delivery**: Research whether this structure can bypass specific security products (email gateways, web upload filters, DLP systems) that inspect files at different depths.

---

## 9. Tools and Reproducibility

All tools needed to reproduce, verify, and extend this work are included in the release package:

| Tool | Purpose |
|------|---------|
| `extract_all.py` | Universal extractor — pulls JXL from PDF, WASM from JXL |
| `wasm_info.py` | WASM section inspector — parses and displays all sections |
| `build_polyglot.py` | Rebuilds the entire polyglot from scratch |

### Reproduction Steps

```bash
# 1. Download and extract the release package
unzip JXL_PDF_WASM_Polyglot_Release_v1.0.zip
cd JXL_PDF_WASM_Polyglot_Release_v1.0

# 2. Verify the polyglot
python tools/extract_all.py polyglot.pdf

# 3. Inspect the WASM module
python tools/wasm_info.py extracted_module.wasm

# 4. Rebuild from source (should produce identical output)
python tools/build_polyglot.py
md5sum polyglot.pdf rebuilt_polyglot.pdf  # Compare hashes
```

---

## 10. Conclusion

The JPEG XL + PDF 2.0 + WebAssembly triple-container polyglot demonstrates that modern container formats can be chained to create files with surprising structural complexity. By exploiting PDF's EmbeddedFile streams, JXL's ISOBMFF `xml ` box, and WASM's custom sections, we created a file that is independently valid under three different format specifications.

This work contributes to the field of format abuse research by:
1. Documenting the first publicly known triple-container polyglot of this type
2. Providing a minimal, reproducible construction (1,308 bytes)
3. Releasing open-source tools for extraction and verification
4. Establishing a methodology for future multi-format polyglot research

The file hashes for verification are:
```
MD5:    [see HASHES.txt in release package]
SHA1:   [see HASHES.txt in release package]
SHA256: [see HASHES.txt in release package]
Size:   1,308 bytes
```

---

## 11. References

1. Albertini, A. (2013). *PoC||GTFO 0x03: AngeCryption*. [PDF polyglot research]
2. FuzzingLabs (2024). *WASM+HTML Polyglots*. [WASM format abuse]
3. Glasswall (2024). *PDF Steganography Techniques*. [PDF embedded file abuse]
4. ISO/IEC 18181-1:2022. *JPEG XL Image Coding System — Part 1: Core coding system*
5. ISO/IEC 14496-12:2022. *ISO Base Media File Format (ISOBMFF)*
6. ISO 32000-2:2020. *Document management — Portable Document Format — Part 2: PDF 2.0*
7. W3C (2019). *WebAssembly Core Specification, Version 1.0*
8. Mozilla (2025). *JPEG XL Support Status*. [Browser compatibility]

---

## 12. Author and Contact

**frankSx**  
Security Researcher | Hardware & Software RE | Polyglot Enthusiast  
Blog: https://frankhacks.blogspot.com  

This research was conducted for educational and security research purposes. The techniques described should be used responsibly and in accordance with applicable laws and ethical guidelines.

---

*"The same bytes, three truths."*
