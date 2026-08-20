import type { Metadata } from 'next';
import '@/styles/globals.css';
import { Navbar } from '@/components/shared/Navbar';
import { Sidebar } from '@/components/shared/Sidebar';
import styles from '@/styles/dashboard.module.css';

export const metadata: Metadata = {
  title: 'Pulse | AI Discovery Engine',
  description:
    'AI-powered qualitative discovery and batch analytics engine diagnosing wishlist drop-off and uncovering non-monetary conversion levers.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <div className={styles.layout}>
          <Sidebar />
          <div className={styles.mainContent}>
            <Navbar />
            <main>{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
