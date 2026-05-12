#!/usr/bin/env python3
import struct, zlib

def leb128(n):
    r = bytearray()
    while True:
        b = n & 0x7f; n >>= 7
        if n: b |= 0x80
        r.append(b)
        if not n: break
    return bytes(r)

def sleb128(n):
    r = bytearray(); more = True
    while more:
        b = n & 0x7f; n >>= 7
        if (n == 0 and not (b & 0x40)) or (n == -1 and (b & 0x40)): more = False
        else: b |= 0x80
        r.append(b)
    return bytes(r)

def build_wasm():
    w = bytearray(b'\x00asm' + struct.pack('<I', 1))
    ts = bytes([0x01,0x60,0x00,0x01,0x7f])
    w += bytes([0x01]) + leb128(len(ts)) + ts
    w += bytes([0x03]) + leb128(2) + bytes([0x01,0x00])
    es = leb128(8) + b'polyglot' + bytes([0x00,0x00])
    w += bytes([0x07]) + leb128(len(es)) + es
    fb = bytes([0x00,0x41]) + sleb128(-889275714) + bytes([0x0b])
    w += bytes([0x0a]) + leb128(len(fb)+1) + bytes([0x01]) + leb128(len(fb)) + fb
    cn = b'polyglot-meta'; cp = b'{"format":"JPEG-XL+PDF+WASM","version":"1.0"}'
    cs = leb128(len(cn)) + cn + cp
    w += bytes([0x00]) + leb128(len(cs)) + cs
    return bytes(w)

def build_jxl(wasm):
    c = bytearray()
    c += struct.pack('>I', 20) + b'ftyp' + b'jxl \x00\x00\x00\x00jxl '
    c += struct.pack('>I', 26) + b'jxlc' + bytes([0xFF,0x0A]+[0x00]*14)
    xml = b'<?xml version="1.0"?><wasm><!--' + wasm + b'--></wasm>'
    c += struct.pack('>I', len(xml)+8) + b'xml ' + xml
    c += struct.pack('>I', 9) + b'jxll' + b'\x05'
    return bytes(c)

def build_pdf(jxl):
    pdf = bytearray(b'%PDF-2.0\n%\xd0\xd4\xc5\xd8\n')
    o1 = b'1 0 obj\n<</Type/Catalog/Pages 2 0 R/Names<</EmbeddedFiles 5 0 R>>>>\nendobj\n'
    o2 = b'2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n'
    pc = b'BT\n/F1 20 Tf\n72 720 Td\n(JXL+PDF+WASM Polyglot) Tj\n0 -25 Td\n/F1 10 Tf\n(Author: frankSx | 2026-05-12) Tj\nET\n'
    o3 = b'3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 4 0 R>>>>/Contents 6 0 R>>\nendobj\n'
    o4 = b'4 0 obj\n<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>\nendobj\n'
    o5 = b'5 0 obj\n<</Names[(polyglot.jxl) 7 0 R]>>\nendobj\n'
    o6 = b'6 0 obj\n<</Length ' + str(len(pc)).encode() + b'>>\nstream\n' + pc + b'\nendstream\nendobj\n'
    o7 = b'7 0 obj\n<</Type/Filespec/F(polyglot.jxl)/UF(polyglot.jxl)/EF<</F 8 0 R>>>>\nendobj\n'
    cj = zlib.compress(jxl, 9); ck = zlib.crc32(jxl) & 0xFFFFFFFF
    d = b'<</Type/EmbeddedFile/Subtype/image#2Fjxl/Length ' + str(len(cj)).encode() + b'/Filter/FlateDecode/Params<</Size ' + str(len(jxl)).encode() + b'/CheckSum<' + format(ck,'08X').encode() + b'>>>>>'
    o8 = b'8 0 obj\n' + d + b'\nstream\n' + cj + b'\nendstream\nendobj\n'
    objs = [o1,o2,o3,o4,o5,o6,o7,o8]
    offs = []; cur = len(pdf)
    for o in objs: offs.append(cur); cur += len(o)
    xs = cur
    xref = b'xref\n0 9\n0000000000 65535 f \n' + b''.join(f'{o:010d} 00000 n \n'.encode() for o in offs)
    tr = b'trailer\n<</Size 9/Root 1 0 R/ID[<DEADBEEF202605120001><CAFEBABE202605120002>]>>\n'
    eof = b'startxref\n' + str(xs).encode() + b'\n%%EOF\n'
    for o in objs: pdf += o
    pdf += xref + tr + eof
    return bytes(pdf)

if __name__ == "__main__":
    w = build_wasm(); j = build_jxl(w); p = build_pdf(j)
    for fn in ["polyglot.pdf","polyglot.jxl","polyglot.wasm"]:
        open(fn, "wb").write(p)
    print(f"Built: {len(p)} bytes")
