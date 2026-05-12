#!/usr/bin/env python3
import sys, zlib, re, struct, hashlib

def analyze(filepath):
    with open(filepath, "rb") as f: data = f.read()
    print(f"=== Polyglot Analysis: {filepath} ===")
    print(f"Size: {len(data)} bytes | MD5: {hashlib.md5(data).hexdigest()}")
    print(f"[PDF] Valid: {data[:8] == b'%PDF-2.0'}")

    streams = re.findall(b'stream
(.+?)
endstream', data, re.DOTALL)
    for i,s in enumerate(streams):
        try:
            dec = zlib.decompress(s)
            if dec[4:8] == b'ftyp':
                print(f"[JXL] Stream {i}: {len(dec)} bytes")
                open("extracted_container.jxl","wb").write(dec)
                off=0
                while off < len(dec):
                    sz = struct.unpack('>I', dec[off:off+4])[0]
                    bt = dec[off+4:off+8]
                    if bt == b'xml ':
                        xml = dec[off+8:off+sz]
                        ws, we = xml.find(b'<!--'), xml.find(b'-->')
                        if ws!=-1 and we!=-1:
                            wasm = xml[ws+4:we]
                            print(f"[WASM] Module: {len(wasm)} bytes")
                            open("extracted_module.wasm","wb").write(wasm)
                            break
                    off += sz
        except: pass
    print("=== Done ===")

if __name__ == "__main__":
    analyze(sys.argv[1]) if len(sys.argv)>1 else print("Usage: extract_all.py <file>")
