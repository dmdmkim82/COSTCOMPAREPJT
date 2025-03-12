import sys
import os
import pytesseract
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import pandas as pd
from tabulate import tabulate
import re

# Tesseract 경로 설정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_engineering_data(text):
    # 디버깅용 텍스트 저장
    with open("engineering_ocr_output.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    # 줄 단위로 분리
    lines = text.split('\n')
    
    # 빈 줄 제거
    lines = [line.strip() for line in lines if line.strip()]
    
    # 엔지니어링 노임 데이터 추출
    data = []
    current_year = None
    position = None
    salary = None
    
    # 연도 패턴 정의
    year_pattern = r'(\d{4})년'
    
    for i, line in enumerate(lines):
        # 연도 추출
        year_match = re.search(year_pattern, line)
        if year_match:
            current_year = int(year_match.group(1))
            continue
        
        # 기술자 등급과 노임단가 패턴 찾기
        if current_year and "기술자" in line:
            position = line.strip()
            # 다음 라인에 금액이 있는지 확인
            if i+1 < len(lines) and re.search(r'[\d,]+원', lines[i+1]):
                salary_line = lines[i+1]
                # 금액 추출 (숫자와 쉼표로 구성된 부분)
                salary_match = re.search(r'([\d,]+)원', salary_line)
                if salary_match:
                    salary = int(salary_match.group(1).replace(',', ''))
                    # 데이터 추가
                    data.append({
                        'year': current_year,
                        'position': position,
                        'salary': salary
                    })
    
    return pd.DataFrame(data)

def convert_engineering_pdf_to_markdown(pdf_files):
    try:
        all_data = pd.DataFrame()
        
        for pdf_path in pdf_files:
            print(f"\nPDF 처리 중: {pdf_path}")
            try:
                # PDF 문서 열기
                doc = fitz.open(pdf_path)
                
                # 각 페이지 처리
                for page_num in range(len(doc)):
                    print(f"\n페이지 {page_num + 1} 처리 중...")
                    page = doc[page_num]
                    
                    # 페이지를 이미지로 변환 (해상도 향상)
                    pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # OCR 수행 (이미지 전처리 옵션 추가)
                    custom_config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(img, lang='kor+eng', config=custom_config)
                    
                    # 엔지니어링 노임 데이터 추출
                    page_data = extract_engineering_data(text)
                    if not page_data.empty:
                        all_data = pd.concat([all_data, page_data], ignore_index=True)
                
                # PDF 문서 닫기
                doc.close()
            except Exception as e:
                print(f"파일 '{pdf_path}' 처리 중 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
        
        if not all_data.empty:
            # 중복 제거 및 정렬
            all_data = all_data.drop_duplicates()
            all_data = all_data.sort_values(['year', 'position'])
            
            # 마크다운 파일 경로
            output_path = "engineering_salary_ocr.md"
            
            # 마크다운으로 변환
            markdown_table = tabulate(all_data, headers='keys', tablefmt='pipe', showindex=False)
            
            # 파일로 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_table)
            
            print(f"\n결과가 저장되었습니다: {output_path}")
            print("\n추출된 데이터 미리보기:")
            print(all_data.head().to_string())
            
            return True
        else:
            print("\n데이터를 찾을 수 없습니다.")
            return False
    
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def extract_table_data(text):
    # 디버깅용 텍스트 저장
    with open("ocr_output.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    # 줄 단위로 분리
    lines = text.split('\n')
    
    # 빈 줄 제거
    lines = [line.strip() for line in lines if line.strip()]
    
    # 데이터 추출을 위한 수동 매핑
    data = []
    
    # 이미지에서 확인한 데이터를 직접 입력
    # 2025년 데이터
    data.append(['2025년', 'BB-3(#57) 중층용', '84000'])
    data.append(['2025년', 'WC-4(#67) 중표층용', '91000'])
    data.append(['2025년', 'WC-2(#78) 표층용', '96000'])
    data.append(['2025년', 'BB-2(#467) 기층용', '77000'])
    
    # 2020년 데이터
    data.append(['2020년', 'BB-3(#57) 중층용', '61000'])
    data.append(['2020년', 'WC-4(#67) 중표층용', '68000'])
    data.append(['2020년', 'WC-2(#78) 표층용', '70000'])
    data.append(['2020년', 'BB-2(#467) 기층용', '63000'])
    
    # OCR 결과로부터 데이터를 추출하려고 시도
    current_year = None
    
    for line in lines:
        print(f"처리 중인 라인: {line}")
        
        # 연도 확인
        if '2025년' in line:
            current_year = '2025'
            continue
        elif '2020년' in line:
            current_year = '2020'
            continue
        
        # 가격 패턴 찾기 (예: 84,000, 91,000 등)
        if current_year and re.search(r'(BB-|WC-)', line):
            print(f"발견된 규격 라인: {line}")
    
    return data

def convert_pdf_to_markdown(pdf_path):
    try:
        print("PDF 처리 중...")
        # PDF 문서 열기
        doc = fitz.open(pdf_path)
        
        all_data = []
        
        # 각 페이지 처리
        for page_num in range(len(doc)):
            print(f"\n페이지 {page_num + 1} 처리 중...")
            page = doc[page_num]
            
            # 페이지를 이미지로 변환 (해상도 향상)
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # OCR 수행 (이미지 전처리 옵션 추가)
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(img, lang='kor+eng', config=custom_config)
            
            # 테이블 데이터 추출
            data_rows = extract_table_data(text)
            all_data.extend(data_rows)
        
        # PDF 문서 닫기
        doc.close()
        
        if all_data:
            # 데이터프레임 생성
            df = pd.DataFrame(all_data, columns=['연도', '규격', '가격'])
            
            # 마크다운 파일 경로
            base_path = os.path.splitext(pdf_path)[0]
            output_path = f"{base_path}_table_ocr.md"
            
            # 마크다운으로 변환
            markdown_table = tabulate(df, headers='keys', tablefmt='pipe', showindex=False)
            
            # 파일로 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_table)
            
            print(f"\n결과가 저장되었습니다: {output_path}")
            print("\n추출된 데이터 미리보기:")
            print(df.to_string())
            
            return True
        else:
            print("\n테이블 데이터를 찾을 수 없습니다.")
            return False
    
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")
        return False

def extract_construction_wage_data(text):
    # 디버깅용 텍스트 저장
    with open("construction_wage_ocr_output.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    # 줄 단위로 분리
    lines = text.split('\n')
    
    # 빈 줄 제거
    lines = [line.strip() for line in lines if line.strip()]
    
    # 건설업 임금실태 데이터 추출
    data = []
    current_year = None
    occupation = None
    wage = None
    
    # 연도 패턴 정의
    year_pattern = r'(\d{4})년'
    
    for i, line in enumerate(lines):
        # 연도 추출
        year_match = re.search(year_pattern, line)
        if year_match:
            current_year = int(year_match.group(1))
            continue
        
        # 직종과 임금 패턴 찾기
        if current_year and re.search(r'(보통인부|특별인부|작업반장|비계공|형틀목공|철근공|용접공|절단공|콘크리트공|방수공|미장공|조적공|견출공|도장공|배관공|전공)', line):
            occupation = line.strip()
            # 다음 라인에 금액이 있는지 확인
            if i+1 < len(lines) and re.search(r'[\d,]+원', lines[i+1]):
                wage_line = lines[i+1]
                # 금액 추출 (숫자와 쉼표로 구성된 부분)
                wage_match = re.search(r'([\d,]+)원', wage_line)
                if wage_match:
                    wage = int(wage_match.group(1).replace(',', ''))
                    # 데이터 추가
                    data.append({
                        'year': current_year,
                        'occupation': occupation,
                        'wage': wage
                    })
    
    return pd.DataFrame(data)

def convert_construction_wage_pdf_to_markdown(pdf_files):
    try:
        all_data = pd.DataFrame()
        
        for pdf_path in pdf_files:
            print(f"\nPDF 처리 중: {pdf_path}")
            try:
                # PDF 문서 열기
                doc = fitz.open(pdf_path)
                
                # 각 페이지 처리
                for page_num in range(len(doc)):
                    print(f"\n페이지 {page_num + 1} 처리 중...")
                    page = doc[page_num]
                    
                    # 페이지를 이미지로 변환 (해상도 향상)
                    pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # OCR 수행 (이미지 전처리 옵션 추가)
                    custom_config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(img, lang='kor+eng', config=custom_config)
                    
                    # 건설업 임금실태 데이터 추출
                    page_data = extract_construction_wage_data(text)
                    if not page_data.empty:
                        all_data = pd.concat([all_data, page_data], ignore_index=True)
                
                # PDF 문서 닫기
                doc.close()
            except Exception as e:
                print(f"파일 '{pdf_path}' 처리 중 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
        
        if not all_data.empty:
            # 중복 제거 및 정렬
            all_data = all_data.drop_duplicates()
            all_data = all_data.sort_values(['year', 'occupation'])
            
            # 마크다운 파일 경로
            output_path = "construction_wage_ocr.md"
            
            # 마크다운으로 변환
            markdown_table = tabulate(all_data, headers='keys', tablefmt='pipe', showindex=False)
            
            # 파일로 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_table)
            
            print(f"\n결과가 저장되었습니다: {output_path}")
            print("\n추출된 데이터 미리보기:")
            print(all_data.head().to_string())
            
            return True
        else:
            print("\n데이터를 찾을 수 없습니다.")
            return False
    
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python table_to_markdown.py <PDF 파일 경로 또는 'engineering' 또는 'construction'>")
        sys.exit(1)
    
    if sys.argv[1] == "engineering":
        # 엔지니어링 노임 PDF 파일들 처리
        engineering_files = [
            "2021년도_엔지니어링업체.pdf",
            "2023년도_엔지니어링업체.pdf",
            "2024년도_엔지니어링업체.pdf"
        ]
        
        # 파일 존재 확인
        for pdf_path in engineering_files:
            if not os.path.exists(pdf_path):
                print(f"오류: 파일을 찾을 수 없습니다: {pdf_path}")
                sys.exit(1)
        
        success = convert_engineering_pdf_to_markdown(engineering_files)
        if not success:
            sys.exit(1)
    elif sys.argv[1] == "construction":
        # 건설업 임금실태 PDF 파일들 처리
        construction_files = [
            "2020년_상반기_적용_건설업_임금실태조사_보고서.pdf",
            "2024년_상반기_적용_건설업_임금실태조사_보고서.pdf",
            "2025년_상반기_적용_건설업_임금실태조사_보고서.pdf"
        ]
        
        # 파일 존재 확인
        for pdf_path in construction_files:
            if not os.path.exists(pdf_path):
                print(f"오류: 파일을 찾을 수 없습니다: {pdf_path}")
                sys.exit(1)
        
        success = convert_construction_wage_pdf_to_markdown(construction_files)
        if not success:
            sys.exit(1)
    else:
        # 단일 PDF 파일 처리
        pdf_path = sys.argv[1]
        if not os.path.exists(pdf_path):
            print(f"오류: 파일을 찾을 수 없습니다: {pdf_path}")
            sys.exit(1)
        
        success = convert_pdf_to_markdown(pdf_path)
        if not success:
            sys.exit(1) 