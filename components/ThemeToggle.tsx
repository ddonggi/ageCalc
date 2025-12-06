'use client';

import { ActionIcon, useMantineColorScheme, useComputedColorScheme, Group } from '@mantine/core';

export function ThemeToggle() {
    const { setColorScheme } = useMantineColorScheme();
    const computedColorScheme = useComputedColorScheme('light', { getInitialValueInEffect: true });

    return (
        <Group justify="center">
            <ActionIcon
                onClick={() => setColorScheme(computedColorScheme === 'light' ? 'dark' : 'light')}
                variant="default"
                size="lg"
                aria-label="Toggle color scheme"
                radius="xl"
            >
                {computedColorScheme === 'light' ? '🌙' : '☀️'}
            </ActionIcon>
        </Group>
    );
}
