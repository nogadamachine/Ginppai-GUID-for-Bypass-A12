# Ginppai-GUID-for-Bypass-A12

iOS A12 계열 기기에서 **Books(iBooks) 앱 컨테이너 GUID**를 로그 기반으로 추출하는 도구입니다.
A12 바이패스 과정에서 필요한 GUID를 자동으로 수집·분석합니다.

---

## 개요

이 프로젝트는 다음 작업을 자동화합니다.

- 연결된 iOS 기기 감지 (UDID 자동 탐색)
- `pymobiledevice3`를 이용한 시스템 로그 수집
- 로그 아카이브에서 Books 관련 컨테이너 GUID 탐색
- 가장 신뢰도 높은 GUID 1개를 결과로 출력

추출된 GUID는 **A12 바이패스 과정**에서 사용됩니다.

---

## 파일 구성

```
Ginppai-GUID-for-bypass-A12/
├── ginppai_guid.py
└── README.md
```

---

## 요구 사항

- Python 3.8 이상
- macOS / Linux  
  (Windows 사용 시 libimobiledevice 별도 구성 필요)
- iOS A12 계열 기기
- 아래 도구가 PATH에 등록되어 있어야 함
  - `pymobiledevice3`
  - `ideviceinfo` (libimobiledevice)

---

## 사전 준비

### pymobiledevice3 설치
```bash
pip install pymobiledevice3
```

### libimobiledevice 설치 (macOS)
```bash
brew install libimobiledevice
```

설치 확인
```bash
ideviceinfo
```

정상적으로 기기 정보가 출력되어야 합니다.

---

## 사용 방법

### UDID 자동 감지
```bash
python3 ginppai_guid.py
```

### UDID 직접 지정
```bash
python3 ginppai_guid.py <UDID>
```

### 상세 로그 출력
```bash
python3 ginppai_guid.py -v
```

또는
```bash
python3 ginppai_guid.py <UDID> --verbose
```

---

## 실행 결과 예시

```
============================================================
iOS A12 바이패스 - GUID 추출 도구
============================================================

연결된 기기 자동 탐색 중...

============================================================
✓ GUID 추출 성공: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
============================================================

이 GUID는 A12 바이패스 과정에서 사용됩니다.
Books 앱 컨테이너를 식별하는 값입니다.
```

---

## GUID를 찾지 못하는 경우

다음 원인이 있을 수 있습니다.

1. Books / iBooks 앱 사용 이력이 없음
2. 로그에 BLDatabaseManager 항목이 존재하지 않음
3. iOS 버전 변경으로 로그 구조가 변경됨

권장 조치:

- Books 앱을 한 번 실행한 후 재시도
- 기기 재부팅 후 재시도
- `-v` 옵션으로 상세 로그 확인

---

## 주의 사항

- 기기는 반드시 **신뢰된 상태**여야 합니다.
- 실행 중 생성되는 `.logarchive` 파일은 자동으로 정리됩니다.
- 본 프로젝트는 **연구·개발 목적**으로 제공됩니다.
- 불법 행위 및 그로 인한 책임은 사용자 본인에게 있습니다.

---

## 프로젝트 정보

- Project: **Ginppai-GUID-for-Bypass-A12**
- Main Script: **ginppai_guid.py**
- Purpose: iOS A12 Bypass용 Books 컨테이너 GUID 추출
