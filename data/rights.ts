export interface RightInfo {
    age: number;
    text: string;
    link?: string;
    maxAge?: boolean; // true if "age 이하" (under age), false/undefined if "age 이상" (over age)
}

export const rightsData: RightInfo[] = [
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
    { age: 24, text: '일부 공공기관 청년 우대금리 통장 가입 가능', maxAge: true },
    { age: 34, text: '청년 월세 특별 지원 (국토부, 지자체)', link: 'https://www.molit.go.kr/', maxAge: true },
    { age: 34, text: '청년 전세자금 대출 (버팀목 전세자금 등)', maxAge: true },
    { age: 34, text: '청년 주택 청약 우대 (신혼부부 특별공급 등은 만 39세 이하까지 확대되기도 함)', maxAge: true },
    { age: 39, text: '청년 주택/장기전세주택 입주 가능 연령', maxAge: true },
    { age: 39, text: '청년 창업 지원 (중소기업청, 창업지원금 등)', link: 'https://www.semas.or.kr/', maxAge: true },
    { age: 39, text: '일부 지자체 청년 지원 정책 상한선', maxAge: true },
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

export const pensionRights: RightInfo[] = [
    { age: 61, text: '노령연금 지급 시작 (1953-56년생)', link: 'https://www.nps.or.kr/' },
    { age: 62, text: '노령연금 지급 시작 (1957-60년생)', link: 'https://www.nps.or.kr/' },
    { age: 63, text: '노령연금 지급 시작 (1961-64년생)', link: 'https://www.nps.or.kr/' },
    { age: 64, text: '노령연금 지급 시작 (1965-68년생)', link: 'https://www.nps.or.kr/' },
    { age: 65, text: '노령연금 지급 시작 (1969년생 이후)', link: 'https://www.nps.or.kr/' }
];
