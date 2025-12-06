'use client';

import { AgeCalculator } from '../components/AgeCalculator';
import { Center, Box, Container } from '@mantine/core';
import { Background3DWrapper } from '../components/Background3DWrapper';
import { LegacyContent } from '../components/LegacyContent';

export default function Home() {
  return (
    <>
      <Background3DWrapper />
      <Box style={{ position: 'relative', zIndex: 1 }}>
        <Container size="sm" py="xl">
          <AgeCalculator />
          <LegacyContent />
        </Container>
      </Box>
    </>
  );
}
