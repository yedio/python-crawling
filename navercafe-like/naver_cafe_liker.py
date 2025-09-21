import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import urllib.parse

class NaverCafeLiker:
    def __init__(self, root):
        self.root = root
        self.root.title("네이버 카페 자동 좋아요 프로그램")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        self.driver = None
        self.is_running = False
        self.like_count = 0
        self.target_like_count = 0
        
        self.create_ui()
        
    def create_ui(self):
        """UI 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 로그인 정보 섹션
        login_frame = ttk.LabelFrame(main_frame, text="네이버 로그인 정보", padding="10")
        login_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(login_frame, text="아이디:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(login_frame, text="비밀번호:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.password_entry = ttk.Entry(login_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 카페 정보 섹션
        cafe_frame = ttk.LabelFrame(main_frame, text="카페 설정", padding="10")
        cafe_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(cafe_frame, text="카페 URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.cafe_url_entry = ttk.Entry(cafe_frame, width=50)
        self.cafe_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.cafe_url_entry.insert(0, "https://cafe.naver.com/f-e/cafes/17373998/menus/1618?viewType=L")
        
        ttk.Label(cafe_frame, text="목표 좋아요 수:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.target_count_entry = ttk.Entry(cafe_frame, width=10)
        self.target_count_entry.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        self.target_count_entry.insert(0, "10")
        
        # 제어 버튼
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="시작", command=self.start_automation)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="중지", command=self.stop_automation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 상태 정보
        status_frame = ttk.LabelFrame(main_frame, text="상태 정보", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="대기 중...")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.count_label = ttk.Label(status_frame, text="좋아요 수: 0")
        self.count_label.grid(row=1, column=0, sticky=tk.W)
        
        # 로그 출력
        log_frame = ttk.LabelFrame(main_frame, text="실행 로그", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        login_frame.columnconfigure(1, weight=1)
        cafe_frame.columnconfigure(1, weight=1)
        
    def log_message(self, message):
        """로그 메시지 출력"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_status(self, status, count=None):
        """상태 업데이트"""
        self.status_label.config(text=status)
        if count is not None:
            self.like_count = count
            self.count_label.config(text=f"좋아요 수: {self.like_count}/{self.target_like_count}")
        self.root.update()
        
    def start_automation(self):
        """자동화 시작"""
        # 입력값 검증
        if not self.username_entry.get().strip():
            messagebox.showerror("오류", "아이디를 입력해주세요.")
            return
            
        if not self.password_entry.get().strip():
            messagebox.showerror("오류", "비밀번호를 입력해주세요.")
            return
            
        if not self.cafe_url_entry.get().strip():
            messagebox.showerror("오류", "카페 URL을 입력해주세요.")
            return
            
        try:
            self.target_like_count = int(self.target_count_entry.get())
            if self.target_like_count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("오류", "올바른 목표 좋아요 수를 입력해주세요.")
            return
            
        self.is_running = True
        self.like_count = 0
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 별도 스레드에서 자동화 실행
        thread = threading.Thread(target=self.run_automation)
        thread.daemon = True
        thread.start()
        
    def stop_automation(self):
        """자동화 중지"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("중지됨")
        self.log_message("사용자에 의해 중지되었습니다.")
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            
    def setup_driver(self):
        """웹드라이버 설정"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except Exception as e:
            self.log_message(f"웹드라이버 설정 실패: {str(e)}")
            return False
            
    def login_naver(self):
        """네이버 로그인"""
        try:
            self.log_message("네이버 로그인 페이지로 이동 중...")
            self.driver.get("https://nid.naver.com/nidlogin.login")
            
            # 로그인 폼 대기
            wait = WebDriverWait(self.driver, 10)
            
            # 아이디 입력
            username_field = wait.until(EC.presence_of_element_located((By.ID, "id")))
            username_field.clear()
            username_field.send_keys(self.username_entry.get())
            
            # 비밀번호 입력
            password_field = self.driver.find_element(By.ID, "pw")
            password_field.clear()
            password_field.send_keys(self.password_entry.get())
            
            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.ID, "log.login")
            login_button.click()
            
            # 로그인 완료 대기 (메인 페이지 또는 2단계 인증 페이지)
            time.sleep(3)
            
            # 2단계 인증이 필요한 경우
            if "2단계" in self.driver.page_source or "인증" in self.driver.page_source:
                self.log_message("2단계 인증이 필요합니다. 수동으로 완료해주세요.")
                # 사용자가 2단계 인증을 완료할 때까지 대기
                while "naver.com" not in self.driver.current_url or "login" in self.driver.current_url:
                    if not self.is_running:
                        return False
                    time.sleep(1)
            
            self.log_message("네이버 로그인 완료")
            return True
            
        except Exception as e:
            self.log_message(f"로그인 실패: {str(e)}")
            return False
            
    def navigate_to_cafe(self):
        """카페로 이동"""
        try:
            cafe_url = self.cafe_url_entry.get().strip()
            self.log_message(f"카페로 이동 중: {cafe_url}")
            self.driver.get(cafe_url)
            time.sleep(2)
            
            # 카페 페이지인지 확인
            if "cafe.naver.com" not in self.driver.current_url:
                raise Exception("올바른 카페 URL이 아닙니다.")
                
            self.log_message("카페 접속 완료")
            return True
            
        except Exception as e:
            self.log_message(f"카페 접속 실패: {str(e)}")
            return False
            
    def get_post_links(self):
        """게시글 링크 목록 가져오기 (공지글 제외)"""
        try:
            post_links = []
            
            # article-board div 찾기
            article_board = self.driver.find_element(By.CLASS_NAME, "article-board")
            
            # article-table 찾기
            article_table = article_board.find_element(By.CLASS_NAME, "article-table")
            
            # tbody 요소들 찾기
            tbodies = article_table.find_elements(By.TAG_NAME, "tbody")
            
            for tbody in tbodies:
                # 첫 번째 tr이 공지글인지 확인
                first_tr = tbody.find_elements(By.TAG_NAME, "tr")[0]
                if "board-notice" in first_tr.get_attribute("class"):
                    self.log_message("공지글 tbody 건너뛰기")
                    continue
                
                # 일반글 tr들 처리
                trs = tbody.find_elements(By.TAG_NAME, "tr")
                for tr in trs:
                    if "board-notice" not in tr.get_attribute("class"):
                        try:
                            # board-list 클래스를 가진 td 찾기
                            board_list_td = tr.find_element(By.CLASS_NAME, "board-list")
                            # a 태그 찾기
                            link_element = board_list_td.find_element(By.TAG_NAME, "a")
                            href = link_element.get_attribute("href")
                            title = link_element.text.strip()
                            
                            if href:
                                post_links.append((href, title))
                                self.log_message(f"게시글 발견: {title}")
                                
                        except NoSuchElementException:
                            continue
            
            return post_links
            
        except Exception as e:
            self.log_message(f"게시글 목록 가져오기 실패: {str(e)}")
            return []
            
    def like_post(self, post_url, post_title):
        """게시글 좋아요"""
        try:
            self.log_message(f"게시글 접속: {post_title}")
            self.driver.get(post_url)
            time.sleep(3)  # 페이지 로딩 대기 시간 증가
            
            # iframe이 있는지 확인하고 전환
            try:
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                if iframes:
                    self.log_message(f"iframe 발견: {len(iframes)}개")
                    # 가장 큰 iframe으로 전환 시도
                    main_iframe = None
                    max_size = 0
                    for iframe in iframes:
                        try:
                            size = iframe.size['width'] * iframe.size['height']
                            if size > max_size:
                                max_size = size
                                main_iframe = iframe
                        except:
                            continue
                    
                    if main_iframe:
                        self.driver.switch_to.frame(main_iframe)
                        self.log_message("메인 iframe으로 전환함")
                        time.sleep(1)
            except Exception as e:
                self.log_message(f"iframe 처리 중 오류: {str(e)}")
            
            # 여러 선택자로 좋아요 버튼 찾기 시도
            wait = WebDriverWait(self.driver, 15)
            like_button = None
            
            # 선택자 우선순위대로 시도
            selectors = [
                ".ReplyBox .box_left .like_article .u_likeit_list_btn",  # 사용자 제공 구조
                ".like_article .u_likeit_list_btn",  # 기존 선택자
                ".u_likeit_list_btn",  # 간단한 선택자
                "a[data-type='like']",  # data-type 속성 기반
                ".like_no.u_likeit_list_btn._button"  # 전체 클래스명
            ]
            
            for selector in selectors:
                try:
                    self.log_message(f"선택자 시도: {selector}")
                    like_button = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, selector)
                    ))
                    self.log_message(f"좋아요 버튼 찾기 성공: {selector}")
                    break
                except TimeoutException:
                    self.log_message(f"선택자 실패: {selector}")
                    continue
            
            if not like_button:
                self.log_message("좋아요 버튼을 찾을 수 없습니다.")
                # 디버깅 정보 출력
                self.debug_page_elements()
                return False
            
            # 이미 좋아요 했는지 확인
            button_class = like_button.get_attribute("class")
            aria_pressed = like_button.get_attribute("aria-pressed")
            
            self.log_message(f"버튼 클래스: {button_class}")
            self.log_message(f"aria-pressed: {aria_pressed}")
            
            # 버튼의 전체 HTML 구조 확인 (디버깅용)
            try:
                outer_html = like_button.get_attribute("outerHTML")
                # HTML이 너무 길면 일부만 출력
                if len(outer_html) > 200:
                    outer_html = outer_html[:200] + "..."
                self.log_message(f"버튼 HTML: {outer_html}")
            except Exception as e:
                self.log_message(f"HTML 구조 확인 실패: {str(e)}")
            
            # 좋아요 상태 정확히 판단
            # aria-pressed 속성을 우선적으로 확인
            if aria_pressed == "true":
                self.log_message("이미 좋아요한 게시글입니다. (aria-pressed=true)")
                return False
            elif aria_pressed == "false":
                self.log_message("좋아요 가능한 게시글입니다. (aria-pressed=false)")
            else:
                # aria-pressed가 없으면 클래스로 판단
                if " on" in button_class or button_class.endswith(" on"):
                    self.log_message("이미 좋아요한 게시글입니다. (클래스에 on 포함)")
                    return False
                elif " off" in button_class or button_class.endswith(" off"):
                    self.log_message("좋아요 가능한 게시글입니다. (클래스에 off 포함)")
                else:
                    self.log_message(f"좋아요 상태 불명확 - 일단 시도해보기")
                    self.log_message(f"클래스: {button_class}, aria-pressed: {aria_pressed}")
            
            # 스크롤하여 버튼이 보이도록 함
            self.driver.execute_script("arguments[0].scrollIntoView(true);", like_button)
            time.sleep(1)
                
            # 좋아요 클릭 (여러 방법 시도)
            self.log_message("좋아요 버튼 클릭 시도...")
            
            # 방법 1: 일반 클릭
            try:
                like_button.click()
                time.sleep(2)
            except Exception as e1:
                self.log_message(f"일반 클릭 실패: {str(e1)}")
                
                # 방법 2: JavaScript 클릭
                try:
                    self.log_message("JavaScript 클릭 시도...")
                    self.driver.execute_script("arguments[0].click();", like_button)
                    time.sleep(2)
                except Exception as e2:
                    self.log_message(f"JavaScript 클릭 실패: {str(e2)}")
                    
                    # 방법 3: ActionChains 클릭
                    try:
                        self.log_message("ActionChains 클릭 시도...")
                        ActionChains(self.driver).move_to_element(like_button).click().perform()
                        time.sleep(2)
                    except Exception as e3:
                        self.log_message(f"ActionChains 클릭 실패: {str(e3)}")
                        return False
            
            # 좋아요 성공 확인
            updated_class = like_button.get_attribute("class")
            updated_aria = like_button.get_attribute("aria-pressed")
            
            self.log_message(f"클릭 후 클래스: {updated_class}")
            self.log_message(f"클릭 후 aria-pressed: {updated_aria}")
            
            # 좋아요 성공 확인 - aria-pressed 우선 확인
            if updated_aria == "true":
                self.log_message(f"좋아요 완료: {post_title} (aria-pressed=true)")
                return True
            elif aria_pressed == "false" and updated_aria == "true":
                self.log_message(f"좋아요 완료: {post_title} (false->true)")
                return True
            else:
                # 클래스 변화로 확인
                if (" off" in button_class or button_class.endswith(" off")) and (" on" in updated_class or updated_class.endswith(" on")):
                    self.log_message(f"좋아요 완료: {post_title} (off->on)")
                    return True
                elif " on" in updated_class or updated_class.endswith(" on"):
                    self.log_message(f"좋아요 완료: {post_title} (클래스에 on 포함)")
                    return True
                else:
                    self.log_message("좋아요 실패 - 상태가 변경되지 않음")
                    self.log_message(f"이전 클래스: {button_class}")
                    self.log_message(f"이후 클래스: {updated_class}")
                    self.log_message(f"이전 aria-pressed: {aria_pressed}")
                    self.log_message(f"이후 aria-pressed: {updated_aria}")
                    return False
                
        except Exception as e:
            self.log_message(f"좋아요 처리 실패: {str(e)}")
            # 페이지 소스에서 좋아요 관련 요소 확인
            try:
                if "like_article" in self.driver.page_source:
                    self.log_message("페이지에 like_article 요소가 존재함")
                else:
                    self.log_message("페이지에 like_article 요소가 없음")
            except:
                pass
            return False
        finally:
            # iframe에서 빠져나오기
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
    def debug_page_elements(self):
        """페이지의 좋아요 관련 요소들을 디버깅"""
        try:
            self.log_message("=== 페이지 요소 디버깅 시작 ===")
            
            # 좋아요 관련 모든 요소 찾기
            like_elements = self.driver.find_elements(By.CSS_SELECTOR, "*[class*='like']")
            self.log_message(f"'like'가 포함된 요소 수: {len(like_elements)}")
            
            for i, elem in enumerate(like_elements[:5]):  # 처음 5개만 출력
                try:
                    tag = elem.tag_name
                    classes = elem.get_attribute("class")
                    text = elem.text[:50] if elem.text else ""
                    self.log_message(f"  {i+1}. {tag} - class: {classes} - text: {text}")
                except:
                    continue
            
            # ReplyBox 찾기
            reply_boxes = self.driver.find_elements(By.CSS_SELECTOR, "*[class*='ReplyBox'], *[class*='reply']")
            self.log_message(f"ReplyBox/reply 관련 요소 수: {len(reply_boxes)}")
            
            # 버튼 요소들 찾기
            buttons = self.driver.find_elements(By.TAG_NAME, "a")
            like_buttons = [btn for btn in buttons if "like" in btn.get_attribute("class").lower()]
            self.log_message(f"좋아요 관련 버튼 수: {len(like_buttons)}")
            
            for i, btn in enumerate(like_buttons[:3]):
                try:
                    classes = btn.get_attribute("class")
                    data_type = btn.get_attribute("data-type")
                    aria_pressed = btn.get_attribute("aria-pressed")
                    self.log_message(f"  버튼 {i+1}: class={classes}, data-type={data_type}, aria-pressed={aria_pressed}")
                except:
                    continue
                    
            self.log_message("=== 페이지 요소 디버깅 완료 ===")
            
        except Exception as e:
            self.log_message(f"디버깅 중 오류: {str(e)}")
            
    def go_to_next_page(self, current_page):
        """다음 페이지로 이동"""
        try:
            cafe_url = self.cafe_url_entry.get().strip()
            next_page = current_page + 1
            
            # URL에 페이지 파라미터 추가
            if "?" in cafe_url:
                next_url = f"{cafe_url}&page={next_page}"
            else:
                next_url = f"{cafe_url}?page={next_page}"
                
            self.log_message(f"다음 페이지로 이동: {next_page}페이지")
            self.driver.get(next_url)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.log_message(f"페이지 이동 실패: {str(e)}")
            return False
            
    def run_automation(self):
        """자동화 메인 로직"""
        try:
            self.update_status("웹드라이버 설정 중...")
            if not self.setup_driver():
                self.stop_automation()
                return
                
            self.update_status("네이버 로그인 중...")
            if not self.login_naver():
                self.stop_automation()
                return
                
            self.update_status("카페 접속 중...")
            if not self.navigate_to_cafe():
                self.stop_automation()
                return
                
            current_page = 1
            
            while self.is_running and self.like_count < self.target_like_count:
                self.update_status(f"게시글 탐색 중... ({current_page}페이지)")
                
                # 현재 페이지의 게시글 링크 가져오기
                post_links = self.get_post_links()
                
                if not post_links:
                    self.log_message("더 이상 게시글이 없습니다.")
                    break
                    
                # 각 게시글에 좋아요
                for post_url, post_title in post_links:
                    if not self.is_running or self.like_count >= self.target_like_count:
                        break
                        
                    if self.like_post(post_url, post_title):
                        self.like_count += 1
                        self.update_status(f"좋아요 진행 중...", self.like_count)
                        
                        if self.like_count >= self.target_like_count:
                            self.log_message(f"목표 좋아요 수({self.target_like_count})에 도달했습니다!")
                            break
                            
                    time.sleep(1)  # 요청 간격
                    
                # 다음 페이지로 이동
                if self.is_running and self.like_count < self.target_like_count:
                    if not self.go_to_next_page(current_page):
                        break
                    current_page += 1
                    
            if self.like_count >= self.target_like_count:
                self.update_status("완료!")
                self.log_message("자동화가 성공적으로 완료되었습니다.")
            else:
                self.update_status("중단됨")
                
        except Exception as e:
            self.log_message(f"자동화 실행 중 오류: {str(e)}")
            self.update_status("오류 발생")
            
        finally:
            self.stop_automation()

if __name__ == "__main__":
    root = tk.Tk()
    app = NaverCafeLiker(root)
    root.mainloop()
