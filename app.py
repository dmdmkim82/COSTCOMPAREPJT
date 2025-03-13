import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import re
from datetime import datetime
import plotly.express as px

st.set_page_config(
    page_title="건설자재 가격비교",
    page_icon="⚡",
    layout="wide"
)

# 폰트 크기 설정 (CSS 스타일링에 사용될 기본값)
all_font_size = 16

# 스타일 적용
st.markdown(f"""
    <style>
    .main {{
        padding: 2rem;
    }}
    .stSelectbox, .stMultiSelect {{
        margin-bottom: 1rem;
    }}
    
    /* 전체 폰트 크기 조절 */
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, .stWidgetLabel, .st-emotion-cache-16txtl3 {{
        font-size: {all_font_size}px !important;
    }}
    
    /* 헤더는 상대적으로 크게 유지 */
    h1 {{
        font-size: {all_font_size + 10}px !important;
    }}
    h2 {{
        font-size: {all_font_size + 6}px !important;
    }}
    h3 {{
        font-size: {all_font_size + 4}px !important;
    }}
    
    /* 사이드바 폰트 사이즈 유지 */
    .sidebar .stMarkdown, .sidebar .stText, .sidebar p, .sidebar h1, .sidebar h2, .sidebar h3, .sidebar h4, .sidebar h5, .sidebar h6 {{
        font-size: 16px !important;
    }}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_process_data():
    try:
        # 전기 케이블 데이터 로드 (마크다운 파일에서)
        try:
            # 마크다운 파일에서 케이블 데이터 읽기
            with open('cable_data.md', 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 마크다운 테이블 파싱
            import re
            rows = re.findall(r'\|(.*?)\|', markdown_content)
            
            # 헤더와 구분선 건너뛰기
            rows = [row for row in rows if '----' not in row]
            if len(rows) > 1:  # 헤더와 데이터 행이 있는 경우
                # 헤더 파싱
                headers = [h.strip() for h in rows[0].split('|')]
                
                # 데이터 행 파싱
                data = []
                for row in rows[1:]:
                    values = [val.strip() for val in row.split('|')]
                    entry = {headers[i]: values[i] for i in range(len(headers)) if i < len(values)}
                    data.append(entry)
                
                cable_df = pd.DataFrame(data)
                
                # 숫자형 변환
                for year in ['2021', '2022', '2023', '2024']:
                    if year in cable_df.columns:
                        cable_df[year] = pd.to_numeric(cable_df[year])
                
                print("케이블 데이터 로드 완료 (마크다운 파일)")
            else:
                # 마크다운 파싱 실패 시 JSON 파일 대체
                raise Exception("마크다운 파싱 실패")
        except Exception as e:
            print(f"마크다운 로드 오류, JSON으로 대체: {e}")
            # 기존 JSON 파일 로드 (대체 방법)
            with open('onlycable.json', 'r', encoding='utf-8') as f:
                cable_data = json.load(f)
            cable_df = pd.DataFrame(cable_data)
        
        # 토목 자재 데이터 로드
        try:
            with open('concre_table_ocr.md', 'r', encoding='utf-8') as f:
                concre_df = pd.read_csv(f, delimiter='|')
                concre_df = concre_df.iloc[:, 1:-1]  # 첫 번째와 마지막 열 제거 (마크다운 형식으로 인한 빈 열)
                concre_df.columns = concre_df.columns.str.strip()  # 열 이름의 공백 제거
        except Exception as e:
            print(f"토목 데이터 로드 오류: {e}")
            concre_df = pd.DataFrame()
        
        # 엔지니어링 노임 데이터 로드
        try:
            with open('engineering_salary_ocr.md', 'r', encoding='utf-8') as f:
                eng_df = pd.read_csv(f, delimiter='|')
                eng_df = eng_df.iloc[:, 1:-1]  # 첫 번째와 마지막 열 제거 (마크다운 형식으로 인한 빈 열)
                eng_df.columns = eng_df.columns.str.strip()  # 열 이름의 공백 제거
        except Exception as e:
            print(f"엔지니어링 노임 데이터 로드 오류: {e}")
            eng_df = pd.DataFrame()
            
        # 건설업 임금실태 데이터 로드
        try:
            with open('construction_wage_ocr.md', 'r', encoding='utf-8') as f:
                construction_df = pd.read_csv(f, delimiter='|')
                construction_df = construction_df.iloc[:, 1:-1]  # 첫 번째와 마지막 열 제거 (마크다운 형식으로 인한 빈 열)
                construction_df.columns = construction_df.columns.str.strip()  # 열 이름의 공백 제거
        except Exception as e:
            print(f"건설업 임금실태 데이터 로드 오류: {e}")
            construction_df = pd.DataFrame()
        
        return {
            'cable': cable_df,
            'concre': concre_df,
            'engineering': eng_df,
            'construction': construction_df
        }
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {e}")
        return None

@st.cache_data
def load_concrete_data():
    try:
        # Markdown 파일에서 테이블 읽기
        with open('concre_table_ocr.md', 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        # 마크다운 테이블을 파싱하여 데이터프레임으로 변환
        lines = markdown_text.strip().split('\n')
        if len(lines) < 3:  # 헤더, 구분선, 데이터 행이 최소한 있어야 함
            return pd.DataFrame()
        
        # 헤더 추출
        headers = [h.strip() for h in lines[0].split('|')[1:-1]]
        
        # 데이터 행 추출
        data = []
        for line in lines[2:]:  # 첫 번째 줄은 헤더, 두 번째 줄은 구분선
            values = [val.strip() for val in line.split('|')[1:-1]]
            if len(values) == len(headers):
                row = {}
                for i, header in enumerate(headers):
                    if i == 0:  # 연도
                        row['year'] = int(values[i].replace('년', ''))
                    elif i == 1:  # 규격
                        row['spec'] = values[i]
                    elif i == 2:  # 가격
                        row['price'] = int(values[i])
                data.append(row)
        
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"콘크리트 데이터 로드 중 오류 발생: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def load_engineering_salary_data():
    try:
        # Markdown 파일에서 테이블 읽기
        with open('engineering_salary_ocr.md', 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        # 마크다운 테이블을 파싱하여 데이터프레임으로 변환
        lines = markdown_text.strip().split('\n')
        if len(lines) < 3:  # 헤더, 구분선, 데이터 행이 최소한 있어야 함
            return pd.DataFrame()
        
        # 헤더 추출
        headers = [h.strip() for h in lines[0].split('|')[1:-1]]
        
        # 데이터 행 추출
        data = []
        for line in lines[2:]:  # 첫 번째 줄은 헤더, 두 번째 줄은 구분선
            values = [val.strip() for val in line.split('|')[1:-1]]
            if len(values) == len(headers):
                row = {}
                for i, header in enumerate(headers):
                    if i == 0:  # 연도
                        row['year'] = int(values[i])
                    elif i == 1:  # 직위
                        row['position'] = values[i]
                    elif i == 2:  # 금액
                        row['salary'] = int(values[i])
                data.append(row)
        
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"엔지니어링 노임단가 데이터 로드 중 오류 발생: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def load_construction_wage_data():
    try:
        # Markdown 파일에서 테이블 읽기
        with open('construction_wage_ocr.md', 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        # 마크다운 테이블을 파싱하여 데이터프레임으로 변환
        lines = markdown_text.strip().split('\n')
        if len(lines) < 3:  # 헤더, 구분선, 데이터 행이 최소한 있어야 함
            return pd.DataFrame()
        
        # 헤더 추출
        headers = [h.strip() for h in lines[0].split('|')[1:-1]]
        
        # 데이터 행 추출
        data = []
        for line in lines[2:]:  # 첫 번째 줄은 헤더, 두 번째 줄은 구분선
            values = [val.strip() for val in line.split('|')[1:-1]]
            if len(values) == len(headers):
                row = {}
                for i, header in enumerate(headers):
                    if i == 0:  # 연도
                        row['year'] = int(values[i])
                    elif i == 1:  # 직종
                        row['occupation'] = values[i]
                    elif i == 2:  # 임금
                        row['wage'] = int(values[i])
                data.append(row)
        
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"건설업 임금실태 데이터 로드 중 오류 발생: {str(e)}")
        return pd.DataFrame()

def calculate_price_changes(df, size):
    size_data = df[df['size'] == size].sort_values('year')
    if len(size_data) >= 2:
        initial_price = size_data.iloc[0]['price']
        final_price = size_data.iloc[-1]['price']
        years_diff = size_data.iloc[-1]['year'] - size_data.iloc[0]['year']
        
        if years_diff > 0:
            total_change = ((final_price - initial_price) / initial_price) * 100
            avg_annual_change = ((final_price / initial_price) ** (1/years_diff) - 1) * 100
            return total_change, avg_annual_change
    return None, None

def calculate_concrete_price_change(df, spec):
    # 특정 규격의 데이터만 필터링
    spec_data = df[df['spec'] == spec]
    
    if len(spec_data) == 2:  # 2020년과 2025년 데이터가 모두 있는 경우
        price_2020 = spec_data[spec_data['year'] == 2020]['price'].values[0]
        price_2025 = spec_data[spec_data['year'] == 2025]['price'].values[0]
        
        # 총 변동률
        total_change = ((price_2025 - price_2020) / price_2020) * 100
        
        # 연평균 변동률
        years_diff = 5  # 2025 - 2020
        avg_annual_change = ((price_2025 / price_2020) ** (1/years_diff) - 1) * 100
        
        return price_2020, price_2025, total_change, avg_annual_change
    return None, None, None, None

@st.cache_data
def load_cable_data():
    try:
        # Markdown 파일에서 케이블 데이터 읽기
        print("cable_data.md 파일 읽기 시도...")
        
        with open('cable_data.md', 'r', encoding='utf-8') as f:
            markdown_text = f.read()
            # BOM 제거
            if markdown_text.startswith('\ufeff'):
                markdown_text = markdown_text[1:]
            print(f"파일 로드 성공: {len(markdown_text)} 바이트")
            
        # 마크다운 테이블을 파싱하여 데이터프레임으로 변환
        lines = markdown_text.strip().split('\n')
        print(f"파싱된 라인 수: {len(lines)}")
        
        # 테이블 부분만 추출 (처음 몇 줄은 제목일 수 있음)
        table_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('|') and '|' in line[1:]:
                table_start = i
                break
        
        if table_start == -1 or table_start + 2 >= len(lines):
            print("마크다운 테이블을 찾을 수 없습니다.")
            return pd.DataFrame()
        
        # 헤더 행 추출
        header_line = lines[table_start]
        headers = [h.strip() for h in header_line.split('|')[1:-1]]
        print(f"추출된 헤더: {headers}")
        
        # 구분선 건너뛰기
        # 데이터 행 추출 (구분선 다음부터)
        data_lines = lines[table_start + 2:]
        
        cable_data = []
        for line in data_lines:
            if not line.strip().startswith('|'):
                continue
                
            values = [val.strip() for val in line.split('|')[1:-1]]
            if len(values) != len(headers):
                print(f"열 개수 불일치: {len(values)} vs {len(headers)}, 값: {values}")
                continue
                
            # 연도별 데이터 항목 생성
            brand = values[0]  # 품명
            size = values[1]   # 규격
            unit = values[2]   # 단위
            
            for i, year in enumerate(['2021', '2022', '2023', '2024']):
                year_idx = i + 3  # 품명, 규격, 단위 다음이 2021년부터
                if year_idx < len(values) and values[year_idx] and values[year_idx].strip():
                    try:
                        # 가격에 쉼표가 있을 경우 제거
                        price_str = values[year_idx].replace(',', '')
                        price = int(price_str)
                        cable_data.append({
                            'year': int(year),
                            'brand': brand,
                            'size': size,
                            'unit': unit,
                            'price': price
                        })
                    except ValueError as e:
                        print(f"가격 변환 오류: {values[year_idx]}, 오류: {e}")
        
        print(f"추출된 데이터 항목 수: {len(cable_data)}")
        
        if not cable_data:
            print("파싱된 데이터가 없습니다. 원본 테이블 일부 출력:")
            for i in range(min(5, len(lines))):
                print(lines[i])
            return pd.DataFrame()
        
        # 데이터프레임 생성
        df = pd.DataFrame(cable_data)
        print(f"생성된 데이터프레임 크기: {df.shape}")
        print(df.head())
        
        return df
    
    except FileNotFoundError:
        error_msg = "cable_data.md 파일을 찾을 수 없습니다."
        print(error_msg)
        st.error(error_msg)
        return pd.DataFrame()
    except Exception as e:
        import traceback
        error_msg = f"케이블 데이터 로드 중 오류 발생: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        st.error(error_msg)
        return pd.DataFrame()

# 메인 타이틀
col1, col2 = st.columns([1, 3])
with col1:
    st.image("skci.png", width=80)
with col2:
    st.title("단가변동 시스템")

# 사이드바에 분야 선택 추가
selected_field = st.sidebar.selectbox(
    "분야 선택",
    ["엔지니어링노임", "건설업 임금실태", "토목", "전기"]
)

if selected_field == "전기":
    st.header("전기자재 - 케이블 가격비교")
    
    try:
        # 케이블 데이터 로드
        df = load_cable_data()
        
        if not df.empty:
            # 사이드바에 필터 추가
            st.sidebar.header("필터 설정")
            
            # 연도 선택
            years = sorted(df['year'].unique())
            selected_years = st.sidebar.multiselect(
                "연도 선택",
                years,
                default=years
            )
            
            # 케이블 유형 선택
            brands = sorted(df['brand'].unique())
            selected_brand = st.sidebar.selectbox(
                "케이블 유형 선택",
                brands
            )
            
            # 케이블 사이즈 선택
            sizes = sorted(df[df['brand'] == selected_brand]['size'].unique())
            selected_size = st.sidebar.selectbox(
                "케이블 사이즈 선택",
                sizes
            )
            
            # 데이터 필터링
            filtered_df = df[
                (df['year'].isin(selected_years)) &
                (df['brand'] == selected_brand) &
                (df['size'] == selected_size)
            ]
            
            # 메인 영역
            st.header(f"{selected_brand} {selected_size} 가격 변동")
            
            # 데이터 시각화
            if not filtered_df.empty:
                # 가격 변동 그래프
                fig = px.line(
                    filtered_df, 
                    x='year', 
                    y='price',
                    markers=True,
                    title=f"{selected_brand} {selected_size} 연도별 가격 변동"
                )
                fig.update_layout(
                    xaxis_title="연도",
                    yaxis_title="가격(원)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 가격 데이터 테이블
                st.subheader("가격 데이터")
                price_data = filtered_df[['year', 'price']].sort_values('year')
                st.dataframe(price_data, use_container_width=True)
                
                # 가격 변동률 계산
                if len(price_data) >= 2:
                    min_year = min(price_data['year'])
                    max_year = max(price_data['year'])
                    
                    min_price = price_data[price_data['year'] == min_year]['price'].values[0]
                    max_price = price_data[price_data['year'] == max_year]['price'].values[0]
                    
                    total_change = max_price - min_price
                    total_change_percent = (total_change / min_price) * 100
                    years_diff = max_year - min_year
                    annual_change_percent = total_change_percent / years_diff if years_diff > 0 else 0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("총 변동액", f"{total_change:,}원", f"{total_change_percent:.1f}%")
                    with col2:
                        st.metric("연평균 변동률", f"{annual_change_percent:.1f}%")
                
                # 모든 사이즈 비교
                st.header("케이블 사이즈별 가격 변동률 비교")
                
                if len(selected_years) >= 2:
                    min_year = min(selected_years)
                    max_year = max(selected_years)
                    
                    change_data = []
                    for size in sizes:
                        size_data = df[
                            (df['brand'] == selected_brand) &
                            (df['size'] == size) & 
                            (df['year'].isin([min_year, max_year]))
                        ]
                        
                        if len(size_data) == 2:
                            min_year_price = size_data[size_data['year'] == min_year]['price'].values[0]
                            max_year_price = size_data[size_data['year'] == max_year]['price'].values[0]
                            
                            change = max_year_price - min_year_price
                            change_percent = (change / min_year_price) * 100
                            
                            change_data.append({
                                'size': size,
                                'min_price': min_year_price,
                                'max_price': max_year_price,
                                'change': change,
                                'change_percent': change_percent
                            })
                    
                    change_df = pd.DataFrame(change_data)
                    if not change_df.empty:
                        # 변동률 그래프
                        fig = px.bar(
                            change_df, 
                            x='size', 
                            y='change_percent',
                            title=f"{min_year}년 대비 {max_year}년 가격 변동률(%)"
                        )
                        fig.update_layout(
                            xaxis_title="케이블 사이즈",
                            yaxis_title="변동률(%)",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 변동률 데이터 테이블
                        st.subheader("사이즈별 가격 변동 데이터")
                        change_df['min_price'] = change_df['min_price'].apply(lambda x: f"{x:,}원")
                        change_df['max_price'] = change_df['max_price'].apply(lambda x: f"{x:,}원")
                        change_df['change'] = change_df['change'].apply(lambda x: f"{x:,}원")
                        change_df['change_percent'] = change_df['change_percent'].apply(lambda x: f"{x:.1f}%")
                        
                        st.dataframe(change_df[['size', 'min_price', 'max_price', 'change', 'change_percent']], use_container_width=True)
            else:
                st.warning("선택한 조건에 맞는 데이터가 없습니다.")
        else:
            st.error("케이블 데이터를 로드할 수 없습니다.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
        st.exception(e)

elif selected_field == "토목":
    st.header("토목자재 - 아스팔트 콘크리트 가격비교")
    
    try:
        # 콘크리트 데이터 로드
        concrete_df = load_concrete_data()
        
        if not concrete_df.empty:
            # 사이드바에 필터 추가
            st.sidebar.header("필터 설정")
            
            # 연도 선택 추가
            years = sorted(concrete_df['year'].unique())
            selected_years = st.sidebar.multiselect(
                "연도 선택",
                years,
                default=years
            )
            
            # 아스팔트 콘크리트 규격 선택
            specs = sorted(concrete_df['spec'].unique())
            selected_spec = st.sidebar.selectbox(
                "아스팔트 콘크리트 규격 선택",
                specs
            )
            
            # 선택한 연도로 데이터 필터링
            filtered_concrete_df = concrete_df[concrete_df['year'].isin(selected_years)]
            
            if len(selected_years) >= 2 and len(filtered_concrete_df) >= 2:
                # 선택된 규격의 데이터만 필터링
                spec_df = filtered_concrete_df[filtered_concrete_df['spec'] == selected_spec]
                
                if len(spec_df) >= 2:
                    # 가격 변동 계산 (선택된 연도 범위)
                    min_year = min(selected_years)
                    max_year = max(selected_years)
                    
                    min_year_price = spec_df[spec_df['year'] == min_year]['price'].values[0]
                    max_year_price = spec_df[spec_df['year'] == max_year]['price'].values[0]
                    
                    # 총 변동률
                    total_change = ((max_year_price - min_year_price) / min_year_price) * 100
                    
                    # 연평균 변동률
                    years_diff = max_year - min_year
                    if years_diff > 0:
                        avg_annual_change = ((max_year_price / min_year_price) ** (1/years_diff) - 1) * 100
                    else:
                        avg_annual_change = 0
                    
                    # 2개의 컬럼 생성
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 가격 비교 그래프
                        st.subheader(f"가격 비교 ({min_year}년 vs {max_year}년)")
                        
                        comp_df = pd.DataFrame({
                            '연도': [f'{min_year}년', f'{max_year}년'],
                            '가격': [min_year_price, max_year_price]
                        })
                        
                        fig = px.bar(comp_df, x='연도', y='가격',
                                   title=f'{selected_spec} 가격 비교',
                                   color='연도',
                                   labels={'연도': '', '가격': '가격 (원)'},
                                   text_auto=True)
                        st.plotly_chart(fig)
                        
                    with col2:
                        # 가격 변동 분석
                        st.subheader("가격 변동 분석")
                        
                        st.metric(
                            label=f"{min_year}년 가격",
                            value=f"{min_year_price:,} 원"
                        )
                        
                        st.metric(
                            label=f"{max_year}년 가격",
                            value=f"{max_year_price:,} 원",
                            delta=f"{total_change:.2f}%"
                        )
                        
                        st.write(f"**총 변동률 ({min_year}-{max_year}):** {total_change:.2f}%")
                        if years_diff > 0:
                            st.write(f"**연평균 변동률:** {avg_annual_change:.2f}%")
                    
                    # 모든 연도의 선택된 규격 가격 추이 그래프
                    if len(spec_df) > 1:
                        st.subheader(f"{selected_spec} 가격 추이")
                        trend_fig = px.line(spec_df.sort_values('year'), x='year', y='price',
                                        title=f'{selected_spec} 연도별 가격 추이',
                                        labels={'year': '연도', 'price': '가격 (원)'},
                                        markers=True)
                        st.plotly_chart(trend_fig)
                    
                    # 모든 규격의 가격 변동률 비교
                    st.subheader("규격별 가격 변동률 비교")
                    
                    # 모든 규격의 변동률 계산
                    change_data = []
                    for spec in specs:
                        spec_data = filtered_concrete_df[filtered_concrete_df['spec'] == spec]
                        if len(spec_data) >= 2 and min_year in spec_data['year'].values and max_year in spec_data['year'].values:
                            min_price = spec_data[spec_data['year'] == min_year]['price'].values[0]
                            max_price = spec_data[spec_data['year'] == max_year]['price'].values[0]
                            spec_change = ((max_price - min_price) / min_price) * 100
                            change_data.append({
                                '규격': spec,
                                '변동률': spec_change
                            })
                    
                    change_df = pd.DataFrame(change_data)
                    if not change_df.empty:
                        fig_all = px.bar(change_df, x='규격', y='변동률',
                                      title=f'규격별 가격 변동률 ({min_year}-{max_year})',
                                      labels={'규격': '', '변동률': '변동률 (%)'},
                                      color='변동률',
                                      text_auto='.2f')
                        st.plotly_chart(fig_all)
                    
                    # 원본 데이터 표시
                    st.subheader("원본 데이터")
                    st.dataframe(spec_df.sort_values('year'))
                else:
                    st.warning(f"선택한 규격 '{selected_spec}'에 대한 선택된 연도({', '.join(map(str, selected_years))})의 데이터가 충분하지 않습니다.")
            else:
                st.warning("분석을 위해 최소 2개 이상의 연도를 선택해주세요.")
        else:
            st.error("아스팔트 콘크리트 데이터를 불러올 수 없습니다. 파일이 존재하는지 확인해주세요.")
    
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
        st.exception(e)

elif selected_field == "엔지니어링노임":
    st.header("엔지니어링 노임단가 비교")
    
    try:
        # 엔지니어링 노임데이터 로드
        engineering_df = load_engineering_salary_data()
        
        if not engineering_df.empty:
            # 사이드바에 필터 추가
            st.sidebar.header("필터 설정")
            
            # 연도 선택
            years = sorted(engineering_df['year'].unique())
            selected_years = st.sidebar.multiselect(
                "연도 선택",
                years,
                default=years
            )
            
            # 기술자 등급 선택
            positions = sorted(engineering_df['position'].unique())
            selected_position = st.sidebar.selectbox(
                "기술자 등급 선택",
                positions
            )
            
            # 선택한 연도로 데이터 필터링
            filtered_engineering_df = engineering_df[engineering_df['year'].isin(selected_years)]
            
            if len(selected_years) >= 2 and len(filtered_engineering_df) >= 2:
                # 선택된 기술자 등급의 데이터만 필터링
                position_df = filtered_engineering_df[filtered_engineering_df['position'] == selected_position]
                
                if len(position_df) >= 2:
                    # 가격 변동 계산 (선택된 연도 범위)
                    min_year = min(selected_years)
                    max_year = max(selected_years)
                    
                    min_year_salary = position_df[position_df['year'] == min_year]['salary'].values[0]
                    max_year_salary = position_df[position_df['year'] == max_year]['salary'].values[0]
                    
                    # 총 변동률
                    total_change = ((max_year_salary - min_year_salary) / min_year_salary) * 100
                    
                    # 연평균 변동률
                    years_diff = max_year - min_year
                    if years_diff > 0:
                        avg_annual_change = ((max_year_salary / min_year_salary) ** (1/years_diff) - 1) * 100
                    else:
                        avg_annual_change = 0
                    
                    # 2개의 컬럼 생성
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 노임단가 비교 그래프
                        st.subheader(f"노임단가 비교 ({min_year}년 vs {max_year}년)")
                        
                        comp_df = pd.DataFrame({
                            '연도': [f'{min_year}년', f'{max_year}년'],
                            '노임단가': [min_year_salary, max_year_salary]
                        })
                        
                        fig = px.bar(comp_df, x='연도', y='노임단가',
                                   title=f'{selected_position} 노임단가 비교',
                                   color='연도',
                                   labels={'연도': '', '노임단가': '노임단가 (원)'},
                                   text_auto=True)
                        st.plotly_chart(fig)
                        
                        # 모든 연도의 선택된 기술자 등급 노임단가 추이 그래프
                        st.subheader(f"{selected_position} 노임단가 추이")
                        trend_fig = px.line(position_df.sort_values('year'), x='year', y='salary',
                                        title=f'{selected_position} 연도별 노임단가 추이',
                                        labels={'year': '연도', 'salary': '노임단가 (원)'},
                                        markers=True)
                        st.plotly_chart(trend_fig)
                    
                    with col2:
                        # 노임단가 변동 분석
                        st.subheader("노임단가 변동 분석")
                        
                        st.metric(
                            label=f"{min_year}년 노임단가",
                            value=f"{min_year_salary:,} 원"
                        )
                        
                        st.metric(
                            label=f"{max_year}년 노임단가",
                            value=f"{max_year_salary:,} 원",
                            delta=f"{total_change:.2f}%"
                        )
                        
                        st.write(f"**총 변동률 ({min_year}-{max_year}):** {total_change:.2f}%")
                        if years_diff > 0:
                            st.write(f"**연평균 변동률:** {avg_annual_change:.2f}%")
                        
                        # 연도별 노임단가 테이블
                        st.subheader("상세 데이터")
                        st.dataframe(position_df[['year', 'salary']].set_index('year').sort_index())
                    
                    # 모든 기술자 등급의 노임단가 변동률 비교
                    st.subheader("기술자 등급별 노임단가 변동률 비교")
                    
                    # 모든 기술자 등급의 변동률 계산
                    change_data = []
                    for position in positions:
                        position_data = filtered_engineering_df[filtered_engineering_df['position'] == position]
                        if len(position_data) >= 2 and min_year in position_data['year'].values and max_year in position_data['year'].values:
                            min_salary = position_data[position_data['year'] == min_year]['salary'].values[0]
                            max_salary = position_data[position_data['year'] == max_year]['salary'].values[0]
                            position_change = ((max_salary - min_salary) / min_salary) * 100
                            change_data.append({
                                '기술자 등급': position,
                                '변동률': position_change
                            })
                    
                    change_df = pd.DataFrame(change_data)
                    if not change_df.empty:
                        fig_all = px.bar(change_df, x='기술자 등급', y='변동률',
                                      title=f'기술자 등급별 노임단가 변동률 ({min_year}-{max_year})',
                                      labels={'기술자 등급': '', '변동률': '변동률 (%)'},
                                      color='변동률',
                                      text_auto='.2f')
                        st.plotly_chart(fig_all)
                    
                    # 원본 데이터 표시
                    st.subheader("원본 데이터")
                    st.dataframe(position_df.sort_values('year'))
                else:
                    st.warning(f"선택한 기술자 등급 '{selected_position}'에 대한 선택된 연도({', '.join(map(str, selected_years))})의 데이터가 충분하지 않습니다.")
            else:
                st.warning("분석을 위해 최소 2개 이상의 연도를 선택해주세요.")
        else:
            st.error("엔지니어링 노임단가 데이터를 불러올 수 없습니다. 파일이 존재하는지 확인해주세요.")
    
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
        st.exception(e)

elif selected_field == "건설업 임금실태":
    st.header("건설업 임금실태 비교")
    
    try:
        # 건설업 임금실태 데이터 로드
        construction_df = load_construction_wage_data()
        
        if not construction_df.empty:
            # 사이드바에 필터 추가
            st.sidebar.header("필터 설정")
            
            # 연도 선택
            years = sorted(construction_df['year'].unique())
            selected_years = st.sidebar.multiselect(
                "연도 선택",
                years,
                default=years
            )
            
            # 직종 선택
            occupations = sorted(construction_df['occupation'].unique())
            selected_occupation = st.sidebar.selectbox(
                "직종 선택",
                occupations
            )
            
            # 선택한 연도로 데이터 필터링
            filtered_construction_df = construction_df[construction_df['year'].isin(selected_years)]
            
            if len(selected_years) >= 2 and len(filtered_construction_df) >= 2:
                # 선택된 직종의 데이터만 필터링
                occupation_df = filtered_construction_df[filtered_construction_df['occupation'] == selected_occupation]
                
                if len(occupation_df) >= 2:
                    # 임금 변동 계산 (선택된 연도 범위)
                    min_year = min(selected_years)
                    max_year = max(selected_years)
                    
                    min_year_wage = occupation_df[occupation_df['year'] == min_year]['wage'].values[0]
                    max_year_wage = occupation_df[occupation_df['year'] == max_year]['wage'].values[0]
                    
                    # 총 변동률
                    total_change = ((max_year_wage - min_year_wage) / min_year_wage) * 100
                    
                    # 연평균 변동률
                    years_diff = max_year - min_year
                    if years_diff > 0:
                        avg_annual_change = ((max_year_wage / min_year_wage) ** (1/years_diff) - 1) * 100
                    else:
                        avg_annual_change = 0
                    
                    # 2개의 컬럼 생성
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 임금 비교 그래프
                        st.subheader(f"임금 비교 ({min_year}년 vs {max_year}년)")
                        
                        comp_df = pd.DataFrame({
                            '연도': [f'{min_year}년', f'{max_year}년'],
                            '임금': [min_year_wage, max_year_wage]
                        })
                        
                        fig = px.bar(comp_df, x='연도', y='임금',
                                   title=f'{selected_occupation} 임금 비교',
                                   color='연도',
                                   labels={'연도': '', '임금': '임금 (원)'},
                                   text_auto=True)
                        st.plotly_chart(fig)
                        
                        # 모든 연도의 선택된 직종 임금 추이 그래프
                        st.subheader(f"{selected_occupation} 임금 추이")
                        trend_fig = px.line(occupation_df.sort_values('year'), x='year', y='wage',
                                        title=f'{selected_occupation} 연도별 임금 추이',
                                        labels={'year': '연도', 'wage': '임금 (원)'},
                                        markers=True)
                        st.plotly_chart(trend_fig)
                    
                    with col2:
                        # 임금 변동 분석
                        st.subheader("임금 변동 분석")
                        
                        st.metric(
                            label=f"{min_year}년 임금",
                            value=f"{min_year_wage:,} 원"
                        )
                        
                        st.metric(
                            label=f"{max_year}년 임금",
                            value=f"{max_year_wage:,} 원",
                            delta=f"{total_change:.2f}%"
                        )
                        
                        st.write(f"**총 변동률 ({min_year}-{max_year}):** {total_change:.2f}%")
                        if years_diff > 0:
                            st.write(f"**연평균 변동률:** {avg_annual_change:.2f}%")
                        
                        # 연도별 임금 테이블
                        st.subheader("상세 데이터")
                        st.dataframe(occupation_df[['year', 'wage']].set_index('year').sort_index())
                    
                    # 모든 직종의 임금 변동률 비교
                    st.subheader("직종별 임금 변동률 비교")
                    
                    # 모든 직종의 변동률 계산
                    change_data = []
                    for occupation in occupations:
                        occupation_data = filtered_construction_df[filtered_construction_df['occupation'] == occupation]
                        if len(occupation_data) >= 2 and min_year in occupation_data['year'].values and max_year in occupation_data['year'].values:
                            min_wage = occupation_data[occupation_data['year'] == min_year]['wage'].values[0]
                            max_wage = occupation_data[occupation_data['year'] == max_year]['wage'].values[0]
                            occupation_change = ((max_wage - min_wage) / min_wage) * 100
                            change_data.append({
                                '직종': occupation,
                                '변동률': occupation_change
                            })
                    
                    change_df = pd.DataFrame(change_data)
                    if not change_df.empty:
                        fig_all = px.bar(change_df, x='직종', y='변동률',
                                      title=f'직종별 임금 변동률 ({min_year}-{max_year})',
                                      labels={'직종': '', '변동률': '변동률 (%)'},
                                      color='변동률',
                                      text_auto='.2f')
                        st.plotly_chart(fig_all)
                    
                    # 원본 데이터 표시
                    st.subheader("원본 데이터")
                    st.dataframe(occupation_df.sort_values('year'))
                else:
                    st.warning(f"선택한 직종 '{selected_occupation}'에 대한 선택된 연도({', '.join(map(str, selected_years))})의 데이터가 충분하지 않습니다.")
            else:
                st.warning("분석을 위해 최소 2개 이상의 연도를 선택해주세요.")
        else:
            st.error("건설업 임금실태 데이터를 불러올 수 없습니다. 파일이 존재하는지 확인해주세요.")
    
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
        st.exception(e)

# 사이드바 맨 아래에 폰트 크기 조절 섹션 추가
st.sidebar.markdown("---")
st.sidebar.header("폰트 크기 설정")

# 전체 폰트 크기 조절 (슬라이더로 제어)
all_font_size = st.sidebar.slider(
    "전체 폰트 크기",
    min_value=10,
    max_value=24,
    value=all_font_size,  # 기본값으로 초기에 설정한 값 사용
    step=1,
    key="font_size_slider"  # 고유한 키 추가
)

# 폰트 크기가 변경되면 스타일 업데이트
st.markdown(f"""
    <style>
    /* 전체 폰트 크기 조절 */
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, .stWidgetLabel, .st-emotion-cache-16txtl3 {{
        font-size: {all_font_size}px !important;
    }}
    
    /* 헤더는 상대적으로 크게 유지 */
    h1 {{
        font-size: {all_font_size + 10}px !important;
    }}
    h2 {{
        font-size: {all_font_size + 6}px !important;
    }}
    h3 {{
        font-size: {all_font_size + 4}px !important;
    }}
    </style>
""", unsafe_allow_html=True) 