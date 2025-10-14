import "./globals.css";

export const metadata = {
  title: "Intraday Co-Pilot",
  description: "Live-only intraday console",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
