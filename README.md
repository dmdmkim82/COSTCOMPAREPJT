# 단가변동 시스템

건설 자재 및 인력 단가의 변동 추이를 분석하고 시각화하는 대시보드 애플리케이션입니다.

## 주요 기능

- **전기자재**: 케이블 사이즈별 가격 변동 분석
- **토목자재**: 아스팔트 콘크리트 규격별 가격 변동 분석
- **엔지니어링노임**: 기술자 등급별 노임단가 변동 분석
- **건설업 임금실태**: 직종별 임금 변동 분석

## 특징

- 연도별 가격 비교 및 추이 그래프
- 총 변동률 및 연평균 변동률 계산
- 품목별 가격 변동률 비교
- 폰트 크기 조절 기능

## 설치 및 실행 방법

1. 저장소 복제:
   ```bash
   git clone https://github.com/[사용자명]/[저장소명].git
   cd [저장소명]
   ```

2. 필요한 패키지 설치:
   ```bash
   pip install -r requirements.txt
   ```

3. 애플리케이션 실행:
   ```bash
   streamlit run app.py
   ```

## 데이터 소스

이 애플리케이션은 다음과 같은 데이터 파일을 사용합니다:
- onlycable.json: 전기 케이블 가격 데이터
- concre_table_ocr.md: 아스팔트 콘크리트 가격 데이터
- engineering_salary_ocr.md: 엔지니어링 노임단가 데이터
- construction_wage_ocr.md: 건설업 임금실태 데이터 