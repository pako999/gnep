import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
    title: 'GNEP - AI Real Estate Locator',
    description: 'Automatically match real estate listings with GURS cadastral data using AI',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="sl">
            <body>{children}</body>
        </html>
    )
}
