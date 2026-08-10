/**
 * 만 나이 계산기 JavaScript 모듈
 * 날짜 입력 자동화 및 폼 처리 기능
 */
class AgeCalculatorUI {
    constructor() {
        this.birthInput = null;
        this.birthErrorEl = null;
        this.hiddenDateInput = null;
        this.form = null;
        this.adRefreshTimer = null; // 구글 애드 리프레시 타이머
        this.autoCalcTimer = null; // 자동 계산 타이머

        this.init();
    }

    /**
     * 초기화
     */
    init() {
        // 생년월일 8자리 입력 요소
        this.birthInput = document.getElementById('birth-input');
        this.birthErrorEl = document.getElementById('birth-error');
        this.form = document.querySelector('.age-form');

        if (this.validateElements()) {
            this.bindEvents();
            this.setInitialFocus();
            this.initializeZodiacInfo();
            setTimeout(() => {
                this.loadFromUrl();
            }, 100);
        }
    }

    /**
     * 필수 요소들이 존재하는지 검증
     */
    validateElements() {
        return this.birthInput !== null && this.form !== null;
    }

    /**
     * 이벤트 바인딩
     */
    bindEvents() {
        this.bindBirthDateInputEvents();
        this.bindAutoCalculation();
        this.bindZodiacPreview();
        this.bindShareEvents();
        this.bindCookieEvents();
        this.bindScrollTopEvents();
        this.bindCalendarToggle();
    }

    /**
     * 음력/양력 토글 이벤트 바인딩
     */
    bindCalendarToggle() {
        const radioButtons = document.querySelectorAll('input[name="calendar_type"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', () => {
                // 값이 유효하면 재계산
                if (this.birthInput && this.birthInput.value.length === 8) {
                    const v = this.validateBirthDate(this.birthInput.value);
                    if (v.valid) {
                        this.autoCalculateFromBirthDate(v);
                    }
                }
            });
        });
    }

    /**
     * 입력 이벤트 바인딩
     */
    bindInputEvents() {
        // 년도 입력 시 자동 포커스 이동
        this.yearInput.addEventListener('input', (e) => {
            if (e.target.value.length === 4) {
                this.monthInput.focus();
            }
        });

        // 월 입력 시 자동 포커스 이동
        this.monthInput.addEventListener('input', (e) => {
            if (e.target.value.length === 2) {
                this.dayInput.focus();
            }
        });
    }

    bindBirthDateInputEvents() {
        if (!this.birthInput) return;

        // 숫자만 입력 허용
        this.birthInput.addEventListener('keypress', (e) => {
            if (!/[0-9]/.test(e.key)) {
                e.preventDefault();
            }
        });
    }

    /**
     * 키 입력 제한 (숫자만 허용)
     */
    bindKeyPressEvents() {
        const inputs = [this.yearInput, this.monthInput, this.dayInput];

        inputs.forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (!/[0-9]/.test(e.key)) {
                    e.preventDefault();
                }
            });
        });
    }

    /**
     * 백스페이스로 이전 필드 이동
     */
    bindBackspaceEvents() {
        // 월 필드에서 백스페이스
        this.monthInput.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && e.target.value.length === 0) {
                this.yearInput.focus();
            }
        });

        // 일 필드에서 백스페이스
        this.dayInput.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && e.target.value.length === 0) {
                this.monthInput.focus();
            }
        });
    }

    /**
     * 엔터키 이벤트 처리
     */
    bindEnterKeyEvents() {
        // 년도 필드에서 엔터키
        this.yearInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (this.validateYear(this.yearInput.value)) {
                    this.monthInput.focus();
                } else {
                    this.showError(this.yearInput, '올바른 년도를 입력하세요 (1900년 이상)');
                }
            }
        });

        // 월 필드에서 엔터키
        this.monthInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (this.validateMonth(this.monthInput.value)) {
                    this.dayInput.focus();
                } else {
                    this.showError(this.monthInput, '올바른 월을 입력하세요 (01-12)');
                }
            }
        });

        // 일 필드에서 엔터키 - 폼 제출
        this.dayInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (this.validateDay(this.dayInput.value)) {
                    this.submitForm();
                } else {
                    this.showError(this.dayInput, '올바른 일을 입력하세요 (01-31)');
                }
            }
        });
    }



    /**
     * 12지신 정보 업데이트 (단순화된 버전)
     */
    updateZodiacInfo() {
        //const year = parseInt(this.yearInput.value);
        const year = this.getBirthYear();
        console.log('12지신 업데이트 시도, 년도:', year); // 디버깅용

        if (year && year >= 1900) {
            const zodiacInfo = DateUtils.getZodiacSign(year);
            console.log('12지신 정보:', zodiacInfo); // 디버깅용

            // 12지신 정보를 DOM에 업데이트 (단순화된 버전)
            const zodiacSimple = document.getElementById('zodiac-simple');

            if (zodiacSimple) {
                zodiacSimple.textContent = `(${zodiacInfo.emoji} ${zodiacInfo.animal})`;
                console.log('12지신 정보 업데이트 완료'); // 디버깅용
            } else {
                console.log('12지신 DOM 요소를 찾을 수 없음'); // 디버깅용
            }
        } else {
            console.log('유효하지 않은 년도:', year); // 디버깅용
        }
    }

    /**
     * 입력 필드 변경 시 12지신 미리보기 (제거됨 - 단순화)
     */
    bindZodiacPreview() {
        // 12지신 미리보기 기능 제거 - 단순화
    }

    /**
     * 공유하기 이벤트 처리
     */
    bindShareEvents() {
        const shareButtons = document.querySelectorAll('[data-share]');

        shareButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const shareType = e.currentTarget.getAttribute('data-share');
                this.handleShare(shareType);
            });
        });

        // 링크 복사 버튼 이벤트 처리
        const linkCopyBtn = document.querySelector('.link-copy-btn');
        if (linkCopyBtn) {
            linkCopyBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.copyLinkToClipboard();
            });
        }

        // 이미지 저장 버튼 이벤트 처리
        const imageSaveBtn = document.querySelector('.image-save-btn');
        if (imageSaveBtn) {
            imageSaveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.saveResultAsImage();
            });
        }
    }

    /**
     * 쿠키 동의 이벤트 처리
     */
    bindCookieEvents() {
        const cookieBanner = document.getElementById('cookie-banner');
        const acceptBtn = document.getElementById('accept-cookies');
        const rejectBtn = document.getElementById('reject-cookies');

        if (!cookieBanner || !acceptBtn || !rejectBtn) return;

        // 쿠키 동의 상태 확인
        if (this.getCookie('cookieConsent')) {
            cookieBanner.classList.add('hidden');
        }

        // 동의 버튼
        acceptBtn.addEventListener('click', () => {
            this.setCookie('cookieConsent', 'accepted', 365);
            cookieBanner.classList.add('hidden');
            this.enableAnalytics();
        });

        // 거부 버튼
        rejectBtn.addEventListener('click', () => {
            this.setCookie('cookieConsent', 'rejected', 365);
            cookieBanner.classList.add('hidden');
        });
    }

    /**
     * 스크롤 상단 버튼 이벤트 처리
     */
    bindScrollTopEvents() {
        const scrollTopBtn = document.getElementById('scroll-top');
        if (!scrollTopBtn) return;

        // 스크롤 이벤트
        // 스크롤 이벤트
        window.addEventListener('scroll', () => {
            const scrollY = window.pageYOffset;

            // 스크롤 상단 버튼 표시/숨김
            if (scrollY > 300) {
                scrollTopBtn.style.display = 'block';
            } else {
                scrollTopBtn.style.display = 'none';
            }
        });

        // 클릭 이벤트
        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }



    /**
     * 쿠키 설정
     */
    setCookie(name, value, days) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    }

    /**
     * 쿠키 가져오기
     */
    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    /**
     * 애널리틱스 활성화
     */
    enableAnalytics() {
        // Google Analytics 활성화 로직
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'analytics_storage': 'granted'
            });
        }
    }

    /**
     * 비동기 나이 계산
     */
    async calculateAgeAsync(isoBirthDate) {
        const calendarType = document.querySelector('input[name="calendar_type"]:checked').value;
        const validated = isoBirthDate
            ? { valid: true, iso: isoBirthDate }
            : this.validateBirthDate(this.birthInput.value);
        if (!validated.valid) {
            throw new Error(validated.msg || '잘못된 생년월일입니다.');
        }

        if (calendarType === 'solar') {
            return this.calculateSolarAgeLocally(validated.iso);
        }

        const formData = new FormData();
        formData.set('birth_date', validated.iso);
        formData.set('calendar_type', 'lunar');

        const endpoint = (this.form && this.form.getAttribute('action')) || window.location.pathname || '/age';
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return result;
    }

    calculateSolarAgeLocally(isoBirthDate) {
        const today = new Date();
        const referenceDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        try {
            const age = AgeCalcDateRules.calculateManAge(isoBirthDate, referenceDate);
            return { success: true, message: `생년월일: ${isoBirthDate}`, age };
        } catch (error) {
            const message = String(error && error.message || '');
            return {
                success: false,
                message: message.includes('future')
                    ? '미래의 생년월일은 계산할 수 없습니다.'
                    : '올바른 날짜를 입력해주세요.',
                age: null,
            };
        }
    }

    /**
     * 결과 표시
     */
    displayResult(result) {
        const resultContainer = document.getElementById('result-container');
        const resultContent = document.getElementById('result-content');

        if (!resultContainer || !resultContent) {
            console.error('결과 컨테이너를 찾을 수 없습니다.');
            return;
        }

        if (result.success) {
            // 성공 결과 표시
            resultContent.innerHTML = this.createSuccessResultHTML(result);
            resultContainer.classList.add('show');

            // 5초 후 구글 애드 리프레시
            this.scheduleAdRefresh();



            // 공유 이벤트 다시 바인딩
            this.bindShareEvents();

        } else {
            // 에러 결과 표시
            resultContent.innerHTML = this.createErrorResultHTML(result);
            resultContainer.classList.add('show');
        }


    }

    /**
     * 결과 숨기기
     */
    hideResult() {
        const resultContainer = document.getElementById('result-container');
        const resultContent = document.getElementById('result-content');
        if (resultContainer && resultContent) {
            // 결과 내용만 비우고 컨테이너는 유지
            resultContent.innerHTML = '';
            resultContainer.classList.remove('show');
        }


    }



    /**
     * 성공 결과 HTML 생성
     */
    createSuccessResultHTML(result) {
        // 12지신 정보 가져오기
        //const year = parseInt(this.yearInput.value);
        const year = this.getBirthYear();
        const zodiacInfo = year && year >= 1900 ? DateUtils.getZodiacSign(year) : null;
        const zodiacText = zodiacInfo ? `(${zodiacInfo.emoji} ${zodiacInfo.animal})` : '';

        // 권리·제도 정보 생성
        const rightsInfo = this.generateRightsInfo(result.age);

        return `
            <div class="result success">
                <p class="message">${result.message}</p>
                <div class="age-info">
                    <p class="age">만 나이: <span class="age-number">${result.age}세</span> <span class="zodiac-simple">${zodiacText}</span></p>
                </div>
                
                <!-- 권리·제도 정보 -->
                <div class="rights-info">
                    <h4>🧑 현재 나이로 가능한 권리·제도</h4>
                    <div class="rights-list">
                        ${rightsInfo}
                    </div>
                </div>
                
                <!-- 공유하기 섹션 -->
                <div class="share-section">
                    <h4>결과 공유하기 <button class="link-copy-btn" title="링크 복사">📋</button> <button class="image-save-btn" title="이미지로 저장">📸</button></h4>
                    <div class="share-buttons">
                        <button class="share-btn kakao" data-share="kakao" title="카카오톡 공유">
                            <span class="share-icon">K</span>
                        </button>
                        <button class="share-btn instagram" data-share="instagram" title="인스타그램 공유">
                            <svg class="share-icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                            </svg>
                        </button>
                        <button class="share-btn facebook" data-share="facebook" title="페이스북 공유">
                            <svg class="share-icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                            </svg>
                        </button>
                        <button class="share-btn twitter" data-share="twitter" title="X 공유">
                            <svg class="share-icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M18.244 2.25h3.308l-7.228 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 권리·제도 정보 생성
     */
    generateRightsInfo(age) {
        // 기본 권리·제도 목록
        const basicRights = [
            { age: 14, text: '카카오톡, SNS 등 대부분 온라인 서비스 가입 가능', link: 'https://www.kakaocorp.com/page/' },
            { age: 14, text: '형사 미성년자(만 14세 미만) → 형사처벌 불가, 만 14세부터는 형사책임 인정' },
            { age: 15, text: '근로기준법상 취직 가능 연령 (부모 동의 필요)', link: 'https://www.moel.go.kr/' },
            { age: 17, text: '주민등록증 발급 가능', link: 'https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000013' },
            { age: 18, text: '자동차 운전면허 취득 가능 (2종 보통 기준)', link: 'https://www.safedriving.or.kr/' },
            { age: 18, text: '선거권 부여 (국회의원, 대통령 선거 모두 가능)', link: 'https://www.nec.go.kr/' },
            { age: 18, text: '혼인 가능 (민법 개정 후 남녀 모두 만 18세 이상부터)', link: 'https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=12700000050' },
            { age: 18, text: '일부 청년 정책(교통·문화 할인, 청소년 우대 등) 종료' },
            { age: 19, text: '술·담배 구매 가능 (청소년보호법)' },
            { age: 19, text: '성인영화/게임/유흥업소 출입 가능' },
            { age: 20, text: '군 입대 의무 본격 적용 (징병검사, 현역 입영 가능)', link: 'https://www.mma.go.kr/' },
            { age: 20, text: '대학 등록금·청년 지원금 일부 제도 만 20세 이상 대상', link: 'https://www.kosaf.go.kr/ko/main.do' },
            { age: 24, text: '일부 공공기관 청년 우대금리 통장 가입 가능' },
            { age: 34, text: '청년 월세 특별 지원 (국토부, 지자체)', link: 'https://www.molit.go.kr/' },
            { age: 34, text: '청년 전세자금 대출 (버팀목 전세자금 등)' },
            { age: 34, text: '청년 주택 청약 우대 (신혼부부 특별공급 등은 만 39세 이하까지 확대되기도 함)' },
            { age: 39, text: '청년 주택/장기전세주택 입주 가능 연령' },
            { age: 39, text: '청년 창업 지원 (중소기업청, 창업지원금 등)', link: 'https://www.semas.or.kr/' },
            { age: 39, text: '일부 지자체 청년 지원 정책 상한선' },
            { age: 40, text: '중장년층 창업 지원 (중소기업청, 중장년 창업지원금)', link: 'https://www.semas.or.kr/' },
            { age: 40, text: '중장년층 재취업 지원 (고용지원센터)', link: 'https://www.work.go.kr/' },
            { age: 45, text: '중장년층 전용 주택 청약 (일부 지자체)', link: 'https://www.molit.go.kr/' },
            { age: 50, text: '중장년층 전용 취업 지원 프로그램', link: 'https://www.work.go.kr/' },
            { age: 50, text: '중장년층 건강검진 무료 (국가건강검진)', link: 'https://www.nhis.or.kr/' },
            { age: 55, text: '중장년층 전용 주택 분양 (일부 아파트)', link: 'https://www.molit.go.kr/' },
            { age: 60, text: '중장년층 특별 지원 (일부 지자체)', link: 'https://www.mohw.go.kr/' },
            { age: 65, text: '노인복지법상 노인 혜택 시작', link: 'https://www.mohw.go.kr/' },
            { age: 65, text: '노인교통카드 할인 (대중교통)', link: 'https://www.work.go.kr/' },
            { age: 65, text: '노인 문화시설 할인 (박물관, 영화관 등)', link: 'https://www.mohw.go.kr/' },
            { age: 65, text: '기초연금 수급 자격 (만 65세 이상)', link: 'https://www.nps.or.kr/' },
            { age: 65, text: '노인장기요양보험 수급 자격', link: 'https://www.longtermcare.or.kr/' },
            { age: 70, text: '노인 우선 대기 및 할인 혜택 확대', link: 'https://www.mohw.go.kr/' }
        ];

        // 노령연금 정보 (출생연도별)
        const pensionRights = [
            { age: 61, text: '노령연금 지급 시작 (1953-56년생)', link: 'https://www.nps.or.kr/' },
            { age: 62, text: '노령연금 지급 시작 (1957-60년생)', link: 'https://www.nps.or.kr/' },
            { age: 63, text: '노령연금 지급 시작 (1961-64년생)', link: 'https://www.nps.or.kr/' },
            { age: 64, text: '노령연금 지급 시작 (1965-68년생)', link: 'https://www.nps.or.kr/' },
            { age: 65, text: '노령연금 지급 시작 (1969년생 이후)', link: 'https://www.nps.or.kr/' }
        ];

        // 사용자의 출생연도에 따른 노령연금 정보 선택
        //const userYear = parseInt(this.yearInput.value);
        const userYear = this.getBirthYear();
        let selectedPension = null;

        if (userYear && userYear >= 1953) {
            if (userYear >= 1953 && userYear <= 1956) {
                selectedPension = pensionRights[0]; // 61세
            } else if (userYear >= 1957 && userYear <= 1960) {
                selectedPension = pensionRights[1]; // 62세
            } else if (userYear >= 1961 && userYear <= 1964) {
                selectedPension = pensionRights[2]; // 63세
            } else if (userYear >= 1965 && userYear <= 1968) {
                selectedPension = pensionRights[3]; // 64세
            } else if (userYear >= 1969) {
                selectedPension = pensionRights[4]; // 65세
            }
        }

        // 기본 권리와 선택된 노령연금 정보를 합침
        const allRights = [...basicRights];
        if (selectedPension) {
            allRights.push(selectedPension);
        }

        let html = '';
        allRights.forEach(right => {
            let isAvailable;
            if (right.age === 24 || right.age === 29 || right.age === 34 || right.age === 39) {
                // 24세, 29세, 34세, 39세는 "이하" 기준
                isAvailable = age <= right.age;
            } else {
                // 나머지는 "이상" 기준
                isAvailable = age >= right.age;
            }
            const icon = isAvailable ? '✅' : '🔒';
            const textColor = isAvailable ? '#333' : '#999';

            if (right.link) {
                html += `<div class="right-item ${isAvailable ? 'available' : 'locked'}">
                    <span class="right-icon">${icon}</span>
                    <a href="${right.link}" target="_blank" style="color: ${textColor};">${right.text}</a>
                </div>`;
            } else {
                html += `<div class="right-item ${isAvailable ? 'available' : 'locked'}">
                    <span class="right-icon">${icon}</span>
                    <span style="color: ${textColor};">${right.text}</span>
                </div>`;
            }
        });

        return html;
    }

    /**
     * 에러 결과 HTML 생성
     */
    createErrorResultHTML(result) {
        return `
            <div class="result error">
                <p class="message">${result.message}</p>
            </div>
        `;
    }

    /**
     * 입력값 검증
     */
    validateInputs() {
        const v = this.validateBirthDate(this.birthInput.value);
        if (!v.valid) {
            this.showBirthError(v.msg);
            return false;
        }
        return true;
    }

    /**
     * 로딩 상태 표시/해제
     */
    showLoading(show) {
        // 로딩 상태를 결과 컨테이너에 표시
        const resultContainer = document.getElementById('result-container');
        const resultContent = document.getElementById('result-content');

        if (show) {
            // 로딩 메시지 표시
            resultContent.innerHTML = `
                <div class="result loading">
                    <div class="loading-message">
                        <span class="loading-spinner">⏳</span>
                        <p>나이를 계산하고 있습니다...</p>
                    </div>
                </div>
            `;
            resultContainer.classList.add('show');
        } else {
            // 로딩 상태는 displayResult에서 자동으로 해제됨
        }
    }

    /**
     * 구글 애드 리프레시 스케줄링
     */
    scheduleAdRefresh() {
        // 기존 타이머가 있다면 제거
        if (this.adRefreshTimer) {
            clearTimeout(this.adRefreshTimer);
        }

        // 5초 후 애드 리프레시 실행
        this.adRefreshTimer = setTimeout(() => {
            this.refreshGoogleAds();
        }, 5000);
    }

    /**
     * 구글 애드 리프레시 실행
     */
    refreshGoogleAds() {
        try {
            // Google AdSense가 로드되어 있는지 확인
            if (window.adsbygoogle && window.adsbygoogle.push) {
                console.log('Google AdSense 리프레시 실행');

                // 모든 광고 블록을 새로고침
                const adBlocks = document.querySelectorAll('ins.adsbygoogle');
                adBlocks.forEach(adBlock => {
                    try {
                        (window.adsbygoogle = window.adsbygoogle || []).push({});
                    } catch (error) {
                        console.warn('광고 블록 리프레시 실패:', error);
                    }
                });

                // 또는 페이지의 모든 광고를 새로고침
                if (window.googletag && window.googletag.pubads) {
                    window.googletag.pubads().refresh();
                }

            } else if (window.googletag && window.googletag.pubads) {
                // Google Publisher Tags 사용 시
                console.log('Google Publisher Tags 리프레시 실행');
                window.googletag.pubads().refresh();

            } else {
                console.log('Google AdSense가 로드되지 않았습니다.');
            }

        } catch (error) {
            console.error('Google AdSense 리프레시 오류:', error);
        }
    }

    /**
     * 공유하기 처리
     */
    async handleShare(shareType) {
        switch (shareType) {
            case 'kakao':
                await this.shareToKakao();
                break;
            case 'instagram':
                await this.shareToInstagram();
                break;
            case 'facebook':
                await this.shareToFacebook();
                break;
            case 'twitter':
                await this.shareToX();
                break;
            case 'copy':
                await this.copyToClipboard();
                break;
        }
    }

    /**
     * 카카오톡 공유
     */
    async shareToKakao() {
        const currentResult = this.getCurrentResult();
        const shareUrl = await this.generateShareUrl();

        let text = '만 나이 계산기로 정확한 나이를 계산해보세요! 🎂';
        if (currentResult) {
            text = `저는 ${currentResult.age}세입니다! 만 나이 계산기로 정확한 나이를 확인해보세요! 🎂`;
        }

        if (navigator.share) {
            navigator.share({
                title: '만 나이 계산기',
                text: text,
                url: shareUrl
            });
        } else {
            // 카카오톡 공유 링크 생성
            const kakaoUrl = `https://story.kakao.com/share?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(text)}`;
            window.open(kakaoUrl, '_blank');
        }
    }

    /**
     * 페이스북 공유
     */
    async shareToFacebook() {
        const shareUrl = await this.generateShareUrl();
        const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
        window.open(facebookUrl, '_blank', 'width=600,height=400');
    }

    /**
     * 인스타그램 공유
     */
    async shareToInstagram() {
        const currentResult = this.getCurrentResult();
        const shareUrl = await this.generateShareUrl();

        let text = '만 나이 계산기로 정확한 나이를 계산해보세요! 🎂';
        if (currentResult) {
            text = `저는 ${currentResult.age}세입니다! 만 나이 계산기로 정확한 나이를 확인해보세요! 🎂`;
        }

        // 인스타그램 공유 시도 (여러 방법)
        this.tryInstagramShare(text, shareUrl);
    }

    /**
     * 인스타그램 공유 시도 (링크 복사 후 인스타그램 이동)
     */
    tryInstagramShare(text, url) {
        const shareText = `${text}\n\n${url}`;

        // 먼저 클립보드에 복사
        navigator.clipboard.writeText(shareText).then(() => {
            // 복사 성공 시 시각적 피드백
            const instagramBtn = document.querySelector('[data-share="instagram"]');
            const originalText = instagramBtn.innerHTML;
            instagramBtn.innerHTML = '<span class="share-icon">✅</span>';
            instagramBtn.style.background = '#27ae60';

            // 복사 완료 알림
            alert('공유할 내용이 클립보드에 복사되었습니다! 📋\n\n이제 인스타그램으로 이동합니다.');

            // 인스타그램으로 이동
            const instagramUrl = 'https://www.instagram.com/';
            window.open(instagramUrl, '_blank', 'width=600,height=700');

            // 2초 후 버튼 원래 상태로 복원
            setTimeout(() => {
                instagramBtn.innerHTML = originalText;
                instagramBtn.style.background = '';
            }, 2000);

        }).catch(() => {
            // 클립보드 복사 실패 시
            alert('클립보드 복사에 실패했습니다.\n\n직접 복사해주세요:\n\n' + shareText);
        });
    }



    /**
     * X (구 트위터) 공유
     */
    async shareToX() {
        const currentResult = this.getCurrentResult();
        const shareUrl = await this.generateShareUrl();

        let text = '만 나이 계산기로 정확한 나이를 계산해보세요! 🎂';
        if (currentResult) {
            text = `저는 ${currentResult.age}세입니다! 만 나이 계산기로 정확한 나이를 확인해보세요! 🎂`;
        }

        const xUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`;
        window.open(xUrl, '_blank', 'width=600,height=400');
    }

    /**
     * 링크 복사 (제목 옆 버튼용)
     */
    async copyLinkToClipboard() {
        // 먼저 결과가 있는지 확인
        const resultContainer = document.querySelector('.result');
        if (!resultContainer) {
            alert('먼저 나이를 계산해주세요!');
            return;
        }

        const shareUrl = await this.generateShareUrl();

        navigator.clipboard.writeText(shareUrl).then(() => {
            // 버튼 시각적 피드백만 표시 (alert 없음)
            const linkCopyBtn = document.querySelector('.link-copy-btn');
            if (linkCopyBtn) {
                const originalText = linkCopyBtn.textContent;
                linkCopyBtn.textContent = '✅';
                linkCopyBtn.style.background = '#27ae60';

                setTimeout(() => {
                    linkCopyBtn.textContent = originalText;
                    linkCopyBtn.style.background = '#6c757d';
                }, 2000);
            }
        }).catch(() => {
            // 실패 시에도 시각적 피드백만
            const linkCopyBtn = document.querySelector('.link-copy-btn');
            if (linkCopyBtn) {
                const originalText = linkCopyBtn.textContent;
                linkCopyBtn.textContent = '❌';
                linkCopyBtn.style.background = '#dc3545';

                setTimeout(() => {
                    linkCopyBtn.textContent = originalText;
                    linkCopyBtn.style.background = '#6c757d';
                }, 2000);
            }
        });
    }

    /**
     * 결과를 이미지로 저장
     */
    saveResultAsImage() {
        // result-content만 캡처 (제목 제외)
        const resultContent = document.getElementById('result-content');
        if (!resultContent || !resultContent.innerHTML.trim()) {
            alert('먼저 나이를 계산해주세요!');
            return;
        }

        this.captureAndSaveImage(resultContent);
    }

    /**
     * 이미지 캡처 및 저장
     */
    captureAndSaveImage(element) {
        const options = {
            scale: 2, // 고해상도
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#FFF8E7', // 테마에 맞는 크림색 배경
            width: element.offsetWidth,
            height: element.offsetHeight
        };

        html2canvas(element, options).then(canvas => {
            try {
                // 모바일과 PC 모두 호환되는 다운로드 방식
                if (this.isMobile()) {
                    this.downloadImageMobile(canvas);
                } else {
                    this.downloadImagePC(canvas);
                }
            } catch (error) {
                console.error('이미지 저장 중 오류:', error);
                alert('이미지 저장에 실패했습니다.');
            }
        }).catch(error => {
            console.error('이미지 캡처 중 오류:', error);
            alert('이미지 캡처에 실패했습니다.');
        });
    }

    /**
     * 모바일 기기 여부 확인
     */
    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    /**
     * PC에서 이미지 다운로드
     */
    downloadImagePC(canvas) {
        const link = document.createElement('a');
        link.download = `나이계산결과_${new Date().toISOString().slice(0, 10)}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
    }

    /**
     * 모바일에서 이미지 저장
     */
    downloadImageMobile(canvas) {
        // 모바일에서는 새 창을 열어 이미지를 표시하고 사용자가 직접 저장하도록 함
        const newWindow = window.open();
        newWindow.document.write(`
            <html>
                <head>
                    <title>나이 계산 결과</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { 
                            margin: 0; 
                            padding: 20px; 
                            background: #f8f9fa; 
                            font-family: Arial, sans-serif;
                            text-align: center;
                        }
                        .image-container { 
                            background: white; 
                            padding: 20px; 
                            border-radius: 10px; 
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            margin: 0 auto;
                            max-width: 100%;
                        }
                        img { 
                            max-width: 100%; 
                            height: auto; 
                            border-radius: 5px;
                        }
                        .instructions {
                            margin-top: 20px;
                            color: #666;
                            font-size: 14px;
                        }
                        .download-btn {
                            background: #007bff;
                            color: white;
                            border: none;
                            padding: 12px 24px;
                            border-radius: 5px;
                            font-size: 16px;
                            margin: 10px;
                            cursor: pointer;
                        }
                        .download-btn:hover {
                            background: #0056b3;
                        }
                    </style>
                </head>
                <body>
                    <div class="image-container">
                        <h2>📸 나이 계산 결과</h2>
                        <img src="${canvas.toDataURL('image/png')}" alt="나이 계산 결과">
                        <div class="instructions">
                            <p>이미지를 길게 누르거나 우클릭하여 저장하세요</p>
                            <p>📱 모바일: 이미지를 길게 누르고 "이미지 저장" 선택</p>
                            <p>💻 PC: 이미지를 우클릭하고 "이미지 저장" 선택</p>
                        </div>
                        <button class="download-btn" onclick="window.print()">🖨️ 인쇄하기</button>
                    </div>
                </body>
            </html>
        `);
        newWindow.document.close();
    }

    /**
     * 클립보드 복사 (공유 버튼용)
     */
    async copyToClipboard() {
        const shareUrl = await this.generateShareUrl();

        navigator.clipboard.writeText(shareUrl).then(() => {
            // 복사 성공 메시지
            const copyBtn = document.querySelector('.link-copy-btn');
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '✅ 복사됨!';
            copyBtn.style.background = '#27ae60';

            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.style.background = '';
            }, 2000);
        }).catch(() => {
            alert('링크 복사에 실패했습니다. 직접 복사해주세요: ' + shareUrl);
        });
    }

    /** 공유 링크에는 개인 입력값을 포함하지 않는다. */
    async generateShareUrl() {
        return window.location.origin + window.location.pathname;
    }

    /**
     * 현재 결과 가져오기
     */
    getCurrentResult() {
        const resultContainer = document.querySelector('.result');
        if (!resultContainer) return null;

        const birthDateElement = resultContainer.querySelector('.birth-date');

        if (!birthDateElement) return null;

        return {
            birth_date: birthDateElement.textContent.replace('생년월일: ', '')
        };
    }

    /**
     * URL에서 결과 로드
     */
    async loadFromUrl() {
        if (window.location.search) {
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    /**
     * 자동 계산 이벤트
     */
    bindAutoCalculation() {
        if (!this.birthInput) return;

        this.birthInput.addEventListener('input', () => {
            this.checkAndCalculateBirthDate();
        });

        // 폼 제출은 막고, 자동 계산만 사용
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
        });
    }

    /**
     * 입력값 확인 및 자동 계산
     */
    checkAndCalculate() {
        const year = this.yearInput.value.trim();
        const month = this.monthInput.value.trim();
        const day = this.dayInput.value.trim();

        // 입력값이 변경되면 기존 결과 숨기기
        this.hideResult();

        // 모든 필드가 채워지고 유효한 경우에만 계산
        if (year && month && day) {
            // 입력 완료 후 약간의 지연을 두고 계산 (사용자 입력 완료 대기)
            if (this.autoCalcTimer) {
                clearTimeout(this.autoCalcTimer);
            }

            this.autoCalcTimer = setTimeout(() => {
                this.autoCalculate();
            }, 500); // 0.5초 지연
        }
    }

    // 8자리 YYYYMMDD 검증. 두 자리 연도는 세기가 모호하므로 받지 않습니다.
    validateBirthDate(raw) {
        const digits = (raw || '').replace(/\D/g, '');

        if (digits.length !== 8) {
            return { valid: false, msg: '생년월일 8자리(YYYYMMDD)를 입력해주세요.' };
        }
        try {
            const date = AgeCalcDateRules.parseBirthDateDigits(digits);
            const iso = AgeCalcDateRules.formatIsoDate(date);

            return { valid: true, msg: '', iso, digits };
        } catch (error) {
            const message = String(error && error.message || '');
            return {
                valid: false,
                msg: message.includes('future') ? '미래 날짜는 입력할 수 없습니다.' : '존재하지 않는 날짜입니다.'
            };
        }
    }

    showBirthError(msg) {
        if (!this.birthErrorEl || !this.birthInput) return;
        this.birthErrorEl.textContent = msg || '';
        if (msg) {
            this.birthInput.classList.add('error');
        } else {
            this.birthInput.classList.remove('error');
        }
    }

    // 8자리 모드에서 입력 시 호출
    checkAndCalculateBirthDate() {
        const raw = this.birthInput.value;
        const digits = raw.replace(/\D/g, '');

        // 입력이 바뀌면 기존 결과 숨기기
        this.hideResult();

        if (digits.length < 8) {
            this.showBirthError('');
            return;
        }

        const v = this.validateBirthDate(raw);
        if (!v.valid) {
            this.showBirthError(v.msg);
            return;
        }

        this.showBirthError('');

        if (this.autoCalcTimer) {
            clearTimeout(this.autoCalcTimer);
        }
        this.autoCalcTimer = setTimeout(() => {
            this.autoCalculateFromBirthDate(v);
        }, 500);
    }


    async autoCalculateFromBirthDate(v) {
        // 여기서 v.iso = YYYY-MM-DD
        this.showLoading(true);
        try {
            const result = await this.calculateAgeAsync(v.iso);
            this.displayResult(result);
        } catch (error) {
            console.error('나이 계산 오류:', error);
            this.showError(null, '나이 계산 중 오류가 발생했습니다. 다시 시도해주세요.');
        } finally {
            this.showLoading(false);
        }
    }


    /**
     * 자동 계산 실행
     */
    async autoCalculate() {
        // 입력값 검증
        if (!this.validateInputs()) {
            return;
        }

        // 로딩 상태 표시
        this.showLoading(true);

        try {
            // 서버에 비동기 요청
            const result = await this.calculateAgeAsync();

            // 결과 표시
            this.displayResult(result);

        } catch (error) {
            console.error('나이 계산 오류:', error);
            this.showError(null, '나이 계산 중 오류가 발생했습니다. 다시 시도해주세요.');
        } finally {
            // 로딩 상태 해제
            this.showLoading(false);
        }
    }

    /**
     * 초기 포커스 설정
     */
    setInitialFocus() {
        const target = this.birthInput || this.yearInput;
        if (target) {
            if (document.readyState === 'complete') {
                target.focus();
            } else {
                document.addEventListener('DOMContentLoaded', () => target.focus());
                window.addEventListener('load', () => target.focus());
            }
        }
    }

    /**
     * 초기 12지신 정보 설정 (제거됨 - 단순화)
     */
    initializeZodiacInfo() {
        // 12지신 초기화 기능 제거 - 단순화
    }

    /**
     * 년도 검증
     */
    validateYear(year) {
        const yearNum = parseInt(year);
        return year.length === 4 && yearNum >= 1900;
    }

    /**
     * 월 검증
     */
    validateMonth(month) {
        const monthNum = parseInt(month);
        return month.length === 2 && monthNum >= 1 && monthNum <= 12;
    }

    /**
     * 일 검증
     */
    validateDay(day) {
        const dayNum = parseInt(day);
        return day.length === 2 && dayNum >= 1 && dayNum <= 31;
    }

    /**
     * 에러 표시
     */
    showError(input, message) {
        // 기존 에러 메시지 제거
        this.removeError(input);

        // 에러 스타일 적용
        input.classList.add('error');

        // 에러 메시지를 날짜 입력 영역 아래에 표시
        const dateInputsContainer = document.querySelector('.date-inputs');
        const existingError = dateInputsContainer.parentNode.querySelector('.error-message');

        if (existingError) {
            existingError.remove();
        }

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;

        // 에러 메시지를 날짜 입력 영역 다음에 추가
        dateInputsContainer.parentNode.insertBefore(errorDiv, dateInputsContainer.nextSibling);

        // 3초 후 에러 메시지 자동 제거
        setTimeout(() => {
            this.removeError(input);
        }, 3000);
    }

    /**
     * 에러 제거
     */
    removeError(input) {
        input.classList.remove('error');
        const errorMessage = document.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.remove();
        }
    }

    /**
     * 제출 전 날짜 형식 변환
     */
    formatDateBeforeSubmit() {
        const year = this.yearInput.value;
        const month = this.monthInput.value.padStart(2, '0');
        const day = this.dayInput.value.padStart(2, '0');

        if (year && month && day) {
            this.hiddenDateInput.value = `${year}-${month}-${day}`;
        }
    }

    /**
     * 입력 필드 초기화
     */
    clearInputs() {
        this.yearInput.value = '';
        this.monthInput.value = '';
        this.dayInput.value = '';
        this.hiddenDateInput.value = '';
        this.yearInput.focus();
    }

    /**
     * 입력 필드에 값 설정
     */
    setDateValues(year, month, day) {
        if (year) this.yearInput.value = year;
        if (month) this.monthInput.value = month;
        if (day) this.dayInput.value = day;
    }

    getBirthYear() {
        // 8자리 모드
        if (this.birthInput) {
            const iso = this.hiddenDateInput && this.hiddenDateInput.value;
            if (iso && DateUtils.validateDateFormat(iso)) {
                return parseInt(iso.split('-')[0], 10);
            }
            const digits = this.birthInput.value.replace(/\D/g, '');
            if (digits.length === 8) {
                return parseInt(digits.slice(0, 4), 10);
            }
            return null;
        }

        // 기존 3필드 모드
        if (this.yearInput && this.yearInput.value) {
            return parseInt(this.yearInput.value, 10);
        }
        return null;
    }

}

/**
 * 유틸리티 함수들
 */
const DateUtils = {
    /**
     * 날짜 유효성 검사
     */
    isValidDate: (year, month, day) => {
        const date = new Date(year, month - 1, day);
        return date.getFullYear() === parseInt(year) &&
            date.getMonth() === parseInt(month) - 1 &&
            date.getDate() === parseInt(day);
    },

    /**
     * 현재 년도 가져오기
     */
    getCurrentYear: () => new Date().getFullYear(),

    /**
     * 날짜 형식 검증 (YYYY-MM-DD)
     */
    validateDateFormat: (dateString) => {
        const regex = /^\d{4}-\d{2}-\d{2}$/;
        return regex.test(dateString);
    },

    /**
     * 12지신 계산 (단순화된 버전)
     */
    getZodiacSign: (year) => {
        const zodiacSigns = [
            { animal: '원숭이', emoji: '🐒' },
            { animal: '닭', emoji: '🐔' },
            { animal: '개', emoji: '🐕' },
            { animal: '돼지', emoji: '🐷' },
            { animal: '쥐', emoji: '🐭' },
            { animal: '소', emoji: '🐂' },
            { animal: '호랑이', emoji: '🐅' },
            { animal: '토끼', emoji: '🐇' },
            { animal: '용', emoji: '🐉' },
            { animal: '뱀', emoji: '🐍' },
            { animal: '말', emoji: '🐎' },
            { animal: '양', emoji: '🐑' }
        ];

        return zodiacSigns[year % 12];
    }
};

/**
 * DOM 로드 완료 시 초기화
 */
document.addEventListener('DOMContentLoaded', function () {
    try {
        new AgeCalculatorUI();
        console.log('Age Calculator UI initialized successfully');
    } catch (error) {
        console.error('Failed to initialize Age Calculator UI:', error);
    }
});

// 모듈 내보내기 (필요시)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AgeCalculatorUI, DateUtils };
}
