'use client';

import { useState, useEffect } from 'react';
import { Dialog, Text, Button, Group } from '@mantine/core';

export function CookieConsent() {
    const [opened, setOpened] = useState(false);

    useEffect(() => {
        const consent = localStorage.getItem('cookie-consent');
        if (!consent) {
            setOpened(true);
        }
    }, []);

    const handleAccept = () => {
        localStorage.setItem('cookie-consent', 'accepted');
        setOpened(false);
    };

    const handleDecline = () => {
        localStorage.setItem('cookie-consent', 'declined');
        setOpened(false);
    };

    return (
        <Dialog
            opened={opened}
            withCloseButton
            onClose={() => setOpened(false)}
            size="lg"
            radius="md"
            style={{
                backgroundColor: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.15)'
            }}
        >
            <Text size="sm" mb="xs" fw={700} c="indigo.9">
                🍪 쿠키 사용 안내
            </Text>
            <Text size="xs" c="dimmed" mb="md">
                이 사이트는 사용자 경험 개선을 위해 쿠키를 사용합니다.
            </Text>
            <Group align="flex-end" justify="flex-end">
                <Button variant="subtle" color="gray" onClick={handleDecline} size="xs">거부</Button>
                <Button variant="light" color="indigo" onClick={handleAccept} size="xs">승인</Button>
            </Group>
        </Dialog>
    );
}
