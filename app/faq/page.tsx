'use client';

import { Container, Title, Text, Stack, Paper, Accordion } from '@mantine/core';
import { Background3DWrapper } from '../../components/Background3DWrapper';

export default function FAQPage() {
    return (
        <>
            <Background3DWrapper />
            <Container size="sm" py="xl">
                <Paper p="xl" radius="lg" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
                    <Stack gap="lg">
                        <Title order={1}>자주 묻는 질문(FAQ)</Title>
                        <Text>만나이 계산, 윤년/음력 처리, 데이터 저장 여부 등 자주 묻는 질문을 정리했습니다.</Text>

                        <Accordion variant="separated">
                            <Accordion.Item value="calc">
                                <Accordion.Control>만나이는 어떻게 계산하나요?</Accordion.Control>
                                <Accordion.Panel>만나이는 출생일을 기준으로 생일이 지날 때 1살이 증가합니다. 오늘 날짜가 생일 전이면 전년도 나이가 유지됩니다.</Accordion.Panel>
                            </Accordion.Item>

                            <Accordion.Item value="leap">
                                <Accordion.Control>2월 29일(윤년) 출생은 어떻게 처리하나요?</Accordion.Control>
                                <Accordion.Panel>윤년이 아닌 해에는 통상 2월 28일 또는 3월 1일을 기준으로 간주하는 관행이 있습니다.</Accordion.Panel>
                            </Accordion.Item>

                            <Accordion.Item value="lunar">
                                <Accordion.Control>음력 생일은 지원하나요?</Accordion.Control>
                                <Accordion.Panel>현재 계산기는 양력 기준으로 동작합니다. 음력 생일의 경우 해당 연도의 양력 환산일을 확인한 뒤 입력해 주세요.</Accordion.Panel>
                            </Accordion.Item>

                            <Accordion.Item value="privacy">
                                <Accordion.Control>입력한 생년월일이 서버에 저장되나요?</Accordion.Control>
                                <Accordion.Panel>아니요. 계산은 브라우저 내에서 처리되며, 서버로 전송·저장하지 않습니다.</Accordion.Panel>
                            </Accordion.Item>
                        </Accordion>
                    </Stack>
                </Paper>
            </Container>
        </>
    );
}
