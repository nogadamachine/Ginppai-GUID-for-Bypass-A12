#!/usr/bin/env python3
import os
import re
import sys
import shutil
import subprocess
from collections import Counter

GUID_RE = re.compile(rb"[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}", re.I)
GUID_OK_RE = re.compile(r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$")
NEEDLES = [
    b"/Documents/BLDatabaseManager",
    b"BLDatabaseManager",
    b"SystemGroup",
    b"bookassetd",
    b"BLDatabase",
]
PATH_PATTERNS = [
    re.compile(r"/SystemGroup/([0-9A-F\-]{36})/", re.I),
    re.compile(r"SystemGroup[^/]*/([0-9A-F\-]{36})", re.I),
    re.compile(r"file://[^/]*SystemGroup[^/]*/([0-9A-F\-]{36})", re.I),
]

def _run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

def _find_ideviceinfo():
    p = shutil.which("ideviceinfo")
    if p:
        return p
    base = os.path.join(os.path.dirname(__file__), "tools", "libimobiledevice")
    exe = os.path.join(base, "ideviceinfo.exe")
    return exe if os.path.exists(exe) else None

def _detect_udid():
    idev = _find_ideviceinfo()
    if not idev:
        raise Exception("ideviceinfo를 찾을 수 없고 UDID도 지정되지 않았습니다")
    r = _run([idev, "-k", "UniqueDeviceID"], 10)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    r = _run([idev], 10)
    if r.returncode != 0:
        raise Exception("연결된 기기가 없거나 UDID를 찾을 수 없습니다")
    for line in r.stdout.splitlines():
        if "UniqueDeviceID" in line and ": " in line:
            v = line.split(": ", 1)[1].strip()
            if v:
                return v
    raise Exception("연결된 기기가 없거나 UDID를 찾을 수 없습니다")

def _collect_logs(udid, log_path, verbose):
    if os.path.exists(log_path):
        shutil.rmtree(log_path)
    if verbose:
        print(f"[정보] 기기 로그 수집 중: {udid}")
    r = _run(["pymobiledevice3", "syslog", "collect", log_path], 120)
    if r.returncode != 0 or not os.path.exists(log_path):
        raise Exception("로그 수집 실패")

def _gather_log_files(log_path, max_files=100):
    files = []
    trace = os.path.join(log_path, "logdata.LiveData.tracev3")
    if os.path.exists(trace):
        files.append(trace)
    exts = (".log", ".txt", ".plist", ".trace")
    for root, _, fnames in os.walk(log_path):
        for fn in fnames:
            if len(files) >= max_files:
                return files
            if fn.lower().endswith(exts):
                files.append(os.path.join(root, fn))
    return files

def _read_all(files, max_size=100 * 1024 * 1024, verbose=False):
    bufs, total = [], 0
    if verbose:
        print(f"[정보] 로그 파일 읽는 중 ({len(files)}개)")
    for i, f in enumerate(files, 1):
        try:
            sz = os.path.getsize(f)
            if total + sz > max_size:
                continue
            with open(f, "rb") as fp:
                bufs.append(fp.read())
            total += sz
            if verbose and i % 50 == 0:
                print(f"  진행: {i}/{len(files)} ({total/1024/1024:.1f} MB)")
        except Exception:
            continue
    if not bufs:
        raise Exception("로그 데이터를 읽을 수 없습니다")
    if verbose:
        print(f"[정보] 총 로그 용량: {total/1024/1024:.1f} MB")
    return b"".join(bufs)

def _extract_from_data(data, verbose=False):
    candidates, seen = [], set()
    win = 2048

    if verbose:
        print("[정보] GUID 패턴 검색 중")

    for needle in NEEDLES:
        if verbose:
            print(f"  키워드 검색: {needle.decode('ascii', errors='ignore')}")
        pos = 0
        while True:
            pos = data.find(needle, pos)
            if pos == -1:
                break
            s = max(0, pos - win)
            e = min(len(data), pos + len(needle) + win)
            for raw in GUID_RE.findall(data[s:e]):
                g = raw.decode("ascii", errors="ignore").upper()
                if GUID_OK_RE.match(g) and g not in seen:
                    seen.add(g)
                    candidates.append(g)
            pos += len(needle)

    if verbose:
        print("[정보] 경로 기반 GUID 검색 중")

    if len(candidates) < 5:
        try:
            chunk = 10 * 1024 * 1024
            text = []
            for i in range(0, len(data), chunk):
                text.append(data[i:i+chunk].decode("utf-8", errors="ignore"))
            text = "".join(text)
            for pat in PATH_PATTERNS:
                for g in pat.findall(text):
                    g = g.upper()
                    if GUID_OK_RE.match(g) and g not in seen:
                        seen.add(g)
                        candidates.append(g)
        except Exception:
            pass

    if not candidates:
        return None

    return Counter(candidates).most_common(1)[0][0]

def extract_guid_from_device(udid=None, cleanup=True, verbose=False):
    if udid is None:
        udid = _detect_udid()

    log_path = f"{udid}.logarchive"
    _collect_logs(udid, log_path, verbose)

    log_files = _gather_log_files(log_path)
    if not log_files:
        raise Exception("로그 파일을 찾을 수 없습니다")

    try:
        data = _read_all(log_files, verbose=verbose)
        return _extract_from_data(data, verbose=verbose)
    finally:
        if cleanup and os.path.exists(log_path):
            shutil.rmtree(log_path, ignore_errors=True)

def main():
    import time
    t0 = time.time()

    verbose = any(a in ("-v", "--verbose") for a in sys.argv[1:])
    udid = next((a for a in sys.argv[1:] if a not in ("-v", "--verbose")), None)

    print("=" * 60)
    print("iOS A12 바이패스 - GUID 추출 도구")
    print("=" * 60)
    print()
    print(f"기기 UDID: {udid}" if udid else "연결된 기기 자동 탐색 중...")
    print()

    try:
        t1 = time.time()
        guid = extract_guid_from_device(udid=udid, cleanup=True, verbose=verbose)
        dt = time.time() - t1

        if not guid:
            print("=" * 60)
            print("✗ GUID를 찾지 못했습니다")
            print("=" * 60)
            print()
            print("가능한 원인:")
            print("1. Books / iBooks 앱 사용 이력이 없음")
            print("2. 로그에 BLDatabaseManager 항목이 없음")
            print("3. GUID 형식 또는 위치가 변경됨")
            sys.exit(1)

        print()
        print("=" * 60)
        print(f"✓ GUID 추출 성공: {guid}")
        print("=" * 60)
        print()
        print("이 GUID는 A12 바이패스 과정에서 사용됩니다.")
        print("Books 앱 컨테이너를 식별하는 값입니다.")

        if verbose:
            print("\n성능 정보:")
            print(f"  GUID 추출 시간: {dt:.1f}초")
            print(f"  총 실행 시간: {time.time() - t0:.1f}초")

    except Exception as e:
        print(f"[오류] GUID 추출 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()