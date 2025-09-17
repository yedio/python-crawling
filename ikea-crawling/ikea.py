
import time
import csv
import datetime
import os
import pandas as pd
import requests
from io import BytesIO
from PIL import Image
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.utils import get_column_letter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

def extract_product_data(url):
    """
    Selenium을 사용하여 이케아 웹사이트에서 제품 데이터를 추출합니다.
    더보기 기능은 잠시 중단하고 현재 페이지의 제품들만 수집합니다.
    """
    service = Service()
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 브라우저 창을 보지 않고 실행하려면 주석을 해제하세요.
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"URL: {url}")
        driver.get(url)

        # 페이지가 로드될 때까지 최대 15초 대기
        print("페이지가 로드되기를 기다립니다...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.plp-fragment-wrapper"))
        )
        print("초기 페이지 로드 완료.")
        
        # 추가 대기 시간 (동적 콘텐츠 로딩을 위해)
        time.sleep(3)
        print("동적 콘텐츠 로딩을 위해 3초 대기...")

        # --- plp-fragment-wrapper 아이템들의 데이터 수집 ---
        item_selector = "div.plp-fragment-wrapper"
        item_elements = driver.find_elements(By.CSS_SELECTOR, item_selector)
        print(f"총 {len(item_elements)}개의 아이템을 찾았습니다.")
        
        # 첫 번째 아이템이 제대로 로드되었는지 확인
        if len(item_elements) > 0:
            try:
                first_item = item_elements[0]
                print("첫 번째 아이템 확인 중...")
                # 첫 번째 아이템에서 이름이 있는지 확인
                name_elements = first_item.find_elements(By.CSS_SELECTOR, "span.plp-price-module__product-name")
                if name_elements:
                    print(f"첫 번째 아이템 이름: {name_elements[0].text.strip()}")
                else:
                    print("첫 번째 아이템에서 이름을 찾을 수 없습니다. 추가 대기...")
                    time.sleep(2)
                    # 다시 요소들을 찾기
                    item_elements = driver.find_elements(By.CSS_SELECTOR, item_selector)
                    print(f"재검색 후 총 {len(item_elements)}개의 아이템을 찾았습니다.")
            except Exception as e:
                print(f"첫 번째 아이템 확인 중 오류: {e}")
                time.sleep(2)
                item_elements = driver.find_elements(By.CSS_SELECTOR, item_selector)
                print(f"재검색 후 총 {len(item_elements)}개의 아이템을 찾았습니다.")
        
        products = []
        for i in range(len(item_elements)):
            try:
                # 매번 새로운 요소를 찾아서 stale element 문제 해결
                current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                if i >= len(current_items):
                    print(f"아이템 {i+1}을 찾을 수 없습니다. (인덱스 초과)")
                    break
                
                # 요소를 다시 찾기
                item = current_items[i]
                product_data = {}
                
                # 첫 번째 아이템에 대한 특별한 처리
                if i == 0:
                    print(f"\n=== 첫 번째 아이템 처리 중 ===")
                    print(f"첫 번째 아이템 HTML 구조 확인 중...")
                    
                    # 첫 번째 아이템의 경우 추가 대기
                    time.sleep(2)
                    
                    # 요소가 완전히 로드되었는지 확인
                    try:
                        # 다양한 선택자로 이름 요소 확인
                        name_selectors_check = [
                            "span.plp-price-module__product-name",
                            "div.plp-mastercard span.plp-price-module__product-name",
                            "h3.plp-price-module__product-name",
                            "div.plp-mastercard h3"
                        ]
                        
                        name_found_in_check = False
                        for selector in name_selectors_check:
                            name_elements = item.find_elements(By.CSS_SELECTOR, selector)
                            if name_elements and name_elements[0].text.strip():
                                print(f"첫 번째 아이템에서 이름 발견: {name_elements[0].text.strip()}")
                                name_found_in_check = True
                                break
                        
                        if not name_found_in_check:
                            print("첫 번째 아이템이 아직 완전히 로드되지 않았습니다. 추가 대기...")
                            time.sleep(3)
                            # 다시 요소 찾기
                            current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                            if len(current_items) > 0:
                                item = current_items[0]
                                print("첫 번째 아이템을 다시 찾았습니다.")
                            else:
                                print("첫 번째 아이템을 다시 찾을 수 없습니다.")
                                continue
                    except Exception as e:
                        print(f"첫 번째 아이템 확인 중 오류: {e}")
                        time.sleep(2)
                
                # 각 데이터 추출 시마다 요소를 다시 찾기
                try:
                    # 1. 이름 추출 - 여러 선택자 시도
                    name_found = False
                    name_selectors = [
                        "div.plp-mastercard span.plp-price-module__product-name",
                        "span.plp-price-module__product-name",
                        "h3.plp-price-module__product-name",
                        "div.plp-mastercard h3",
                        "a[data-testid='product-link'] span",
                        "a[data-testid='product-link'] h3"
                    ]
                    
                    for selector in name_selectors:
                        try:
                            # 현재 아이템을 다시 찾기
                            current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                            if i < len(current_items):
                                item = current_items[i]
                                name_element = item.find_element(By.CSS_SELECTOR, selector)
                                if name_element and name_element.text.strip():
                                    product_data['name'] = name_element.text.strip()
                                    print(f"{i+1}. {product_data['name']}")
                                    name_found = True
                                    break
                        except Exception as e:
                            continue
                    
                    if not name_found:
                        print(f"아이템 {i+1} 이름 추출 실패 - 모든 선택자 시도 완료")
                        product_data['name'] = ""
                    
                    # 2. 사진 URL 추출 (첫 번째 이미지)
                    try:
                        # 현재 아이템을 다시 찾기
                        current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                        if i < len(current_items):
                            item = current_items[i]
                            image_element = item.find_element(By.CSS_SELECTOR, "div.plp-mastercard div.plp-mastercard__image img")
                            product_data['image_url'] = image_element.get_attribute('src')
                        else:
                            product_data['image_url'] = ""
                    except Exception as e1:
                        try:
                            # 현재 아이템을 다시 찾기
                            current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                            if i < len(current_items):
                                item = current_items[i]
                                image_element = item.find_element(By.CSS_SELECTOR, "div.plp-mastercard__image img")
                                product_data['image_url'] = image_element.get_attribute('src')
                            else:
                                product_data['image_url'] = ""
                        except Exception as e2:
                            print(f"아이템 {i+1} 이미지 URL 추출 실패: {e1}, {e2}")
                            product_data['image_url'] = ""
                    
                    # 3. 사이즈 추출 (description에서 cm 또는 L이 포함된 부분)
                    try:
                        # 현재 아이템을 다시 찾기
                        current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                        if i < len(current_items):
                            item = current_items[i]
                            desc_element = item.find_element(By.CSS_SELECTOR, "div.plp-mastercard span.plp-price-module__description")
                            description = desc_element.text.strip()
                            # , 로 분리하여 cm 또는 L이 포함된 부분 찾기
                            parts = description.split(',')
                            size = ""
                            for part in parts:
                                part = part.strip()
                                if 'cm' in part or 'L' in part:
                                    size = part
                                    break
                            product_data['size'] = size
                        else:
                            product_data['size'] = ""
                    except Exception as e1:
                        try:
                            # 현재 아이템을 다시 찾기
                            current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                            if i < len(current_items):
                                item = current_items[i]
                                desc_element = item.find_element(By.CSS_SELECTOR, "span.plp-price-module__description")
                                description = desc_element.text.strip()
                                # , 로 분리하여 cm 또는 L이 포함된 부분 찾기
                                parts = description.split(',')
                                size = ""
                                for part in parts:
                                    part = part.strip()
                                    if 'cm' in part or 'L' in part:
                                        size = part
                                        break
                                product_data['size'] = size
                            else:
                                product_data['size'] = ""
                        except Exception as e2:
                            print(f"아이템 {i+1} 사이즈 추출 실패: {e1}, {e2}")
                            product_data['size'] = ""
                    
                    # 4. 색상 추출 (description에서 색상 텍스트 찾기)
                    try:
                        # 현재 아이템을 다시 찾기
                        current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                        if i < len(current_items):
                            item = current_items[i]
                            desc_element = item.find_element(By.CSS_SELECTOR, "div.plp-mastercard span.plp-price-module__description")
                            description = desc_element.text.strip()
                            # , 로 분리하여 색상 텍스트 찾기
                            parts = description.split(',')
                            color = ""
                            color_keywords = ['화이트', '투명', '그레이', '블랙', '핑크', '블루', '옐로', '그린']
                            for part in parts:
                                part = part.strip()
                                for keyword in color_keywords:
                                    if keyword in part:
                                        color = part
                                        break
                                if color:
                                    break
                            product_data['color'] = color
                        else:
                            product_data['color'] = ""
                    except Exception as e1:
                        try:
                            # 현재 아이템을 다시 찾기
                            current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                            if i < len(current_items):
                                item = current_items[i]
                                desc_element = item.find_element(By.CSS_SELECTOR, "span.plp-price-module__description")
                                description = desc_element.text.strip()
                                # , 로 분리하여 색상 텍스트 찾기
                                parts = description.split(',')
                                color = ""
                                color_keywords = ['화이트', '투명', '그레이', '블랙', '핑크', '블루', '옐로', '그린']
                                for part in parts:
                                    part = part.strip()
                                    for keyword in color_keywords:
                                        if keyword in part:
                                            color = part
                                            break
                                    if color:
                                        break
                                product_data['color'] = color
                            else:
                                product_data['color'] = ""
                        except Exception as e2:
                            print(f"아이템 {i+1} 색상 추출 실패: {e1}, {e2}")
                            product_data['color'] = ""
                    
                    # 5. 가격 추출 (숫자만)
                    try:
                        # 현재 아이템을 다시 찾기
                        current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                        if i < len(current_items):
                            item = current_items[i]
                            price_element = item.find_element(By.CSS_SELECTOR, "div.plp-mastercard span.plp-price__sr-text")
                            price_text = price_element.text.strip()
                            # "가격 ￦ 1700"에서 숫자만 추출
                            import re
                            price_match = re.search(r'(\d+)', price_text)
                            if price_match:
                                product_data['price'] = price_match.group(1)
                            else:
                                product_data['price'] = ""
                        else:
                            product_data['price'] = ""
                    except Exception as e1:
                        try:
                            # 현재 아이템을 다시 찾기
                            current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                            if i < len(current_items):
                                item = current_items[i]
                                price_element = item.find_element(By.CSS_SELECTOR, "span.plp-price__sr-text")
                                price_text = price_element.text.strip()
                                # "가격 ￦ 1700"에서 숫자만 추출
                                import re
                                price_match = re.search(r'(\d+)', price_text)
                                if price_match:
                                    product_data['price'] = price_match.group(1)
                                else:
                                    product_data['price'] = ""
                            else:
                                product_data['price'] = ""
                        except Exception as e2:
                            print(f"아이템 {i+1} 가격 추출 실패: {e1}, {e2}")
                            product_data['price'] = ""
                    
                    # 6. 링크 추출
                    try:
                        # 현재 아이템을 다시 찾기
                        current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                        if i < len(current_items):
                            item = current_items[i]
                            link_element = item.find_element(By.CSS_SELECTOR, "div.plp-mastercard a.plp-price-link-wrapper")
                            product_data['product_url'] = link_element.get_attribute('href')
                        else:
                            product_data['product_url'] = ""
                    except Exception as e1:
                        try:
                            # 현재 아이템을 다시 찾기
                            current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                            if i < len(current_items):
                                item = current_items[i]
                                link_element = item.find_element(By.CSS_SELECTOR, "a.plp-price-link-wrapper")
                                product_data['product_url'] = link_element.get_attribute('href')
                            else:
                                product_data['product_url'] = ""
                        except Exception as e2:
                            print(f"아이템 {i+1} 링크 추출 실패: {e1}, {e2}")
                            product_data['product_url'] = ""
                    
                    products.append(product_data)
                    
                except Exception as e:
                    print(f"아이템 {i+1} 전체 데이터 추출 실패: {e}")
                    # 빈 데이터라도 추가
                    product_data = {
                        'name': '',
                        'image_url': '',
                        'size': '',
                        'color': '',
                        'price': '',
                        'product_url': ''
                    }
                    products.append(product_data)
                    continue
                
            except Exception as e:
                print(f"아이템 {i+1} 전체 데이터 추출 실패: {e}")
                # 빈 데이터라도 추가
                product_data = {
                    'name': '',
                    'image_url': '',
                    'size': '',
                    'color': '',
                    'price': '',
                    'product_url': ''
                }
                products.append(product_data)
                continue

    except Exception as e:
        print(f"크롤링 중 오류가 발생했습니다: {e}")
        products = []

    finally:
        print("브라우저를 닫습니다.")
        driver.quit()

    return products

def download_and_resize_image(image_url, target_width=140, target_height=140):
    """
    이미지를 다운로드하고 크기를 조정합니다. (셀에 꽉 채우도록)
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # PIL Image로 열기
        img = Image.open(BytesIO(response.content))
        
        # 이미지 크기를 정확한 크기로 리사이즈 (비율 무시하고 셀에 꽉 채움)
        img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # BytesIO에 저장
        img_byte_arr = BytesIO()
        img_resized.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr
    except Exception as e:
        print(f"이미지 다운로드 실패 ({image_url}): {e}")
        return None

def sanitize_sheet_name(sheet_name):
    """
    Excel 시트 이름에 사용할 수 없는 문자를 제거하거나 대체합니다.
    """
    # Excel에서 사용할 수 없는 문자들
    invalid_chars = ['/', '\\', '?', '*', '[', ']', ':', "'"]
    
    # 특수문자 제거
    for char in invalid_chars:
        sheet_name = sheet_name.replace(char, '_')
    
    # 시트 이름 길이 제한 (31자)
    if len(sheet_name) > 31:
        sheet_name = sheet_name[:31]
    
    # 빈 문자열이면 기본값 사용
    if not sheet_name.strip():
        sheet_name = "Sheet1"
    
    return sheet_name

def save_to_excel_multi_sheet(sheet_data_dict, filename_prefix="ikea_products"):
    """
    여러 시트로 나누어서 제품 정보를 Excel 파일로 저장합니다.
    sheet_data_dict: {시트이름: [제품리스트], ...} 형태의 딕셔너리
    """
    if not sheet_data_dict:
        print("저장할 제품 정보가 없습니다.")
        return

    # outputs 폴더 생성 (존재하지 않는 경우)
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"'{output_dir}' 폴더를 생성했습니다.")
    
    # 현재 시간을 포함한 파일명 생성 (시간별로 구분)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)

    # Excel 파일로 저장
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for original_sheet_name, products in sheet_data_dict.items():
            if not products:
                print(f"'{original_sheet_name}' 시트에 저장할 제품 정보가 없습니다.")
                continue
            
            # 시트 이름을 안전하게 변환
            safe_sheet_name = sanitize_sheet_name(original_sheet_name)
            if safe_sheet_name != original_sheet_name:
                print(f"시트 이름을 '{original_sheet_name}' → '{safe_sheet_name}'로 변경했습니다.")
                
            print(f"\n=== '{safe_sheet_name}' 시트 처리 중 ===")
            print(f"제품 수: {len(products)}개")
            
            # DataFrame 생성
            df = pd.DataFrame(products)
            
            # 컬럼 순서 정리 (이미지, 이름, 사이즈, 색상, 가격, 링크)
            df['이미지'] = ''  # 이미지 전용 컬럼
            columns = ['이미지', 'name', 'size', 'color', 'price', 'product_url']
            df = df.reindex(columns=columns)
            
            # 컬럼명을 한국어로 변경
            df.columns = ['이미지', '이름', '사이즈', '색상', '가격', '링크']
            
            # 시트에 데이터 저장
            df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
            # 워크시트 가져오기
            worksheet = writer.sheets[safe_sheet_name]
            
            # 헤더 행(1행)은 기본 높이로, 데이터 행들은 152px로 설정
            worksheet.row_dimensions[1].height = 15  # 헤더는 기본 높이
            for i in range(2, len(products) + 2):  # 데이터 행들만
                worksheet.row_dimensions[i].height = 114  # 152px ≈ 114 포인트 (1포인트 = 1.33픽셀)
            
            # 이미지 삽입 (첫 번째 컬럼이 이미지)
            print(f"'{safe_sheet_name}' 시트 이미지 다운로드 중...")
            for i, product in enumerate(products, start=2):  # 2부터 시작 (헤더 제외)
                if product.get('image_url'):
                    print(f"이미지 다운로드 중: {i-1}/{len(products)} - {product.get('name', 'Unknown')}")
                    img_data = download_and_resize_image(product['image_url'], target_width=140, target_height=140)
                    if img_data:
                        try:
                            # Excel 이미지 객체 생성
                            excel_img = ExcelImage(img_data)
                            excel_img.width = 140  # 이미지 너비 (셀에 꽉 채움)
                            excel_img.height = 140  # 이미지 높이 (셀에 꽉 채움)
                            
                            # A열(이미지 컬럼)에 이미지 삽입
                            cell_ref = f'A{i}'
                            worksheet.add_image(excel_img, cell_ref)
                            
                        except Exception as e:
                            print(f"이미지 삽입 실패 (행 {i}): {e}")
            
            # 컬럼 너비 설정 (타이틀 영역을 넓게)
            worksheet.column_dimensions['A'].width = 20  # 이미지 컬럼
            worksheet.column_dimensions['B'].width = 25  # 이름 컬럼 (넓게)
            worksheet.column_dimensions['C'].width = 20  # 사이즈 컬럼
            worksheet.column_dimensions['D'].width = 15  # 색상 컬럼
            worksheet.column_dimensions['E'].width = 15  # 가격 컬럼
            worksheet.column_dimensions['F'].width = 50  # 링크 컬럼 (넓게)
            
            # 모든 셀을 가운데 정렬 (가로, 세로 모두)
            from openpyxl.styles import Alignment
            from openpyxl.styles import Font
            
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 링크 컬럼(F열)에 URL 설정
            print(f"'{safe_sheet_name}' 시트 링크 설정 중...")
            for i, product in enumerate(products, start=2):  # 2부터 시작 (헤더 제외)
                if product.get('product_url'):
                    link_cell = worksheet[f'F{i}']  # F열은 링크 컬럼
                    # URL을 텍스트로 설정하고 파란색으로 표시
                    link_cell.value = product['product_url']
                    link_cell.font = Font(color="0000FF", underline="single")
                    print(f"링크 설정: {i-1}/{len(products)} - {product.get('name', 'Unknown')}")
                else:
                    link_cell = worksheet[f'F{i}']
                    link_cell.value = "링크 없음"
            
            print(f"'{safe_sheet_name}' 시트 완료!")

    total_products = sum(len(products) for products in sheet_data_dict.values())
    print(f"\n'{filepath}' 파일에 총 {len(sheet_data_dict)}개 시트, {total_products}개의 제품 정보를 성공적으로 저장했습니다.")

def save_to_excel(products, filename_prefix="ikea_products"):
    """
    단일 시트로 제품 정보를 Excel 파일로 저장합니다. (기존 호환성 유지)
    """
    if not products:
        print("저장할 제품 정보가 없습니다.")
        return

    # 단일 시트용으로 변환
    sheet_data = {"Products": products}
    save_to_excel_multi_sheet(sheet_data, filename_prefix)

def get_urls_from_excel():
    """
    Excel 파일에서 시트이름과 URL을 읽어옵니다.
    Excel 파일 형식: A열=시트이름, B열=URL
    """
    print("\nExcel 파일에서 URL을 읽어옵니다.")
    print("Excel 파일 형식:")
    print("A열: 시트이름")
    print("B열: URL")
    print("=" * 50)
    
    while True:
        file_path = input("Excel 파일 경로를 입력하세요: ").strip()
        
        if not file_path:
            print("파일 경로를 입력해주세요.")
            continue
            
        if not os.path.exists(file_path):
            print("파일을 찾을 수 없습니다. 다시 입력해주세요.")
            continue
            
        try:
            # Excel 파일 읽기
            df = pd.read_excel(file_path)
            
            # A열과 B열이 있는지 확인
            if len(df.columns) < 2:
                print("Excel 파일에 최소 2개의 컬럼(A열: 시트이름, B열: URL)이 필요합니다.")
                continue
                
            sheet_data = {}
            for index, row in df.iterrows():
                sheet_name = str(row.iloc[0]).strip()  # A열
                url = str(row.iloc[1]).strip()  # B열
                
                if sheet_name and url and sheet_name != 'nan' and url != 'nan':
                    sheet_data[sheet_name] = url
                    print(f"읽어온 데이터: '{sheet_name}' → {url}")
            
            if not sheet_data:
                print("유효한 데이터를 찾을 수 없습니다.")
                continue
                
            print(f"\n총 {len(sheet_data)}개의 시트 데이터를 읽어왔습니다.")
            return sheet_data
            
        except Exception as e:
            print(f"Excel 파일을 읽는 중 오류가 발생했습니다: {e}")
            continue

def get_multiple_urls_manual():
    """
    사용자로부터 여러 시트와 URL을 직접 입력받습니다.
    """
    print("이케아 제품 크롤링을 시작합니다.")
    print("여러 카테고리를 한 번에 크롤링할 수 있습니다.")
    print("=" * 60)
    print("입력 형식:")
    print("시트이름: 침실가구")
    print("링크: https://www.ikea.com/kr/ko/cat/bedroom-furniture-10601/")
    print("시트이름: 거실가구")
    print("링크: https://www.ikea.com/kr/ko/cat/living-room-furniture-10602/")
    print("시트이름: 완료")
    print("=" * 60)
    
    sheet_data = {}
    
    while True:
        print(f"\n현재 등록된 시트: {list(sheet_data.keys())}")
        
        sheet_name = input("시트이름을 입력하세요 (완료하려면 '완료' 입력): ").strip()
        
        if sheet_name.lower() == '완료':
            break
            
        if not sheet_name:
            print("시트이름을 입력해주세요.")
            continue
            
        url = input("해당 시트의 이케아 URL을 입력하세요: ").strip()
        
        if not url:
            print("URL을 입력해주세요.")
            continue
            
        sheet_data[sheet_name] = url
        print(f"'{sheet_name}' 시트가 등록되었습니다.")
    
    if not sheet_data:
        print("등록된 시트가 없습니다. 기본 URL을 사용합니다.")
        sheet_data = {"Products": "https://www.ikea.com/kr/ko/cat/storage-boxes-baskets-10550/?filters=f-materials%3A47675"}
    
    return sheet_data

def get_multiple_urls():
    """
    사용자로부터 입력 방식을 선택받고 해당 방식으로 URL을 가져옵니다.
    """
    print("이케아 제품 크롤링을 시작합니다.")
    print("=" * 60)
    print("입력 방식을 선택하세요:")
    print("1. Excel 파일에서 읽어오기 (여러 개)")
    print("2. 직접 입력하기 (1개 또는 여러 개)")
    print("=" * 60)
    
    while True:
        choice = input("선택하세요 (1 또는 2): ").strip()
        
        if choice == '1':
            return get_urls_from_excel()
        elif choice == '2':
            return get_multiple_urls_manual()
        else:
            print("1 또는 2를 입력해주세요.")
            continue

class IkeaCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("이케아 제품 크롤러")
        self.root.geometry("800x600")
        
        # 스타일 설정
        self.setup_styles()
        
        # 변수 초기화
        self.sheet_data = {}
        self.is_crawling = False
        
        self.setup_ui()
        
    def setup_styles(self):
        """GUI 스타일 설정"""
        style = ttk.Style()
        
        # 기본 테마 설정
        style.theme_use('clam')
        
        # 다크 테마 색상 설정
        bg_color = '#2b2b2b'  # 다크 배경
        fg_color = '#ffffff'  # 흰색 텍스트
        select_bg = '#404040'  # 선택된 배경
        accent_color = '#0078d4'  # 파란색 액센트
        
        # 루트 윈도우 배경 설정
        self.root.configure(bg=bg_color)
        
        # 탭 스타일 설정 - 동일한 크기로 고정
        style.configure('TNotebook', background=bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', 
                       padding=[30, 12],  # 동일한 패딩으로 크기 고정
                       background=bg_color,
                       foreground=fg_color,
                       borderwidth=1,
                       focuscolor='none')
        style.map('TNotebook.Tab', 
                 background=[('selected', select_bg), ('active', '#3a3a3a')],
                 foreground=[('selected', fg_color), ('active', fg_color)])
        
        # 버튼 스타일 설정
        style.configure('TButton', 
                       padding=[15, 8],
                       background=accent_color,
                       foreground=fg_color,
                       borderwidth=0,
                       focuscolor='none')
        style.map('TButton',
                 background=[('active', '#106ebe'), ('pressed', '#005a9e')],
                 foreground=[('active', fg_color), ('pressed', fg_color)])
        
        # 엔트리 스타일 설정
        style.configure('TEntry', 
                       fieldbackground='#404040', 
                       foreground=fg_color,
                       borderwidth=1,
                       insertcolor=fg_color)
        
        # 라벨 스타일 설정
        style.configure('TLabel', 
                       foreground=fg_color,
                       background=bg_color)
        
        # 프레임 스타일 설정
        style.configure('TFrame', background=bg_color)
        
        # 프로그레스바 스타일 설정
        style.configure('TProgressbar', 
                       background=accent_color,
                       troughcolor='#404040',
                       borderwidth=0)
        
        # 라벨프레임 스타일 설정
        style.configure('TLabelframe', 
                       background=bg_color,
                       foreground=fg_color,
                       borderwidth=1)
        style.configure('TLabelframe.Label', 
                       background=bg_color,
                       foreground=fg_color)
        
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="이케아 제품 크롤러", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 탭 생성
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 탭 선택 이벤트 바인딩
        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 탭 1: 단일 URL 입력
        single_frame = ttk.Frame(notebook, padding="10")
        notebook.add(single_frame, text="단일 URL 크롤링")
        
        # 단일 URL 입력
        ttk.Label(single_frame, text="시트 이름:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.single_sheet_entry = ttk.Entry(single_frame, width=50, font=('Arial', 10))
        self.single_sheet_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        ttk.Label(single_frame, text="URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.single_url_entry = ttk.Entry(single_frame, width=50, font=('Arial', 10))
        self.single_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        ttk.Button(single_frame, text="크롤링 시작", command=self.start_single_crawling).grid(row=2, column=0, columnspan=2, pady=10)
        
        # 탭 2: Excel 파일 업로드
        excel_frame = ttk.Frame(notebook, padding="10")
        notebook.add(excel_frame, text="Excel 파일 업로드")
        
        # Excel 파일 선택
        ttk.Label(excel_frame, text="Excel 파일 선택:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.excel_file_path = tk.StringVar()
        ttk.Entry(excel_frame, textvariable=self.excel_file_path, width=50, state="readonly", font=('Arial', 10)).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        ttk.Button(excel_frame, text="파일 선택", command=self.select_excel_file).grid(row=0, column=2, pady=5, padx=(5, 0))
        
        # Excel 파일 형식 안내
        format_label = ttk.Label(excel_frame, text="Excel 파일 형식: A열=시트이름, B열=URL", font=("Arial", 9))
        format_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Button(excel_frame, text="크롤링 시작", command=self.start_excel_crawling).grid(row=2, column=0, columnspan=3, pady=10)
        
        # 진행 상황 표시
        progress_frame = ttk.LabelFrame(main_frame, text="진행 상황", padding="10")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 프로그레스 바
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 로그 텍스트
        self.log_text = scrolledtext.ScrolledText(
            progress_frame, 
            height=15, 
            width=80,
            bg='#1e1e1e',
            fg='#ffffff',
            font=('Consolas', 9),
            wrap=tk.WORD,
            insertbackground='#ffffff',
            selectbackground='#404040',
            selectforeground='#ffffff'
        )
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        single_frame.columnconfigure(1, weight=1)
        excel_frame.columnconfigure(1, weight=1)
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)
        
    def on_tab_changed(self, event):
        """탭이 변경될 때 호출되는 이벤트 핸들러"""
        # 탭 변경 시 포커스 업데이트
        self.root.update()
        
    def log_message(self, message):
        """로그 메시지를 텍스트 위젯에 추가"""
        self.log_text.insert(tk.END, f"{datetime.datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def select_excel_file(self):
        """Excel 파일 선택"""
        file_path = filedialog.askopenfilename(
            title="Excel 파일 선택",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.excel_file_path.set(file_path)
            self.log_message(f"Excel 파일 선택됨: {file_path}")
            
    def start_single_crawling(self):
        """단일 URL 크롤링 시작"""
        sheet_name = self.single_sheet_entry.get().strip()
        url = self.single_url_entry.get().strip()
        
        if not sheet_name or not url:
            messagebox.showerror("오류", "시트 이름과 URL을 모두 입력해주세요.")
            return
            
        self.sheet_data = {sheet_name: url}
        self.start_crawling_thread()
        
    def start_excel_crawling(self):
        """Excel 파일 크롤링 시작"""
        file_path = self.excel_file_path.get()
        
        if not file_path:
            messagebox.showerror("오류", "Excel 파일을 선택해주세요.")
            return
            
        try:
            # Excel 파일 읽기
            df = pd.read_excel(file_path)
            
            if len(df.columns) < 2:
                messagebox.showerror("오류", "Excel 파일에 최소 2개의 컬럼(A열: 시트이름, B열: URL)이 필요합니다.")
                return
                
            sheet_data = {}
            for index, row in df.iterrows():
                sheet_name = str(row.iloc[0]).strip()
                url = str(row.iloc[1]).strip()
                
                if sheet_name and url and sheet_name != 'nan' and url != 'nan':
                    sheet_data[sheet_name] = url
                    
            if not sheet_data:
                messagebox.showerror("오류", "유효한 데이터를 찾을 수 없습니다.")
                return
                
            self.sheet_data = sheet_data
            self.log_message(f"Excel 파일에서 {len(sheet_data)}개의 시트 데이터를 읽어왔습니다.")
            self.start_crawling_thread()
            
        except Exception as e:
            messagebox.showerror("오류", f"Excel 파일을 읽는 중 오류가 발생했습니다: {e}")
            
    def start_crawling_thread(self):
        """크롤링을 별도 스레드에서 실행"""
        if self.is_crawling:
            messagebox.showwarning("경고", "이미 크롤링이 진행 중입니다.")
            return
            
        self.is_crawling = True
        self.progress.start()
        self.log_text.delete(1.0, tk.END)
        
        # 별도 스레드에서 크롤링 실행
        thread = threading.Thread(target=self.run_crawling)
        thread.daemon = True
        thread.start()
        
    def run_crawling(self):
        """실제 크롤링 실행"""
        try:
            self.log_message(f"총 {len(self.sheet_data)}개의 시트를 크롤링합니다.")
            
            all_sheet_data = {}
            
            for i, (sheet_name, url) in enumerate(self.sheet_data.items(), 1):
                self.log_message(f"\n=== '{sheet_name}' 시트 크롤링 시작 ({i}/{len(self.sheet_data)}) ===")
                self.log_message(f"URL: {url}")
                
                products = extract_product_data(url)
                self.log_message(f"'{sheet_name}' 시트 크롤링 완료: {len(products)}개 제품")
                
                all_sheet_data[sheet_name] = products
                
                # 제품 이름 목록 출력
                self.log_message(f"'{sheet_name}' 시트 수집된 제품 목록:")
                for j, product in enumerate(products, 1):
                    self.log_message(f"  {j}. {product.get('name', 'N/A')}")
            
            # Excel 파일 저장
            self.log_message(f"\n=== Excel 파일 저장 시작 ===")
            save_to_excel_multi_sheet(all_sheet_data)
            
            self.log_message("\n모든 크롤링이 완료되었습니다!")
            messagebox.showinfo("완료", "크롤링이 완료되었습니다!")
            
        except Exception as e:
            self.log_message(f"크롤링 중 오류가 발생했습니다: {e}")
            messagebox.showerror("오류", f"크롤링 중 오류가 발생했습니다: {e}")
            
        finally:
            self.is_crawling = False
            self.progress.stop()

def main():
    root = tk.Tk()
    app = IkeaCrawlerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()