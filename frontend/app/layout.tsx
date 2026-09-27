import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Water Can Delivery",
  description: "Order fresh drinking water delivered to your door.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
