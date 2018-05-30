# 인터파크 투어 사이트에서 여행지를 입력 후 검색 -> 잠시 후 -> 결과
# 로그인 시 PC 웹사이트에서 처리가 어려울 경우 -> 모바일 로그인으로 진입
# 모듈 가져오기
# pip install selenium
import sys
import time

from bs4 import BeautifulSoup
from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tour import TourInfo

# 사전에 필요한 정보를 로드 => DB 혹은 쉘, batch 파일에서 인자로 받아서 세팅
main_url = 'http://tour.interpark.com'
keyword = '로마'
# 상품 정보 리스트
tour_list = []

# 드라이버 로드
driver = wd.Chrome(executable_path="chromedriver.exe")
# todo 옵션 부여 (proxy, agent 변경, 이미지를 배제)
# 크롤링을 오래 돌릴 경우 임시 파일들이 누적 됨 -> temp 폴더 정리

# 사이트 접속 (get)
driver.get(main_url)

# 검색창 찾아서 검색어 입력
driver.find_element_by_id('SearchGNBText').send_keys(keyword)

# 검색 버튼 클릭
driver.find_element_by_css_selector('button.search-btn').click()

# wait -> page 로드되고 나서 즉각적으로 데이터를 획득하는 행위는 자제
# 명시적 대기 -> 특정 요소를 배치 될 때(located)까지 대기
try:
    element = WebDriverWait(driver, 10).until(
        # 지정한 요소가 배치되면 wait 종료
        EC.presence_of_element_located(By.CLASS_NAME, 'oTravelBox')
    )
except Exception as e1:
    print('error occurred', e1)
# 묵시적 대기 -> DOM이 전부 로드 될 때까지 대기
driver.implicitly_wait(10)
# 무조건 대기 -> 지정한 시간만큼 무조건 대기 -> time.sleep() : 디도스 방어 솔루션을 대처하기 위함

# 더보기 눌러서 게시판 진입
driver.find_element_by_css_selector('.oTravelBox>.boxList>.moreBtnWrap>.moreBtn').click()

# 게시판에서 데이터를 가져올 때
# 데이터가 많으면 세션 관리
# 특정 단위 별로 로그아웃 -> 로그인을 반복
# 특정 게시물이 존재하지 않을 경우 처리 검토
# 게시판 스캔 시 해당 목록의 끝을 모를 수 있음
# 게시판 메타 정보 획득하여 방문 처리

# 페이지 이동 -> searchModule.SetCategoryList(1, '')
for page in range(1, 2):
    try:
        # 페이지 이동 js 실행
        driver.execute_script("searchModule.SetCategoryList(%s, '')" % page)
        time.sleep(2)
        print('page %s load' % page)

        # 상품명, 코멘트, 기간1, 기간2, 가격, 평점, 썸네일, 상세정보 링크
        boxItems = driver.find_elements_by_css_selector('.oTravelBox>.boxList>li')
        # 각 상품마다 방문
        for li in boxItems:
            thumbnail = li.find_element_by_css_selector('img').get_attribute('src')
            print('썸네일', thumbnail)
            link = li.find_element_by_css_selector('a').get_attribute('onclick')
            print('링크', link)
            title = li.find_element_by_css_selector('h5.proTit').text
            print('상품명', title)
            comment = li.find_element_by_css_selector('.proSub').text
            print('코멘트', comment)
            price = li.find_element_by_css_selector('.proPrice').text
            print('가격: ', price)

            info_list = li.find_elements_by_css_selector('.info-row .proInfo')
            for info in info_list:
                print(info.text)
            print('=' * 50)

            # 데이터 저장 (데이터가 부족하거나 없을 수 있으므로 인덱스 참조는 위험성 존재)
            tour_info = TourInfo(title, price, info_list[1].text, link, thumbnail)
            tour_list.append(tour_info)
    except Exception as e1:
        print('오류 발생', e1)

print(tour_list, len(tour_list))

# 수집한 여행 정보 각각의 페이지 방문 -> 상품 상세 정보 획득 -> DB
for tour in tour_list:
    print(type(tour))
    # link 전처리 (onclick~~~ 제거)
    token = tour.link.split(',')
    if token:
        # 대체
        link = token[0].replace('searchModule.OnClickDetail(', '')
        # 슬라이싱 (앞 뒤의 홑따옴표 ' 제거)
        detail_url = link[1:-1]
        # 상세 페이지 이동 : 절대경로인지 상대경로인지 확인
        driver.get(detail_url)
        time.sleep(2)

        # pip install bs4
        # 현재 페이지를 BeautifuleSoup으로 DOM 구성
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data = soup.select('.tip-cover')
        print(type(data), len(data))

        # DB 저장


# 종료
driver.close()
driver.quit()
sys.exit()
