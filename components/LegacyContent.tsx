import { Paper, Title, Text, Stack, Timeline, ThemeIcon, useComputedColorScheme } from '@mantine/core';

export function LegacyContent() {
    const computedColorScheme = useComputedColorScheme('light', { getInitialValueInEffect: true });
    const isDark = computedColorScheme === 'dark';

    const glassStyle = {
        background: isDark ? 'rgba(0, 0, 0, 0.3)' : 'rgba(255, 255, 255, 0.4)',
        backdropFilter: 'blur(10px)',
        border: isDark ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(255, 255, 255, 0.2)'
    };

    return (
        <Stack gap="xl" mt={50} mb={50}>
            <Paper p="xl" radius="lg" style={glassStyle}>
                <Title order={2} mb="md" c={isDark ? 'indigo.3' : 'indigo'}>연령별 주요 권리·제도 (만나이 기준)</Title>
                <Timeline active={-1} bulletSize={24} lineWidth={2} color="indigo">
                    <Timeline.Item title="만 0세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>0</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>부모급여, 아동수당, 첫만남이용권</Text>
                    </Timeline.Item>
                    <Timeline.Item title="만 6세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>6</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>취학통지서 발송</Text>
                    </Timeline.Item>
                    <Timeline.Item title="만 7세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>7</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>초등학교 입학</Text>
                    </Timeline.Item>
                    <Timeline.Item title="만 14세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>14</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>근로 가능 (취직인허증), 정당 가입 가능, 형사 미성년자 종료</Text>
                    </Timeline.Item>
                    <Timeline.Item title="만 18세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>18</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>선거권, 운전면허, 군 입대, 아르바이트/취업, 청소년 관람불가 영화, 결혼 (부모 동의)</Text>
                    </Timeline.Item>
                    <Timeline.Item title="만 19세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>19</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>성인 (술/담배 구매), 부모 동의 없이 결혼</Text>
                    </Timeline.Item>
                    <Timeline.Item title="만 40세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>40</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>중장년 창업지원금</Text>
                    </Timeline.Item>
                    <Timeline.Item title="만 60세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>60</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>국민연금 수령 시작 (출생연도별 상이)</Text>
                    </Timeline.Item>
                    <Timeline.Item title="만 65세" bullet={<Text size="xs" c={isDark ? 'white' : 'dark'}>65</Text>}>
                        <Text size="sm" c={isDark ? 'dimmed' : 'dark'}>기초연금, 지하철 무료, 노인장기요양보험</Text>
                    </Timeline.Item>
                </Timeline>
            </Paper>

            <Paper p="xl" radius="lg" style={glassStyle}>
                <Title order={2} mb="md" c={isDark ? 'indigo.3' : 'indigo'}>만나이 계산 방식</Title>
                <Text mb="md" c={isDark ? 'dimmed' : 'dark'}>
                    만나이는 출생일을 기준으로 오늘 날짜와의 차이를 연·월·일 단위로 계산해 산출합니다.
                </Text>
                <Text mb="md" c={isDark ? 'dimmed' : 'dark'}>
                    생일이 지났을 때만 한 살이 증가하며, 생일 전에는 전년도 나이가 유지됩니다.
                    본 계산기는 양력 기준으로 동작하고, 시간대/서머타임에 따른 시·분 정보는 배제하여 날짜 단위만 사용합니다.
                    윤년과 말일(예: 2월 29일 출생)도 예외 없이 처리하며, 윤년이 아닌 해의 2월 29일은 통상 2월 28일 또는 3월 1일을 기준으로 간주하는 관행을 안내합니다.
                </Text>
                <ul style={{ paddingLeft: '20px', margin: 0, color: isDark ? '#aaa' : 'inherit' }}>
                    <li><Text size="sm" c={isDark ? 'dimmed' : 'dark'}>기준일: 사용자가 페이지 접속 시점의 현지 날짜</Text></li>
                    <li><Text size="sm" c={isDark ? 'dimmed' : 'dark'}>윤년/말일 보정: 2월 29일 출생 등 특수 케이스 안내</Text></li>
                    <li><Text size="sm" c={isDark ? 'dimmed' : 'dark'}>서머타임/타임존: 날짜만 계산, 시·분은 사용하지 않음</Text></li>
                </ul>
            </Paper>

            <Paper p="xl" radius="lg" style={glassStyle}>
                <Title order={2} mb="md" c={isDark ? 'indigo.3' : 'indigo'}>한국식/국제식 나이 비교</Title>
                <Text mb="md" c={isDark ? 'dimmed' : 'dark'}>
                    대한민국은 2023년 6월부터 공적 영역에서 만나이로 통일되었습니다.
                    일상에서는 여전히 '세는 나이'(태어나자마자 1살)를 사용하는 경우도 있지만,
                    법적·행정적 기준은 '만 나이'가 원칙입니다.
                </Text>
            </Paper>
        </Stack>
    );
}
