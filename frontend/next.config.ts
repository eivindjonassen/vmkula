import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n.ts");

const nextConfig: NextConfig = {
	// Firebase Hosting static export configuration
	output: "export",

	// Image optimization for static export
	images: {
		unoptimized: true,
	},
};

export default withNextIntl(nextConfig);
