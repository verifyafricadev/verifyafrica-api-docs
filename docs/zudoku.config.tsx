import type { ZudokuConfig } from "zudoku";

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
	metadata: {
		title: "VerifyAfrica Docs",
		description: "VerifyAfrica API Documentation",
	},
	navigation: [
		{
			type: "category",
			label: "Documentation",
			items: [
				{
					type: "category",
					label: "Getting Started",
					icon: "sparkles",
					items: [
						{
							type: "doc",
							file: "introduction",
						},
						{
							type: "doc",
							file: "markdown",
						},
					],
				},
				{
					type: "category",
					label: "Useful Links",
					collapsible: false,
					icon: "link",
					items: [
						{
							type: "link",
							label: "Zuplo Docs",
							to: "https://zuplo.com/docs/dev-portal/introduction",
						},
						{
							type: "link",
							label: "Developer Portal Docs",
							to: "https://zuplo.com/docs/dev-portal/introduction",
						},
					],
				},
			],
		},
		{
			type: "link",
			to: "/api",
			label: "API Reference",
		},
	],
	redirects: [{ from: "/", to: "/api" }],
	apis: [
		{
			type: "file",
			input: "../config/routes.oas.json",
			path: "api",
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
