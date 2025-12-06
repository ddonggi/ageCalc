'use client';

import { useWindowScroll } from '@mantine/hooks';
import { Affix, Button, Transition, rem } from '@mantine/core';

export function ScrollToTop() {
    const [scroll, scrollTo] = useWindowScroll();

    return (
        <Affix position={{ bottom: 20, right: 20 }}>
            <Transition transition="slide-up" mounted={scroll.y > 0}>
                {(transitionStyles) => (
                    <Button
                        leftSection="↑"
                        style={transitionStyles}
                        onClick={() => scrollTo({ y: 0 })}
                        variant="light"
                        color="indigo"
                        size="md"
                        radius="xl"
                    >
                        Top
                    </Button>
                )}
            </Transition>
        </Affix>
    );
}
