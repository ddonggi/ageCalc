'use client';

import { Container, Title, Text, Stack, Paper, List } from '@mantine/core';
import { Background3DWrapper } from '../../components/Background3DWrapper';

export default function PrivacyPage() {
    return (
        <>
            <Background3DWrapper />
            <Container size="sm" py="xl">
                <Paper p="xl" radius="lg" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
                    <Stack gap="lg">
                        <Title order={1}>개인정보 처리 방침</Title>
                        <Text>만나이 계산기(이하 “서비스”)는 개인정보보호법 등 관련 법령을 준수하며, 이용자의 개인정보 보호를 위해 아래와 같이 처리 방침을 공개합니다.</Text>

                        <Title order={2} size="h3">1. 처리 목적</Title>
                        <List>
                            <List.Item>나이 계산 서비스 제공: 입력한 생년월일을 바탕으로 만나이를 계산하고 관련 정보를 안내</List.Item>
                            <List.Item>서비스 품질 개선: 오류 복구, 보안 강화, 이용 통계 분석(동의 시)</List.Item>
                            <List.Item>고객 지원: 문의 대응 및 기술 지원</List.Item>
                        </List>

                        <Title order={2} size="h3">2. 수집 항목 및 수집 방법</Title>
                        <Text fw={700}>핵심 원칙: 생년월일 등 계산 입력값은 브라우저에서만 처리되며 서버에 저장하지 않습니다.</Text>
                        <List>
                            <List.Item>직접 수집: (필수) 없음 / (선택) 문의 시 이메일 주소</List.Item>
                            <List.Item>자동 수집: 필수 보안 로그(IP, User-Agent 등), 쿠키/유사기술</List.Item>
                        </List>

                        <Title order={2} size="h3">3. 이용·보유 기간</Title>
                        <List>
                            <List.Item>브라우저 입력값: 저장하지 않음</List.Item>
                            <List.Item>서버 보안 로그: 보안 목적 달성 시까지 최소한으로 보관 후 파기(통상 3~6개월 내)</List.Item>
                        </List>

                        <Title order={2} size="h3">4. 제3자 제공</Title>
                        <Text>원칙적으로 개인정보를 제3자에게 제공하지 않습니다. 법령에 근거한 요구가 있는 경우 예외적으로 제공될 수 있습니다.</Text>

                        <Title order={2} size="h3">5. 쿠키에 대한 안내</Title>
                        <Text>서비스 품질 개선 및 광고 제공을 위해 쿠키를 사용할 수 있습니다. 브라우저 설정에서 쿠키를 차단할 수 있습니다.</Text>

                        <Title order={2} size="h3">6. 문의처</Title>
                        <Text>문의: ldg6153@gmail.com</Text>
                    </Stack>
                </Paper>
            </Container>
        </>
    );
}
