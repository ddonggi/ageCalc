import { createTheme, rem } from '@mantine/core';

export const theme = createTheme({
    primaryColor: 'indigo',
    defaultRadius: 'lg',
    fontFamily: 'var(--font-inter)',
    headings: {
        fontFamily: 'var(--font-inter)',
        fontWeight: '700',
    },
    components: {
        Button: {
            defaultProps: {
                size: 'md',
            },
        },
        Paper: {
            defaultProps: {
                shadow: 'sm',
                withBorder: true,
            },
        },
    },
});
