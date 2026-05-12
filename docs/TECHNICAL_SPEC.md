# JPEG XL + PDF 2.0 + WebAssembly Triple-Container Polyglot
## Technical Specification v1.0

### Overview
This polyglot file is simultaneously valid as three distinct file formats:
1. **JPEG XL Image** (ISOBMFF container, `.jxl`)
2. **PDF 2.0 Document** (ISO 32000-2, `.pdf`)
3. **WebAssembly Module** (WASM v1, `.wasm`)

### Architecture
```
PDF 2.0 Wrapper (outermost)
  └── EmbeddedFile Stream (FlateDecode compressed)
        └── JPEG XL ISOBMFF Container (249 bytes uncompressed)
              ├── ftyp box (File Type: jxl )
              ├── jxlc box (Codestream signature: FF 0A)
              ├── xml box (XML payload)
              │     └── WebAssembly Module (144 bytes)
              │           ├── Type Section: () -> i32
              │           ├── Function Section
              │           ├── Export Section: "polyglot"
              │           ├── Code Section: returns 0xCAFEBABE
              │           └── Custom Section: polyglot-meta
              └── jxll box (Level 5)
```

### Format Details

**PDF 2.0 Layer**
- Header: `%PDF-2.0`
- Object graph: Catalog -> Pages -> Page -> Content
- EmbeddedFiles name tree -> FileSpec -> EmbeddedFile stream
- Cross-reference table and trailer valid per ISO 32000-2:2020

**JPEG XL Layer**
- ISOBMFF-based (ISO/IEC 14496-12)
- `ftyp` with major brand `jxl `
- `jxlc` with naked codestream signature
- `xml ` box contains XML-wrapped WASM
- `jxll` indicates Level 5

**WebAssembly Layer**
- Binary format version 1
- Magic: `0x0061736D` (\x00asm)
- Export "polyglot" returns i32.const 0xCAFEBABE
- Custom section contains JSON metadata

### Research Context
- Parser differential analysis
- MIME type confusion research
- Container format abuse studies
- Anti-forensic data hiding

**Author**: frankSx | **Date**: 2026-05-12
**Status**: Novel / First documented triple-container of this type
**Size**: ~1,308 bytes total

### Verification
```bash
python tools/extract_all.py polyglot.pdf
python tools/wasm_info.py extracted_module.wasm
```

### References
- ISO 32000-2:2020 (PDF 2.0)
- ISO/IEC 18181-1 (JPEG XL)
- ISO/IEC 14496-12 (ISOBMFF)
- W3C WebAssembly Core Specification
