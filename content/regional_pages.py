"""Complete editorial copy for calculators that intentionally support select locales."""

REGIONAL_COPY = {
    ("lunar_birthday", "ko"): {
        "title": "음력 생일 계산기 - 올해 양력 생일·평달·윤달 | AgeCalc",
        "h1": "음력 생일 계산기",
        "description": "음력 월·일과 평달·윤달을 선택해 올해와 앞으로의 양력 생일 날짜를 확인하세요.",
        "intro": "해마다 달라지는 음력 생일을 양력 날짜로 바꿔 봅니다. 평달과 윤달을 구분해 조회일 이후 가장 가까운 생일과 현재 음력 연도부터 6개 연도의 일정을 보여드립니다.",
        "privacy_note": "입력값은 계산할 때만 사용하고 저장하지 않습니다. 결과 페이지도 캐시하지 않습니다.",
        "form_title": "음력 생일을 입력하세요", "submit": "음력 생일 계산",
        "fields": {"month": "음력 월", "day": "음력 일", "leap": "윤달로 계산", "reference": "조회 기준일"},
        "labels": {"next_birthday": "다음 음력 생일", "lunar_year": "음력 연도", "solar_date": "양력 날짜", "status": "변환 상태", "available": "확인됨", "missing_leap_month": "해당 윤달 없음", "invalid_lunar_date": "해당 음력 날짜 없음", "unsupported_year": "지원 범위 밖", "next_unavailable": "지원 범위 안에서 다음 생일을 계산할 수 없음"},
        "notes": {"lunar_birthday_note": "윤달이 없는 해, 선택한 날짜가 존재하지 않는 달, 변환 지원 범위를 벗어난 연도는 표에서 각각 구분해 표시합니다."},
        "errors": {"invalid_parameters": "필수 값을 모두 입력해 주세요.", "invalid_date": "실제로 존재하는 기준일을 입력해 주세요.", "invalid_integer": "월과 일은 숫자로 입력해 주세요.", "invalid_range": "음력 월과 일의 범위를 확인해 주세요.", "unsupported_range": "이 날짜는 현재 지원하는 음양력 변환 범위를 벗어납니다.", "unavailable_lunar_date": "선택한 음력 날짜를 변환할 수 없습니다."},
        "sections": [
            {"heading": "출생일 변환과 해마다의 생일 계산은 다릅니다", "paragraphs": ["음력 생년월일을 한 번 양력으로 바꾸는 것만으로는 올해 생일을 알 수 없습니다. 같은 음력 월·일도 양력에서는 해마다 다른 날짜가 됩니다. 이 도구는 현재 음력 연도부터 각 생일을 다시 변환합니다.", "나이 계산이 필요하다면 만 나이 계산기를 이용하세요. 이 페이지는 나이를 계산하거나 법적 생일을 판단하지 않습니다."]},
            {"heading": "평달과 윤달을 구분합니다", "paragraphs": ["태어난 달이 윤달이었다면 윤달을 선택할 수 있습니다. 모든 해에 같은 윤달이 생기지는 않으므로 변환할 수 없는 해가 있을 수 있습니다.", "가족마다 윤달 생일을 기념하는 방식이 다를 수 있습니다. 이 계산기는 한 가지 관행을 정답으로 정하지 않으며 윤달이 없는 해의 기념일을 자동으로 평달에 배정하지 않습니다."]},
            {"heading": "계산 범위와 기준", "paragraphs": ["한국 음력을 기준으로 계산합니다. 조회 기준일로 입력할 수 있는 연도는 1900년부터 2049년까지입니다. 지원 범위 밖의 날짜는 추정하지 않습니다."]}
        ],
        "faq": [
            {"question": "음력 생일이 매년 같은 양력 날짜인가요?", "answer": "아닙니다. 음력과 양력의 달 길이와 윤달 구조가 달라 양력 날짜가 해마다 달라집니다."},
            {"question": "윤달이 없는 해에는 어떻게 표시되나요?", "answer": "그 해는 변환할 수 없다고 표시합니다. 평달 날짜로 자동 변경하지 않습니다."},
            {"question": "입력한 생일을 저장하나요?", "answer": "저장하지 않습니다. 입력값은 계산할 때만 사용하며 결과 페이지도 캐시하지 않습니다."}
        ],
        "source_label": "한국천문연구원 음양력 정보", "source_url": "https://astro.kasi.re.kr/life/pageView/31"
    },
    ("business_days", "ja"): {
        "title": "営業日計算 - 日数・営業日後の日付（日本の祝日）| AgeCalc", "h1": "営業日計算",
        "description": "土日と日本の国民の祝日、指定した除外日を除いて営業日数または営業日後の日付を計算します。2025年から2027年対応。",
        "intro": "期間内の営業日数と、指定日から何営業日後・前の日付を一つの画面で計算します。土日、内閣府公表の祝日、入力した休業日を除外します。",
        "privacy_note": "入力内容は計算のためだけに使用し、保存しません。結果ページもキャッシュしません。",
        "form_title": "営業日の条件を入力", "submit": "営業日を計算",
        "fields": {"mode": "計算方法", "count": "期間内の日数", "add": "営業日を足す", "subtract": "営業日を引く", "start": "開始日", "end": "終了日", "amount": "営業日数", "include_end": "終了日を含める", "excluded": "追加の休業日（1行に1日、YYYY-MM-DD）"},
        "labels": {"workdays": "営業日数", "result_date": "計算した日付"},
        "notes": {"holiday_range_note": "国民の祝日は2025年から2027年まで対応しています。地方の休日や会社独自の休業日は追加欄に入力してください。"},
        "errors": {"invalid_parameters": "必須項目を入力してください。", "invalid_date": "実在する日付を入力してください。", "invalid_integer": "営業日数は0以上の整数で入力してください。", "invalid_mode": "計算方法を選択してください。", "invalid_range": "終了日は開始日以降にし、営業日数は0以上で入力してください。", "unsupported_range": "祝日データの対応範囲は2025年から2027年です。", "too_many_excluded_dates": "追加できる休業日は100件までです。", "holiday_data_unavailable": "祝日データを読み込めませんでした。しばらくしてからもう一度お試しください。"},
        "sections": [{"heading": "祝日データの範囲", "paragraphs": ["内閣府が公表した国民の祝日と休日を使います。2025年から2027年までの計算に限り、範囲外の日付を祝日なしとして扱うことはありません。", "都道府県、自治体、会社の休日は自動では入りません。必要な日は追加の休業日に指定してください。"]}, {"heading": "営業日を足すときの数え方", "paragraphs": ["開始日は0日目です。1営業日後は、開始日の次に来る営業日です。0を入力すると開始日を返します。", "契約や申請の期限には独自の初日算入・満了日規則があります。この結果だけで法的期限を判断しないでください。"]}],
        "faq": [{"question": "振替休日も除外しますか？", "answer": "はい。内閣府の一覧に休日として掲載された日も除外します。"}, {"question": "会社の年末年始休業を入れられますか？", "answer": "はい。追加の休業日に1行ずつ入力できます。"}, {"question": "開始日を1営業日目に数えますか？", "answer": "営業日を足す・引く計算では開始日を0日目とします。期間の日数計算では開始日を含みます。"}],
        "source_label": "内閣府「国民の祝日について」", "source_url": "https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html"
    },
    ("business_days", "pt-BR"): {
        "title": "Calculadora de dias úteis no Brasil | AgeCalc", "h1": "Calculadora de dias úteis",
        "description": "Conte dias úteis ou some e subtraia dias úteis, excluindo fins de semana, feriados nacionais do Brasil e datas informadas.",
        "intro": "Calcule quantos dias úteis existem em um período ou encontre uma data após determinado número de dias úteis. A conta exclui sábados, domingos, feriados nacionais cadastrados e folgas adicionais.",
        "privacy_note": "Os dados são usados apenas para gerar a resposta, não são armazenados e a página de resultado não é mantida em cache.",
        "form_title": "Informe o período e as regras", "submit": "Calcular dias úteis",
        "fields": {"mode": "Tipo de cálculo", "count": "Contar em um período", "add": "Somar dias úteis", "subtract": "Subtrair dias úteis", "start": "Data inicial", "end": "Data final", "amount": "Quantidade de dias úteis", "include_end": "Incluir a data final", "excluded": "Outras folgas (uma data por linha, AAAA-MM-DD)"},
        "labels": {"workdays": "Dias úteis", "result_date": "Data calculada"},
        "notes": {"holiday_range_note": "Os feriados nacionais cadastrados cobrem 2025 a 2027. Feriados estaduais, municipais, pontos facultativos e folgas da empresa devem ser informados à parte."},
        "errors": {"invalid_parameters": "Preencha os campos obrigatórios.", "invalid_date": "Informe uma data real.", "invalid_integer": "Use um número inteiro igual ou maior que zero.", "invalid_mode": "Escolha o tipo de cálculo.", "invalid_range": "A data final deve ser igual ou posterior à inicial, e a quantidade não pode ser negativa.", "unsupported_range": "O calendário de feriados atende somente aos anos de 2025 a 2027.", "too_many_excluded_dates": "É possível adicionar até 100 datas de folga.", "holiday_data_unavailable": "Não foi possível carregar os feriados. Tente novamente em instantes."},
        "sections": [{"heading": "O que entra no calendário", "paragraphs": ["A versão inicial cobre os feriados nacionais definidos em lei federal entre 2025 e 2027. Datas estaduais e municipais, Carnaval, pontos facultativos e paralisações da empresa não são presumidos.", "Use o campo de folgas adicionais para ajustar a conta à sua cidade ou organização. A ferramenta rejeita intervalos fora dos anos publicados em vez de calcular como se não houvesse feriados."]}, {"heading": "Como a data inicial é contada", "paragraphs": ["Na soma ou subtração, a data inicial corresponde ao dia zero. Ao somar um dia útil, o resultado é o próximo dia que atende às regras. A quantidade zero devolve a data inicial.", "Prazos judiciais, bancários e contratuais podem seguir calendários e regras de contagem próprios. Consulte a fonte responsável pelo prazo antes de tomar uma decisão."]}],
        "faq": [{"question": "A calculadora inclui Carnaval?", "answer": "Não automaticamente. Carnaval e outros pontos facultativos não são tratados como feriados nacionais nesta versão; adicione as datas se forem folgas no seu caso."}, {"question": "Posso cadastrar feriados municipais?", "answer": "Sim. Informe cada data no campo de folgas adicionais."}, {"question": "O sábado é contado como dia útil?", "answer": "Não. A configuração desta página exclui sábado e domingo."}],
        "source_label": "Legislação federal de feriados nacionais", "source_url": "https://www.planalto.gov.br/ccivil_03/leis/l0662.htm"
    },
    ("school_year", "ja"): {
        "title": "入学・卒業年度計算 - 生年月日から履歴書の学歴を確認 | AgeCalc", "h1": "入学・卒業年度計算",
        "description": "生年月日から小学校・中学校・高校・大学の入学年月と卒業年月を計算します。早生まれ、浪人・留年、大学の修業年数に対応。",
        "intro": "履歴書の学歴欄を確認するときに使える目安です。4月1日生まれまでと4月2日生まれ以降の学年境界を分け、空白年数と大学の修業年数を反映します。",
        "privacy_note": "入力内容は計算のためだけに使用し、保存しません。結果ページもキャッシュしません。",
        "form_title": "生年月日と進学条件を入力", "submit": "学歴年度を計算",
        "fields": {"birth": "生年月日", "gap": "浪人・留年などの空白年数", "course": "大学の修業年数"},
        "labels": {"elementary_entry": "小学校入学", "elementary_graduation": "小学校卒業", "junior_high_entry": "中学校入学", "junior_high_graduation": "中学校卒業", "high_school_entry": "高校入学", "high_school_graduation": "高校卒業", "university_entry": "大学入学", "university_graduation": "大学卒業"},
        "notes": {"school_year_note": "標準的な4月入学・3月卒業を基準にした目安です。実際の在籍記録や制度上の例外は学校の証明書で確認してください。"},
        "errors": {"invalid_parameters": "必須項目を入力してください。", "invalid_date": "実在する生年月日を入力してください。", "invalid_integer": "空白年数と修業年数を確認してください。", "invalid_range": "空白年数は0から10年、大学は2・4・6年から選択してください。", "unsupported_range": "計算できる年月の範囲を超えています。"},
        "sections": [{"heading": "4月1日生まれまでが同じ学年", "paragraphs": ["日本の学年は4月2日から翌年4月1日までに生まれた人を一つの学年として扱います。たとえば2020年4月1日生まれは2026年4月、4月2日生まれは2027年4月の小学校入学として計算します。", "結果は標準的な就学年齢による年月です。早期入学、海外の学校、編入、休学などは自動判定しません。"]}, {"heading": "履歴書では証明書を優先", "paragraphs": ["空白年数は高校卒業後から大学入学までに加えます。留年や休学の時期が異なる場合は、表示された年をそのまま使わず実際の在籍記録に合わせてください。", "和暦で記載する場合は和暦・西暦変換も利用できます。元号の切替日をまたぐ年月は日付まで確認してください。"]}],
        "faq": [{"question": "早生まれに対応していますか？", "answer": "はい。1月1日から4月1日生まれを前年4月2日以降と同じ学年として計算します。"}, {"question": "浪人した年数を反映できますか？", "answer": "高校卒業後から大学入学までの空白年数として0年から10年を指定できます。"}, {"question": "履歴書にそのまま転記できますか？", "answer": "目安として利用できますが、最終的には卒業証明書などの記録を確認してください。"}],
        "source_label": "厚生労働省 ハローワーク応募書類資料", "source_url": "https://www.hellowork.mhlw.go.jp/doc/ouboshorui_pamphlet_202005.pdf"
    },
    ("birth_date_range", "en"): {
        "title": "Date of Birth Calculator from Age - Possible Date Range | AgeCalc", "h1": "Date of Birth Calculator from Age",
        "description": "Enter a completed age and reference date to find the inclusive range of possible birth dates without inventing an exact birthday.",
        "intro": "When a record gives only a person's completed age on a known date, their exact birthday is unknown. This calculator returns the earliest and latest possible birth dates consistent with that information.",
        "privacy_note": "Your entries are used only to produce the response, are not stored, and the result page is not cached.",
        "form_title": "Enter the recorded age", "submit": "Find possible birth dates",
        "fields": {"reference": "Reference date", "age": "Completed age on that date"},
        "labels": {"earliest": "Earliest possible birth date", "latest": "Latest possible birth date"},
        "notes": {"birth_date_range_note": "The result is an inclusive range, not an exact birth date. It uses completed Gregorian years and treats March 1 as the anniversary of a February 29 birth in non-leap years."},
        "errors": {"invalid_parameters": "Complete all required fields.", "invalid_date": "Enter a real reference date.", "invalid_integer": "Age must be a whole number.", "invalid_range": "Enter an age from 0 through 150.", "unsupported_range": "The result falls outside the supported Gregorian date range."},
        "sections": [{"heading": "Why age produces a date range", "paragraphs": ["A person recorded as age 30 on 15 September 2026 may have been born from 16 September 1995 through 15 September 1996. Someone born earlier would already be 31; someone born later would still be 29.", "Use the result to narrow a search in census, genealogy or administrative records. Do not treat either endpoint as the person's confirmed birthday without another source."]}, {"heading": "Calendar-year subtraction is not enough", "paragraphs": ["Subtracting 30 from 2026 gives two candidate years but does not settle the month and day. The reference date and whether the birthday has occurred define the interval.", "The calculator uses completed Gregorian years. Historical records may use stated age, age at next birthday or another convention, so check how the source recorded age."]}],
        "faq": [{"question": "Can this recover an exact date of birth?", "answer": "No. Completed age alone normally identifies a one-year inclusive range."}, {"question": "Are both endpoint dates possible?", "answer": "Yes. The earliest and latest dates are included under the completed-age convention."}, {"question": "Can I use an age recorded at death?", "answer": "Yes when the record states completed age and the reference date is the date at which that age applied. Check the record's convention first."}],
        "source_label": "Calculation method and limitations", "source_url": "https://www.brantfordlibrary.ca/en/news/resources/Home-Based/Genealogy-Reference-Tools.pdf"
    },
    ("birth_date_range", "pt-BR"): {
        "title": "Calcular data de nascimento pela idade - intervalo possível | AgeCalc", "h1": "Calcular data de nascimento pela idade",
        "description": "Informe a idade completa e a data de referência para encontrar o intervalo inclusivo de datas de nascimento possíveis.",
        "intro": "Uma idade completa registrada em certa data não revela um aniversário exato. A calculadora mostra a primeira e a última data de nascimento compatíveis com essa informação.",
        "privacy_note": "Os dados são usados apenas para gerar a resposta, não são armazenados e a página de resultado não é mantida em cache.",
        "form_title": "Informe a idade registrada", "submit": "Calcular intervalo de nascimento",
        "fields": {"reference": "Data de referência", "age": "Idade completa nessa data"},
        "labels": {"earliest": "Primeira data de nascimento possível", "latest": "Última data de nascimento possível"},
        "notes": {"birth_date_range_note": "O resultado é um intervalo inclusivo, não uma data exata. A conta usa anos completos do calendário gregoriano e considera 1º de março como aniversário de quem nasceu em 29 de fevereiro nos anos não bissextos."},
        "errors": {"invalid_parameters": "Preencha todos os campos obrigatórios.", "invalid_date": "Informe uma data de referência real.", "invalid_integer": "A idade deve ser um número inteiro.", "invalid_range": "Informe uma idade de 0 a 150 anos.", "unsupported_range": "O resultado fica fora do intervalo de datas aceito."},
        "sections": [{"heading": "Por que o resultado é um intervalo", "paragraphs": ["Se uma pessoa tinha 30 anos completos em 15 de setembro de 2026, ela pode ter nascido entre 16 de setembro de 1995 e 15 de setembro de 1996. As duas datas das extremidades fazem parte do intervalo.", "O cálculo ajuda a filtrar registros antigos ou cadastros incompletos. Não confirme uma data de nascimento sem consultar outra fonte."]}, {"heading": "A convenção do registro importa", "paragraphs": ["A conta presume que a idade informada é a quantidade de aniversários já completados. Alguns documentos históricos usam idade declarada, idade aproximada ou outro modo de contagem.", "Quando houver dúvida, preserve o intervalo e anote a convenção adotada. Subtrair apenas o ano da idade não resolve o mês e o dia."]}],
        "faq": [{"question": "A calculadora encontra o aniversário exato?", "answer": "Não. Somente a idade completa costuma produzir um intervalo de aproximadamente um ano."}, {"question": "As duas datas-limite estão incluídas?", "answer": "Sim. A primeira e a última data exibidas são possibilidades válidas."}, {"question": "Posso usar a idade registrada em uma certidão antiga?", "answer": "Pode usar como filtro, desde que verifique se a idade foi registrada em anos completos e qual era a data de referência."}],
        "source_label": "Método e limites do cálculo", "source_url": "https://calculadoradaidade.com.br/calcular-data-de-nascimento/"
    },
    ("japanese_era", "ja"): {
        "title": "和暦・西暦変換 - 明治・大正・昭和・平成・令和 | AgeCalc", "h1": "和暦・西暦変換",
        "description": "明治6年以降の日付を、明治・大正・昭和・平成・令和と西暦の間で相互変換します。元号の切替日も確認できます。",
        "intro": "西暦の日付を和暦に、和暦の日付を西暦に変換します。年だけでなく月日まで確認し、元号が変わった年の誤表記を防ぎます。",
        "privacy_note": "入力内容は変換のためだけに使用し、保存しません。結果ページもキャッシュしません。",
        "form_title": "変換する日付を入力", "submit": "日付を変換",
        "fields": {"mode": "変換方向", "to_era": "西暦から和暦", "from_era": "和暦から西暦", "date": "西暦の日付", "era": "元号", "era_year": "年（元年は1）", "month": "月", "day": "日"},
        "labels": {"era_date": "和暦", "gregorian_date": "西暦"},
        "notes": {"japanese_era_note": "グレゴリオ暦を採用した1873年1月1日以降に対応します。旧暦の日付変換ではありません。"},
        "errors": {"invalid_parameters": "必須項目を入力してください。", "invalid_date": "その元号に実在する日付を入力してください。", "invalid_integer": "年・月・日は整数で入力してください。", "invalid_mode": "変換方向を選択してください。", "invalid_range": "元号と年月日の範囲を確認してください。", "invalid_era": "元号を選択してください。", "invalid_era_date": "入力した日付は選択した元号の期間外です。", "unsupported_range": "1873年1月1日より前の日付には対応していません。"},
        "sections": [{"heading": "元号の初年は元年と表示", "paragraphs": ["2019年5月1日は令和元年5月1日です。同じ2019年でも4月30日は平成31年なので、年だけを換算すると元号を誤ることがあります。", "大正は1912年7月30日、昭和は1926年12月25日、平成は1989年1月8日、令和は2019年5月1日から始まります。境界日を含めて判定します。"]}, {"heading": "明治6年より前は対象外", "paragraphs": ["このページは日本がグレゴリオ暦を採用した1873年1月1日以降の日付を扱います。それ以前の和暦や旧暦を単純な西暦日付に置き換えることはできません。", "公的な届出や履歴書では提出先の指定を優先してください。学校の入学・卒業年月は専用計算で確認できます。"]}],
        "faq": [{"question": "昭和64年の日付はすべて有効ですか？", "answer": "いいえ。昭和64年は1989年1月1日から1月7日までです。1月8日は平成元年です。"}, {"question": "元年は1年と入力しますか？", "answer": "はい。入力では1を使い、結果では元年と表示します。"}, {"question": "旧暦から西暦へ変換できますか？", "answer": "できません。このページは1873年以降のグレゴリオ暦の日付と元号表記を変換します。"}],
        "source_label": "厚生労働省 和暦表記と西暦表記の対照表", "source_url": "https://www.mhlw.go.jp/content/11200000/001154310.pdf"
    }
}


def regional_copy(page_key, locale):
    return REGIONAL_COPY[(page_key, locale)]
