
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

        # 페이지가 로드될 때까지 최대 10초 대기
        print("페이지가 로드되기를 기다립니다...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.plp-fragment-wrapper"))
        )
        print("초기 페이지 로드 완료.")

        # --- plp-fragment-wrapper 아이템들의 데이터 수집 ---
        item_selector = "div.plp-fragment-wrapper"
        item_elements = driver.find_elements(By.CSS_SELECTOR, item_selector)
        print(f"총 {len(item_elements)}개의 아이템을 찾았습니다.")
        
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
                
                # 각 데이터 추출 시마다 요소를 다시 찾기
                try:
                    # 1. 이름 추출 - 여러 선택자 시도
                    try:
                        # 현재 아이템을 다시 찾기
                        current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                        if i < len(current_items):
                            item = current_items[i]
                            # 먼저 plp-mastercard 안에서 찾기
                            name_element = item.find_element(By.CSS_SELECTOR, "div.plp-mastercard span.plp-price-module__product-name")
                            product_data['name'] = name_element.text.strip()
                            print(f"{i+1}. {product_data['name']}")
                        else:
                            product_data['name'] = ""
                    except Exception as e1:
                        try:
                            # 현재 아이템을 다시 찾기
                            current_items = driver.find_elements(By.CSS_SELECTOR, item_selector)
                            if i < len(current_items):
                                item = current_items[i]
                                # 다른 선택자로 시도
                                name_element = item.find_element(By.CSS_SELECTOR, "span.plp-price-module__product-name")
                                product_data['name'] = name_element.text.strip()
                                print(f"{i+1}. {product_data['name']}")
                            else:
                                product_data['name'] = ""
                        except Exception as e2:
                            print(f"아이템 {i+1} 이름 추출 실패: {e1}, {e2}")
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

def save_to_excel(products, filename_prefix="ikea_products"):
    """
    수집된 제품 정보를 Excel 파일로 저장합니다.
    """
    if not products:
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

    # DataFrame 생성
    df = pd.DataFrame(products)
    
    # 컬럼 순서 정리 (이미지, 이름, 사이즈, 색상, 가격, 링크)
    # 이미지 전용 컬럼을 추가하기 위해 빈 컬럼을 먼저 생성
    df['이미지'] = ''  # 이미지 전용 컬럼
    columns = ['이미지', 'name', 'size', 'color', 'price', 'product_url']
    df = df.reindex(columns=columns)
    
    # 컬럼명을 한국어로 변경
    df.columns = ['이미지', '이름', '사이즈', '색상', '가격', '링크']
    
    # Excel 파일로 저장
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)
        
        # 워크시트 가져오기
        worksheet = writer.sheets['Products']
        
        # 헤더 행(1행)은 기본 높이로, 데이터 행들은 152px로 설정
        worksheet.row_dimensions[1].height = 15  # 헤더는 기본 높이
        for i in range(2, len(products) + 2):  # 데이터 행들만
            worksheet.row_dimensions[i].height = 114  # 152px ≈ 114 포인트 (1포인트 = 1.33픽셀)
        
        # 이미지 삽입 (첫 번째 컬럼이 이미지)
        print("이미지를 다운로드하고 엑셀에 삽입하는 중...")
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
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(horizontal='center', vertical='center')

    print(f"'{filepath}' 파일에 총 {len(products)}개의 제품 정보를 성공적으로 저장했습니다.")

if __name__ == "__main__":
    TARGET_URL = "https://www.ikea.com/kr/ko/cat/storage-boxes-baskets-10550/?filters=f-materials%3A47675"
    products = extract_product_data(TARGET_URL)
    print(f"\n최종 결과: 총 {len(products)}개의 제품 데이터를 수집했습니다.")
    
    # Excel 파일로 저장
    save_to_excel(products)
    
    print("\n수집된 제품 이름 목록:")
    for i, product in enumerate(products, 1):
        print(f"{i}. {product.get('name', 'N/A')}")