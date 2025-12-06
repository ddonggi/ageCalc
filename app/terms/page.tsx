'use client';

import { Container, Title, Text, Stack, Paper, List } from '@mantine/core';
import { Background3DWrapper } from '../../components/Background3DWrapper';

export default function TermsPage() {
    return (
        <>
            <Background3DWrapper />
            <Container size="sm" py="xl">
                <Paper p="xl" radius="lg" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
                    <Stack gap="lg">
                        <Title order={1}>이용약관</Title>
                        <Text>만나이 계산기(이하 “서비스”)의 이용과 관련하여 서비스 제공자와 이용자 간의 권리, 의무 및 책임사항을 규정합니다.</Text>

                        <Title order={2} size="h3">제1조 (약관의 효력 및 변경)</Title>
                        <Text>본 약관은 서비스 화면에 게시하거나 기타 방법으로 공지함으로써 효력을 발생합니다. 합리적인 사유가 있을 경우 약관을 변경할 수 있습니다.</Text>

                        <Title order={2} size="h3">제2조 (서비스의 정의)</Title>
                        <Text>“서비스”란 생년월일 입력을 바탕으로 만나이를 계산하고, 연령별 주요 권리·제도 정보를 안내하는 웹 기반 서비스를 의미합니다.</Text>

                        <Title order={2} size="h3">제3조 (서비스의 제공)</Title>
                        <Text>서비스는 연중무휴, 1일 24시간 제공을 원칙으로 합니다. 다만, 시스템 점검 등 불가피한 사유로 중단될 수 있습니다.</Text>

                        <Title order={2} size="h3">제4조 (개인정보보호)</Title>
                        <Text fw={700}>서비스는 계산 입력값을 서버에 저장하지 않습니다. 입력한 생년월일은 브라우저 내에서 처리됩니다.</Text>

                        <Title order={2} size="h3">제5조 (면책사항)</Title>
                        <Text>서비스에서 제공하는 정보는 일반적인 참고용이며, 실제 법적 효력이나 구체적 혜택 적용은 관계 기관의 최신 안내를 반드시 확인하시기 바랍니다. 서비스 이용으로 인한 손해에 대해 책임을 지지 않습니다.</Text>

                        <Title order={2} size="h3">제6조 (문의)</Title>
                        <Text>문의: ldg6153@gmail.com</Text>
                    </Stack>
                </Paper>
            </Container>
        </>
    );
}
