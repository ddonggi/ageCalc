import '@mantine/core/styles.css';
import { ColorSchemeScript, MantineProvider } from '@mantine/core';
import { Footer } from '../components/Footer';
import { CookieConsent } from '../components/CookieConsent';
import { ScrollToTop } from '../components/ScrollToTop';

export const metadata = {
  title: 'Age Calculator',
  description: 'Calculate your precise age in years, months, and days.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider>
          <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            {children}
            <Footer />
          </div>
          <CookieConsent />
          <ScrollToTop />
        </MantineProvider>
      </body>
    </html>
  );
}
