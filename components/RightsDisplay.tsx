import { Paper, Text, List, ThemeIcon, Group, Anchor, SimpleGrid, Title } from '@mantine/core';
import { rightsData, pensionRights } from '../data/rights';

interface RightsDisplayProps {
    age: number;
    birthYear: number;
}

export function RightsDisplay({ age, birthYear }: RightsDisplayProps) {
    // Filter basic rights
    const availableRights = rightsData.map(right => {
        let isAvailable = false;
        if (right.maxAge) {
            isAvailable = age <= right.age;
        } else {
            isAvailable = age >= right.age;
        }
        return { ...right, isAvailable };
    });

    // Filter pension rights
    let pensionRight = null;
    if (birthYear >= 1953) {
        if (birthYear <= 1956) pensionRight = pensionRights[0];
        else if (birthYear <= 1960) pensionRight = pensionRights[1];
        else if (birthYear <= 1964) pensionRight = pensionRights[2];
        else if (birthYear <= 1968) pensionRight = pensionRights[3];
        else pensionRight = pensionRights[4];
    }

    const allRights = [...availableRights];
    if (pensionRight) {
        const isAvailable = age >= pensionRight.age;
        allRights.push({ ...pensionRight, isAvailable, maxAge: false });
    }

    // Sort by age? Or keep original order? Original order seems grouped by age.
    // We want to show available ones differently?
    // The legacy app showed all, with checkmark or lock.

    return (
        <div style={{ marginTop: '2rem', width: '100%' }}>
            <Title order={3} mb="md" ta="left">🧑 연령별 권리 및 혜택</Title>
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
                {allRights.map((right, index) => (
                    <Group key={index} align="flex-start" wrap="nowrap">
                        <Text size="xl">{right.isAvailable ? '✅' : '🔒'}</Text>
                        <div>
                            <Text size="sm" fw={700} c={right.isAvailable ? 'dark' : 'dimmed'}>
                                {right.maxAge ? `${right.age}세 미만` : `${right.age}세 이상`}
                            </Text>
                            {right.link ? (
                                <Anchor href={right.link} target="_blank" size="sm" c={right.isAvailable ? 'blue' : 'gray'}>
                                    {right.text}
                                </Anchor>
                            ) : (
                                <Text size="sm" c={right.isAvailable ? 'dark' : 'dimmed'}>
                                    {right.text}
                                </Text>
                            )}
                        </div>
                    </Group>
                ))}
            </SimpleGrid>
        </div>
    );
}
