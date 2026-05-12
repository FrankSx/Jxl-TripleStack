#!/usr/bin/env python3
import sys, struct

def decode_leb128(data, offset):
    result, shift = 0, 0
    while True:
        byte = data[offset]
        result |= (byte & 0x7f) << shift
        offset += 1
        if (byte & 0x80) == 0: break
        shift += 7
    return result, offset

def inspect(filepath):
    with open(filepath, "rb") as f: data = f.read()
    print(f"WASM: {filepath} ({len(data)} bytes)")
    if data[:4] != b'\x00asm':
        print("Invalid magic!"); return
    print(f"Version: {struct.unpack('<I', data[4:8])[0]}")
    off = 8
    names = {0:"Custom",1:"Type",3:"Function",7:"Export",10:"Code"}
    while off < len(data):
        sid = data[off]; off += 1
        size, off = decode_leb128(data, off)
        sd = data[off:off+size]; off += size
        print(f"  {names.get(sid, sid)}: {size} bytes")
        if sid == 7:
            cnt, pos = decode_leb128(sd, 0)
            for _ in range(cnt):
                nl, pos = decode_leb128(sd, pos)
                name = sd[pos:pos+nl].decode(); pos += nl
                kind = sd[pos]; pos += 2
                print(f"    Export: {name}")
        if sid == 0:
            nl, pos = decode_leb128(sd, 0)
            print(f"    Custom: {sd[pos:pos+nl].decode()}")

if __name__ == "__main__":
    inspect(sys.argv[1]) if len(sys.argv)>1 else print("Usage: wasm_info.py <file>")
