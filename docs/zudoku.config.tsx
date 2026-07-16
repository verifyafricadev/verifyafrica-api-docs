import type { ZudokuConfig } from "zudoku";
import { endpointNavigation } from "./endpoint-navigation";
import { seoPlugin } from "./seo-plugin";
import {
	SITE_DESCRIPTION,
	SITE_KEYWORDS,
	SITE_NAME,
	SITE_TITLE,
	SITE_URL,
} from "./site-seo";

/**
 * Developer Portal Configuration
 * For more information, see:
 * https://zuplo.com/docs/dev-portal/zudoku/configuration/overview
 */
const config: ZudokuConfig = {
	site: {
		title: "VerifyAfrica Docs",
		logo: {
			src: {
				light: "/assets/brand/logo-white.svg",
				dark: "/assets/brand/logo-white.svg",
			},
			width: 80,
			alt: "VerifyAfrica",
			href: "/",
		},
	},
	canonicalUrlOrigin: SITE_URL,
	metadata: {
		title: SITE_TITLE,
		defaultTitle:
			"VerifyAfrica: Identity Verification, Compliance Screening & Government Registry API",
		description: SITE_DESCRIPTION,
		favicon: "/assets/brand/logo.svg",
		generator: "Zudoku",
		applicationName: SITE_NAME,
		referrer: "strict-origin-when-cross-origin",
		keywords: SITE_KEYWORDS,
		authors: [SITE_NAME],
		creator: SITE_NAME,
		publisher: SITE_NAME,
		robots: "index, follow",
	},
	plugins: [seoPlugin],
	sitemap: {
		siteUrl: SITE_URL,
		changefreq: "weekly",
		priority: 0.7,
	},
	navigation: endpointNavigation,
	redirects: [{ from: "/", to: "/introduction" }],
	apis: [
		{
			type: "file",
			input: "../config/routes.oas.json",
			path: "api",
		},
	],
	// Show "Get verification detail" as a single root item (no nested folders).
	// OpenAPI would otherwise render tag → operation nesting.
	navigationRules: [
		{
			type: "insert",
			match: "API Reference/0",
			position: "after",
			items: [
				{
					type: "link",
					label: "Get verification detail",
					to: "/api/public-verification-detail",
				},
			],
		},
		{
			type: "remove",
			match: "API Reference/Get verification detail",
		},
	],
	theme: {
		light: {
			primary: "#009688",
			primaryForeground: "#1B263B",
		},
		dark: {
			primary: "#009688",
			primaryForeground: "#1B263B",
		},
	},
};

export default config;
