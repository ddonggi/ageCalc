'use client';

import { useState, useRef } from 'react';
import { Paper, Title, TextInput, Button, Text, Stack, Container, Transition, SegmentedControl, Group, MantineProvider, useComputedColorScheme } from '@mantine/core';
import { calculateAge } from '../utils/calculateAge';
import { convertLunarToSolar } from '../utils/lunar';
import { getZodiacSign } from '../utils/zodiac';
import { RightsDisplay } from './RightsDisplay';
import { ThemeToggle } from './ThemeToggle';
import html2canvas from 'html2canvas';

export function AgeCalculator() {
    const [birthInput, setBirthInput] = useState('');
    const [calendarType, setCalendarType] = useState('solar');
    const [age, setAge] = useState<number | null>(null);
    const [zodiac, setZodiac] = useState<{ animal: string; emoji: string } | null>(null);
    const [birthYear, setBirthYear] = useState<number | null>(null);
    const [error, setError] = useState('');
    const resultRef = useRef<HTMLDivElement>(null);
    const computedColorScheme = useComputedColorScheme('light', { getInitialValueInEffect: true });
    const isDark = computedColorScheme === 'dark';

    const parseYYMMDD = (input: string): Date | null => {
        if (!/^\d{6}$/.test(input)) return null;
        const yy = parseInt(input.substring(0, 2));
        const mm = parseInt(input.substring(2, 4));
        const dd = parseInt(input.substring(4, 6));

        const currentYear = new Date().getFullYear();
        const currentYY = currentYear % 100;

        let year = (yy <= currentYY) ? 2000 + yy : 1900 + yy;

        const date = new Date(year, mm - 1, dd);
        if (date.getMonth() + 1 !== mm || date.getDate() !== dd) return null;

        return date;
    };

    const calculate = (input: string, type: string) => {
        const date = parseYYMMDD(input);
        if (!date) {
            setAge(null);
            setZodiac(null);
            setBirthYear(null);
            setError('Invalid date format (YYMMDD)');
            return;
        }

        let targetDate = date;
        let year = date.getFullYear();
        let month = date.getMonth() + 1;
        let day = date.getDate();

        if (type === 'lunar') {
            try {
                const solar = convertLunarToSolar(year, month, day);
                targetDate = new Date(solar.year, solar.month - 1, solar.day);
            } catch (e) {
                setError('Invalid Lunar Date');
                return;
            }
        }

        const calculatedAge = calculateAge(targetDate);
        setAge(calculatedAge);
        setBirthYear(year);
        setZodiac(getZodiacSign(year));
        setError('');
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.currentTarget.value.replace(/[^0-9]/g, '').slice(0, 6);
        setBirthInput(val);

        if (val.length === 6) {
            calculate(val, calendarType);
        } else {
            setAge(null);
            setZodiac(null);
            setBirthYear(null);
            setError('');
        }
    };

    const handleCalendarTypeChange = (val: string) => {
        setCalendarType(val);
        if (birthInput.length === 6) {
            calculate(birthInput, val);
        }
    };

    const handleShare = async () => {
        const url = window.location.href;
        const text = age !== null ? `I am ${age} years old! Check yours at Age Calculator` : 'Check your precise age!';

        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Age Calculator',
                    text: text,
                    url: url,
                });
            } catch (err) {
                console.log('Share failed', err);
            }
        } else {
            navigator.clipboard.writeText(`${text} ${url}`);
            alert('Link copied to clipboard!');
        }
    };

    const handleSaveImage = async () => {
        if (resultRef.current) {
            try {
                const canvas = await html2canvas(resultRef.current, {
                    backgroundColor: '#ffffff',
                    scale: 2,
                });
                const link = document.createElement('a');
                link.download = `age-result-${new Date().toISOString().split('T')[0]}.png`;
                link.href = canvas.toDataURL();
                link.click();
            } catch (err) {
                console.error('Failed to save image', err);
                alert('Failed to save image');
            }
        }
    };

    const glassStyle = {
        backgroundColor: isDark ? 'rgba(0, 0, 0, 0.3)' : 'rgba(255, 255, 255, 0.25)',
        backdropFilter: 'blur(20px)',
        border: isDark ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(255, 255, 255, 0.3)',
        boxShadow: isDark ? '0 8px 32px 0 rgba(0, 0, 0, 0.3)' : '0 8px 32px 0 rgba(31, 38, 135, 0.15)'
    };

    return (
        <Container size="sm">
            <Group justify="flex-end" mb="md">
                <ThemeToggle />
            </Group>
            <Paper
                shadow="xl"
                p="xl"
                radius="lg"
                withBorder
                style={glassStyle}
            >
                <Stack gap="lg">
                    <Title order={1} ta="center" c={isDark ? 'indigo.3' : 'indigo'} style={{ textShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                        Age Calculator
                    </Title>

                    <SegmentedControl
                        value={calendarType}
                        onChange={handleCalendarTypeChange}
                        data={[
                            { label: 'Solar (양력)', value: 'solar' },
                            { label: 'Lunar (음력)', value: 'lunar' },
                        ]}
                        w="auto"
                        maw={300}
                        mx="auto"
                        radius="md"
                        color="indigo"
                        style={{ backgroundColor: isDark ? 'rgba(0, 0, 0, 0.3)' : 'rgba(255, 255, 255, 0.5)' }}
                    />

                    <TextInput
                        label="Date of Birth (생년월일 6자리)"
                        placeholder="예: 921002"
                        size="xl"
                        radius="md"
                        value={birthInput}
                        onChange={handleInputChange}
                        error={error}
                        maxLength={6}
                        styles={{
                            input: {
                                textAlign: 'center',
                                fontSize: '1.5rem',
                                letterSpacing: '0.2em',
                                backgroundColor: isDark ? 'rgba(0, 0, 0, 0.3)' : 'rgba(255, 255, 255, 0.5)',
                                backdropFilter: 'blur(5px)',
                                color: isDark ? '#fff' : undefined
                            },
                            label: {
                                color: isDark ? '#ddd' : undefined
                            }
                        }}
                    />
                </Stack>
            </Paper>

            <Transition mounted={age !== null} transition="fade" duration={400}>
                {(styles) => (
                    <div style={{ ...styles }}>
                        <Paper
                            p="xl"
                            radius="lg"
                            mt="xl"
                            ref={resultRef as React.RefObject<HTMLDivElement>}
                            style={{
                                backgroundColor: isDark ? 'rgba(0, 0, 0, 0.4)' : 'rgba(255, 255, 255, 0.3)',
                                backdropFilter: 'blur(15px)',
                                border: isDark ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(255, 255, 255, 0.4)',
                                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)'
                            }}
                        >
                            <Stack align="center" gap="md">
                                <Text size="lg" fw={500} c={isDark ? 'dimmed' : 'dimmed'}>만나이</Text>
                                <Text size="6rem" fw={900} style={{ lineHeight: 1, color: isDark ? '#fff' : '#4c6ef5' }}>
                                    {age}세
                                </Text>

                                {zodiac && (
                                    <Group gap="xs" mt="sm">
                                        <Text size="2rem">{zodiac.emoji}</Text>
                                        <Text size="xl" fw={500} c={isDark ? 'gray.3' : 'gray.7'}>
                                            {birthYear}년생 ({zodiac.animal}띠)
                                        </Text>
                                    </Group>
                                )}

                                {age !== null && birthYear !== null && (
                                    <RightsDisplay age={age} birthYear={birthYear} />
                                )}

                                <Group justify="center" gap="md" mt="xl">
                                    <Button variant="light" color="indigo" size="lg" onClick={handleShare} leftSection="🔗">
                                        공유하기
                                    </Button>
                                    <Button variant="light" color="indigo" size="lg" onClick={handleSaveImage} leftSection="📸">
                                        이미지 저장
                                    </Button>
                                </Group>
                            </Stack>
                        </Paper>
                    </div>
                )}
            </Transition>
        </Container>
    );
}
