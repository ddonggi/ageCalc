'use client';

import { Container, Title, Text, Stack, Paper, Table } from '@mantine/core';
import { Background3DWrapper } from '../../components/Background3DWrapper';

export default function GuidePage() {
    return (
        <>
            <Background3DWrapper />
            <Container size="sm" py="xl">
                <Paper p="xl" radius="lg" style={{ background: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(10px)' }}>
                    <Stack gap="lg">
                        <Title order={1}>만나이 가이드</Title>
                        <Text>2023년 법 개정으로 통일된 만나이 제도와 계산 방법을 정리했습니다.</Text>

                        <Title order={2} size="h3">만나이란?</Title>
                        <Text>
                            만나이는 태어난 날을 기준으로 생일이 지날 때만 나이가 증가하는 방식입니다.<br />
                            예를 들어 1992년 10월 2일에 태어났다면, 2023년 10월 1일에는 만 30세, 10월 2일 생일이 지나면 만 31세가 됩니다.
                        </Text>

                        <Title order={2} size="h3">왜 만나이로 통일되었을까?</Title>
                        <Text>
                            대한민국에서는 과거에 한국식 나이, 연 나이, 만나이가 혼용되어 혼란이 많았습니다.
                            이에 따라 2023년 6월 28일부로 모든 공적 영역에서 만나이 기준이 공식 채택되었습니다.
                        </Text>

                        <Title order={2} size="h3">다른 나이 계산 방식과 비교</Title>
                        <Table>
                            <Table.Thead>
                                <Table.Tr>
                                    <Table.Th>구분</Table.Th>
                                    <Table.Th>정의</Table.Th>
                                </Table.Tr>
                            </Table.Thead>
                            <Table.Tbody>
                                <Table.Tr>
                                    <Table.Td>만나이</Table.Td>
                                    <Table.Td>생일이 지나야 1살 증가 (국제 표준)</Table.Td>
                                </Table.Tr>
                                <Table.Tr>
                                    <Table.Td>연 나이</Table.Td>
                                    <Table.Td>올해 − 출생연도 (일부 행정상 편의)</Table.Td>
                                </Table.Tr>
                                <Table.Tr>
                                    <Table.Td>한국식 나이(폐지)</Table.Td>
                                    <Table.Td>태어나면 1세, 해마다 1월 1일에 증가</Table.Td>
                                </Table.Tr>
                            </Table.Tbody>
                        </Table>
                    </Stack>
                </Paper>
            </Container>
        </>
    );
}
