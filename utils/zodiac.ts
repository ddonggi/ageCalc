export interface ZodiacSign {
    animal: string;
    emoji: string;
}

export const zodiacSigns: ZodiacSign[] = [
    { animal: '원숭이', emoji: '🐒' },
    { animal: '닭', emoji: '🐔' },
    { animal: '개', emoji: '🐕' },
    { animal: '돼지', emoji: '🐷' },
    { animal: '쥐', emoji: '🐭' },
    { animal: '소', emoji: '🐂' },
    { animal: '호랑이', emoji: '🐅' },
    { animal: '토끼', emoji: '🐇' },
    { animal: '용', emoji: '🐉' },
    { animal: '뱀', emoji: '🐍' },
    { animal: '말', emoji: '🐎' },
    { animal: '양', emoji: '🐑' }
];

export function getZodiacSign(year: number): ZodiacSign {
    return zodiacSigns[year % 12];
}
