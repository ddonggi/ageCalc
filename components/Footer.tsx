'use client';

import { Container, Group, Anchor, Text, Stack } from '@mantine/core';
import Link from 'next/link';

export function Footer() {
    return (
        <footer style={{ marginTop: 'auto', padding: '2rem 0' }}>
            <Container size="sm">
                <Stack align="center" gap="xs">
                    <Text size="sm" c="dimmed">문의: ldg6153@gmail.com</Text>
                    <Group gap="xs">
                        <Anchor component={Link} href="/privacy" size="sm" c="dimmed">개인정보처리방침</Anchor>
                        <Text size="sm" c="dimmed">|</Text>
                        <Anchor component={Link} href="/terms" size="sm" c="dimmed">이용약관</Anchor>
                        <Text size="sm" c="dimmed">|</Text>
                        <Anchor component={Link} href="/guide" size="sm" c="dimmed">만나이 가이드</Anchor>
                        <Text size="sm" c="dimmed">|</Text>
                        <Anchor component={Link} href="/faq" size="sm" c="dimmed">자주 묻는 질문</Anchor>
                    </Group>
                    <Text size="xs" c="dimmed" mt="md">
                        &copy; 2025 만나이 계산기. All rights reserved.
                    </Text>
                </Stack>
            </Container>
        </footer>
    );
}
