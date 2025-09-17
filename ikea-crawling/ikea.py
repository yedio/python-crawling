
import time
import csv
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_product_titles(url):
    """
    Selenium을 사용하여 이케아 웹사이트에서 '더 보기' 버튼을 모두 클릭한 후
    plp-fragment-wrapper 클래스를 가진 아이템들의 타이틀을 수집합니다.
    """
    service = Service()
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # 브라우저 창을 보지 않고 실행하려면 주석을 해제하세요.
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"URL: {url}")
        driver.get(url)

        # 페이지가 로드될 때까지 최대 5초 대기
        print("페이지가 로드되기를 기다립니다...")
        WebDriverWait(driver,5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.plp-fragment-wrapper"))
        )
        print("초기 페이지 로드 완료.")

        # --- '더 보기' 버튼을 반복해서 클릭하여 모든 제품 로드 ---
        click_count = 0
        max_pages = 10  # 최대 페이지 수 제한 (무한루프 방지)
        
        while click_count < max_pages:
            try:
                # 현재 URL 확인
                current_url = driver.current_url
                print(f"\n=== {click_count + 1}번째 시도 ===")
                print(f"현재 URL: {current_url}")
                
                # 현재 아이템 개수 확인
                current_items = driver.find_elements(By.CSS_SELECTOR, "div.plp-fragment-wrapper")
                print(f"현재 아이템 개수: {len(current_items)}개")
                
                # 더보기 버튼 찾기
                print("더보기 버튼을 찾는 중...")
                try:
                    more_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[aria-label="더 많은 제품 보기"]'))
                    )
                    print("✓ 더보기 버튼을 찾았습니다!")
                except Exception as e:
                    print(f"❌ 더보기 버튼을 찾을 수 없습니다: {e}")
                    print("모든 페이지를 로드했습니다.")
                    break
                
                # 클릭 전 URL 저장
                url_before_click = driver.current_url
                
                # 버튼을 클릭하기 위해 스크롤
                print("버튼으로 스크롤 중...")
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
                    time.sleep(3) # 스크롤 후 버튼 활성화를 위한 대기
                except Exception as e:
                    print(f"스크롤 중 오류: {e}")
                
                print("더보기 버튼 클릭 중...")
                try:
                    # JavaScript로 클릭 시도 (더 안정적)
                    driver.execute_script("arguments[0].click();", more_button)
                    click_count += 1
                    print(f"✓ 더 보기 버튼 클릭 완료 ({click_count}번째).")
                except Exception as e:
                    print(f"JavaScript 클릭 실패, 일반 클릭 시도: {e}")
                    try:
                        more_button.click()
                        click_count += 1
                        print(f"✓ 더 보기 버튼 클릭 완료 ({click_count}번째).")
                    except Exception as e2:
                        print(f"❌ 클릭 실패: {e2}")
                        break
                
                # 페이지 이동 대기 (URL이 변경될 수 있음)
                print("페이지 로딩 대기 중...")
                time.sleep(5) # 페이지 로딩을 위한 대기 시간
                
                # URL이 변경되었는지 확인
                try:
                    url_after_click = driver.current_url
                    if url_before_click != url_after_click:
                        print(f"✓ 페이지 이동 감지: {url_before_click} -> {url_after_click}")
                        # 페이지 이동 후 새로운 요소들이 로드될 때까지 추가 대기
                        print("새 페이지 로딩 대기 중...")
                        time.sleep(3)
                    else:
                        print("URL 변경 없음 (AJAX 로딩)")
                except Exception as e:
                    print(f"URL 확인 중 오류: {e}")
                
                # 클릭 후 아이템 개수 확인
                try:
                    new_items = driver.find_elements(By.CSS_SELECTOR, "div.plp-fragment-wrapper")
                    print(f"클릭 후 아이템 개수: {len(new_items)}개")
                    
                    # 아이템 개수가 변하지 않으면 더 이상 로드할 것이 없음
                    if len(new_items) == len(current_items):
                        print("❌ 새로운 아이템이 로드되지 않았습니다. 종료합니다.")
                        break
                    else:
                        print(f"✓ {len(new_items) - len(current_items)}개의 새 아이템이 로드되었습니다.")
                except Exception as e:
                    print(f"아이템 개수 확인 중 오류: {e}")
                    # 오류가 발생해도 계속 진행
                
            except Exception as e:
                # 더 이상 '더 보기' 버튼이 없으면 루프 종료
                print(f"❌ 더 이상 '더 보기' 버튼이 없습니다. 모든 제품을 로드했습니다. (총 {click_count}번 클릭)")
                print(f"에러 상세: {e}")
                break

        # --- plp-fragment-wrapper 아이템들의 타이틀 수집 ---
        item_selector = "div.plp-fragment-wrapper"
        item_elements = driver.find_elements(By.CSS_SELECTOR, item_selector)
        print(f"총 {len(item_elements)}개의 아이템을 찾았습니다.")
        
        titles = []
        for i, item in enumerate(item_elements):
            try:
                # 제품 타이틀 추출
                title_element = item.find_element(By.CSS_SELECTOR, "span.plp-price-module__product-name")
                title = title_element.text.strip()
                titles.append(title)
                print(f"{i+1}. {title}")
            except Exception as e:
                print(f"아이템 {i+1} 타이틀 추출 실패: {e}")
                continue

    except Exception as e:
        print(f"크롤링 중 오류가 발생했습니다: {e}")
        titles = []

    finally:
        print("브라우저를 닫습니다.")
        driver.quit()

    return titles

def save_to_csv(products, filename_prefix="ikea_products"):
    """
    수집된 제품 정보를 CSV 파일로 저장합니다.
    """
    if not products:
        print("저장할 제품 정보가 없습니다.")
        return

    today = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"{filename_prefix}_{today}.csv"

    with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
        fieldnames = ['name', 'price', 'image_url', 'product_url']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

    print(f"'{filename}' 파일에 총 {len(products)}개의 제품 정보를 성공적으로 저장했습니다.")

if __name__ == "__main__":
    TARGET_URL = "https://www.ikea.com/kr/ko/cat/storage-boxes-baskets-10550/?filters=f-materials%3A47675"
    product_titles = get_product_titles(TARGET_URL)
    print(f"\n최종 결과: 총 {len(product_titles)}개의 제품 타이틀을 수집했습니다.")
    print("\n수집된 타이틀 목록:")
    for i, title in enumerate(product_titles, 1):
        print(f"{i}. {title}")